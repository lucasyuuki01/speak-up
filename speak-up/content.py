"""Conteúdo pedagógico da Speak Up.

Todo o vocabulário fica aqui, separado da lógica (logic.py) e das rotas (app.py).
Para adicionar uma palavra, basta incluir uma linha com a função `_w(...)`.

Pronúncia simplificada: é uma aproximação feita com letras do português.
  rr  = "h" aspirado, como um sopro leve (hello -> rrelôu)
  th  = língua entre os dentes (three -> thrí)
  â   = som neutro, bem curtinho
"""

import re

# Tipos de exercício disponíveis
TODOS = ["flashcards", "quiz", "associacao", "traducao", "traducao_inversa", "revisao"]
SO_TEXTO = ["flashcards", "traducao", "traducao_inversa", "revisao"]  # sem exercícios de imagem


def _w(en, pt, pron, ex_en, ex_pt, visual, **extra):
    """Cria uma palavra. `visual` = (tipo, valor): ("emoji","🍎"), ("cor","#E53935") ou ("texto","7")."""
    d = {"en": en, "pt": pt, "pron": pron, "ex_en": ex_en, "ex_pt": ex_pt,
         "visual": {"tipo": visual[0], "valor": visual[1]}}
    d.update(extra)
    return d


# ---------------------------------------------------------------- Módulo 1
_letras = [
    ("A", "êi", "apple", "maçã", "🍎"), ("B", "bi", "book", "livro", "📖"),
    ("C", "si", "cat", "gato", "🐱"), ("D", "di", "dog", "cachorro", "🐶"),
    ("E", "i", "egg", "ovo", "🥚"), ("F", "éf", "fish", "peixe", "🐟"),
    ("G", "dji", "girl", "menina", "👧"), ("H", "êitch", "house", "casa", "🏠"),
    ("I", "ái", "ice cream", "sorvete", "🍦"), ("J", "djêi", "juice", "suco", "🧃"),
    ("K", "kêi", "key", "chave", "🔑"), ("L", "él", "lemon", "limão", "🍋"),
    ("M", "ém", "milk", "leite", "🥛"), ("N", "én", "nose", "nariz", "👃"),
    ("O", "ôu", "orange", "laranja", "🍊"), ("P", "pi", "pizza", "pizza", "🍕"),
    ("Q", "kiú", "queen", "rainha", "👑"), ("R", "ár", "rain", "chuva", "🌧️"),
    ("S", "és", "sun", "sol", "☀️"), ("T", "ti", "tree", "árvore", "🌳"),
    ("U", "iú", "umbrella", "guarda-chuva", "☂️"), ("V", "vi", "violin", "violino", "🎻"),
    ("W", "dâbliu", "water", "água", "💧"), ("X", "éks", "xylophone", "xilofone", "🎹"),
    ("Y", "uái", "yellow", "amarelo", "🟡"), ("Z", "zi", "zebra", "zebra", "🦓"),
]
ALFABETO = [
    _w(L, f"letra {L}", pron, f"{L} is for {ex}.", f"{L} é de {ex} ({pt}).", ("texto", L),
       dica_emoji=emo)
    for L, pron, ex, pt, emo in _letras
]

