# Speak Up

**Aprenda inglês. Ganhe confiança. Fale sem medo!**

Speak Up é uma startup fictícia de educação e tecnologia (EdTech) que ensina inglês para iniciantes. Este repositório contém o site da plataforma: aulas por módulos, vocabulário com imagem, tradução, pronúncia e frase de exemplo, além de flashcards, quizzes, associação de palavras, revisão, pontuação e acompanhamento de progresso.

## Tecnologias

| Tecnologia | Para que serve |
|---|---|
| **Python 3.10+** | Linguagem principal: regras, correção das respostas, pontuação e progresso |
| **Flask** | Rotas, páginas (templates Jinja) e API em JSON |
| **HTML5 / CSS3** | Estrutura e estilo responsivo (sem frameworks de CSS) |
| **JavaScript (puro)** | Interface dos exercícios e áudio (Web Speech API do navegador) |
| **Pyodide** | Python rodando no navegador (versão para o GitHub Pages) |
| **gunicorn** | Servidor de produção da versão Flask (usado só na hospedagem) |

## Estrutura de pastas

```
speak-up/
├── app.py               # Rotas das páginas e da API (Flask)
├── content.py           # Módulos e vocabulário (edite aqui para mudar o conteúdo)
├── logic.py             # Perguntas, correção, pontos e progresso (usado pelo Flask E pelo Pyodide)
├── ponte.py             # Liga o JavaScript ao logic.py na versão que roda no navegador (Pyodide)
├── build_static.py      # Gera a versão estática (pasta docs/) para o GitHub Pages
├── docs/                # Versão estática pronta para o GitHub Pages (gerada pelo build_static.py)
├── requirements.txt     # Dependências Python
├── Procfile             # Comando de início para hospedagens (gunicorn)
├── iniciar.bat          # Atalho para iniciar no Windows
├── iniciar.sh           # Atalho para iniciar no Linux/macOS
├── README.md
├── .gitignore
├── templates/           # Páginas HTML (Jinja)
│   ├── base.html        # Cabeçalho, menu e rodapé
│   ├── _macros.html     # Peças reutilizáveis (imagem da palavra, botões de áudio, barra)
│   ├── index.html       # Página inicial
│   ├── aulas.html       # Lista de módulos
│   ├── modulo.html      # Aula de um módulo
│   ├── exercicios.html  # Flashcards, quizzes, associação, tradução e revisão
│   ├── progresso.html   # Pontos e progresso
│   ├── erro.html        # Mensagem amigável para falhas
│   └── 404.html
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   ├── images/          # logo.png, logo-icon.png, favicon.png
│   │   └── vocab/       # (opcional) fotos/ilustrações das palavras
│   └── audio/           # (opcional) arquivos de áudio próprios
├── tests/test_app.py    # Testes automáticos
└── .github/workflows/tests.yml  # Roda os testes a cada push no GitHub
```

## Como executar localmente

