from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
)
from datetime import date, datetime
from io import BytesIO
from collections import defaultdict
from matplotlib.figure import Figure
from fpdf import FPDF

from cliente import Clientes
from movimentacao import Movimentacao
from relatorio import Relatorio
from database import criar_tabelas


app = Flask(__name__)
app.config["DEBUG"] = True

app.secret_key = "secret-estacionamento"  # troque em produção


# ------------------- INDEX -------------------
@app.route("/")
def index():
    return render_template("index.html")


# ------------------- CLIENTES -------------------
@app.route("/clientes")
def listar_clientes():
    clientes = Clientes.listar()
    return render_template("clientes.html", clientes=clientes)


@app.route("/clientes/novo", methods=["POST"])
def novo_cliente():
    nome = request.form.get("nome", "").strip()
    cpf = request.form.get("cpf", "").strip()
    placa = request.form.get("placa", "").strip()
    tipo = request.form.get("tipo", "").strip()

    if not nome or not cpf or not placa:
        flash("Nome, CPF e Placa são obrigatórios.", "erro")
        return redirect(url_for("listar_clientes"))

    try:
        Clientes.cadastrar(nome, cpf, placa, tipo)
        flash("Cliente cadastrado com sucesso!", "sucesso")
    except Exception as e:
        flash(f"Erro ao cadastrar cliente: {e}", "erro")

    return redirect(url_for("listar_clientes"))


# ------------------- MOVIMENTAÇÃO -------------------
@app.route("/movimentacao")
def movimentacao():
    return render_template("movimentacao.html")


@app.route("/movimentacao/entrada", methods=["POST"])
def registrar_entrada():
    placa = request.form.get("placa", "").strip().upper()

    if not placa:
        flash("Informe a placa.", "erro")
        return redirect(url_for("movimentacao"))

    try:
        mov_id = Movimentacao.registrar_entrada(placa)

        # gerar ticket de entrada em PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Ticket de Entrada - Estacionamento", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"ID movimentacao: {mov_id}", ln=True)
        pdf.cell(0, 8, f"Placa: {placa}", ln=True)
        pdf.cell(0, 8, f"Data/Hora entrada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
        pdf.ln(5)
        pdf.cell(0, 8, "Guarde este ticket para apresentacao na saida.", ln=True)

        pdf_bytes = pdf.output(dest="S")
        buffer = BytesIO(pdf_bytes)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"ticket_entrada_{placa}.pdf",
            mimetype="application/pdf",
        )

    except Exception as e:
        flash(f"Erro ao registrar entrada: {e}", "erro")
        return redirect(url_for("movimentacao"))


@app.route("/movimentacao/saida", methods=["POST"])
def registrar_saida():
    placa = request.form.get("placa", "").strip().upper()

    if not placa:
        flash("Informe a placa.", "erro")
        return redirect(url_for("movimentacao"))

    try:
        valor = Movimentacao.registrar_saida(placa)
        if valor is None:
            flash("Nenhuma entrada em aberto para essa placa.", "erro")
            return redirect(url_for("movimentacao"))

        flash(f"Saída registrada para {placa}. Valor: R$ {valor:.2f}", "sucesso")

        # gerar ticket de saída em PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Ticket de Saida - Estacionamento", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"Placa: {placa}", ln=True)
        pdf.cell(0, 8, f"Data/Hora saida: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
        pdf.cell(0, 8, f"Valor a pagar: R$ {valor:.2f}", ln=True)
        pdf.ln(5)
        pdf.cell(0, 8, "Obrigado pela preferencia!", ln=True)

        pdf_bytes = pdf.output(dest="S")
        buffer = BytesIO(pdf_bytes)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"ticket_saida_{placa}.pdf",
            mimetype="application/pdf",
        )

    except Exception as e:
        flash(f"Erro ao registrar saída: {e}", "erro")
        return redirect(url_for("movimentacao"))



@app.route("/movimentacao/pagamento", methods=["POST"])
def registrar_pagamento():
    placa = request.form.get("placa", "").strip().upper()

    if not placa:
        flash("Informe a placa.", "erro")
        return redirect(url_for("movimentacao"))

    try:
        valor = Movimentacao.registrar_pagamento(placa)
        flash(f"Pagamento registrado para {placa}: R$ {valor:.2f}", "sucesso")
    except Exception as e:
        flash(f"Erro ao registrar pagamento: {e}", "erro")

    return redirect(url_for("movimentacao"))

