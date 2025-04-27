from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import pool
from datetime import datetime
import logging
import urllib.parse
from flask_mail import Mail, Message

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave_secreta_padrao")  # Necessário para flash messages

# Configuração do Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Servidor SMTP (exemplo: Gmail)
app.config['MAIL_PORT'] = 587  # Porta do servidor SMTP
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")  # E-mail do remetente
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")  # Senha do e-mail do remetente

mail = Mail(app)

# Obter variáveis de ambiente
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Pool de conexões para gerenciar conexões com o banco de dados
try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        5,  # minconn
        20, # maxconn
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )
    logger.info("Pool de conexões inicializado com sucesso!")
except Exception as e:
    logger.error(f"Erro ao inicializar o pool de conexões: {e}")
    connection_pool = None

# Cache em memória (em vez de Redis)
cache_participantes = None
cache_presentes_disponiveis = None

def get_db_connection():
    """Obtém uma conexão do pool e retorna a conexão e o cursor"""
    if connection_pool:
        try:
            conn = connection_pool.getconn()
            cursor = conn.cursor()
            return conn, cursor
        except Exception as e:
            logger.error(f"Erro ao obter conexão do pool: {e}")
            return None, None
    return None, None

def release_db_connection(conn):
    """Devolve a conexão ao pool"""
    if connection_pool and conn:
        connection_pool.putconn(conn)

@app.route('/')
def index():
    global cache_participantes, cache_presentes_disponiveis
    conn, cursor = get_db_connection()
    participantes = []
    presentes_disponiveis = []
    participante_id = None  # Inicialize o participante_id como None
    
    try:
        if cursor:
            # Consultar participantes
            cursor.execute("SELECT id, nome, confirmado, presente, data_confirmacao FROM participante;")
            participantes = cursor.fetchall()

            # Obter os presentes já selecionados
            cursor.execute("SELECT DISTINCT presente FROM participante WHERE presente IS NOT NULL")
            presentes_selecionados = [row[0] for row in cursor.fetchall()]

            # Consultar presentes disponíveis
            cursor.execute("SELECT nome FROM presentes WHERE disponivel = TRUE;")
            todos_presentes = [row[0] for row in cursor.fetchall()]

            # Filtrar os presentes disponíveis removendo os já selecionados
            presentes_disponiveis = [p for p in todos_presentes if p not in presentes_selecionados]

            # Exemplo: Defina um participante_id fictício para testes
            if participantes:
                participante_id = participantes[0][0]  # Pegue o ID do primeiro participante

            # Armazenar em cache na memória
            cache_participantes = participantes
            cache_presentes_disponiveis = presentes_disponiveis
        else:
            print("Não foi possível conectar ao banco de dados. Tente novamente mais tarde.", "error")
    except Exception as e:
        logger.error(f"Erro ao consultar dados: {e}")
        print(f"Ocorreu um erro ao carregar os dados. Por favor, tente novamente.", "error")
    finally:
        release_db_connection(conn)

    return render_template('index.html', participantes=participantes, disponiveis=presentes_disponiveis, participante_id=participante_id)

def flash_with_logging(message, category="message"):
    """Função personalizada para registrar mensagens de flash no terminal."""
    logger.info(f"Flash message - Categoria: {category}, Mensagem: {message}")
    flash(message, category)