# ---------------------------------------------------------------- Módulo 2
NUMEROS_CORES = [
    _w("one", "um", "uân", "I have one dog.", "Eu tenho um cachorro.", ("texto", "1"), grupo="numeros"),
    _w("two", "dois", "tú", "I have two books.", "Eu tenho dois livros.", ("texto", "2"), grupo="numeros"),
    _w("three", "três", "thrí", "I have three cats.", "Eu tenho três gatos.", ("texto", "3"), grupo="numeros"),
    _w("four", "quatro", "fór", "I have four pens.", "Eu tenho quatro canetas.", ("texto", "4"), grupo="numeros"),
    _w("five", "cinco", "fáiv", "I have five apples.", "Eu tenho cinco maçãs.", ("texto", "5"), grupo="numeros"),
    _w("six", "seis", "síks", "I have six keys.", "Eu tenho seis chaves.", ("texto", "6"), grupo="numeros"),
    _w("seven", "sete", "sévn", "I have seven bananas.", "Eu tenho sete bananas.", ("texto", "7"), grupo="numeros"),
    _w("eight", "oito", "êit", "I have eight birds.", "Eu tenho oito pássaros.", ("texto", "8"), grupo="numeros"),
    _w("nine", "nove", "náin", "I have nine eggs.", "Eu tenho nove ovos.", ("texto", "9"), grupo="numeros"),
    _w("ten", "dez", "tén", "I have ten fingers.", "Eu tenho dez dedos.", ("texto", "10"), grupo="numeros"),
    _w("red", "vermelho", "réd", "The apple is red.", "A maçã é vermelha.", ("cor", "#E53935"), grupo="cores"),
    _w("blue", "azul", "blú", "The sky is blue.", "O céu é azul.", ("cor", "#1E5BD8"), grupo="cores"),
    _w("green", "verde", "grín", "The tree is green.", "A árvore é verde.", ("cor", "#2E9E4F"), grupo="cores"),
    _w("yellow", "amarelo", "iélou", "The sun is yellow.", "O sol é amarelo.", ("cor", "#FFD21F"), grupo="cores"),
    _w("orange", "laranja (cor)", "órinj", "The bag is orange.", "A bolsa é laranja.", ("cor", "#FF8A00"), grupo="cores"),
    _w("black", "preto", "blék", "The cat is black.", "O gato é preto.", ("cor", "#111827"), grupo="cores"),
    _w("white", "branco", "uáit", "The milk is white.", "O leite é branco.", ("cor", "#FFFFFF"), grupo="cores"),
    _w("pink", "rosa", "pínk", "The pig is pink.", "O porco é rosa.", ("cor", "#F472B6"), grupo="cores"),
]

# ---------------------------------------------------------------- Módulo 3
ANIMAIS = [
    _w("dog", "cachorro", "dóg", "I have a dog.", "Eu tenho um cachorro.", ("emoji", "🐶")),
    _w("cat", "gato", "két", "The cat is small.", "O gato é pequeno.", ("emoji", "🐱")),
    _w("bird", "pássaro", "bérd", "The bird is blue.", "O pássaro é azul.", ("emoji", "🐦")),
    _w("fish", "peixe", "fích", "The fish is orange.", "O peixe é laranja.", ("emoji", "🐟")),
    _w("horse", "cavalo", "rrórs", "The horse is big.", "O cavalo é grande.", ("emoji", "🐴")),
    _w("cow", "vaca", "cáu", "The cow is white.", "A vaca é branca.", ("emoji", "🐮")),
    _w("pig", "porco", "pig", "The pig is pink.", "O porco é rosa.", ("emoji", "🐷")),
    _w("rabbit", "coelho", "rébit", "The rabbit is white.", "O coelho é branco.", ("emoji", "🐰")),
]

# ---------------------------------------------------------------- Módulo 4
FRUTAS_ALIMENTOS = [
    _w("apple", "maçã", "épol", "I like the apple.", "Eu gosto da maçã.", ("emoji", "🍎")),
    _w("banana", "banana", "banéna", "The banana is yellow.", "A banana é amarela.", ("emoji", "🍌")),
    _w("lemon", "limão", "lémon", "The lemon is green.", "O limão é verde.", ("emoji", "🍋")),
    _w("grape", "uva", "grêip", "The grape is purple.", "A uva é roxa.", ("emoji", "🍇")),
    _w("strawberry", "morango", "stróbéri", "The strawberry is red.", "O morango é vermelho.", ("emoji", "🍓")),
    _w("bread", "pão", "bréd", "I eat bread.", "Eu como pão.", ("emoji", "🍞")),
    _w("milk", "leite", "mílk", "I drink milk.", "Eu bebo leite.", ("emoji", "🥛")),
    _w("rice", "arroz", "ráis", "I eat rice.", "Eu como arroz.", ("emoji", "🍚")),
]

