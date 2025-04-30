from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import pool
from datetime import datetime
import logging
import urllib.parse
from flask_mail import Mail, Message
from email.mime.image import MIMEImage
from io import BytesIO

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
    conn, cursor = get_db_connection()
    participantes = []
    presentes_disponiveis = []
    participante_id = None
    presentes_info = {}

    try:
        if cursor:
            cursor.execute("""
                SELECT nome, quantidade_maxima, quantidade_reservada, imagem_url, link_compra
                  FROM presentes
                 WHERE disponivel = TRUE
                   AND (quantidade_reservada < quantidade_maxima)
            """)
            todos_presentes = cursor.fetchall()
            presentes_disponiveis = [row[0] for row in todos_presentes]
            presentes_info = {row[0]: {'max': row[1], 'reservado': row[2], 'imagem_url': row[3], 'link_compra': row[4]} for row in todos_presentes}
            cursor.execute("SELECT id, nome, confirmado, presente, data_confirmacao FROM participante;")
            participantes = cursor.fetchall()
            if participantes:
                participante_id = participantes[0][0]
            # Ordena alfabeticamente
            presentes_disponiveis = sorted(presentes_disponiveis)
        else:
            flash("Não foi possível conectar ao banco de dados. Tente novamente mais tarde.", "error")
    except Exception as e:
        logger.error(f"Erro ao consultar dados: {e}")
        flash("Ocorreu um erro ao carregar os dados. Por favor, tente novamente.", "error")
    finally:
        if cursor: cursor.close()
        release_db_connection(conn)

    return render_template(
        'index.html',
        participantes=participantes,
        disponiveis=presentes_disponiveis,
        presentes_info=presentes_info,
        participante_id=participante_id
    )

def flash_with_logging(message, category="message"):
    """Função personalizada para registrar mensagens de flash no terminal."""
    logger.info(f"Flash message - Categoria: {category}, Mensagem: {message}")
    flash(message, category)