Você precisa do Python 3.10 ou mais novo ([python.org](https://www.python.org/downloads/)). No Windows, marque **"Add python.exe to PATH"** na instalação.

**Jeito mais fácil**
- **Windows:** dê dois cliques em `iniciar.bat`.
- **Linux/macOS:** `bash iniciar.sh`

**Pelo terminal** (no VS Code: Terminal → Novo Terminal, **dentro da pasta `speak-up`**)

```bash
python -m pip install -r requirements.txt
python app.py
```

Abra **http://127.0.0.1:5000** no navegador. Para parar, use `Ctrl + C`.

> Usamos `python -m pip` (e não só `pip`) porque, no Windows, o atalho `pip` sozinho muitas vezes não é reconhecido. Se o próprio `python` não for reconhecido, troque por `py`:
> `py -m pip install -r requirements.txt` e depois `py app.py`.

O ambiente virtual (`python -m venv .venv`) é **opcional**. Se quiser usar no Windows e o PowerShell bloquear a ativação, rode uma vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, ou apenas pule o ambiente virtual.

Para rodar os testes: `python -m unittest discover -s tests -v`

### Erros comuns e como resolver

| Mensagem ou sintoma | Causa provável | Solução |
|---|---|---|
| `No module named 'flask'` | Bibliotecas não instaladas | `python -m pip install -r requirements.txt` |
| `'python' não é reconhecido` | Python fora do PATH do Windows | Use `py` no lugar de `python`, ou reinstale marcando "Add to PATH" |
| `'pip' não é reconhecido` | Atalho do pip fora do PATH | Use `python -m pip ...` |
| `can't open file 'app.py'` ou `TemplateNotFound` | Terminal em outra pasta | Entre na pasta `speak-up` (`cd speak-up`) antes de rodar |
| `Address already in use` / porta ocupada | Outro programa usa a porta 5000 | Feche o outro programa ou rode com outra porta: `set PORT=5001` (Windows CMD), `$env:PORT=5001` (PowerShell) e depois `python app.py` |
| A página não abre ao dar dois cliques em `index.html` ou nos arquivos de `templates/` | Os arquivos de `templates/` são modelos do Flask, não páginas prontas | Rode `python app.py` e abra `http://127.0.0.1:5000` |
| Site em branco, sem estilo, ou o GitHub Pages mostrando o README | Pages apontando para a pasta errada, ou publicando a versão Flask | Em Settings → Pages, escolha branch `main` e pasta `/docs` (veja a seção abaixo) |
| "Não foi possível iniciar o Python no navegador" | Sem internet na primeira abertura, ou CDN bloqueada pela rede | Conecte-se à internet e recarregue; em redes escolares, libere `cdn.jsdelivr.net` |
| Sem som nos botões 🔊 | Navegador sem voz em inglês | Teste no Chrome ou Edge atuais e confira o volume; o site avisa na tela |
| Progresso sumiu | Cookies foram limpos ou outro navegador | O progresso fica no cookie do navegador (veja "Como cada recurso funciona") |

Se aparecer outra mensagem de erro, copie o texto do terminal e a linha em que ela acontece: isso mostra a causa.

## Como publicar no GitHub

1. Crie um repositório vazio em [github.com/new](https://github.com/new) (por exemplo, `speak-up`).
2. No terminal, dentro da pasta do projeto:

```bash
git init
git add .
git commit -m "Speak Up: primeira versão"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/speak-up.git
git push -u origin main
```

Depois do envio, o GitHub executa os testes automaticamente (aba **Actions**).

### Duas formas de colocar o site no ar

O **GitHub Pages só hospeda arquivos prontos (HTML, CSS e JS)** e não executa o servidor Flask. Por isso o projeto tem **duas versões**, que usam o **mesmo código Python de lógica** (`logic.py`):

| | Versão Flask (servidor) | Versão estática com Pyodide (GitHub Pages) |
|---|---|---|
| Onde roda o Python | No servidor | **No navegador do aluno**, via [Pyodide](https://pyodide.org) |
| Hospedagem | Render, Railway, PythonAnywhere... | **GitHub Pages** (grátis) |
| Progresso salvo em | Cookie de sessão | `localStorage` do navegador |
| Como gerar | `python app.py` | `python build_static.py` (gera a pasta `docs/`) |

#### Publicar no GitHub Pages (Python com Pyodide)

1. Gere a versão estática (a pasta `docs/` já vem pronta no projeto, mas gere de novo sempre que mudar o conteúdo ou o código):

```bash
python build_static.py
```

2. Envie tudo ao GitHub (`git add .`, `git commit`, `git push`, como acima).
3. No repositório, abra **Settings → Pages**. Em **Build and deployment**, escolha **Deploy from a branch**, branch **main** e pasta **/docs**, e clique em **Save**.
4. Em alguns minutos o site fica em `https://SEU-USUARIO.github.io/NOME-DO-REPOSITORIO/`.

**Para testar a versão estática no seu computador** (precisa de internet, pois o Pyodide vem da CDN jsDelivr):

```bash
python -m http.server 8000 --directory docs
```

Abra `http://127.0.0.1:8000`. Abrir os arquivos de `docs/` com dois cliques (`file://`) **não funciona**, porque o navegador bloqueia o carregamento dos arquivos Python.

**Como o Pyodide é usado**
- Nas páginas de exercícios, o navegador baixa o Pyodide (versão fixa 314.0.7, em `static/js/script.js`), grava `content.py`, `logic.py` e `ponte.py` (pasta `docs/python/`) no sistema de arquivos do Pyodide e importa `ponte`.
- `ponte.py` recebe o progresso (texto JSON do `localStorage`), usa `logic.py` para gerar perguntas, corrigir e pontuar, e devolve o novo progresso.
- **Limites:** a primeira abertura dos exercícios baixa alguns MB e leva alguns segundos; é preciso internet nessa primeira vez (depois o navegador costuma guardar em cache). As páginas de aula e de progresso não precisam do Pyodide. Como o código roda no navegador, o aluno pode ver a lógica e as respostas, o que não é problema num site de estudo.

#### Publicar a versão Flask (servidor)

Conecte o repositório a uma hospedagem que rode Python, como Render, Railway ou PythonAnywhere (os planos gratuitos mudam; confira no site de cada uma).

Exemplo no Render (Web Service ligado ao repositório):

| Campo | Valor |
|---|---|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app` |
| Variável `SECRET_KEY` | uma sequência longa e aleatória (veja abaixo) |
| Variável `SESSION_COOKIE_SECURE` | `1` (o site precisa estar em HTTPS) |

Gerar uma `SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"`

## Configurações

| Variável | Para que serve | Padrão |
|---|---|---|
| `SECRET_KEY` | Assina o cookie de progresso. **Defina em produção.** | chave de desenvolvimento |
| `SESSION_COOKIE_SECURE` | `1` envia o cookie só por HTTPS | desligado |
| `FLASK_DEBUG` | `1` liga o modo de depuração (só local) | desligado |
| `PORT` | Porta ao rodar `python app.py` | 5000 |

## Como cada recurso funciona (e seus limites)

- **Imagens:** cada palavra usa um **emoji grande** como ilustração (com texto alternativo para leitores de tela). Cores aparecem como amostras e números/letras como texto. Para usar fotos ou ilustrações próprias, salve o arquivo em `static/images/vocab/` com o **id da palavra** (por exemplo, `animais-dog.png`, `frutas-alimentos-apple.webp`; formatos: webp, png, jpg, svg). O site passa a usar a imagem automaticamente. O id aparece nos testes e é montado como `slug-do-módulo` + `-` + `palavra`.
- **Áudio:** usa a **síntese de voz do navegador** (Web Speech API), em inglês dos EUA. Não há arquivos de áudio gravados. A qualidade depende da voz inglesa instalada no aparelho, e alguns navegadores não oferecem voz. O site avisa quando não encontra o recurso. Se você tiver gravações, a pasta `static/audio/` está pronta, mas o código atual não as usa.
- **Pontuação:** 10 pontos por acerto na primeira tentativa. Errar não tira pontos; a palavra apenas entra na lista de revisão.
- **Progresso:** na versão Flask, no **cookie de sessão assinado** (até 1 ano); na versão estática, no **`localStorage`** do navegador. Nas duas, sem nome, e-mail ou outros dados pessoais. Limpar os dados do site ou trocar de aparelho zera o progresso. Uma palavra conta como "sabida" ao ser acertada ou marcada como "Já sei" nos flashcards; o módulo é concluído quando todas as palavras são sabidas. Se um dia for necessário guardar em banco de dados, a lógica está concentrada em `logic.py` (funções `_estado` e `_salvar`).
- **Conferência das respostas:** na versão Flask, acontece no servidor (`/api/responder`) e o navegador não recebe a resposta certa antes de responder. Na versão estática, acontece em Python no próprio navegador (Pyodide).

## Como adicionar conteúdo

Em `content.py`, adicione uma linha com `_w(inglês, português, pronúncia, frase_en, frase_pt, visual)` na lista do módulo. Para criar um módulo novo, acrescente um item em `MODULOS`. Os testes verificam se o conteúdo está completo.

## Licença e uso

Projeto educacional/acadêmico. Speak Up é uma empresa fictícia.