# ---------------------------------------------------------------- Módulo 5
OBJETOS = [
    _w("book", "livro", "búk", "I have a book.", "Eu tenho um livro.", ("emoji", "📖")),
    _w("chair", "cadeira", "tchér", "The chair is brown.", "A cadeira é marrom.", ("emoji", "🪑")),
    _w("phone", "celular, telefone", "fôun", "I have a phone.", "Eu tenho um celular.", ("emoji", "📱")),
    _w("key", "chave", "kí", "I have a key.", "Eu tenho uma chave.", ("emoji", "🔑")),
    _w("bag", "bolsa", "bég", "The bag is black.", "A bolsa é preta.", ("emoji", "👜")),
    _w("pen", "caneta", "pén", "I have a blue pen.", "Eu tenho uma caneta azul.", ("emoji", "🖊️")),
    _w("clock", "relógio de parede", "clák", "The clock is on the wall.", "O relógio está na parede.", ("emoji", "🕒")),
    _w("door", "porta", "dór", "The door is open.", "A porta está aberta.", ("emoji", "🚪")),
]

# ---------------------------------------------------------------- Módulo 6
# `so_texto`: palavras cuja imagem seria ambígua (mãe/mulher, pai/homem...).
# Elas aparecem nos flashcards e na tradução, mas não nos exercícios de imagem.
FAMILIA = [
    _w("family", "família", "fémili", "I love my family.", "Eu amo minha família.", ("emoji", "👨‍👩‍👧‍👦")),
    _w("man", "homem", "mén", "The man is tall.", "O homem é alto.", ("emoji", "👨")),
    _w("woman", "mulher", "uúmân", "The woman is happy.", "A mulher está feliz.", ("emoji", "👩")),
    _w("boy", "menino", "bói", "The boy is small.", "O menino é pequeno.", ("emoji", "👦")),
    _w("girl", "menina", "guérl", "The girl has a book.", "A menina tem um livro.", ("emoji", "👧")),
    _w("baby", "bebê", "bêibi", "The baby is happy.", "O bebê está feliz.", ("emoji", "👶")),
    _w("mother", "mãe", "máder", "My mother is happy.", "Minha mãe está feliz.", ("emoji", "👩"), so_texto=True),
    _w("father", "pai", "fáder", "My father has a car.", "Meu pai tem um carro.", ("emoji", "👨"), so_texto=True),
    _w("brother", "irmão", "bráder", "My brother has a dog.", "Meu irmão tem um cachorro.", ("emoji", "👦"), so_texto=True),
    _w("sister", "irmã", "síster", "My sister has a cat.", "Minha irmã tem um gato.", ("emoji", "👧"), so_texto=True),
]

# ---------------------------------------------------------------- Módulo 7
CORPO = [
    _w("eye", "olho", "ái", "I have two eyes.", "Eu tenho dois olhos.", ("emoji", "👁️")),
    _w("ear", "orelha", "ír", "I have two ears.", "Eu tenho duas orelhas.", ("emoji", "👂")),
    _w("nose", "nariz", "nôuz", "I have one nose.", "Eu tenho um nariz.", ("emoji", "👃")),
    _w("mouth", "boca", "máuth", "I have one mouth.", "Eu tenho uma boca.", ("emoji", "👄")),
    _w("hand", "mão", "rrénd", "I have two hands.", "Eu tenho duas mãos.", ("emoji", "✋")),
    _w("foot", "pé", "fút", "I have one foot here.", "Eu tenho um pé aqui.", ("emoji", "🦶")),
    _w("leg", "perna", "lég", "I have two legs.", "Eu tenho duas pernas.", ("emoji", "🦵")),
    _w("tooth", "dente", "túth", "I have one tooth here.", "Eu tenho um dente aqui.", ("emoji", "🦷")),
]

