import sqlite3
import os


DB_NAME = "estacionamento.db"


def conectar():
    caminho = os.path.join(os.path.dirname(__file__), DB_NAME)
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row
    return conn


class Clientes:
    @staticmethod
    def cadastrar(nome, cpf, placa, tipo, mensalista=0, valor_mensalidade=None):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO clientes (nome, cpf, placa, tipo, mensalista, valor_mensalidade)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, cpf, placa, tipo, mensalista, valor_mensalidade))
        conn.commit()
        conn.close()

    @staticmethod
    def listar():
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, nome, cpf, placa, tipo FROM clientes")
        clientes = cur.fetchall()
        conn.close()
        return clientes

    @staticmethod
    def atualizar(id_cliente, nome, cpf, placa, tipo):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            UPDATE clientes SET nome=?, cpf=?, placa=?, tipo=? WHERE id=?
        """, (nome, cpf, placa, tipo, id_cliente))
        conn.commit()
        conn.close()

    @staticmethod
    def excluir(id_cliente):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("DELETE FROM clientes WHERE id=?", (id_cliente,))
        conn.commit()
        conn.close()
