"""Ponte entre o JavaScript e a lógica em Python (logic.py) na versão que roda no navegador (Pyodide).

Como funciona:
  - O navegador guarda o progresso no localStorage e o envia a cada chamada, em texto JSON.
  - Cada função abaixo recebe esse estado, usa o MESMO logic.py do Flask e devolve um texto JSON com:
        dados  -> o resultado (ou None)
        erro   -> mensagem amigável (ou None)
        estado -> o novo progresso, para o navegador salvar
        resumo -> pontos e progresso por módulo, para atualizar a tela
Este arquivo não depende do Flask.
"""

import json

import logic


class _Sessao(dict):
    """Imita a sessão do Flask: um dicionário com o atributo `permanent`."""
    permanent = False


def _abrir(estado_json):
    sessao = _Sessao()
    try:
        estado = json.loads(estado_json) if estado_json else None
    except ValueError:
        estado = None
    if isinstance(estado, dict):
        sessao["p"] = estado  # logic._estado confere os tipos de cada campo
    return sessao


def _saida(sessao, dados=None, erro=None):
    return json.dumps({"dados": dados, "erro": erro, "estado": sessao.get("p"),
                       "resumo": logic.resumo(sessao)}, ensure_ascii=False)


def _corpo(corpo_json):
    try:
        corpo = json.loads(corpo_json)
    except (TypeError, ValueError):
        return None
    return corpo if isinstance(corpo, dict) else None


def _resolvedor(imagens_json):
    try:
        mapa = json.loads(imagens_json) if imagens_json else {}
    except ValueError:
        mapa = {}
    mapa = mapa if isinstance(mapa, dict) else {}
    return lambda palavra_id: mapa.get(palavra_id)


def exercicio(estado_json, tipo, modulo, quantidade="6", imagens_json=""):
    sessao = _abrir(estado_json)
    try:
        n = int(quantidade)
    except (TypeError, ValueError):
        return _saida(sessao, erro="Quantidade inválida.")
    dados, erro = logic.gerar(sessao, tipo, modulo, n)
    if erro:
        return _saida(sessao, erro=erro)
    return _saida(sessao, dados=logic.com_imagem(dados, _resolvedor(imagens_json)))


def responder(estado_json, corpo_json):
    sessao = _abrir(estado_json)
    corpo = _corpo(corpo_json)
    if corpo is None:
        return _saida(sessao, erro="Envie os dados em formato JSON.")
    dados, erro = logic.responder(sessao, corpo.get("palavra_id"), corpo.get("tipo"),
                                  corpo.get("resposta"), corpo.get("tentativa", 1))
    return _saida(sessao, dados=dados, erro=erro)


def carta(estado_json, corpo_json):
    sessao = _abrir(estado_json)
    corpo = _corpo(corpo_json)
    if corpo is None or not isinstance(corpo.get("sabia"), bool):
        return _saida(sessao, erro="Envie palavra_id e sabia (verdadeiro/falso) em JSON.")
    dados, erro = logic.marcar_carta(sessao, corpo.get("palavra_id"), corpo["sabia"])
    return _saida(sessao, dados=dados, erro=erro)


def reiniciar(estado_json=""):
    sessao = _abrir(estado_json)
    logic.reiniciar(sessao)
    return _saida(sessao)
