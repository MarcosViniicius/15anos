# ==========================================================
# Desenvolvido por Marcos Vinicius - github.com/MarcosViniicius
# ==========================================================

import pytest
from index import app, get_db_connection, release_db_connection

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def print_response_info(test_name, response):
    print(f"\n[Teste: {test_name}]")
    print("Status Code:", response.status_code)
    print("Headers:", dict(response.headers))
    print("Body (200 primeiros caracteres):", response.data.decode('utf-8')[:200])

def test_index_route(client):
    response = client.get('/')
    print_response_info("test_index_route", response)
    assert response.status_code == 200
    assert b"formConfirmacao" in response.data

def test_confirmar_route_get(client):
    response = client.get('/confirmar')
    print_response_info("test_confirmar_route_get", response)
    assert response.status_code == 405

def test_confirmar_route_post_invalid(client):
    response = client.post('/confirmar', data={}, follow_redirects=True)
    print_response_info("test_confirmar_route_post_invalid", response)
    assert response.status_code == 200
    assert b"Por favor, informe seu nome completo." in response.data

def test_confirmar_route_post_valid(client, mocker):
    mocker.patch('index.get_db_connection', return_value=(None, None))
    data = {
        'nome': 'João Silva',
        'confirmado': 'sim',
        'quantidade_pessoas': '2',
        'presente': 'Livro',
        'forma_presente': 'presente'
    }
    response = client.post('/confirmar', data=data, follow_redirects=True)
    print_response_info("test_confirmar_route_post_valid", response)
    assert response.status_code == 200
    assert "Sua presença foi confirmada com sucesso!".encode('utf-8') in response.data

def test_confirmados_route(client):
    response = client.get('/confirmados')
    print_response_info("test_confirmados_route", response)
    assert response.status_code == 200
    assert b"participantes" in response.data

def test_calendar_link_route(client):
    response = client.get('/calendar-link')
    print_response_info("test_calendar_link_route", response)
    assert response.status_code == 302  # Redirecionamento

def test_pix_route(client):
    response = client.get('/pix')
    print_response_info("test_pix_route", response)
    assert response.status_code == 200
    assert b"chavepix" in response.data

def test_404_error(client):
    response = client.get('/rota-inexistente')
    print_response_info("test_404_error", response)
    assert response.status_code == 404
    assert b"404" in response.data

def test_get_db_connection_success(mocker):
    mock_connection = mocker.Mock()
    mock_connection.cursor.return_value = mocker.Mock()
    mocker.patch('index.connection_pool.getconn', return_value=mock_connection)
    conn, cursor = get_db_connection()
    print(f"\n[Teste: test_get_db_connection_success] Conexão: {conn}, Cursor: {cursor}")
    assert conn == mock_connection
    assert cursor is not None

def test_get_db_connection_failure(mocker):
    mocker.patch('index.connection_pool.getconn', side_effect=Exception("Erro ao obter conexão"))
    conn, cursor = get_db_connection()
    print(f"\n[Teste: test_get_db_connection_failure] Conexão: {conn}, Cursor: {cursor}")
    assert conn is None
    assert cursor is None

def test_release_db_connection(mocker):
    mock_putconn = mocker.patch('index.connection_pool.putconn')
    conn = 'mock_connection'
    release_db_connection(conn)
    print(f"\n[Teste: test_release_db_connection] Conexão devolvida: {conn}")
    mock_putconn.assert_called_once_with(conn)

def test_release_db_connection_no_pool(mocker):
    mocker.patch('index.connection_pool', None)
    conn = 'mock_connection'
    release_db_connection(conn)
    print(f"\n[Teste: test_release_db_connection_no_pool] Conexão devolvida sem pool: {conn}")
