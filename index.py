from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import pool
import urllib.parse
from datetime import datetime
import logging

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
        1,  # minconn
        10,  # maxconn
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
        else:
            flash("Não foi possível conectar ao banco de dados. Tente novamente mais tarde.", "error")
    except Exception as e:
        logger.error(f"Erro ao consultar dados: {e}")
        flash(f"Ocorreu um erro ao carregar os dados. Por favor, tente novamente.", "error")
    finally:
        release_db_connection(conn)

    return render_template('index.html', participantes=participantes, disponiveis=presentes_disponiveis)

@app.route('/confirmados')
def confirmados():
    conn, cursor = get_db_connection()
    participantes_confirmados = []
    presentes_disponiveis = []

    try:
        if cursor:
            # Consultar os participantes confirmados
            cursor.execute("SELECT id, nome, confirmado, presente, data_confirmacao FROM participante WHERE confirmado = TRUE;")
            participantes_confirmados = cursor.fetchall()

            # Consultar os presentes disponíveis
            cursor.execute("SELECT nome FROM presentes WHERE disponivel = TRUE;")
            presentes_disponiveis = [row[0] for row in cursor.fetchall()]

    except Exception as e:
        logger.error(f"Erro ao consultar dados: {e}")
        flash(f"Ocorreu um erro ao carregar os dados. Por favor, tente novamente.", "error")
    finally:
        release_db_connection(conn)

    return render_template('confirmados.html', participantes=participantes_confirmados, disponiveis=presentes_disponiveis)



@app.route('/confirmar', methods=['POST'])
def confirmar():
    conn, cursor = get_db_connection()
    try:
        if not cursor:
            flash("Erro de conexão com o banco de dados.", "error")
            return redirect(url_for('index'))
            
        nome = request.form.get('nome', '').strip()
        confirmado = request.form.get('confirmado', '')
        presente = request.form.get('presente')
        
        # Validações básicas
        if not nome:
            flash("Nome é obrigatório.", "error")
            return redirect(url_for('index'))
            
        # Convertendo 'sim'/'não' para booleano
        if confirmado == 'sim':
            confirmado = True
        elif confirmado == 'nao':
            confirmado = False
        else:
            flash("Confirmação inválida.", "error")
            return redirect(url_for('index'))

        # Verificar se o presente ainda está disponível, se um foi selecionado
        if presente:
            cursor.execute("SELECT disponivel FROM presentes WHERE nome = %s", (presente,))
            result = cursor.fetchone()
            if not result or not result[0]:
                flash(f"O presente '{presente}' não está mais disponível. Por favor, escolha outro.", "error")
                return redirect(url_for('index'))

        # Inserir dados no banco de dados com timestamp atual
        cursor.execute(
            "INSERT INTO participante (nome, confirmado, presente, data_confirmacao) VALUES (%s, %s, %s, %s)",
            (nome, confirmado, presente, datetime.now())
        )

        # Marcar o presente como indisponível
        if presente:
            cursor.execute("UPDATE presentes SET disponivel = FALSE WHERE nome = %s", (presente,))

        conn.commit()
        flash("Confirmação realizada com sucesso!", "success")
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Erro no banco de dados: {e}")
        flash("Ocorreu um erro ao processar sua confirmação. Por favor, tente novamente.", "error")
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao confirmar participação: {e}")
        flash("Ocorreu um erro inesperado. Por favor, tente novamente.", "error")
    finally:
        release_db_connection(conn)

    return redirect(url_for('index'))

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