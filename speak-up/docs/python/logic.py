"""Lógica da Speak Up: geração de perguntas, correção das respostas, pontuação e progresso.

O progresso fica no cookie de sessão assinado do Flask (nada de dados pessoais):
    pts  -> pontos acumulados
    resp -> total de respostas dadas
    ac   -> total de acertos
    ok   -> índices das palavras que o aluno já sabe
    fr   -> índices das palavras que precisam de revisão
"""

import random

import content

PONTOS_POR_ACERTO = 10
TIPOS_COM_PERGUNTA = ("quiz", "traducao", "traducao_inversa", "associacao")
MENSAGENS_ACERTO = ["Muito bem!", "Isso mesmo!", "Excelente!", "Você acertou!", "Continue assim!"]


# ------------------------------------------------------------------ Sessão
def _inteiro(valor):
    """Número inteiro >= 0; qualquer valor estranho (dado corrompido) vira 0."""
    return valor if isinstance(valor, int) and not isinstance(valor, bool) and valor >= 0 else 0


def _indices(valor):
    """Conjunto de índices de palavras válidos; ignora o que não for um índice existente."""
    if not isinstance(valor, list):
        return set()
    return {i for i in valor if isinstance(i, int) and not isinstance(i, bool) and 0 <= i < len(content.PALAVRAS)}


def _estado(sessao):
    """Devolve o estado de progresso (com valores padrão se for o primeiro acesso)."""
    bruto = sessao.get("p")
    if not isinstance(bruto, dict):
        bruto = {}
    return {
        "pts": _inteiro(bruto.get("pts")),
        "resp": _inteiro(bruto.get("resp")),
        "ac": _inteiro(bruto.get("ac")),
        "ok": _indices(bruto.get("ok")),
        "fr": _indices(bruto.get("fr")),
    }


def _salvar(sessao, estado):
    sessao["p"] = {
        "pts": estado["pts"], "resp": estado["resp"], "ac": estado["ac"],
        "ok": sorted(estado["ok"]), "fr": sorted(estado["fr"]),
    }
    sessao.permanent = True


def reiniciar(sessao):
    sessao.pop("p", None)


def resumo(sessao):
    """Resumo do progresso para as páginas e para a API."""
    e = _estado(sessao)
    modulos, concluidos = {}, 0
    for m in content.MODULOS:
        total = len(m["palavras"])
        sabidas = sum(1 for p in m["palavras"] if p["indice"] in e["ok"])
        pct = round(100 * sabidas / total)
        if sabidas == total:
            concluidos += 1
        modulos[m["slug"]] = {"sabidas": sabidas, "total": total, "pct": pct, "concluido": sabidas == total}
    return {
        "pontos": e["pts"],
        "respondidas": e["resp"],
        "acertos": e["ac"],
        "precisao": round(100 * e["ac"] / e["resp"]) if e["resp"] else 0,
        "palavras_sabidas": len(e["ok"]),
        "total_palavras": len(content.PALAVRAS),
        "para_revisar": len(e["fr"]),
        "modulos_concluidos": concluidos,
        "total_modulos": len(content.MODULOS),
        "modulos": modulos,
    }


# ------------------------------------------------------------------ Regras de cada tipo
def tipos_da_palavra(palavra):
    """Quais perguntas podem ser feitas sobre uma palavra (usado na Revisão)."""
    modulo = content.MODULO_POR_SLUG[palavra["modulo"]]
    permitidos = modulo["exercicios"]
    return [t for t in ("quiz", "traducao", "traducao_inversa") if t in permitidos]


def resposta_correta(palavra, tipo):
    modulo = content.MODULO_POR_SLUG[palavra["modulo"]]
    if tipo == "quiz" and modulo.get("modo_quiz") == "som":
        return palavra["pron"]
    if tipo == "traducao":
        return palavra["pt"]
    return palavra["en"]  # quiz de imagem, associação e tradução inversa


def _opcao(palavra, tipo):
    valor = resposta_correta(palavra, tipo)
    rotulo = valor.upper() if tipo in ("quiz", "associacao") and valor == palavra["en"] else valor
    return {"valor": valor, "rotulo": rotulo}


def _visual(palavra):
    v = dict(palavra["visual"])
    v["alt"] = palavra["alt"]
    return v


