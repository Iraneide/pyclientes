# PAINEL DE CLIENTES — servidor Flask.
# Fluxo: navegador -> rota -> validação -> MySQL -> template HTML -> navegador.
# GET apenas consulta; POST cadastra, altera ou exclui registros.
# conexao.py fornece conectar(); Template/index.html contém a interface e os modais.

# Bibliotecas padrão: ambiente, expressões regulares, tokens seguros e datas.
import os
import re
import secrets
from datetime import date

# Flask: páginas, formulários, sessão, mensagens e respostas HTTP.
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
# Error permite tratar falhas do MySQL sem expor detalhes ao visitante.
from mysql.connector import Error
from conexao import conectar

# Inicialização: informa onde ficam os templates Jinja.
app = Flask(__name__, template_folder='Template')
# Assina a sessão do navegador. SECRET_KEY fixa no ambiente mantém sessões entre reinícios.
# A chave aleatória é uma alternativa; muda quando este processo é reiniciado.
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
# Limita o corpo de cada requisição a 16 KiB.
app.config['MAX_CONTENT_LENGTH'] = 16384


# Monta a página compartilhada por listagem e retornos de validação.
# formulario: valores a exibir; erros: mensagens por campo; status: código HTTP;
# editando: ID do cliente ou None para cadastro.
def pagina(formulario=None, erros=None, status=200, editando=None):
    # Cria um token CSRF por sessão para verificar a origem dos envios de formulário.
    session.setdefault('csrf_token', secrets.token_hex(32))
    # Inicialização permite liberar apenas os recursos que chegaram a ser abertos.
    conn = cursor = None
    clientes = []
    erro = False
    try:
        conn = conectar()
        # Cada linha vira um dicionário: o template acessa id, nome, email etc.
        cursor = conn.cursor(dictionary=True)
        # Lista todos os clientes, começando pelo cadastro de maior ID.
        cursor.execute('SELECT * FROM clientes ORDER BY id DESC')
        clientes = cursor.fetchall()
    except Error:
        app.logger.exception('Erro ao carregar clientes')
        erro, status = True, 500
    # Libera cursor e conexão tanto no sucesso quanto em caso de erro.
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
    # Na edição, busca o cliente e preenche o formulário sem apagar dados reenviados.
    if editando is not None and not erro:
        cliente = next((c for c in clientes if c['id'] == editando), None)
        if cliente is None:
            abort(404)
        if formulario is None:
            formulario = {campo: cliente.get(campo) or ''
                          for campo in ('nome', 'email', 'telefone', 'data_cadastro')}
            if hasattr(formulario['data_cadastro'], 'isoformat'):
                # O input HTML de data recebe o formato AAAA-MM-DD.
                formulario['data_cadastro'] = formulario['data_cadastro'].isoformat()
    # Jinja recebe os dados; a tupla devolve também o status HTTP da resposta.
    return render_template('index.html', clientes=clientes, erro=erro, editando=editando,
                           formulario=formulario or {'data_cadastro': date.today().isoformat()},
                           erros=erros or {}, csrf_token=session['csrf_token']), status


# Página inicial: consulta os dados e mostra o formulário de novo cliente.
@app.get('/')
def home():
    return pagina()


