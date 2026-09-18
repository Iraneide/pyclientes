# Conexão MySQL: os segredos ficam fora dos arquivos publicados no GitHub.
import json
import os
from pathlib import Path

import mysql.connector

# Configuração privada do computador; esse arquivo está no .gitignore.
_caminho = Path(__file__).with_name('config.local.json')
_local = json.loads(_caminho.read_text(encoding='utf-8-sig')) if _caminho.exists() else {}


def configurar(nome, padrao=None):
    # Variáveis de ambiente têm prioridade, permitindo configurar a hospedagem.
    return os.environ.get(nome, _local.get(nome, padrao))


def conectar():
    # Retorna uma nova conexão. As rotas de app.py a fecham no bloco finally.
    # Erros do MySQL são tratados no servidor, sem mostrar credenciais ao usuário.
    return mysql.connector.connect(
        host=configurar('DB_HOST', 'localhost'),
        user=configurar('DB_USER', 'root'),
        password=configurar('DB_PASSWORD', ''),
        database=configurar('DB_NAME', 'crud_python'),
        port=int(configurar('DB_PORT', 3306)),
    )
