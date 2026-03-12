from database import conectar
from cliente import Clientes



class Movimentacao:
    from datetime import datetime


class Movimentacao:
    @staticmethod
    def registrar_entrada(placa):
        placa = placa.strip().upper()
        if not placa:
            raise ValueError("Placa não informada.")

        agora = datetime.now().isoformat(timespec="seconds")

        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO movimentacoes (placa, entrada)
            VALUES (?, ?)
        """, (placa, agora))
        mov_id = cur.lastrowid         # <<--- IMPORTANTE
        conn.commit()
        conn.close()

        return mov_id                  # <<--- IMPORTANTE


    @staticmethod
    def registrar_saida(placa):
        placa = placa.strip().upper()
        if not placa:
            raise ValueError("Placa não informada.")

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT mensalista, valor_mensalidade
            FROM clientes
            WHERE placa = ?
        """, (placa,))
        cli = cur.fetchone()

        mensalista = 0
        valor_mensalidade = None
        if cli:
            mensalista, valor_mensalidade = cli

        cur.execute("""
            SELECT id, entrada
            FROM movimentacoes
            WHERE placa = ?
              AND (saida IS NULL OR saida = '')
            ORDER BY id DESC
            LIMIT 1
        """, (placa,))
        mov = cur.fetchone()

        if not mov:
            conn.close()
            return None

        mov_id, entrada_iso = mov
        saida_iso = datetime.now().isoformat(timespec="seconds")

        if mensalista:
            valor = 0.0
        else:
            valor = 10.0

        cur.execute("""
            UPDATE movimentacoes
            SET saida = ?, valor = ?
            WHERE id = ?
        """, (saida_iso, valor, mov_id))

        conn.commit()
        conn.close()

        return valor

    @staticmethod
    def registrar_pagamento(placa):
        placa = placa.strip().upper()
        if not placa:
            raise ValueError("Placa não informada.")

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, entrada
            FROM movimentacoes
            WHERE placa = ?
              AND (saida IS NULL OR saida = '')
            ORDER BY id DESC
            LIMIT 1
        """, (placa,))
        row = cur.fetchone()

        if row is None:
            conn.close()
            raise ValueError("Nenhuma movimentação em aberto para essa placa.")

        mov_id, entrada_str = row

        entrada = datetime.fromisoformat(entrada_str)
        agora = datetime.now()
        horas = (agora - entrada).total_seconds() / 3600
        horas_cobradas = max(1, int(horas + 0.9999))
        valor = horas_cobradas * 10.0

        cur.execute("""
            UPDATE movimentacoes
            SET saida = ?, valor = ?
            WHERE id = ?
        """, (agora.isoformat(sep=" "), valor, mov_id))

        conn.commit()
        conn.close()

        return valor