def enviar_email_confirmacao(email, nome, confirmado, quantidade_pessoas, presente, forma_presente):
    try:
        assunto = "Confirmação de Presença - 15 Anos da Ana"
        corpo_texto = f"""
        Olá, {nome}!
        
        Obrigado por confirmar sua presença no aniversário de 15 anos da Ana.

        Detalhes da sua confirmação:
        - Presença: {'Sim' if confirmado == 'sim' else 'Não'}
        - Quantidade de pessoas: {quantidade_pessoas or 'N/A'}
        - Presente: {presente or 'N/A'}
        - Forma de presente: {forma_presente.capitalize()}

        Informações da festa:
        - Data: 14 de junho de 2025
        - Horário: 20:00
        - Local: Bouganville Hall, Av. Comandante Petit, 263 - Centro, Parnamirim - RN
        - Link para o local no Google Maps: https://maps.google.com/?q=Av.+Comandante+Petit,+263+-+Centro,+Parnamirim+-+RN

        Estamos ansiosos para celebrar com você!

        Atenciosamente,
        Organização do Evento
        """

        corpo_html = f"""
        <html>
        <body>
            <h2>Olá, {nome}!</h2>
            <p>Obrigado por confirmar sua presença no aniversário de 15 anos da Ana.</p>
            <p><strong>Detalhes da sua confirmação:</strong></p>
            <ul>
                <li><strong>Presença:</strong> {'Sim' if confirmado == 'sim' else 'Não'}</li>
                <li><strong>Quantidade de pessoas:</strong> {quantidade_pessoas or 'N/A'}</li>
                <li><strong>Presente:</strong> {presente or 'N/A'}</li>
                <li><strong>Forma de presente:</strong> {forma_presente.capitalize()}</li>
            </ul>
            {"<div style='margin-top: 20px;'><p>Você escolheu pagar via Pix. Clique no botão abaixo para acessar as informações de pagamento:</p><a href='https://15anos.vercel.app/pix' style='display: inline-block; padding: 10px 20px; background-color: #007bff; color: #fff; text-decoration: none; border-radius: 5px;'>Ir para a página de Pix</a></div>" if forma_presente == "pix" else ""}
            <p><strong>Informações da festa:</strong></p>
            <ul>
                <li><strong>Data:</strong> 14 de junho de 2025</li>
                <li><strong>Horário:</strong> 20:00</li>
                <li><strong>Local:</strong> Bouganville Hall, Av. Comandante Petit, 263 - Centro, Parnamirim - RN</li>
                <li><strong>Link para o local no Google Maps:</strong> <a href="https://maps.google.com/?q=Av.+Comandante+Petit,+263+-+Centro,+Parnamirim+-+RN" target="_blank">Clique aqui</a></li>
            </ul>
            <p>Estamos ansiosos para celebrar com você!</p>
            <p>Atenciosamente,<br>Organização do Evento</p>
        </body>
        </html>
        """

        msg = Message(
            assunto,
            sender=app.config['MAIL_USERNAME'],
            recipients=[email],
            reply_to=app.config['MAIL_USERNAME']
        )
        msg.body = corpo_texto
        msg.html = corpo_html  # Adiciona a versão HTML
        msg.headers = {'X-Mailer': 'Convite15Anos'}
        mail.send(msg)
        logger.info(f"E-mail enviado com sucesso para {email}")
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail para {email}: {e}")

@app.route('/confirmar', methods=['POST'])
def confirmar():
    # Obter dados do formulário
    nome_submetido = request.form.get('nome')
    email = request.form.get('email')  # Capturar o e-mail
    confirmado_status = request.form.get('confirmado')
    quantidade_pessoas = request.form.get('quantidade_pessoas')
    presente_selecionado = request.form.get('presente')
    forma_presente = request.form.get('forma_presente')

    logger.info(f"Recebido - Nome: '{nome_submetido}', E-mail: '{email}', Status Confirmação: '{confirmado_status}', "
                f"Quantidade de Pessoas: '{quantidade_pessoas}', Presente: '{presente_selecionado}', "
                f"Forma Presente: '{forma_presente}'")

    # Validações básicas
    if not nome_submetido or not email:
        flash("Por favor, informe seu nome completo e e-mail.", "error")
        return redirect(request.referrer or url_for('index') + "#formConfirmacao")

    conn, cursor = get_db_connection()
    if not conn or not cursor:
        flash("Erro ao conectar ao banco de dados. Tente novamente.", "error")
        return redirect(url_for('index') + "#formConfirmacao")

    try:
        agora = datetime.now()
        is_pix = forma_presente == "pix"
        presente_db = None if is_pix else presente_selecionado

        if confirmado_status == 'sim':
            # Inserir no banco de dados
            cursor.execute("""
                INSERT INTO participante (nome, email, confirmado, quantidade_pessoas, presente, data_confirmacao, pix)
                VALUES (%s, %s, TRUE, %s, %s, %s, %s);
            """, (nome_submetido, email, quantidade_pessoas, presente_db, agora, is_pix))
            conn.commit()

            # Enviar e-mail de confirmação
            enviar_email_confirmacao(email, nome_submetido, confirmado_status, quantidade_pessoas, presente_selecionado, forma_presente)

            if is_pix:
                flash("Presença confirmada! Não se esqueça de enviar o comprovante do Pix para que possamos registrar seu pagamento.", "success")
                return redirect(url_for('pix'))
            else:
                flash("Sua presença foi confirmada com sucesso!", "success")

        elif confirmado_status == 'nao':
            cursor.execute("""
                INSERT INTO participante (nome, email, confirmado, quantidade_pessoas, presente, data_confirmacao, pix)
                VALUES (%s, %s, FALSE, NULL, NULL, %s, FALSE);
            """, (nome_submetido, email, agora))
            conn.commit()
            flash("Resposta registrada. Que pena que não poderá comparecer!", "info")

    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao processar confirmação: {e}")
        flash("Ocorreu um erro ao processar sua confirmação.", "error")
    finally:
        release_db_connection(conn)

    return redirect(url_for('index') + "#formConfirmacao")