def _distratores(palavra, tipo, quantidade=3):
    """Escolhe respostas erradas parecidas: mesmo grupo primeiro, depois o mesmo módulo."""
    certo = resposta_correta(palavra, tipo)
    modulo = content.MODULO_POR_SLUG[palavra["modulo"]]
    mesmo_grupo = [p for p in modulo["palavras"] if p is not palavra and p["grupo"] == palavra["grupo"]]
    outros = [p for p in modulo["palavras"] if p is not palavra and p not in mesmo_grupo]
    if tipo in ("quiz", "associacao"):  # exercícios de imagem não usam palavras sem imagem
        mesmo_grupo = [p for p in mesmo_grupo if not p.get("so_texto")]
        outros = [p for p in outros if not p.get("so_texto")]
    random.shuffle(mesmo_grupo)
    random.shuffle(outros)
    vistos, escolhidos = {certo}, []
    for p in mesmo_grupo + outros:
        valor = resposta_correta(p, tipo)
        if valor not in vistos:
            vistos.add(valor)
            escolhidos.append(p)
        if len(escolhidos) == quantidade:
            break
    return escolhidos


def _pergunta(palavra, tipo):
    modulo = content.MODULO_POR_SLUG[palavra["modulo"]]
    opcoes = [_opcao(palavra, tipo)] + [_opcao(p, tipo) for p in _distratores(palavra, tipo)]
    random.shuffle(opcoes)
    p = {"palavra_id": palavra["id"], "tipo": tipo, "opcoes": opcoes}
    if tipo == "quiz":
        p["visual"] = _visual(palavra)
        p["enunciado"] = ("Qual é o nome desta letra em inglês? Escolha como se pronuncia."
                          if modulo.get("modo_quiz") == "som" else "O que é isto em inglês?")
        p["falar"] = palavra["en"]
    elif tipo == "traducao":
        p["enunciado"] = "O que isto significa em português?"
        p["texto"] = palavra["en"]
        p["falar"] = palavra["en"]
    else:  # traducao_inversa
        p["enunciado"] = "Como se diz isto em inglês?"
        p["texto"] = palavra["pt"]
    return p


def _elegiveis(tipo, slug):
    """Palavras que podem entrar num exercício deste tipo."""
    if slug == "todos":
        palavras = list(content.PALAVRAS)
    else:
        palavras = list(content.MODULO_POR_SLUG[slug]["palavras"])
    if tipo in ("quiz", "associacao"):
        palavras = [p for p in palavras if not p.get("so_texto")]
    return palavras


# ------------------------------------------------------------------ Geração de exercícios
def gerar(sessao, tipo, slug, quantidade=6):
    """Cria um exercício. Devolve (dados, erro). As respostas certas NÃO são enviadas ao navegador,
    exceto nos flashcards, que são feitos para virar a carta."""
    if tipo not in content.TODOS:
        return None, "Tipo de exercício desconhecido."
    if slug != "todos" and slug not in content.MODULO_POR_SLUG:
        return None, "Módulo não encontrado."
    if slug == "todos" and tipo != "revisao":
        return None, "Escolha um módulo para este exercício."
    if slug != "todos" and tipo not in content.MODULO_POR_SLUG[slug]["exercicios"]:
        return None, "Este exercício não está disponível neste módulo."
    quantidade = max(3, min(int(quantidade), 10))

    if tipo == "flashcards":
        cartas = list(content.MODULO_POR_SLUG[slug]["palavras"])
        random.shuffle(cartas)
        modulo = content.MODULO_POR_SLUG[slug]
        return {"tipo": tipo, "cartas": [{
            "palavra_id": p["id"], "en": p["en"], "pt": p["pt"], "pron": p["pron"],
            "ex_en": p["ex_en"], "ex_pt": p["ex_pt"], "visual": _visual(p),
            "dica_emoji": p.get("dica_emoji"),
            "frente": "ingles" if (p.get("so_texto") or modulo["frente"] == "ingles") else "imagem",
        } for p in cartas]}, None

    if tipo == "revisao":
        e = _estado(sessao)
        pool = [p for p in _elegiveis("revisao", slug) if p["indice"] in e["ok"] or p["indice"] in e["fr"]]
        if not pool:
            return None, "Ainda não há palavras para revisar. Estude um módulo e pratique primeiro."
        pool.sort(key=lambda p: (p["indice"] not in e["fr"], random.random()))  # as difíceis primeiro
        escolhidas = pool[:quantidade]
        random.shuffle(escolhidas)
        perguntas = []
        for p in escolhidas:
            tipos = tipos_da_palavra(p)
            if tipos:
                perguntas.append(_pergunta(p, random.choice(tipos)))
        return {"tipo": tipo, "perguntas": perguntas}, None

    if tipo == "associacao":
        pool = _elegiveis(tipo, slug)
        # em cada rodada, 4 palavras de um mesmo grupo quando possível
        escolhidas = random.sample(pool, min(4, len(pool)))
        itens = [{"palavra_id": p["id"], "visual": _visual(p)} for p in escolhidas]
        palavras = [_opcao(p, "associacao") for p in escolhidas]
        random.shuffle(palavras)
        return {"tipo": tipo, "itens": itens, "palavras": palavras}, None

    pool = _elegiveis(tipo, slug)
    random.shuffle(pool)
    return {"tipo": tipo, "perguntas": [_pergunta(p, tipo) for p in pool[:quantidade]]}, None


