from database import conectar



class Relatorio:
    @classmethod
    def clientes(cls):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                c.id,
                c.nome,
                c.cpf,
                c.placa,
                c.tipo,
                IFNULL(m.valor, 0)
            FROM clientes c
            LEFT JOIN movimentacoes m
                ON m.placa = c.placa
            ORDER BY c.nome
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    @classmethod
    def movimentacoes(cls):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                id,
                nome,
                placa,
                entrada,
                saida,
                valor
            FROM movimentacoes
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    @classmethod
    def faturamento_total(cls):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM movimentacoes
            WHERE valor IS NOT NULL
        """)
        total = cur.fetchone()[0]
        conn.close()
        return total

    @classmethod
    def faturamento_por_dia(cls):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                substr(entrada, 1, 10) AS dia,   -- YYYY-MM-DD
                COALESCE(SUM(valor), 0) AS total
            FROM movimentacoes
            WHERE valor IS NOT NULL
            GROUP BY dia
            ORDER BY dia
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    @classmethod
    def faturamento_do_dia(cls, data_iso):
        """
        data_iso no formato 'YYYY-MM-DD'
        """
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM movimentacoes
            WHERE valor IS NOT NULL
              AND substr(entrada, 1, 10) = ?
        """, (data_iso,))
        total = cur.fetchone()[0]
        conn.close()
        return total

    @classmethod
    def faturamento_do_mes(cls, ano_mes_iso):
        """
        ano_mes_iso no formato 'YYYY-MM' (ex: '2026-03')
        """
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM movimentacoes
            WHERE valor IS NOT NULL
              AND substr(entrada, 1, 7) = ?
        """, (ano_mes_iso,))
        total = cur.fetchone()[0]
        conn.close()
        return total

    @classmethod
    def movimentacao_do_dia(cls, dia_iso):
        """
        dia_iso no formato 'YYYY-MM-DD' (bate com substr(entrada,1,10))
        Retorna: lista de (placa, entrada_iso, valor)
        """
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                placa,
                entrada,
                COALESCE(valor, 0) AS valor
            FROM movimentacoes
            WHERE substr(entrada, 1, 10) = ?
              AND valor IS NOT NULL
            ORDER BY entrada
        """, (dia_iso,))
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def todos_movimentos():
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT placa, entrada, saida, valor
            FROM movimentacoes
            ORDER BY entrada ASC
        """)
        dados = cur.fetchall()
        conn.close()
        return dados

    @staticmethod
    def recebimentos_em_aberto():
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT placa, entrada, COALESCE(valor, 0)
            FROM movimentacoes
            WHERE valor IS NULL OR valor = 0
            ORDER BY entrada ASC
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def recebimentos():
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT substr(entrada, 1, 10) as data, placa, valor
            FROM movimentacoes
            WHERE valor IS NOT NULL AND valor > 0
            ORDER BY entrada DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    @classmethod
    def top5_clientes(cls):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            SELECT c.nome, c.placa, COUNT(m.id) AS usos,
                   COALESCE(SUM(m.valor), 0) AS total_pago
            FROM clientes c
            JOIN movimentacoes m ON m.placa = c.placa
            WHERE m.entrada >= date('now', '-30 days')
              AND m.valor IS NOT NULL
              AND m.valor > 0
            GROUP BY c.nome, c.placa
            ORDER BY usos DESC, total_pago DESC
            LIMIT 5
        """)
        rows = cur.fetchall()
        conn.close()
        return rows