# ------------------- RELATÓRIO DIÁRIO -------------------
@app.route("/relatorio/diario")
def relatorio_diario():
    dia = request.args.get("dia", date.today().isoformat())
    registros = Relatorio.movimentacao_do_dia(dia)
    total = sum(float(r[2] or 0) for r in registros)
    return render_template(
        "relatorio_diario.html",
        dia=dia,
        registros=registros,
        total=total,
    )


# ------------------- DASHBOARD (evolução) -------------------
@app.route("/dashboard")
def dashboard():
    dia = date.today().isoformat()
    registros = Relatorio.movimentacao_do_dia(dia)
    total = sum(float(r[2] or 0) for r in registros)
    return render_template("dashboard.html", dia=dia, registros=registros, total=total)


@app.route("/dashboard/grafico.png")
def grafico_faturamento_diario():
    dados = Relatorio.faturamento_por_dia()  # [(dia_iso, total), ...]

    fig = Figure(figsize=(5, 3), dpi=100)
    ax = fig.add_subplot(111)

    if not dados:
        ax.set_title("Sem dados")
    else:
        dias = [d[0] for d in dados]
        valores = [d[1] for d in dados]
        ax.bar(dias, valores, color="#10aa3e")
        ax.set_title("Faturamento por dia")
        ax.set_xlabel("Data")
        ax.set_ylabel("Total (R$)")
        ax.tick_params(axis="x", rotation=45)

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/dashboard/relatorio-completo.pdf")
def dashboard_relatorio_completo_pdf():
    try:
        dados = Relatorio.todos_movimentos()
        if not dados:
            flash("Não há dados de movimentação.", "erro")
            return redirect(url_for("dashboard"))

        dias = defaultdict(list)
        semanas = defaultdict(list)
        meses = defaultdict(list)
        total_geral = 0.0

        for placa, entrada, saida, valor in dados:
            dt = datetime.fromisoformat(entrada)
            dia = dt.strftime("%d/%m/%Y")
            semana = f"Semana {dt.isocalendar()[1]} - {dt.year}"
            mes = dt.strftime("%m/%Y")
            dias[dia].append((placa, entrada, saida, valor))
            semanas[semana].append((placa, entrada, saida, valor))
            meses[mes].append((placa, entrada, saida, valor))
            total_geral += float(valor or 0)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Relatório Completo de Movimentação", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 8, f"Total Geral: R$ {total_geral:.2f}", ln=True)
        pdf.ln(5)

        # --------- Por Dia ---------
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Movimentação por Dia", ln=True)
        pdf.set_font("Arial", "", 10)
        for dia, lista in sorted(dias.items()):
            total_dia = sum(float(l[3] or 0) for l in lista)
            pdf.cell(0, 7, f"{dia} - Total: R$ {total_dia:.2f}", ln=True)

            pdf.set_font("Arial", "", 9)
            pdf.cell(30, 7, "Placa", 1)
            pdf.cell(55, 7, "Entrada", 1)
            pdf.cell(55, 7, "Saída", 1)
            pdf.cell(30, 7, "Valor", 1)
            pdf.ln()

            for placa, entrada, saida, valor in lista:
                pdf.cell(30, 7, str(placa), 1)
                pdf.cell(55, 7, str(entrada), 1)
                pdf.cell(55, 7, str(saida) if saida else "-", 1)
                pdf.cell(30, 7, f"{valor:.2f}" if valor else "0.00", 1)
                pdf.ln()

            pdf.ln(2)
            pdf.set_font("Arial", "", 10)
        pdf.ln(5)

        # --------- Por Semana ---------
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Movimentação por Semana", ln=True)
        pdf.set_font("Arial", "", 10)
        for semana, lista in sorted(semanas.items()):
            total_semana = sum(float(l[3] or 0) for l in lista)
            pdf.cell(0, 7, f"{semana} - Total: R$ {total_semana:.2f}", ln=True)
        pdf.ln(5)

        # --------- Por Mês ---------
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Movimentação por Mês", ln=True)
        pdf.set_font("Arial", "", 10)
        for mes, lista in sorted(meses.items()):
            total_mes = sum(float(l[3] or 0) for l in lista)
            pdf.cell(0, 7, f"{mes} - Total: R$ {total_mes:.2f}", ln=True)
        pdf.ln(5)

        pdf_bytes = pdf.output(dest="S")
        buffer = BytesIO(pdf_bytes)
        return send_file(
            buffer,
            as_attachment=True,
            download_name="relatorio_completo_movimentacao.pdf",
            mimetype="application/pdf",
        )

    except Exception as e:
        flash(f"Falha ao gerar PDF: {e}", "erro")
        return redirect(url_for("dashboard"))


# ------------------- MAIN -------------------
if __name__ == "__main__":
    criar_tabelas()
    app.run(debug=True)
