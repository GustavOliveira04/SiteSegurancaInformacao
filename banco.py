import os
import sqlite3

pastaBase = os.path.dirname(os.path.abspath(__file__))
caminhoBanco = os.path.join(pastaBase, "cargoconnect.db")


# ===== CONEXÃO =====
def conectar():
    conexao = sqlite3.connect(caminhoBanco)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def consultarTodos(sql, parametros=()):
    conexao = conectar()
    linhas = conexao.execute(sql, parametros).fetchall()
    conexao.close()
    return linhas


def consultarUm(sql, parametros=()):
    conexao = conectar()
    linha = conexao.execute(sql, parametros).fetchone()
    conexao.close()
    return linha


def executar(sql, parametros=()):
    conexao = conectar()
    cursor = conexao.execute(sql, parametros)
    conexao.commit()
    novoId = cursor.lastrowid
    conexao.close()
    return novoId


# ===== TABELAS =====
def criarTabelas():
    conexao = conectar()
    conexao.executescript("""
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT NOT NULL,
            cnpj TEXT NOT NULL UNIQUE,
            responsavel TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            dataInicio TEXT NOT NULL,
            dataFim TEXT NOT NULL,
            valorMensal REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senhaHash TEXT NOT NULL,
            perfil TEXT NOT NULL CHECK (perfil IN ('administrador', 'operador', 'cliente')),
            contratoId INTEGER REFERENCES contratos(id),
            criadoEm TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS galpoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cidade TEXT NOT NULL,
            endereco TEXT NOT NULL,
            capacidade INTEGER NOT NULL CHECK (capacidade > 0)
        );

        CREATE TABLE IF NOT EXISTS mercadorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            quantidade INTEGER NOT NULL CHECK (quantidade > 0),
            paletes INTEGER NOT NULL CHECK (paletes > 0),
            galpaoId INTEGER NOT NULL REFERENCES galpoes(id),
            contratoId INTEGER NOT NULL REFERENCES contratos(id),
            comprovante TEXT,
            entradaEm TEXT NOT NULL DEFAULT CURRENT_DATE
        );
    """)
    conexao.close()
