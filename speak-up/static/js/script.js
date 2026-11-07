/* Speak Up: interações no navegador.
   A conferência das respostas e a pontuação acontecem no servidor (Python/Flask).
   Aqui ficam apenas: menu, áudio (síntese de voz do navegador) e a interface dos exercícios. */
(() => {
  'use strict';

  const $ = (sel, raiz = document) => raiz.querySelector(sel);
  const $$ = (sel, raiz = document) => Array.from(raiz.querySelectorAll(sel));
  const esc = (t) => String(t).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  /* ---------------------------------------------------------- Menu (celular) */
  const botaoMenu = $('.menu-botao');
  if (botaoMenu) {
    botaoMenu.addEventListener('click', () => {
      const aberto = botaoMenu.getAttribute('aria-expanded') === 'true';
      botaoMenu.setAttribute('aria-expanded', String(!aberto));
      $('#menu-principal').classList.toggle('aberto', !aberto);
    });
  }

  /* ---------------------------------------------------------- Áudio (Web Speech API) */
  const temVoz = 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
  const avisoVoz = $('#aviso-voz');
  let vozIngles = null;

  function mostrarAviso(texto) {
    if (avisoVoz) { avisoVoz.textContent = texto; avisoVoz.hidden = false; }
  }

  function procurarVoz() {
    const vozes = window.speechSynthesis.getVoices();
    vozIngles = vozes.find((v) => v.lang === 'en-US') ||
      vozes.find((v) => v.lang && v.lang.toLowerCase().startsWith('en')) || null;
    return vozes.length;
  }

  if (!temVoz) {
    mostrarAviso('Seu navegador não tem voz para ler em inglês. Você ainda pode estudar com as imagens e a pronúncia escrita. Para ouvir, tente uma versão atual do Chrome, Edge, Safari ou Firefox.');
  } else {
    procurarVoz();
    window.speechSynthesis.addEventListener('voiceschanged', procurarVoz);
    setTimeout(() => {
      if (procurarVoz() > 0 && !vozIngles) {
        mostrarAviso('Não encontramos uma voz em inglês neste aparelho. O áudio pode sair com sotaque do português. Instale uma voz em inglês nas configurações do sistema.');
      }
    }, 1500);
  }

  function falar(texto, velocidade = 0.9) {
    if (!temVoz) { mostrarAviso('Seu navegador não permite ouvir a pronúncia.'); return; }
    window.speechSynthesis.cancel();
    const fala = new SpeechSynthesisUtterance(texto);
    fala.lang = 'en-US';
    fala.rate = velocidade;
    if (vozIngles) fala.voice = vozIngles;
    fala.onerror = () => mostrarAviso('Não foi possível tocar o áudio agora. Verifique o volume do aparelho e tente de novo.');
    window.speechSynthesis.speak(fala);
  }

  document.addEventListener('click', (e) => {
    const b = e.target.closest('[data-falar]');
    if (b) falar(b.dataset.falar, parseFloat(b.dataset.velocidade || '0.9'));
  });

  /* Atualiza pontos, estatísticas e barras de progresso a partir do "resumo" calculado pelo Python. */
  function hidratar(resumo) {
    if (!resumo) return;
    const texto = (id, valor) => { const e = document.getElementById(id); if (e) e.textContent = valor; };
    texto('pontos', resumo.pontos);
    texto('e-pontos', resumo.pontos);
    texto('e-sabidas', `${resumo.palavras_sabidas}/${resumo.total_palavras}`);
    texto('e-modulos', `${resumo.modulos_concluidos}/${resumo.total_modulos}`);
    texto('e-resp', resumo.respondidas);
    texto('e-prec', `${resumo.precisao}%`);
    texto('e-rev', resumo.para_revisar);
    const vazio = document.getElementById('caixa-vazio');
    if (vazio) vazio.hidden = resumo.respondidas > 0 || resumo.palavras_sabidas > 0;
    $$('[data-modulo]').forEach((caixa) => {
      const m = resumo.modulos && resumo.modulos[caixa.dataset.modulo];
      if (!m) return;
      const barra = $('.barra', caixa);
      if (barra) {
        barra.setAttribute('aria-valuenow', m.pct);
        const preenchimento = $('span', barra);
        if (preenchimento) preenchimento.style.width = `${m.pct}%`;
      }
      const legenda = $('small', caixa);
      if (legenda) legenda.textContent = m.concluido ? '✓ Concluído' : `${m.sabidas} de ${m.total} palavras sabidas`;
    });
  }
  function atualizarPontos(resumo) { hidratar(resumo); }

  /* ---------------------------------------------------------- Dois modos de funcionamento
     - Flask (servidor): as chamadas vão para /api/... e o progresso fica no cookie de sessão.
     - Estático (GitHub Pages): o Python (logic.py) roda AQUI, no navegador, via Pyodide,
       e o progresso fica no localStorage. O build (build_static.py) liga este modo. */
  const ESTATICO = window.SPEAKUP_ESTATICO === true;
  const IR_PROGRESSO = ESTATICO ? 'progresso.html' : '/progresso';
  const PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.js';
  const ARQUIVOS_PY = ['content.py', 'logic.py', 'ponte.py'];
  const CHAVE_ESTADO = 'speakup_estado';
  const CHAVE_RESUMO = 'speakup_resumo';

  // localStorage pode estar bloqueado (aba anônima, por exemplo): nesse caso guardamos só na memória.
  const memoria = {};
  function ler(chave) {
    try { const v = window.localStorage.getItem(chave); return v === null ? (memoria[chave] || '') : v; }
    catch (_) { return memoria[chave] || ''; }
  }
  function gravar(chave, valor) {
    if (valor === null || valor === undefined) {
      delete memoria[chave];
      try { window.localStorage.removeItem(chave); } catch (_) { /* sem armazenamento */ }
      return;
    }
    memoria[chave] = valor;
    try { window.localStorage.setItem(chave, valor); } catch (_) { /* fica só na memória */ }
  }

  let motor = null;      // promessa do módulo Python "ponte"
  let imagens = '{}';    // imagens reais opcionais (imagens.json)

  function carregarMotor() {
    if (!motor) {
      motor = (async () => {
        if (typeof window.loadPyodide !== 'function') {
          await new Promise((ok, falha) => {
            const tag = document.createElement('script');
            tag.src = PYODIDE_URL;
            tag.onload = ok;
            tag.onerror = () => falha(new Error('Falha ao baixar o Pyodide.'));
            document.head.appendChild(tag);
          });
        }
        const pyodide = await window.loadPyodide();
        for (const nome of ARQUIVOS_PY) {
          const r = await fetch(`python/${nome}`);
          if (!r.ok) throw new Error(`Arquivo python/${nome} não encontrado.`);
          pyodide.FS.writeFile(`/home/pyodide/${nome}`, new Uint8Array(await r.arrayBuffer()));
        }
        try {
          const r = await fetch('imagens.json');
          if (r.ok) imagens = JSON.stringify(await r.json());
        } catch (_) { /* sem imagens reais: usa emojis */ }
        pyodide.runPython("import sys\nif '/home/pyodide' not in sys.path:\n    sys.path.insert(0, '/home/pyodide')");
        const ponte = pyodide.pyimport('ponte');
        // Devolvemos funções simples (e não o objeto Python direto) para a promessa não confundir o proxy com algo "esperável".
        return {
          exercicio: (...args) => ponte.exercicio(...args),
          responder: (...args) => ponte.responder(...args),
          carta: (...args) => ponte.carta(...args),
        };
      })().catch((erro) => {
        motor = null; // permite tentar de novo
        console.error(erro);
        throw new Error('Não foi possível iniciar o Python no navegador. Verifique sua internet e recarregue a página.');
      });
    }
    return motor;
  }

  // Lê a resposta (texto JSON) do Python, guarda o novo progresso e atualiza a tela.
  function concluir(textoJson) {
    const saida = JSON.parse(textoJson);
    if (saida.estado !== undefined) gravar(CHAVE_ESTADO, saida.estado === null ? null : JSON.stringify(saida.estado));
    if (saida.resumo) { gravar(CHAVE_RESUMO, JSON.stringify(saida.resumo)); hidratar(saida.resumo); }
    if (saida.erro) throw new Error(saida.erro);
    return saida.dados;
  }

  async function api(url, opcoes) {
    let resp;
    try {
      resp = await fetch(url, opcoes);
    } catch (_) {
      throw new Error('Não foi possível conectar ao servidor. Verifique sua internet e tente de novo.');
    }
    const dados = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(dados.erro || 'Algo deu errado. Tente de novo.');
    return dados;
  }
  const enviar = (url, corpo) => api(url, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corpo),
  });

  const chamar = ESTATICO ? {
    exercicio: async (tipo, modulo, n) => { const py = await carregarMotor(); return concluir(py.exercicio(ler(CHAVE_ESTADO), tipo, modulo, String(n), imagens)); },
    responder: async (corpo) => { const py = await carregarMotor(); return concluir(py.responder(ler(CHAVE_ESTADO), JSON.stringify(corpo))); },
    carta: async (corpo) => { const py = await carregarMotor(); return concluir(py.carta(ler(CHAVE_ESTADO), JSON.stringify(corpo))); },
    reiniciar: async () => { gravar(CHAVE_ESTADO, null); gravar(CHAVE_RESUMO, null); },
  } : {
    exercicio: (tipo, modulo, n) => api(`/api/exercicio?tipo=${encodeURIComponent(tipo)}&modulo=${encodeURIComponent(modulo)}&n=${n}`),
    responder: (corpo) => enviar('/api/responder', corpo),
    carta: (corpo) => enviar('/api/carta', corpo),
    reiniciar: () => enviar('/api/reiniciar', {}),
  };

  // Na versão estática, as páginas vêm com progresso zerado: preenchemos com o que está salvo no navegador.
  if (ESTATICO) {
    try { hidratar(JSON.parse(ler(CHAVE_RESUMO) || 'null')); } catch (_) { /* resumo inválido: ignora */ }
  }

  /* ---------------------------------------------------------- Página: Meu progresso */
  const btnReiniciar = $('#btn-reiniciar');
  if (btnReiniciar) {
    btnReiniciar.addEventListener('click', async () => {
      if (!window.confirm('Apagar todos os seus pontos e palavras sabidas? Isso não pode ser desfeito.')) return;
      try { await chamar.reiniciar(); window.location.reload(); } catch (err) { window.alert(err.message); }
    });
  }

  /* ---------------------------------------------------------- Página: Exercícios */
  const palco = $('#palco');
  if (!palco || !window.SPEAKUP_MODULOS) return;

  const META = window.SPEAKUP_MODULOS;
  const selModulo = $('#sel-modulo');
  const botoesTipo = $$('.tipo');
  const ajuda = $('#ajuda-tipo');
  const NOME_TIPO = {
    flashcards: 'Flashcards', quiz: 'Quiz de imagens', associacao: 'Associação de palavras',
    traducao: 'Tradução inglês → português', traducao_inversa: 'Tradução português → inglês', revisao: 'Revisão',
  };
  let ultimo = null; // { tipo, modulo }

  function tipoDisponivel(tipo) {
    if (selModulo.value === 'todos') return tipo === 'revisao';
    return META[selModulo.value].exercicios.includes(tipo);
  }

  function atualizarSeletor() {
    botoesTipo.forEach((b) => {
      const ok = tipoDisponivel(b.dataset.tipo);
      b.disabled = !ok;
      b.setAttribute('aria-disabled', String(!ok));
    });
    if (selModulo.value === 'todos') {
      ajuda.textContent = 'Com "Todos os módulos", só a Revisão está disponível. Ela usa as palavras que você já praticou.';
    } else if (META[selModulo.value].exercicios.length < 6) {
      ajuda.textContent = 'Algumas atividades não aparecem neste módulo porque não fazem sentido para esse conteúdo (por exemplo, imagens para frases).';
    } else {
      ajuda.textContent = '';
    }
  }
  selModulo.addEventListener('change', atualizarSeletor);
  botoesTipo.forEach((b) => b.addEventListener('click', () => iniciar(b.dataset.tipo)));

  function visualHTML(v, classe = '') {
    if (v.imagem) return `<img class="visual visual-img ${classe}" src="${esc(v.imagem)}" alt="${esc(v.alt)}">`;
    if (v.tipo === 'cor') return `<span class="visual visual-cor ${classe}" role="img" aria-label="${esc(v.alt)}" style="background:${esc(v.valor)}"></span>`;
    if (v.tipo === 'texto') return `<span class="visual visual-texto ${classe}" role="img" aria-label="${esc(v.alt)}">${esc(v.valor)}</span>`;
    return `<span class="visual visual-emoji ${classe}" role="img" aria-label="${esc(v.alt)}">${esc(v.valor)}</span>`;
  }
  const botaoOuvir = (texto) => `<button type="button" class="btn btn-pequeno btn-claro" data-falar="${esc(texto)}">🔊 Ouvir</button>`;

  async function iniciar(tipo) {
    ultimo = { tipo, modulo: selModulo.value };
    botoesTipo.forEach((b) => b.classList.toggle('ativo', b.dataset.tipo === tipo));
    palco.innerHTML = '<p class="vazio">Carregando…</p>';
    try {
      const dados = await chamar.exercicio(tipo, selModulo.value, 6);
      if (tipo === 'flashcards') flashcards(dados);
      else if (tipo === 'associacao') associacao(dados);
      else perguntas(dados);
      palco.focus({ preventScroll: false });
    } catch (err) {
      palco.innerHTML = `<div class="feedback erro"><p>${esc(err.message)}</p></div>`;
    }
  }

  function fim(titulo, linhas) {
    palco.innerHTML = `
      <div class="resultado">
        <p class="emoji-grande" aria-hidden="true">🎉</p>
        <h2>${esc(titulo)}</h2>
        ${linhas.map((l) => `<p>${esc(l)}</p>`).join('')}
        <p class="acoes">
          <button type="button" class="btn btn-primario" id="de-novo">Praticar de novo</button>
          <a class="btn btn-claro" href="${IR_PROGRESSO}">Ver meu progresso</a>
        </p>
      </div>`;
    $('#de-novo').addEventListener('click', () => iniciar(ultimo.tipo));
    $('#de-novo').focus();
  }

  /* ----- Quiz, tradução e revisão: uma pergunta por vez ----- */
  function perguntas(dados) {
    const lista = dados.perguntas;
    if (!lista.length) { palco.innerHTML = '<p class="vazio">Não há perguntas disponíveis.</p>'; return; }
    let i = 0, acertos = 0, pontos = 0;

    function mostrar() {
      const q = lista[i];
      palco.innerHTML = `
        <p class="contador">Pergunta ${i + 1} de ${lista.length}</p>
        <h2 class="enunciado">${esc(q.enunciado)}</h2>
        ${q.visual ? `<div class="centro">${visualHTML(q.visual, 'grande')}</div>` : ''}
        ${q.texto ? `<p class="texto-pergunta" ${q.tipo === 'traducao' ? 'lang="en"' : ''}>${esc(q.texto)}</p>` : ''}
        ${q.tipo === 'traducao' ? `<p class="centro">${botaoOuvir(q.falar)}</p>` : ''}
        <div class="opcoes" role="group" aria-label="Alternativas">
          ${q.opcoes.map((o, n) => `<button type="button" class="opcao" data-n="${n}">${esc(o.rotulo)}</button>`).join('')}
        </div>
        <div id="retorno" role="status" aria-live="polite"></div>`;
      $$('.opcao').forEach((b) => b.addEventListener('click', () => responder(q, b)));
    }

    async function responder(q, botao) {
      const escolhida = q.opcoes[Number(botao.dataset.n)];
      $$('.opcao').forEach((b) => { b.disabled = true; });
      try {
        const r = await chamar.responder({ palavra_id: q.palavra_id, tipo: q.tipo, resposta: escolhida.valor, tentativa: 1 });
        atualizarPontos(r.resumo);
        pontos += r.pontos_ganhos;
        if (r.correto) acertos += 1;
        $$('.opcao').forEach((b) => {
          const o = q.opcoes[Number(b.dataset.n)];
          if (o.valor === r.resposta_correta) { b.classList.add('certa'); b.innerHTML = `✓ ${b.innerHTML}`; }
          else if (b === botao) { b.classList.add('errada'); b.innerHTML = `✗ ${b.innerHTML}`; }
        });
        const ultima = i === lista.length - 1;
        $('#retorno').innerHTML = `
          <div class="feedback ${r.correto ? 'certo' : 'erro'}">
            <p><strong>${r.correto ? '✓' : '✗'} ${esc(r.mensagem)}${r.pontos_ganhos ? ` +${r.pontos_ganhos} pontos` : ''}</strong></p>
            ${r.correto ? '' : `<p>Resposta certa: <strong>${esc(r.resposta_correta)}</strong></p>`}
            <p>${esc(r.explicacao)}</p>
            ${q.tipo === 'quiz' && q.falar ? `<p>${botaoOuvir(q.falar)}</p>` : ''}
            <button type="button" class="btn btn-primario" id="proxima">${ultima ? 'Ver resultado' : 'Próxima pergunta'}</button>
          </div>`;
        const prox = $('#proxima');
        prox.focus();
        prox.addEventListener('click', () => {
          if (ultima) fim(`Você acertou ${acertos} de ${lista.length}!`, [`Pontos ganhos nesta rodada: ${pontos}.`, 'Cada palavra que você erra volta na Revisão para você treinar de novo.']);
          else { i += 1; mostrar(); $('#palco').focus(); }
        });
      } catch (err) {
        $$('.opcao').forEach((b) => { b.disabled = false; });
        $('#retorno').innerHTML = `<div class="feedback erro"><p>${esc(err.message)}</p></div>`;
      }
    }
    mostrar();
  }

  /* ----- Associação: ligar imagens às palavras ----- */
  function associacao(dados) {
    const tentativas = {}, feitos = new Set();
    let imagemEscolhida = null, acertos = 0, pontos = 0;
    palco.innerHTML = `
      <h2 class="enunciado">Ligue cada imagem à palavra certa</h2>
      <p class="ajuda">Escolha uma imagem e depois a palavra em inglês.</p>
      <div class="assoc">
        <div class="assoc-col" role="group" aria-label="Imagens">
          ${dados.itens.map((it) => `<button type="button" class="assoc-item" data-id="${esc(it.palavra_id)}" aria-pressed="false">${visualHTML(it.visual)}</button>`).join('')}
        </div>
        <div class="assoc-col" role="group" aria-label="Palavras em inglês">
          ${dados.palavras.map((p) => `<button type="button" class="assoc-palavra" data-valor="${esc(p.valor)}">${esc(p.rotulo)}</button>`).join('')}
        </div>
      </div>
      <div id="retorno" role="status" aria-live="polite"></div>`;
    const retorno = $('#retorno');

    $$('.assoc-item').forEach((b) => b.addEventListener('click', () => {
      if (b.disabled) return;
      $$('.assoc-item').forEach((x) => { x.setAttribute('aria-pressed', 'false'); x.classList.remove('escolhido'); });
      b.setAttribute('aria-pressed', 'true'); b.classList.add('escolhido');
      imagemEscolhida = b;
      retorno.innerHTML = '<p class="ajuda">Agora escolha a palavra.</p>';
    }));

    $$('.assoc-palavra').forEach((b) => b.addEventListener('click', async () => {
      if (!imagemEscolhida) { retorno.innerHTML = '<div class="feedback erro"><p>Primeiro escolha uma imagem.</p></div>'; return; }
      const id = imagemEscolhida.dataset.id;
      tentativas[id] = (tentativas[id] || 0) + 1;
      try {
        const r = await chamar.responder({ palavra_id: id, tipo: 'associacao', resposta: b.dataset.valor, tentativa: tentativas[id] });
        atualizarPontos(r.resumo);
        pontos += r.pontos_ganhos;
        if (r.correto) {
          if (tentativas[id] === 1) acertos += 1;
          feitos.add(id);
          imagemEscolhida.disabled = true; imagemEscolhida.classList.add('certa'); imagemEscolhida.classList.remove('escolhido');
          b.disabled = true; b.classList.add('certa'); b.innerHTML = `✓ ${b.innerHTML}`;
          imagemEscolhida = null;
          retorno.innerHTML = `<div class="feedback certo"><p><strong>✓ ${esc(r.mensagem)}${r.pontos_ganhos ? ` +${r.pontos_ganhos} pontos` : ''}</strong></p><p>${esc(r.explicacao)}</p></div>`;
          if (feitos.size === dados.itens.length) {
            setTimeout(() => fim('Rodada completa!', [`Você acertou ${acertos} de ${dados.itens.length} de primeira.`, `Pontos nesta rodada: ${pontos}.`]), 1400);
          }
        } else {
          retorno.innerHTML = '<div class="feedback erro"><p><strong>✗ Ainda não.</strong> Tudo bem, tente outra palavra para esta imagem.</p></div>';
        }
      } catch (err) {
        retorno.innerHTML = `<div class="feedback erro"><p>${esc(err.message)}</p></div>`;
      }
    }));
  }

  /* ----- Flashcards ----- */
  function flashcards(dados) {
    const cartas = dados.cartas;
    let i = 0, sabidas = 0;

    function frente() {
      const c = cartas[i];
      palco.innerHTML = `
        <p class="contador">Carta ${i + 1} de ${cartas.length}</p>
        <div class="carta">
          ${c.frente === 'imagem' ? visualHTML(c.visual, 'grande') + '<p class="ajuda">Você sabe dizer isto em inglês?</p>'
            : `<p class="texto-pergunta" lang="en">${esc(c.en)}</p><p class="ajuda">Você sabe o que isto significa?</p>`}
          ${c.frente === 'ingles' ? botaoOuvir(c.en) : ''}
        </div>
        <p class="centro"><button type="button" class="btn btn-primario btn-grande" id="revelar">Mostrar resposta</button></p>`;
      $('#revelar').focus();
      $('#revelar').addEventListener('click', verso);
    }

    function verso() {
      const c = cartas[i];
      palco.innerHTML = `
        <p class="contador">Carta ${i + 1} de ${cartas.length}</p>
        <div class="carta verso">
          ${c.frente === 'imagem' ? visualHTML(c.visual) : ''}
          <p class="texto-pergunta" lang="en">${esc(c.frente === 'imagem' && c.visual.tipo !== 'texto' ? c.en.toUpperCase() : c.en)}</p>
          <p class="pt">${esc(c.pt)}</p>
          <p class="pron">Pronúncia: <em>${esc(c.pron)}</em></p>
          <p class="exemplo"><span lang="en">${esc(c.ex_en)}</span><br><small>${esc(c.ex_pt)}</small></p>
          <p>${botaoOuvir(c.en)} <button type="button" class="btn btn-pequeno btn-claro" data-falar="${esc(c.ex_en)}">🔊 Frase</button></p>
        </div>
        <p class="acoes centro">
          <button type="button" class="btn btn-claro" id="rever">Preciso rever</button>
          <button type="button" class="btn btn-primario" id="sei">Já sei</button>
        </p>
        <div id="retorno" role="status" aria-live="polite"></div>`;
      $('#sei').focus();
      $('#sei').addEventListener('click', () => marcar(true));
      $('#rever').addEventListener('click', () => marcar(false));
    }

    async function marcar(sabia) {
      try {
        const r = await chamar.carta({ palavra_id: cartas[i].palavra_id, sabia });
        atualizarPontos(r.resumo);
        if (sabia) sabidas += 1;
        if (i === cartas.length - 1) {
          fim('Flashcards concluídos!', [`Você marcou ${sabidas} de ${cartas.length} cartas como "já sei".`,
            'As cartas que você quis rever ficam disponíveis na Revisão.']);
        } else { i += 1; frente(); }
      } catch (err) {
        $('#retorno').innerHTML = `<div class="feedback erro"><p>${esc(err.message)}</p></div>`;
      }
    }
    frente();
  }

  /* ---------------------------------------------------------- Início automático (?modulo=...&tipo=...) */
  const params = new URLSearchParams(window.location.search);
  if (params.get('modulo') && META[params.get('modulo')]) selModulo.value = params.get('modulo');
  else if (params.get('modulo') === 'todos') selModulo.value = 'todos';
  atualizarSeletor();
  if (ESTATICO) {
    // Começa a baixar o Python assim que a página abre, para os exercícios abrirem mais rápido.
    palco.innerHTML = '<p class="vazio">🐍 Carregando o Python no seu navegador… Na primeira vez pode levar alguns segundos e precisa de internet.</p>';
    carregarMotor()
      .then(() => { if (!ultimo) palco.innerHTML = '<p class="vazio">Python pronto! Escolha uma atividade acima para começar. 🚀</p>'; })
      .catch((err) => { if (!ultimo) palco.innerHTML = `<div class="feedback erro"><p>${esc(err.message)}</p></div>`; });
  }
  if (params.get('tipo') && NOME_TIPO[params.get('tipo')] && tipoDisponivel(params.get('tipo'))) iniciar(params.get('tipo'));
})();