# ------------------------------------------------------------------ Correção
def responder(sessao, palavra_id, tipo, resposta, tentativa=1):
    """Confere a resposta no servidor e atualiza pontos e progresso. Devolve (resultado, erro)."""
    palavra = content.POR_ID.get(palavra_id)
    if palavra is None:
        return None, "Palavra não encontrada."
    if tipo not in TIPOS_COM_PERGUNTA:
        return None, "Tipo de exercício inválido."
    if not isinstance(resposta, str) or not resposta or len(resposta) > 120:
        return None, "Resposta inválida."
    modulo = content.MODULO_POR_SLUG[palavra["modulo"]]
    if tipo not in modulo["exercicios"]:
        return None, "Este exercício não existe neste módulo."
    if not isinstance(tentativa, int) or tentativa < 1:
        tentativa = 1

    certa = resposta_correta(palavra, tipo)
    acertou = resposta.strip() == certa
    e = _estado(sessao)
    ganhou = 0
    if tentativa == 1:  # só conta na estatística a primeira tentativa de cada pergunta
        e["resp"] += 1
        if acertou:
            e["ac"] += 1
    if acertou:
        e["ok"].add(palavra["indice"])
        e["fr"].discard(palavra["indice"])
        if tentativa == 1:
            ganhou = PONTOS_POR_ACERTO
            e["pts"] += ganhou
    else:
        e["fr"].add(palavra["indice"])  # errar não tira pontos: a palavra só volta para a revisão
    _salvar(sessao, e)

    explicacao = f'{palavra["en"]} = {palavra["pt"]}. Exemplo: {palavra["ex_en"]} ({palavra["ex_pt"]})'
    if modulo.get("modo_quiz") == "som" and tipo == "quiz":
        explicacao = f'A letra {palavra["en"]} se pronuncia "{palavra["pron"]}". Exemplo: {palavra["ex_en"]}'
    if acertou:
        mensagem = random.choice(MENSAGENS_ACERTO)
    else:
        mensagem = "Quase! Errar faz parte de aprender. A resposta certa aparece abaixo."
    return {
        "correto": acertou, "resposta_correta": certa, "mensagem": mensagem,
        "explicacao": explicacao, "pontos_ganhos": ganhou, "resumo": resumo(sessao),
    }, None


def marcar_carta(sessao, palavra_id, sabia):
    """Flashcards: o aluno diz se já sabe a palavra ou se quer rever. Não gera pontos."""
    palavra = content.POR_ID.get(palavra_id)
    if palavra is None:
        return None, "Palavra não encontrada."
    e = _estado(sessao)
    if sabia:
        e["ok"].add(palavra["indice"])
        e["fr"].discard(palavra["indice"])
    else:
        e["fr"].add(palavra["indice"])
    _salvar(sessao, e)
    return {"resumo": resumo(sessao)}, None


def com_imagem(dados, resolver):
    """Acrescenta o endereço da imagem real (se existir) em cada visual enviado ao navegador.
    `resolver(palavra_id)` devolve o endereço ou None. Usado pelo Flask e pelo Pyodide."""
    def ajustar(v, palavra_id):
        if v and v.get("tipo") != "cor":
            v["imagem"] = resolver(palavra_id)
    for c in dados.get("cartas", []):
        ajustar(c["visual"], c["palavra_id"])
    for q in dados.get("perguntas", []):
        if "visual" in q:
            ajustar(q["visual"], q["palavra_id"])
    for i in dados.get("itens", []):
        ajustar(i["visual"], i["palavra_id"])
    return dados
