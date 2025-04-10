from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import os
import psycopg2
import urllib.parse

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do Flask
app = Flask(__name__)

# Obter variáveis de ambiente
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Conectar ao banco de dados do Supabase
try:
    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )
    print("Conexão bem-sucedida!")

    # Criar o cursor
    cursor = connection.cursor()

    # Exemplo de consulta para verificar a conexão
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print("Hora Atual:", result)

except Exception as e:
    print(f"Falha ao conectar: {e}")

@app.route('/')
def index():
    # Consultar participantes diretamente no banco de dados
    cursor.execute("SELECT id, nome, confirmado, presente, data_confirmacao FROM participante;")
    participantes = cursor.fetchall()

    # Obter os presentes já selecionados
    cursor.execute("SELECT DISTINCT presente FROM participante WHERE presente IS NOT NULL")
    presentes_selecionados = [row[0] for row in cursor.fetchall()]

    # Consultar presentes disponíveis no banco de dados
    cursor.execute("SELECT nome FROM presentes WHERE disponivel = TRUE;")
    presentes_disponiveis = [row[0] for row in cursor.fetchall()]

    # Filtrar os presentes disponíveis removendo os já selecionados
    presentes_disponiveis = [p for p in presentes_disponiveis if p not in presentes_selecionados]

    return render_template('index.html', participantes=participantes, disponiveis=presentes_disponiveis)


@app.route('/confirmar', methods=['POST'])
def confirmar():
    nome = request.form['nome']
    confirmado = request.form['confirmado']
    presente = request.form.get('presente')

    # Convertendo 'sim'/'não' para booleano
    if confirmado == 'sim':
        confirmado = True
    elif confirmado == 'nao':
        confirmado = False

    # Inserir dados no banco de dados
    cursor.execute(
        "INSERT INTO participante (nome, confirmado, presente) VALUES (%s, %s, %s)",
        (nome, confirmado, presente)
    )

    # Marcar o presente como indisponível
    if presente:
        cursor.execute("UPDATE presentes SET disponivel = FALSE WHERE nome = %s", (presente,))
        connection.commit()

    connection.commit()

    return redirect('/')


@app.route('/calendar-link')
def calendar_link():
    event_title = urllib.parse.quote("Aniversário da Ana")
    location = urllib.parse.quote("Rua Exemplo, 123, Natal - RN")
    details = urllib.parse.quote("Venha comemorar comigo!")
    start = '20250603T190000Z'
    end = '20250603T230000Z'
    link = f"https://www.google.com/calendar/render?action=TEMPLATE&text={event_title}&dates={start}/{end}&details={details}&location={location}&sf=true&output=xml"
    return redirect(link)

if __name__ == '__main__':
    app.run(debug=True)
