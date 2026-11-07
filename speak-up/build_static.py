"""Gera a versão estática do site (pasta docs/) para o GitHub Pages.

Uso:  python build_static.py

As páginas HTML são geradas a partir dos MESMOS templates do Flask. Na versão estática, a lógica em
Python (logic.py) roda no navegador do aluno, via Pyodide, e o progresso fica no localStorage.
"""

import json
import re
import shutil
import sys
from pathlib import Path

import content
from app import app, imagem_da_palavra

RAIZ = Path(__file__).parent
PYODIDE_PY = ["content.py", "logic.py", "ponte.py"]  # arquivos Python enviados ao navegador

PAGINAS = [("/", "index.html"), ("/aulas", "aulas.html"), ("/exercicios", "exercicios.html"),
           ("/progresso", "progresso.html")]
PAGINAS += [(f"/modulo/{m['slug']}", f"modulo-{m['slug']}.html") for m in content.MODULOS]

ATRIBUTO = re.compile(r'(href|src|content)="(/(?!/)[^"]*)"')
SIMPLES = {"/": "index.html", "/aulas": "aulas.html", "/exercicios": "exercicios.html",
           "/progresso": "progresso.html"}


def destino(url):
    """Converte um endereço do Flask (/aulas, /modulo/animais, /static/...) em arquivo relativo."""
    caminho, resto = re.match(r"^([^?#]*)(.*)$", url).groups()
    if caminho in SIMPLES:
        novo = SIMPLES[caminho]
    elif caminho.startswith("/modulo/"):
        novo = f"modulo-{caminho[len('/modulo/'):]}.html"
    elif caminho.startswith("/static/"):
        novo = caminho[1:]
    else:
        raise ValueError(f"Endereço sem equivalente na versão estática: {url}")
    return novo + resto


def construir(saida=None):
    saida = Path(saida) if saida else RAIZ / "docs"
    if saida.exists():
        shutil.rmtree(saida)
    saida.mkdir(parents=True)

    app.config["ESTATICO"] = True
    try:
        cliente = app.test_client()
        for rota, arquivo in PAGINAS:
            resposta = cliente.get(rota)
            if resposta.status_code != 200:
                raise RuntimeError(f"{rota} respondeu {resposta.status_code}")
            html = ATRIBUTO.sub(lambda m: f'{m.group(1)}="{destino(m.group(2))}"',
                                resposta.get_data(as_text=True))
            (saida / arquivo).write_text(html, encoding="utf-8")
    finally:
        app.config["ESTATICO"] = False

    shutil.copytree(RAIZ / "static", saida / "static")
    (saida / "python").mkdir()
    for nome in PYODIDE_PY:
        shutil.copy(RAIZ / nome, saida / "python" / nome)

    # imagens reais (opcionais) de static/images/vocab, conforme o id de cada palavra
    imagens = {p["id"]: imagem_da_palavra(p["id"])[1:] for p in content.PALAVRAS if imagem_da_palavra(p["id"])}
    (saida / "imagens.json").write_text(json.dumps(imagens, ensure_ascii=False), encoding="utf-8")
    (saida / ".nojekyll").write_text("", encoding="utf-8")  # o GitHub Pages não deve processar com Jekyll
    return saida


if __name__ == "__main__":
    pasta = construir(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"Versão estática gerada em: {pasta}")