def enviar_email_confirmacao(email, nome, confirmado, quantidade_pessoas, presente, forma_presente):
    try:
        # Referências para presentes específicos
        referencias_presentes = {

        }

        # Buscar imagem e link de compra do presente no banco
        img_url = None
        link_compra = None
        if presente:
            conn, cursor = get_db_connection()
            if cursor:
                cursor.execute("SELECT imagem_url, link_compra FROM presentes WHERE nome = %s", (presente,))
                row = cursor.fetchone()
                if row:
                    img_url = row[0]
                    link_compra = row[1]
                cursor.close()
                release_db_connection(conn)

        # Detalhes do e-mail
        assunto = "Confirmação de Presença - 15 Anos da Ana"
        corpo_texto = f"""
        Olá, {nome}!
        
        Obrigado por confirmar sua presença no aniversário de 15 anos da Ana.

        Detalhes da sua confirmação:
        - Presença: {'Sim' if confirmado == 'sim' else 'Não'}
        - Quantidade de pessoas: {quantidade_pessoas or 'N/A'}
        {"- Presente: " + (presente or 'N/A') if forma_presente != "pix" else ""}
        - Forma de presente: {forma_presente.capitalize()}
        {"\n" + referencias_presentes.get(presente, "") if presente in referencias_presentes else ""}
        {f"\nRecomendação de compra: {link_compra}\n(A compra pelo site é opcional, serve apenas como indicação para facilitar sua escolha.)" if link_compra else ""}

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
        <body style="font-family: 'Open Sans', Arial, sans-serif; background: #f8f9fa; color: #333; padding: 0; margin: 0;">
            <div style="max-width: 600px; margin: 30px auto; background: #fff; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.10); padding: 32px 28px;">
                <div style="text-align: center;">
                    <h1 style="font-family: 'Great Vibes', cursive; color: #ff69b4; font-size: 2.5rem; margin-bottom: 0.5rem;">
                        Convite Oficial - 15 Anos de Ana Beatriz
                    </h1>
                    <h2 style="font-size: 1.3rem; font-weight: 600; margin-bottom: 0.5rem; color: #333;">
                        Você está convidado para uma noite inesquecível!
                    </h2>
                    <p style="font-size: 1.1rem; color: #888; margin-bottom: 0.5rem;">
                        <b>Data:</b> 14 de junho de 2025<br>
                        <b>Horário:</b> 20:00<br>
                        <b>Local:</b> Bouganville Hall<br>
                        Av. Comandante Petit, 263 - Centro, Parnamirim - RN
                    </p>
                    <a href="https://maps.google.com/?q=Av.+Comandante+Petit,+263+-+Centro,+Parnamirim+-+RN" target="_blank"
                        style="display:inline-block; margin-bottom: 0.7rem; color: #fff; background: #ff69b4; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                        Ver no Google Maps
                    </a>
                    <a href="https://15anos.vercel.app/calendar-link" target="_blank"
                        style="display:inline-block; margin-left: 0.5rem; margin-bottom: 1.2rem; color: #fff; background: #007bff; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                        Adicionar à Agenda
                    </a>
                </div>
                <hr style="margin: 1.5rem 0;">
                <p style="font-size: 1.1rem; text-align: center;">
                    <strong>Olá, {nome}!</strong><br>
                    Obrigada por confirmar sua presença no meu aniversário de 15 anos.<br>
                    <span style="color: #ff69b4;">Sua presença é muito importante para mim!</span>
                </p>
                <div style="background: #ffe6f3; border-radius: 10px; padding: 1.2rem 1rem; margin: 1.5rem 0;">
                    <h3 style="color: #ff69b4; font-size: 1.2rem; margin-bottom: 0.7rem;">Seus dados de confirmação:</h3>
                    <ul style="list-style: none; padding: 0; font-size: 1.05rem; text-align:left;">
                        <li><b>Presença:</b> {'Sim' if confirmado == 'sim' else 'Não'}</li>
                        <li><b>Quantidade de pessoas:</b> {quantidade_pessoas or 'N/A'}</li>
                        {f"<li><b>Presente:</b> {presente or 'N/A'}</li>" if forma_presente != "pix" else ""}
                        <li><b>Forma de presente:</b> {forma_presente.capitalize()}</li>
                    </ul>
                    {"<p style='margin: 0.7rem 0 0 0;'><b>Referência do presente:</b> " + referencias_presentes.get(presente, "") + "</p>" if presente in referencias_presentes else ""}
                    {f"<p style='margin: 0.7rem 0 0 0;'><b>Recomendação de compra:</b> <a href='{link_compra}' target='_blank' style='color:#7c43bd; text-decoration:underline;'>{link_compra}</a><br><span style='font-size:0.95em;color:#555;'>(A compra pelo site é opcional, serve apenas como indicação para facilitar sua escolha.)</span></p>" if link_compra else ""}
                    {"<div style='margin-top: 1.2rem; background: #fff3cd; border-radius: 8px; padding: 0.8rem; color: #856404;'><b>Você escolheu Pix.</b> Clique no botão abaixo para acessar as informações de pagamento <span style='font-weight:bold; color:#d35400;'>(caso não tenha feito anteriormente)</span>:<br><a href='https://15anos.vercel.app/pix' style='display: inline-block; margin-top: 0.7rem; padding: 8px 18px; background-color: #007bff; color: #fff; text-decoration: none; border-radius: 6px;'>Ir para a página de Pix</a></div>" if forma_presente == "pix" else ""}
                    {f"<div style='margin-top: 1.2rem;'><b>Imagem do presente escolhido:</b><br><img src='{img_url}' alt='{presente}' style='max-width:180px; border-radius: 8px; margin-top: 0.5rem;'></div>" if img_url else ""}
                </div>
                <div style="margin: 1.5rem 0;">
                    <h3 style="color: #ff69b4; font-size: 1.2rem;">Informações importantes para o evento:</h3>
                    <ul style="font-size: 1.05rem; padding-left: 1.2rem; text-align:left;">
                        <li><b>Confirmação:</b> Confirme sua presença até <b>01/06/2025</b>.</li>
                        <li><b>Traje:</b> Esporte Fino (evite roupas nas cores <b>rosa</b> e <b>lilás</b> para manter a harmonia da festa).</li>
                        <li><b>Presentes:</b> Escolha um presente na lista do site ou contribua via Pix. A compra do presente é por sua conta.</li>
                        <li><b>Ajuda:</b> Se tiver dúvidas, fale com o(a) responsável pela festapelo WhatsApp: <b>(84) 98795-5400</b>.</li>
                        <li><b>E-mail:</b> Após confirmar, verifique sua caixa de entrada e também o spam/lixo eletrônico para garantir que recebeu todas as informações.</li>
                        <li><b>Endereço:</b> Av. Comandante Petit, 263 - Centro, Parnamirim - RN (<a href="https://maps.google.com/?q=Av.+Comandante+Petit,+263+-+Centro,+Parnamirim+-+RN" target="_blank">Ver no mapa</a>)</li>
                        <li><b>Horário:</b> Chegue com antecedência para não perder nenhum momento especial!</li>
                    </ul>
                </div>
                <div style="background: #f8f9fa; border-radius: 10px; padding: 1.1rem 1rem; margin-bottom: 1.5rem;">
                    <b>Dica:</b> Guarde este e-mail, pois ele contém todas as informações necessárias para a festa e para sua participação.<br>
                    <b>Se não encontrar este e-mail na caixa de entrada, procure no spam/lixo eletrônico.</b>
                </div>
                <div style="text-align: center; margin-top: 2rem;">
                    <p style="font-size: 1.1rem; color: #888;">
                        Com carinho,<br>
                        <span style="color: #ff69b4; font-family: 'Great Vibes', cursive; font-size: 1.5rem;">Ana Beatriz</span>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        # Criar a mensagem de e-mail
        msg = Message(
            assunto,
            sender=app.config['MAIL_USERNAME'],
            recipients=[email],
            reply_to=app.config['MAIL_USERNAME']
        )
        msg.body = corpo_texto
        msg.html = corpo_html

        # Enviar e-mail
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

            if presente_db:
                cursor.execute(
                    "UPDATE presentes SET quantidade_reservada = quantidade_reservada + 1 WHERE nome = %s;",
                    (presente_db,)
                )
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
    conn, cursor = get_db_connection()
    participantes_confirmados = []
    presentes_disponiveis = []
    try:
        if cursor:
            cursor.execute("SELECT id, nome, confirmado, presente, data_confirmacao FROM participante WHERE confirmado = TRUE ORDER BY data_confirmacao DESC LIMIT 50;")
            participantes_confirmados = cursor.fetchall()
            cursor.execute("SELECT nome FROM presentes WHERE disponivel = TRUE LIMIT 10;")
            presentes_disponiveis = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Erro ao consultar dados: {e}")
        flash(f"Ocorreu um erro ao carregar os dados. Por favor, tente novamente.", "error")
    finally:
        if cursor: cursor.close()
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


@app.route('/admin/excluir_participantes', methods=['POST'])
def excluir_participantes():
    ids = request.json.get('ids', [])
    if not ids:
        return jsonify(sucesso=False)
    # Converta para inteiros (importante para o PostgreSQL)
    ids = [int(i) for i in ids]
    conn, cursor = get_db_connection()
    try:
        # Atualiza reservas de presentes antes de excluir
        cursor.execute("SELECT presente FROM participante WHERE id = ANY(%s)", (ids,))
        presentes = [row[0] for row in cursor.fetchall() if row[0]]
        for presente in presentes:
            cursor.execute("UPDATE presentes SET quantidade_reservada = GREATEST(quantidade_reservada - 1, 0) WHERE nome = %s", (presente,))
        cursor.execute("DELETE FROM participante WHERE id = ANY(%s)", (ids,))
        conn.commit()
        return jsonify(sucesso=True)
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao excluir participantes: {e}")
        return jsonify(sucesso=False)
    finally:
        if cursor: cursor.close()
        release_db_connection(conn)

@app.route('/admin/reestabelecer_indice', methods=['POST'])
def reestabelecer_indice():
    conn, cursor = get_db_connection()
    try:
        cursor.execute("SELECT setval('participante_id_seq', (SELECT COALESCE(MAX(id), 1) FROM participante) + 1, false);")
        conn.commit()
        return jsonify(sucesso=True)
    except Exception as e:
        conn.rollback()
        return jsonify(sucesso=False)
    finally:
        if cursor: cursor.close()
        release_db_connection(conn)

@app.route('/admin/atualizar_reservas', methods=['POST'])
def atualizar_reservas():
    conn, cursor = get_db_connection()
    try:
        cursor.execute("UPDATE presentes SET quantidade_reservada = 0;")
        cursor.execute("SELECT presente, COUNT(*) FROM participante WHERE presente IS NOT NULL GROUP BY presente;")
        for presente, count in cursor.fetchall():
            cursor.execute("UPDATE presentes SET quantidade_reservada = %s WHERE nome = %s;", (count, presente))
        conn.commit()
        return jsonify(sucesso=True)
    except Exception as e:
        conn.rollback()
        return jsonify(sucesso=False)
    finally:
        if cursor: cursor.close()
        release_db_connection(conn)


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
    app.run(host='0.0.0.0',debug=True, port=4800)