# As duas rotas compartilham validação: sem ID insere; com ID atualiza.
@app.post('/clientes')
@app.post('/clientes/<int:cliente_id>/editar')
def cadastrar_cliente(cliente_id=None):
    # Lê somente os campos esperados e remove espaços nas extremidades.
    dados = {campo: request.form.get(campo, '').strip()
             for campo in ('nome', 'email', 'telefone', 'data_cadastro')}
    # Rejeita tokens ausentes ou diferentes antes de modificar o banco.
    token = session.get('csrf_token')
    if not token or not secrets.compare_digest(token, request.form.get('csrf_token', '')):
        return pagina(dados, {'geral': 'A sessão expirou. Confira os dados e envie novamente.'}, 400, cliente_id)
    # Validação no servidor continua necessária mesmo com required no HTML.
    erros = {}
    if not 2 <= len(dados['nome']) <= 100:
        erros['nome'] = 'Informe um nome entre 2 e 100 caracteres.'
    # E-mail e telefone são opcionais; quando preenchidos, precisam ser válidos.
    if dados['email'] and (len(dados['email']) > 100 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', dados['email'])):
        erros['email'] = 'Informe um e-mail válido com até 100 caracteres.'
    if dados['telefone'] and (len(dados['telefone']) > 25 or not re.fullmatch(r'[+\d\s().-]+', dados['telefone']) or not 8 <= len(re.sub(r'\D', '', dados['telefone'])) <= 15):
        erros['telefone'] = 'Informe um telefone com 8 a 15 dígitos.'
    try:
        # Converte a data e respeita o ano mínimo usado pelo campo DATE do MySQL.
        data_cadastro = date.fromisoformat(dados['data_cadastro'])
        if data_cadastro.year < 1000:
            raise ValueError
    except ValueError:
        erros['data_cadastro'] = 'Informe uma data válida a partir do ano 1000.'
    # Retorna HTTP 400, preservando o preenchimento para o usuário corrigir.
    if erros:
        return pagina(dados, erros, 400, cliente_id)
    # Inicialização permite liberar apenas os recursos que chegaram a ser abertos.
    conn = cursor = None
    falhou = False
    try:
        conn = conectar()
        cursor = conn.cursor()
        # Parâmetros %s separam valores do SQL; campos opcionais vazios viram NULL.
        valores = (dados['nome'], dados['email'] or None, dados['telefone'] or None, data_cadastro)
        if cliente_id is None:
            cursor.execute(
                'INSERT INTO clientes (nome, email, telefone, data_cadastro) VALUES (%s, %s, %s, %s)', valores)
        else:
            # Bloqueia o registro durante a transação e verifica se ele ainda existe.
            cursor.execute('SELECT id FROM clientes WHERE id = %s FOR UPDATE', (cliente_id,))
            if cursor.fetchone() is None:
                conn.rollback()
                abort(404)
            cursor.execute(
                'UPDATE clientes SET nome = %s, email = %s, telefone = %s, data_cadastro = %s WHERE id = %s',
                valores + (cliente_id,))
        # Confirma a transação: só agora a alteração é persistida.
        conn.commit()
    except Error:
        if conn is not None:
            # Desfaz a transação se ocorrer falha na operação.
            conn.rollback()
        app.logger.exception('Erro ao cadastrar cliente')
        falhou = True
    # Libera cursor e conexão tanto no sucesso quanto em caso de erro.
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
    # Retorna uma mensagem amigável; detalhes técnicos ficam no log do servidor.
    if falhou:
        return pagina(dados, {'geral': 'Não foi possível salvar. Seus dados foram mantidos; tente novamente.'}, 500, cliente_id)
    flash('Cliente atualizado com sucesso!' if cliente_id is not None else 'Cliente cadastrado com sucesso!')
    # POST -> redirecionamento 303 -> GET evita repetir a operação ao atualizar a página.
    return redirect(url_for('home', _anchor='clientes'), code=303)


# O JavaScript busca esta página e extrai o formulário para o modal de edição.
@app.get('/clientes/<int:cliente_id>/editar')
def editar_cliente(cliente_id):
    return pagina(editando=cliente_id)


# Exclusão aceita apenas POST; abrir um link GET não remove um cadastro.
@app.post('/clientes/<int:cliente_id>/excluir')
def excluir_cliente(cliente_id):
    # Rejeita tokens ausentes ou diferentes antes de modificar o banco.
    token = session.get('csrf_token')
    if not token or not secrets.compare_digest(token, request.form.get('csrf_token', '')):
        return pagina(erros={'geral': 'A sessão expirou. Atualize a página e tente novamente.'}, status=400)
    # O formulário de confirmação envia este campo ao clicar no Excluir do modal.
    # Esse campo não substitui o token CSRF nem representa autenticação de usuário.
    if request.form.get('confirmar_exclusao') != 'sim':
        return pagina(erros={'geral': 'Confirme a exclusão do cliente antes de continuar.'}, status=400)
    # Inicialização permite liberar apenas os recursos que chegaram a ser abertos.
    conn = cursor = None
    falhou = False
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM clientes WHERE id = %s', (cliente_id,))
        # Nenhuma linha removida: o cliente não existe mais; responde HTTP 404.
        if cursor.rowcount == 0:
            # Desfaz a transação se ocorrer falha na operação.
            conn.rollback()
            abort(404)
        # Confirma a transação: só agora a alteração é persistida.
        conn.commit()
    except Error:
        if conn is not None:
            # Desfaz a transação se ocorrer falha na operação.
            conn.rollback()
        app.logger.exception('Erro ao excluir cliente')
        falhou = True
    # Libera cursor e conexão tanto no sucesso quanto em caso de erro.
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
    # Retorna uma mensagem amigável; detalhes técnicos ficam no log do servidor.
    if falhou:
        return pagina(erros={'geral': 'Não foi possível excluir o cliente. Tente novamente.'}, status=500)
    flash('Cliente excluído com sucesso!')
    # POST -> redirecionamento 303 -> GET evita repetir a operação ao atualizar a página.
    return redirect(url_for('home', _anchor='clientes'), code=303)


# Executa o servidor de desenvolvimento somente ao rodar este arquivo diretamente.
# debug=True serve ao desenvolvimento; em produção o aplicativo deve usar servidor WSGI.
if __name__ == '__main__':
    app.run(debug=True)
