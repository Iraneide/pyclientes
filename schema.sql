-- Estrutura inicial, sem informações pessoais de clientes.
CREATE DATABASE IF NOT EXISTS crud_python
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE crud_python;

CREATE TABLE IF NOT EXISTS clientes (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) NULL,
    telefone VARCHAR(25) NULL,
    data_cadastro DATE NOT NULL
);
