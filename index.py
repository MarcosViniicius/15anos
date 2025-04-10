from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import pool
from datetime import datetime
import logging
import urllib.parse  # Importar o módulo urllib.parse

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

            # Armazenar em cache na memória
            cache_participantes = participantes
            cache_presentes_disponiveis = presentes_disponiveis
        else:
            flash("Não foi possível conectar ao banco de dados. Tente novamente mais tarde.", "error")
    except Exception as e:
        logger.error(f"Erro ao consultar dados: {e}")
        flash(f"Ocorreu um erro ao carregar os dados. Por favor, tente novamente.", "error")
    finally:
        release_db_connection(conn)

    return render_template('index.html', participantes=participantes, disponiveis=presentes_disponiveis)

@app.route('/')
def home():
    global cache_participantes, cache_presentes_disponiveis
    pagina = request.args.get('pagina', 1, type=int)  # Pega o número da página
    participantes = cache_participantes
    presentes_disponiveis = cache_presentes_disponiveis

    if not participantes or not presentes_disponiveis:
        conn, cursor = get_db_connection()
        try:
            if cursor:
                # Consultar participantes com paginação
                offset = (pagina - 1) * 50  # Exemplo de 50 por página
                cursor.execute("SELECT id, nome, confirmado, presente, data_confirmacao FROM participante LIMIT 50 OFFSET %s;", (offset,))
                participantes = cursor.fetchall()

                # Consultar presentes disponíveis
                cursor.execute("SELECT nome FROM presentes WHERE disponivel = TRUE LIMIT 10;")
                presentes_disponiveis = [row[0] for row in cursor.fetchall()]

                # Armazenar em cache na memória
                cache_participantes = participantes
                cache_presentes_disponiveis = presentes_disponiveis
        except Exception as e:
            logger.error(f"Erro ao consultar dados: {e}")
            flash(f"Ocorreu um erro ao carregar os dados. Por favor, tente novamente.", "error")
        finally:
            release_db_connection(conn)

    return render_template('index.html', participantes=participantes, disponiveis=presentes_disponiveis, pagina=pagina)


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

@app.errorhandler(404)
def page_not_found(e):
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
    app.run(debug=True)