# ---------------------------------------------------------------- Módulo 8
LUGARES = [
    _w("house", "casa", "rráus", "This is my house.", "Esta é a minha casa.", ("emoji", "🏠")),
    _w("school", "escola", "skúl", "I go to school.", "Eu vou para a escola.", ("emoji", "🏫")),
    _w("hospital", "hospital", "rróspitâl", "The hospital is big.", "O hospital é grande.", ("emoji", "🏥")),
    _w("beach", "praia", "bítch", "I like the beach.", "Eu gosto da praia.", ("emoji", "🏖️")),
    _w("car", "carro", "cár", "The car is red.", "O carro é vermelho.", ("emoji", "🚗")),
    _w("bus", "ônibus", "bâs", "The bus is yellow.", "O ônibus é amarelo.", ("emoji", "🚌")),
    _w("bike", "bicicleta", "báik", "I have a blue bike.", "Eu tenho uma bicicleta azul.", ("emoji", "🚲")),
    _w("airplane", "avião", "érplêin", "The airplane is white.", "O avião é branco.", ("emoji", "✈️")),
]

# ---------------------------------------------------------------- Módulo 9
SAUDACOES = [
    _w("hello", "olá", "rrelôu", "Hello! I am Ana.", "Olá! Eu sou a Ana.", ("emoji", "👋")),
    _w("hi", "oi", "rrái", "Hi, Pedro!", "Oi, Pedro!", ("emoji", "🙋")),
    _w("good morning", "bom dia", "gúd mórnin", "Good morning, teacher!", "Bom dia, professor!", ("emoji", "🌅")),
    _w("good afternoon", "boa tarde", "gúd afternún", "Good afternoon, Ana.", "Boa tarde, Ana.", ("emoji", "🌤️")),
    _w("good evening", "boa noite (ao chegar)", "gúd ívnin", "Good evening, everyone.", "Boa noite, pessoal.", ("emoji", "🌆")),
    _w("good night", "boa noite (ao ir dormir)", "gúd náit", "Good night, mom.", "Boa noite, mãe.", ("emoji", "🌙")),
    _w("goodbye", "tchau", "gudbái", "Goodbye, Ana!", "Tchau, Ana!", ("emoji", "👋")),
    _w("thank you", "obrigado, obrigada", "thénk iú", "Thank you, Pedro.", "Obrigado, Pedro.", ("emoji", "🙏")),
    _w("please", "por favor", "plíz", "Water, please.", "Água, por favor.", ("emoji", "🤲")),
    _w("sorry", "desculpe", "sóri", "Sorry, Ana.", "Desculpe, Ana.", ("emoji", "😔")),
    _w("my name is", "meu nome é", "mái nêim iz", "My name is Pedro.", "Meu nome é Pedro.", ("emoji", "🏷️")),
    _w("nice to meet you", "prazer em conhecer você", "náis tu mít iú", "Nice to meet you, Ana.", "Prazer em conhecer você, Ana.", ("emoji", "🤝")),
]

# ---------------------------------------------------------------- Módulo 10
FRASES = [
    _w("How are you?", "Como você está?", "rráu ár iú", "Hi, Ana! How are you?", "Oi, Ana! Como você está?", ("emoji", "💬")),
    _w("I am fine, thank you.", "Eu estou bem, obrigado(a).", "ái ém fáin, thénk iú", "I am fine, thank you.", "Eu estou bem, obrigado(a).", ("emoji", "😊")),
    _w("What is your name?", "Qual é o seu nome?", "uát iz iór nêim", "Hello! What is your name?", "Olá! Qual é o seu nome?", ("emoji", "❓")),
    _w("Do you speak English?", "Você fala inglês?", "dú iú spík ínglich", "Excuse me, do you speak English?", "Com licença, você fala inglês?", ("emoji", "🗣️")),
    _w("I speak a little English.", "Eu falo um pouco de inglês.", "ái spík â lítol ínglich", "I speak a little English.", "Eu falo um pouco de inglês.", ("emoji", "🔤")),
    _w("I do not understand.", "Eu não entendo.", "ái dú nót anderstând", "Sorry, I do not understand.", "Desculpe, eu não entendo.", ("emoji", "🤔")),
    _w("Can you repeat, please?", "Você pode repetir, por favor?", "kén iú ripít, plíz", "Can you repeat, please?", "Você pode repetir, por favor?", ("emoji", "🔁")),
    _w("Where is the bathroom?", "Onde fica o banheiro?", "uér iz dâ bétrum", "Excuse me, where is the bathroom?", "Com licença, onde fica o banheiro?", ("emoji", "🚻")),
    _w("How much is it?", "Quanto custa?", "rráu mâtch iz it", "How much is it, please?", "Quanto custa, por favor?", ("emoji", "💰")),
    _w("I need help.", "Eu preciso de ajuda.", "ái níd rrélp", "Excuse me, I need help.", "Com licença, eu preciso de ajuda.", ("emoji", "🆘")),
]