@app.route('/confirmados')
def confirmados():
    global cache_participantes, cache_presentes_disponiveis
    participantes_confirmados = cache_participantes
    presentes_disponiveis = cache_presentes_disponiveis

    if not participantes_confirmados or not presentes_disponiveis:
        conn, cursor = get_db_connection()
        try:
            if cursor:
                cursor.execute("SELECT id, nome, confirmado, presente, data_confirmacao FROM participante WHERE confirmado = TRUE LIMIT 50;")
                participantes_confirmados = cursor.fetchall()

                cursor.execute("SELECT nome FROM presentes WHERE disponivel = TRUE LIMIT 10;")
                presentes_disponiveis = [row[0] for row in cursor.fetchall()]

                # Armazenar os resultados em cache na memória
                cache_participantes = participantes_confirmados
                cache_presentes_disponiveis = presentes_disponiveis
        except Exception as e:
            logger.error(f"Erro ao consultar dados: {e}")
            flash(f"Ocorreu um erro ao carregar os dados. Por favor, tente novamente.", "error")
        finally:
            release_db_connection(conn)

    return render_template('confirmados.html', participantes=participantes_confirmados, disponiveis=presentes_disponiveis)


@app.route('/calendar-link')
def calendar_link():
    try:
        event_title = urllib.parse.quote("15 anos de Ana Beatriz🥳🎉")
        location = urllib.parse.quote("Av. Comandante Petit, 263 - Centro, Parnamirim - RN")
        details = urllib.parse.quote("Venha comemorar comigo!")
        start = '20250614T230000Z'
        end = '20250615T025900Z'
        link = f"https://www.google.com/calendar/render?action=TEMPLATE&text={event_title}&dates={start}/{end}&details={details}&location={location}&sf=true&output=xml"

        # Adicionar o endereço automaticamente ao evento
        return redirect(link)
    except Exception as e:
        logger.error(f"Erro ao gerar link do calendário: {e}")
        flash("Não foi possível gerar o link para o calendário.", "error")
        return redirect(url_for('index'))


@app.route('/pix')
def pix():
    chave_pix = "84 98621-8388"  # Substitua pela chave Pix real
    numero_whatsapp = "+5584986218388"  # Substitua pelo número real
    return render_template('pix.html', chave_pix=chave_pix, numero_whatsapp=numero_whatsapp)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Função para fechar o pool de conexões quando a aplicação for encerrada
def close_pool():
    try:
        if connection_pool:
            connection_pool.closeall()
    except Exception as e:
        logger.error(f"Erro ao fechar o pool de conexões: {e}")

def reconnect_pool():
    global connection_pool
    if connection_pool is None or connection_pool.closed:
        # Criar o pool novamente
        connection_pool = psycopg2.pool.SimpleConnectionPool(minconn=1, maxconn=10, user='user', password='password', host='localhost', database='mydb')


# Renomear para 'application' como esperado pelo Vercel
application = app

if __name__ == '__main__':
    app.run(debug=True, port=4800)
