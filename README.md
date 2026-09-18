# PyClientes

Aplicação de estudo em Python, Flask e MySQL para gerenciar clientes, com interface em português.

## Funcionalidades

- Cadastro com validação de nome, e-mail, telefone e data.
- Listagem e busca local por dados do cliente.
- Edição em modal e confirmação de exclusão.
- Indicadores de clientes cadastrados, com e-mail e com telefone.
- Proteção CSRF nos formulários e consultas SQL parametrizadas.
- Layout responsivo em azul e amarelo.

## Executar localmente

Requer Python 3.10 ou superior e MySQL em execução.

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item config.example.json config.local.json
```

Edite `config.local.json` com os dados do seu MySQL. Esse arquivo é privado e não deve ser enviado ao GitHub. Se ele já existir, mantenha sua configuração.

Execute `schema.sql` no MySQL Workbench ou em outro cliente MySQL para preparar a estrutura. O script não inclui cadastros reais.

```powershell
.\venv\Scripts\python.exe app.py
```

Abra http://127.0.0.1:5000 no navegador.

Também é possível configurar a conexão pelas variáveis `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` e `DB_PORT`, que têm prioridade sobre o arquivo local.

## Organização

- `app.py`: rotas, validação e operações com os clientes.
- `conexao.py`: configuração e abertura da conexão MySQL.
- `Template/index.html`: interface, CSS e JavaScript dos modais e busca.
- `schema.sql`: estrutura inicial do banco.
- `.vscode/settings.json`: destaque visual dos comentários no editor.

## Publicação e acesso

O projeto ainda não possui login ou controle de acesso: quem acessar a aplicação poderá gerenciar clientes. Antes de disponibilizá-la publicamente, implemente autenticação e autorização, configure uma `SECRET_KEY` fixa e privada e utilize um servidor WSGI com depuração desativada. O comando `python app.py` é destinado ao desenvolvimento local.

Currículos, arquivos temporários, ambiente virtual, configurações privadas e cópias de backup ficam fora do repositório pelo `.gitignore`.
