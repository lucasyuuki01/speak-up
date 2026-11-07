"""Speak Up: aplicação Flask.

Este arquivo só define as rotas (páginas e API). Conteúdo: content.py. Regras: logic.py.
"""

import os
from datetime import timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session

import content
import logic

BASE = Path(__file__).parent

app = Flask(__name__)
app.config.update(
    # Em produção, defina a variável de ambiente SECRET_KEY (veja o README).
    SECRET_KEY=os.environ.get("SECRET_KEY", "chave-de-desenvolvimento-troque-em-producao"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(days=365),
    JSON_AS_ASCII=False,
    MAX_CONTENT_LENGTH=16 * 1024,  # as requisições da API são pequenas
)

EXTENSOES_IMAGEM = ("webp", "png", "jpg", "jpeg", "svg")


def imagem_da_palavra(palavra_id):
    """Se existir static/images/vocab/<id>.<ext>, usa a foto/ilustração no lugar do emoji."""
    for ext in EXTENSOES_IMAGEM:
        if (BASE / "static" / "images" / "vocab" / f"{palavra_id}.{ext}").exists():
            return f"/static/images/vocab/{palavra_id}.{ext}"
    return None


@app.context_processor
def contexto_global():
    return {"resumo": logic.resumo(session), "imagem_da_palavra": imagem_da_palavra,
            "estatico": app.config.get("ESTATICO", False),
            "NOMES_EXERCICIOS": content.NOMES_EXERCICIOS}


# ------------------------------------------------------------------ Páginas
@app.route("/")
def index():
    return render_template("index.html", modulos=content.MODULOS)


@app.route("/aulas")
def aulas():
    return render_template("aulas.html", modulos=content.MODULOS)


@app.route("/modulo/<slug>")
def modulo(slug):
    m = content.MODULO_POR_SLUG.get(slug)
    if m is None:
        return render_template("404.html"), 404
    anterior = content.MODULOS[m["numero"] - 2] if m["numero"] > 1 else None
    proximo = content.MODULOS[m["numero"]] if m["numero"] < len(content.MODULOS) else None
    return render_template("modulo.html", m=m, anterior=anterior, proximo=proximo)


@app.route("/exercicios")
def exercicios():
    meta = {m["slug"]: {"titulo": m["titulo"], "exercicios": m["exercicios"]} for m in content.MODULOS}
    return render_template("exercicios.html", modulos=content.MODULOS, meta=meta)


@app.route("/progresso")
def progresso():
    return render_template("progresso.html", modulos=content.MODULOS)


@app.errorhandler(404)
def nao_encontrado(_erro):
    if request.path.startswith("/api/"):
        return jsonify(erro="Endereço da API não encontrado."), 404
    return render_template("404.html"), 404


@app.errorhandler(405)
@app.errorhandler(500)
def erro_generico(erro):
    """Qualquer falha vira uma mensagem amigável, em vez de uma tela de erro técnica."""
    codigo = getattr(erro, "code", 500)
    if request.path.startswith("/api/"):
        return jsonify(erro="Algo deu errado. Tente de novo."), codigo
    return render_template("erro.html", codigo=codigo), codigo


# ------------------------------------------------------------------ API (JSON)
def _json_do_corpo():
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else None


@app.get("/api/exercicio")
def api_exercicio():
    tipo = request.args.get("tipo", "")
    slug = request.args.get("modulo", "")
    try:
        quantidade = int(request.args.get("n", 6))
    except ValueError:
        return jsonify(erro="Quantidade inválida."), 400
    dados, erro = logic.gerar(session, tipo, slug, quantidade)
    if erro:
        return jsonify(erro=erro), 400
    return jsonify(logic.com_imagem(dados, imagem_da_palavra))


@app.post("/api/responder")
def api_responder():
    corpo = _json_do_corpo()
    if corpo is None:
        return jsonify(erro="Envie os dados em formato JSON."), 400
    resultado, erro = logic.responder(
        session, corpo.get("palavra_id"), corpo.get("tipo"), corpo.get("resposta"), corpo.get("tentativa", 1))
    if erro:
        return jsonify(erro=erro), 400
    return jsonify(resultado)


@app.post("/api/carta")
def api_carta():
    corpo = _json_do_corpo()
    if corpo is None or not isinstance(corpo.get("sabia"), bool):
        return jsonify(erro="Envie palavra_id e sabia (verdadeiro/falso) em JSON."), 400
    resultado, erro = logic.marcar_carta(session, corpo.get("palavra_id"), corpo["sabia"])
    if erro:
        return jsonify(erro=erro), 400
    return jsonify(resultado)


@app.get("/api/progresso")
def api_progresso():
    return jsonify(logic.resumo(session))


@app.post("/api/reiniciar")
def api_reiniciar():
    logic.reiniciar(session)
    return jsonify(logic.resumo(session))


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=int(os.environ.get("PORT", 5000)))