# ---------------------------------------------------------------- Módulos
MODULOS = [
    {"slug": "alfabeto", "titulo": "Alfabeto e pronúncia", "icone": "🔤", "nivel": "Nível 1",
     "objetivo": "Conhecer as 26 letras do alfabeto e como se pronuncia o nome de cada uma.",
     "explicacao": "O alfabeto inglês tem as mesmas 26 letras do português, mas os nomes das letras são diferentes. "
                   "Ouça cada letra e repita em voz alta. Cada letra vem com uma palavra de exemplo.",
     "dica": "Cuidado com E (i) e I (ái): são as letras que mais confundem quem está começando.",
     "modo_quiz": "som", "frente": "imagem",
     "exercicios": ["flashcards", "quiz", "revisao"], "palavras": ALFABETO},
    {"slug": "numeros-cores", "titulo": "Números e cores", "icone": "🔢", "nivel": "Nível 1",
     "objetivo": "Contar de 1 a 10 e dizer 8 cores básicas em inglês.",
     "explicacao": "Números e cores aparecem o tempo todo no dia a dia: preço, idade, roupa, objetos. "
                   "Em inglês, a cor vem antes do nome: red apple (maçã vermelha).",
     "dica": "Em three, o TH é feito com a ponta da língua entre os dentes. Não é 'tri'.",
     "modo_quiz": "imagem", "frente": "imagem", "exercicios": TODOS, "palavras": NUMEROS_CORES},
    {"slug": "animais", "titulo": "Animais", "icone": "🐶", "nivel": "Nível 1",
     "objetivo": "Reconhecer e dizer o nome de 8 animais comuns.",
     "explicacao": "Aprender animais é um jeito divertido de começar. Observe a imagem, leia a palavra e ouça a pronúncia.",
     "dica": "Em inglês, 'a dog' significa 'um cachorro'. A palavra 'a' é o 'um/uma'.",
     "modo_quiz": "imagem", "frente": "imagem", "exercicios": TODOS, "palavras": ANIMAIS},
    {"slug": "frutas-alimentos", "titulo": "Frutas e alimentos", "icone": "🍎", "nivel": "Nível 1",
     "objetivo": "Dizer o nome de 8 frutas e alimentos do dia a dia.",
     "explicacao": "Esses são alimentos que você vê no mercado e na cozinha. Em frases simples, use 'I eat' (eu como) e 'I drink' (eu bebo).",
     "dica": "Banana em inglês se pronuncia 'banéna', com o A do meio forte.",
     "modo_quiz": "imagem", "frente": "imagem", "exercicios": TODOS, "palavras": FRUTAS_ALIMENTOS},
    {"slug": "objetos", "titulo": "Objetos do cotidiano", "icone": "🔑", "nivel": "Nível 1",
     "objetivo": "Nomear 8 objetos que você usa todos os dias.",
     "explicacao": "Objetos da casa e da bolsa: coisas que você pode apontar e nomear. Treine falando o nome quando vir o objeto.",
     "dica": "Em inglês, 'phone' é a palavra usada tanto para telefone quanto para celular.",
     "modo_quiz": "imagem", "frente": "imagem", "exercicios": TODOS, "palavras": OBJETOS},
    {"slug": "familia-pessoas", "titulo": "Família e pessoas", "icone": "👨‍👩‍👧‍👦", "nivel": "Nível 2",
     "objetivo": "Dizer o nome de pessoas e de membros da família.",
     "explicacao": "Aprenda palavras para pessoas e família. Em inglês, 'my' significa 'meu/minha': my mother (minha mãe).",
     "dica": "As palavras mother, father, brother e sister ficam só nos flashcards e na tradução, porque uma imagem sozinha não mostra o parentesco.",
     "modo_quiz": "imagem", "frente": "imagem", "exercicios": TODOS, "palavras": FAMILIA},
    {"slug": "corpo", "titulo": "Partes do corpo", "icone": "🖐️", "nivel": "Nível 2",
     "objetivo": "Reconhecer 8 partes do corpo em inglês.",
     "explicacao": "Partes do corpo são úteis para falar de saúde e de situações do dia a dia. Aponte para a parte do corpo enquanto fala.",
     "dica": "Alguns plurais são diferentes: one foot (um pé), two feet (dois pés). One tooth (um dente), two teeth (dois dentes).",
     "modo_quiz": "imagem", "frente": "imagem", "exercicios": TODOS, "palavras": CORPO},
    {"slug": "lugares-transportes", "titulo": "Lugares e transportes", "icone": "🚌", "nivel": "Nível 2",
     "objetivo": "Nomear lugares e meios de transporte comuns.",
     "explicacao": "Lugares onde você vive e meios de transporte que você usa. Pratique frases como 'I go to school' (eu vou para a escola).",
     "dica": "A palavra 'bus' se pronuncia 'bâs', com um som curto e neutro.",
     "modo_quiz": "imagem", "frente": "imagem", "exercicios": TODOS, "palavras": LUGARES},
    {"slug": "saudacoes", "titulo": "Saudações e apresentações", "icone": "👋", "nivel": "Nível 2",
     "objetivo": "Cumprimentar, agradecer e se apresentar em inglês.",
     "explicacao": "Estas expressões servem para começar uma conversa com educação. Aprenda a frase inteira, não palavra por palavra.",
     "dica": "Em inglês, 'good evening' é usado ao chegar à noite e 'good night' ao se despedir ou ir dormir.",
     "modo_quiz": "imagem", "frente": "ingles", "so_texto": True, "exercicios": SO_TEXTO, "palavras": SAUDACOES},
    {"slug": "frases-basicas", "titulo": "Frases básicas do cotidiano", "icone": "💬", "nivel": "Nível 3",
     "objetivo": "Usar frases simples para pedir ajuda, perguntar e dizer que não entendeu.",
     "explicacao": "São frases prontas que ajudam em situações reais. Mesmo sabendo poucas palavras, você consegue se comunicar com elas.",
     "dica": "Não existe vergonha em dizer 'I do not understand'. É a frase mais útil de quem está aprendendo.",
     "modo_quiz": "imagem", "frente": "ingles", "so_texto": True, "exercicios": SO_TEXTO, "palavras": FRASES},
]

