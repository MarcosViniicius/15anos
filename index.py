from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import pool
from datetime import datetime
import logging
import urllib.parse

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave_secreta_padrao")  # Necessário para flash messages

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

@app.route('/confirmar', methods=['POST'])
def confirmar():
    # Obter dados do formulário
    nome_submetido = request.form.get('nome')
    confirmado_status = request.form.get('confirmado')  # Valor será 'sim' ou 'nao'
    presente_selecionado = request.form.get('presente')  # Pode ser string vazia ""
    forma_presente = request.form.get('forma_presente')  # 'presente' ou 'pix'

    # Log detalhado dos dados recebidos
    logger.info(f"Recebido - Nome: '{nome_submetido}', Status Confirmação: '{confirmado_status}', "
                f"Presente: '{presente_selecionado}', Forma Presente: '{forma_presente}'")

    # Validações básicas
    if not nome_submetido:
        flash("Por favor, informe seu nome completo.", "error")
        return redirect(request.referrer or url_for('index'))
    if not confirmado_status:
        flash("Por favor, selecione se você vai comparecer.", "error")
        return redirect(request.referrer or url_for('index'))

    conn, cursor = get_db_connection()
    if not conn or not cursor:
        flash("Erro ao conectar ao banco de dados. Tente novamente.", "error")
        return redirect(url_for('index'))

    try:
        agora = datetime.now()

        # Determinar se o participante escolheu Pix
        is_pix = True if forma_presente == "pix" else False

        # Se a forma de presente for "pix", insira NULL na coluna "presente"
        presente_db = None if is_pix else presente_selecionado

        if confirmado_status == 'sim':
            # Inserir novo registro de participante confirmado
            cursor.execute("""
                INSERT INTO participante (nome, confirmado, presente, data_confirmacao, pix)
                VALUES (%s, TRUE, %s, %s, %s);
            """, (nome_submetido, presente_db, agora, is_pix))
            conn.commit()

            # Redirecionar para a página do Pix se a forma de presente for "pix"
            if is_pix:
                flash("Presença confirmada! Você será redirecionado para a página do Pix.", "success")
                return redirect(url_for('pix'))
            else:
                flash("Sua presença foi confirmada com sucesso!", "success")

        elif confirmado_status == 'nao':
            # Inserir novo registro de participante que não vai comparecer
            cursor.execute("""
                INSERT INTO participante (nome, confirmado, presente, data_confirmacao, pix)
                VALUES (%s, FALSE, NULL, %s, FALSE);
            """, (nome_submetido, agora))
            conn.commit()
            flash("Resposta registrada. Que pena que não poderá comparecer!", "info")

    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao processar confirmação: {e}")
        flash("Ocorreu um erro ao processar sua confirmação.", "error")
    finally:
        release_db_connection(conn)

    return redirect(url_for('index'))

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
        event_title = urllib.parse.quote("Aniversário da Ana")
        location = urllib.parse.quote("Rua Exemplo, 123, Natal - RN")
        details = urllib.parse.quote("Venha comemorar comigo!")
        start = '20250603T190000Z'
        end = '20250603T230000Z'
        link = f"https://www.google.com/calendar/render?action=TEMPLATE&text={event_title}&dates={start}/{end}&details={details}&location={location}&sf=true&output=xml"
        return redirect(link)
    except Exception as e:
        logger.error(f"Erro ao gerar link do calendário: {e}")
        flash("Não foi possível gerar o link para o calendário.", "error")
        return redirect(url_for('index'))


@app.route('/pix')
def pix():
    chave_pix = "chavepix"  # Substitua pela chave Pix real
    numero_whatsapp = "+55 99999-9999"  # Substitua pelo número real
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