NOMES_EXERCICIOS = {
    "flashcards": "Flashcards", "quiz": "Quiz de imagens", "associacao": "Associação de palavras",
    "traducao": "Tradução: inglês → português", "traducao_inversa": "Tradução: português → inglês",
    "revisao": "Revisão",
}


def slugify(texto):
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


# Índices globais (montados uma vez, ao iniciar)
PALAVRAS = []      # lista global de palavras, na ordem do conteúdo
POR_ID = {}        # id -> palavra
MODULO_POR_SLUG = {}

for _num, _m in enumerate(MODULOS, start=1):
    _m["numero"] = _num
    MODULO_POR_SLUG[_m["slug"]] = _m
    for _p in _m["palavras"]:
        _p["modulo"] = _m["slug"]
        _p["id"] = f'{_m["slug"]}-{slugify(_p["en"])}'
        _p["indice"] = len(PALAVRAS)
        _p.setdefault("grupo", _m["slug"])
        if _m.get("so_texto"):
            _p["so_texto"] = True
        # texto alternativo (alt): nunca revela a resposta em inglês nos exercícios
        _tipo_visual = _p["visual"]["tipo"]
        if _tipo_visual == "emoji":
            _p["alt"] = f'Ilustração: {_p["pt"]}'
        elif _tipo_visual == "cor":
            _p["alt"] = "Amostra de cor"
        else:
            _p["alt"] = _p["visual"]["valor"]
        PALAVRAS.append(_p)
        POR_ID[_p["id"]] = _p
