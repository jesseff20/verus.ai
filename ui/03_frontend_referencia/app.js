/**
 * app.js — Lógica do chat do Agente Bravonix com validação de token.
 *
 * Fluxo:
 *   1. Verificar session token salvo (cookie/localStorage)
 *   2. Se inválido → exibir tela de validação de token promocional
 *   3. Se válido → exibir chat
 *   4. Todas as requisições enviam o token via cookie
 */

(function () {
  'use strict';

  const API_BASE = window.BRAVONIX_API_BASE || '';
  const SESSION_COOKIE = 'bravo_access_session';

  const state = {
    conversationId: null,
    messages: [],
    isProcessing: false,
    theme: 'light',
    accessToken: null,
    isAuthorized: false,
  };

  const dom = {};

  function cacheDom() {
    dom.app = document.getElementById('app');
    dom.chat = document.getElementById('bnx-chat');
    dom.chatInner = document.getElementById('bnx-chat-inner');
    dom.input = document.getElementById('bnx-input');
    dom.sendBtn = document.getElementById('bnx-send');
    dom.themeBtn = document.getElementById('bnx-theme-btn');
    dom.newBtn = document.getElementById('bnx-new-btn');
    dom.statusDot = document.getElementById('bnx-status-dot');
    dom.inputArea = document.querySelector('.bnx-input-area');
    dom.header = document.querySelector('.bnx-header');
    dom.scrollBottom = document.getElementById('bnx-scroll-bottom');
    dom.offlineBanner = document.getElementById('bnx-offline-banner');
    dom.charCount = document.getElementById('bnx-char-count');
  }

  // ── Cookie Helpers ─────────────────────────────────────────────────────

  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
  }

  function setCookie(name, value, days) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = name + '=' + encodeURIComponent(value) +
      '; expires=' + expires + '; path=/; SameSite=Lax';
  }

  // ── Token Validation Screen ────────────────────────────────────────────

  function renderTokenGate() {
    dom.chat.style.display = 'none';
    if (dom.inputArea) dom.inputArea.style.display = 'none';

    const main = document.getElementById('app');
    const gate = document.createElement('div');
    gate.id = 'bnx-token-gate';
    gate.innerHTML = `
      <div class="bnx-token-gate">
        <div class="bnx-token-card">
          <img src="assets/logo.png" alt="Bravonix" class="bnx-token-logo">
          <h2>Agente Bravonix</h2>
          <p>Insira o token promocional para acessar o assistente de IA.</p>
          <div class="bnx-token-input-wrap">
            <input type="password" id="bnx-token-input"
                   placeholder="Token promocional" autocomplete="off"
                   class="bnx-token-input">
            <button id="bnx-token-submit" class="bnx-token-btn">Validar</button>
          </div>
          <p id="bnx-token-error" class="bnx-token-error"></p>
        </div>
      </div>`;
    main.appendChild(gate);

    const input = document.getElementById('bnx-token-input');
    const btn = document.getElementById('bnx-token-submit');
    const errEl = document.getElementById('bnx-token-error');

    async function validateToken() {
      const token = input.value.trim();
      if (!token) { errEl.textContent = 'Digite o token promocional.'; return; }
      btn.disabled = true;
      btn.textContent = 'Validando...';
      errEl.textContent = '';

      try {
        const res = await fetch(API_BASE + '/api/access/validate-promo', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token }),
          credentials: 'same-origin',
        });
        const data = await res.json();
        if (res.ok && data.valid) {
          setCookie(SESSION_COOKIE, data.session_token, 1);  // 24h
          state.accessToken = data.session_token;
          state.isAuthorized = true;
          gate.remove();
          dom.chat.style.display = '';
          if (dom.inputArea) dom.inputArea.style.display = '';
          initChat();
        } else {
          errEl.textContent = data.detail || 'Token inválido.';
          btn.disabled = false;
          btn.textContent = 'Validar';
        }
      } catch (e) {
        errEl.textContent = 'Erro de conexão com o servidor.';
        btn.disabled = false;
        btn.textContent = 'Validar';
      }
    }

    btn.addEventListener('click', validateToken);
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') validateToken(); });
    setTimeout(() => input.focus(), 100);
  }

  // ── Theme ──────────────────────────────────────────────────────────────

  function initTheme() {
    state.theme = localStorage.getItem('bnx-theme') || 'light';
    applyTheme(state.theme);
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    state.theme = theme;
    localStorage.setItem('bnx-theme', theme);

    if (dom.themeBtn) {
      const svg = dom.themeBtn.querySelector('svg path');
      if (svg) {
        svg.setAttribute('d', theme === 'dark'
          ? 'M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z'
          : 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z');
      }
      dom.themeBtn.setAttribute('aria-label', theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro');
    }

    // Header logo is now logo.png (theme-agnostic) — no theme switching needed.
    // Avatar icons are also logo.png — no theme switching needed.
  }

  function toggleTheme() { applyTheme(state.theme === 'dark' ? 'light' : 'dark'); }

  // ── Status ─────────────────────────────────────────────────────────────

  async function checkStatus() {
    try {
      const res = await fetch(API_BASE + '/api/health');
      const data = await res.json();
      if (dom.statusDot) {
        dom.statusDot.className = 'bnx-status-dot ' + (data.watsonx_configured ? 'online' : 'offline');
        dom.statusDot.title = data.watsonx_configured ? 'WatsonX configurado' : 'Modo fallback';
      }
    } catch (err) {
      if (dom.statusDot) {
        dom.statusDot.className = 'bnx-status-dot offline';
        dom.statusDot.title = 'Servidor indisponível';
      }
    }
  }

  // ── Chat Messages ──────────────────────────────────────────────────────

  function scrollToBottom() {
    if (dom.chat) { dom.chat.scrollTop = dom.chat.scrollHeight; }
    updateScrollButton();
  }

  function updateScrollButton() {
    if (!dom.chat || !dom.scrollBottom) return;
    var isNearBottom = dom.chat.scrollHeight - dom.chat.scrollTop - dom.chat.clientHeight < 120;
    dom.scrollBottom.hidden = isNearBottom;
  }

  function clearChat() {
    if (dom.chatInner) dom.chatInner.innerHTML = '';
    state.messages = [];
    state.conversationId = null;
    if (typeof BRAVONIX_VB !== 'undefined' && BRAVONIX_VB.destroyCharts) BRAVONIX_VB.destroyCharts();
    renderWelcome();
  }

  function getTimestamp() { return new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }); }
  function generateId() { return Math.random().toString(36).substring(2, 10); }

  function renderMessage(type, content, visualBlocks, actions, sources, responseContext) {
    const msgEl = document.createElement('div');
    msgEl.className = 'bnx-message ' + type;
    msgEl.dataset.id = generateId();

    const avatar = document.createElement('div');
    avatar.className = 'bnx-message-avatar';
    if (type === 'user') {
      avatar.textContent = 'U';
    } else {
      const img = document.createElement('img');
      img.src = 'assets/logo.png';
      img.alt = 'Bravonix';
      avatar.appendChild(img);
    }
    msgEl.appendChild(avatar);

    const body = document.createElement('div');
    body.className = 'bnx-message-body';
    const bubble = document.createElement('div');
    bubble.className = 'bnx-message-bubble';

    if (type === 'user') {
      bubble.textContent = content;
    } else {
      bubble.innerHTML = simpleMarkdown(content);
    }
    body.appendChild(bubble);

    if (visualBlocks && visualBlocks.length > 0 && type === 'agent') {
      const vb = document.createElement('div');
      vb.className = 'bnx-visual-blocks';
      BRAVONIX_VB.renderBlocks(visualBlocks, vb, responseContext || {});
      body.appendChild(vb);
    }

    if (sources && sources.length > 0 && type === 'agent') {
      body.appendChild(renderSources(sources));
    }

    if (actions && actions.length > 0 && type === 'agent') {
      const ac = document.createElement('div');
      ac.className = 'bnx-block-actions';
      ac.style.marginTop = '8px';
      for (const a of actions) {
        if (a.label && (a.label.includes('Nova') || a.label.includes('Conversa') || a.label.toLowerCase().includes('new'))) continue;
        const btn = document.createElement('button');
        btn.className = 'bnx-action-btn ' + (a.type === 'primary' ? 'primary' : '');
        btn.textContent = a.label;
        ac.appendChild(btn);
      }
      body.appendChild(ac);
    }

    // Message action buttons (copy)
    if (type === 'agent') {
      const actionsDiv = document.createElement('div');
      actionsDiv.className = 'bnx-msg-actions';
      const copyBtn = document.createElement('button');
      copyBtn.className = 'bnx-msg-action-btn';
      copyBtn.textContent = 'Copiar';
      copyBtn.addEventListener('click', function () {
        var textToCopy = content;
        // Also include visual block data
        if (visualBlocks && visualBlocks.length) {
          textToCopy += '\n\n' + visualBlocks.map(function (b) {
            return b.title + ': ' + JSON.stringify(b.data);
          }).join('\n');
        }
        if (sources && sources.length) {
          textToCopy += '\n\nFontes:\n' + normalizeSources(sources).map(function (s, i) {
            return '[' + (i + 1) + '] ' + s.title + ' - ' + s.url;
          }).join('\n');
        }
        navigator.clipboard.writeText(textToCopy).then(function () {
          copyBtn.textContent = 'Copiado!';
          copyBtn.classList.add('copied');
          setTimeout(function () {
            copyBtn.textContent = 'Copiar';
            copyBtn.classList.remove('copied');
          }, 2000);
        }).catch(function () {});
      });
      actionsDiv.appendChild(copyBtn);
      body.appendChild(actionsDiv);
    }

    const time = document.createElement('div');
    time.className = 'bnx-message-time';
    time.textContent = getTimestamp();
    body.appendChild(time);
    msgEl.appendChild(body);

    if (dom.chatInner) {
      dom.chatInner.appendChild(msgEl);
      scrollToBottom();
    }
  }

  
// ── Thinking Panel v2 (SSE-driven, real steps) ────────────────────────

// Step definitions (order matters — matches backend emission order)
var THINKING_STEPS_DEF = [
  { id: 'classifying', label: 'Classificando solicitação',   icon: '🔍' },
  { id: 'history',     label: 'Carregando histórico',        icon: '📋' },
  { id: 'tools',       label: 'Executando ferramentas',      icon: '🔧', optional: true },
  { id: 'llm',         label: 'Gerando resposta',            icon: '🧠' },
  { id: 'parsing',     label: 'Extraindo componentes',       icon: '⚙️' },
  { id: 'validating',  label: 'Validando entrega',           icon: '✔', optional: true },
];

// SVG icons for step states
var ICON_PENDING = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6"/></svg>';
var ICON_ACTIVE  = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" class="bnx-spin"><circle cx="8" cy="8" r="6" stroke-dasharray="28" stroke-dashoffset="10" stroke-linecap="round"/></svg>';
var ICON_DONE    = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3,8 6.5,12 13,4"/></svg>';

var _thinkingStartTime = 0;
var _thinkingDotsTimer = null;

function renderLoading() {
  _thinkingStartTime = Date.now();

  var el = document.createElement('div');
  el.className = 'bnx-message agent bnx-thinking-msg';
  el.id = 'bnx-loading-msg';

  // Avatar
  var avatar = document.createElement('div');
  avatar.className = 'bnx-message-avatar';
  var img = document.createElement('img');
  img.src = 'assets/logo.png'; img.alt = 'Bravonix';
  avatar.appendChild(img);

  var body = document.createElement('div');
  body.className = 'bnx-message-body';

  // ── Rich thinking panel ──
  var panel = document.createElement('div');
  panel.className = 'bnx-tp2';
  panel.id = 'bnx-tp2';

  // Header row
  var header = document.createElement('div');
  header.className = 'bnx-tp2-header';

  var headerLeft = document.createElement('div');
  headerLeft.className = 'bnx-tp2-header-left';

  var pulse = document.createElement('span');
  pulse.className = 'bnx-tp2-pulse';

  var title = document.createElement('span');
  title.className = 'bnx-tp2-title';
  title.id = 'bnx-tp2-title';
  title.textContent = 'Processando';

  var dots = document.createElement('span');
  dots.className = 'bnx-tp2-dots';
  dots.id = 'bnx-tp2-dots';
  dots.textContent = '...';

  headerLeft.appendChild(pulse);
  headerLeft.appendChild(title);
  headerLeft.appendChild(dots);

  var timer = document.createElement('span');
  timer.className = 'bnx-tp2-timer';
  timer.id = 'bnx-tp2-timer';
  timer.textContent = '0s';

  header.appendChild(headerLeft);
  header.appendChild(timer);
  panel.appendChild(header);

  // Progress bar
  var progWrap = document.createElement('div');
  progWrap.className = 'bnx-tp2-progress';
  var progFill = document.createElement('div');
  progFill.className = 'bnx-tp2-progress-fill';
  progFill.id = 'bnx-tp2-fill';
  progFill.style.width = '0%';
  progWrap.appendChild(progFill);
  panel.appendChild(progWrap);

  // Steps list
  var stepsList = document.createElement('div');
  stepsList.className = 'bnx-tp2-steps';
  stepsList.id = 'bnx-tp2-steps';

  THINKING_STEPS_DEF.forEach(function (def) {
    var row = document.createElement('div');
    row.className = 'bnx-tp2-step pending';
    row.id = 'bnx-tp2-step-' + def.id;

    var icon = document.createElement('span');
    icon.className = 'bnx-tp2-step-icon';
    icon.innerHTML = ICON_PENDING;

    var lbl = document.createElement('span');
    lbl.className = 'bnx-tp2-step-label';
    lbl.id = 'bnx-tp2-lbl-' + def.id;
    lbl.textContent = def.label;

    var time = document.createElement('span');
    time.className = 'bnx-tp2-step-time';
    time.id = 'bnx-tp2-time-' + def.id;

    row.appendChild(icon);
    row.appendChild(lbl);
    row.appendChild(time);
    stepsList.appendChild(row);
  });

  panel.appendChild(stepsList);
  body.appendChild(panel);
  el.appendChild(avatar);
  el.appendChild(body);

  if (dom.chatInner) {
    dom.chatInner.appendChild(el);
    scrollToBottom();
  }

  // Animated dots timer
  _thinkingDotsTimer = setInterval(function () {
    var d = document.getElementById('bnx-tp2-dots');
    if (d) { var t = Math.floor(Date.now() / 400) % 4; d.textContent = '.'.repeat(t || 1); }
    var tm = document.getElementById('bnx-tp2-timer');
    if (tm) { tm.textContent = ((Date.now() - _thinkingStartTime) / 1000).toFixed(1) + 's'; }
  }, 200);

  // Header status
  var sd = document.getElementById('bnx-status-dot');
  if (sd) { sd.className = 'bnx-status-dot online'; sd.title = 'Processando...'; }
  var fink = document.getElementById('bnx-fink-status');
  if (fink) { fink.textContent = 'Processando...'; fink.classList.add('visible'); }
}

// Called for each thinking SSE event
function updateThinkingStep(step, status, label, elapsed_ms) {
  var row = document.getElementById('bnx-tp2-step-' + step);
  if (!row) {
    if (step && step !== 'unknown') console.warn('[Bravonix] Thinking step desconhecido:', step);
    return;
  }

  var iconEl = row.querySelector('.bnx-tp2-step-icon');
  var lblEl = document.getElementById('bnx-tp2-lbl-' + step);
  var timeEl = document.getElementById('bnx-tp2-time-' + step);

  // Update label if provided
  if (label && lblEl) lblEl.textContent = label;

  // Update state class
  row.className = 'bnx-tp2-step ' + (status || 'active');

  // Update icon
  if (iconEl) {
    if (status === 'done') {
      iconEl.innerHTML = ICON_DONE;
    } else if (status === 'active') {
      iconEl.innerHTML = ICON_ACTIVE;
    } else {
      iconEl.innerHTML = ICON_PENDING;
    }
  }

  // Update time badge
  if (timeEl && elapsed_ms !== undefined && status === 'done') {
    timeEl.textContent = elapsed_ms < 1000 ? elapsed_ms + 'ms' : (elapsed_ms / 1000).toFixed(1) + 's';
  }

  // Update progress bar
  var steps = THINKING_STEPS_DEF;
  var doneCount = steps.filter(function (s) {
    var r = document.getElementById('bnx-tp2-step-' + s.id);
    return r && r.classList.contains('done');
  }).length;
  var fill = document.getElementById('bnx-tp2-fill');
  if (fill) {
    var pct = Math.min(Math.round((doneCount / steps.length) * 95), 95);
    fill.style.width = pct + '%';
  }

  // Update header title to active step label
  if (status === 'active' && label) {
    var t = document.getElementById('bnx-tp2-title');
    if (t) t.textContent = label;
    var fink = document.getElementById('bnx-fink-status');
    if (fink) fink.textContent = label;
  }

  scrollToBottom();
}

// Called when done event received — collapses panel to summary
function finalizeThinkingPanel(totalMs) {
  if (_thinkingDotsTimer) { clearInterval(_thinkingDotsTimer); _thinkingDotsTimer = null; }

  var panel = document.getElementById('bnx-tp2');
  if (!panel) return;

  // Complete progress bar
  var fill = document.getElementById('bnx-tp2-fill');
  if (fill) fill.style.width = '100%';

  // Mark all remaining active steps as done
  THINKING_STEPS_DEF.forEach(function (def) {
    var row = document.getElementById('bnx-tp2-step-' + def.id);
    if (row && row.classList.contains('active')) {
      row.className = 'bnx-tp2-step done';
      var iconEl = row.querySelector('.bnx-tp2-step-icon');
      if (iconEl) iconEl.innerHTML = ICON_DONE;
    }
  });

  // Update header to "Concluído"
  var title = document.getElementById('bnx-tp2-title');
  if (title) title.textContent = 'Concluído';
  var dots = document.getElementById('bnx-tp2-dots');
  if (dots) dots.textContent = '';
  var timer = document.getElementById('bnx-tp2-timer');
  if (timer && totalMs) timer.textContent = (totalMs / 1000).toFixed(1) + 's';

  // Pulse → done
  var pulse = panel.querySelector('.bnx-tp2-pulse');
  if (pulse) pulse.classList.add('done');

  // Collapse after short delay
  setTimeout(function () {
    panel.classList.add('bnx-tp2-collapsed');
    // Remove from DOM after collapse animation
    setTimeout(function () {
      var msg = document.getElementById('bnx-loading-msg');
      if (msg && msg.parentNode) msg.remove();
    }, 400);
  }, 800);
}

function removeLoading() {
  if (_thinkingDotsTimer) { clearInterval(_thinkingDotsTimer); _thinkingDotsTimer = null; }
  var el = document.getElementById('bnx-loading-msg');
  if (el) {
    el.style.opacity = '0';
    el.style.transform = 'translateY(-8px)';
    el.style.transition = 'all 0.25s ease';
    setTimeout(function () { if (el.parentNode) el.remove(); }, 260);
  }
  var sd = document.getElementById('bnx-status-dot');
  if (sd) { sd.className = 'bnx-status-dot online'; sd.title = 'Conectado'; }
  var fink = document.getElementById('bnx-fink-status');
  if (fink) { fink.textContent = ''; fink.classList.remove('visible'); }
}

  

  function renderWelcome() {
    if (!dom.chatInner) return;
    if (BRAVONIX_VB.destroyCharts) BRAVONIX_VB.destroyCharts();
    dom.chatInner.innerHTML = '<div class="bnx-welcome">' +
      '<div class="bnx-welcome-mark"><img src="assets/logo.png" alt="Bravonix" style="width:44px;height:44px;object-fit:contain"></div>' +
      '<h1>Agente Bravonix</h1>' +
      '<p>Assistente de IA com IBM WatsonX para an&aacute;lise documental, dashboards e respostas inteligentes.</p>' +
      '<div class="bnx-welcome-chips">' +
      '<button class="bnx-suggestion-chip" data-prompt="Cenário: Mercado de IA no Brasil em 2025. Contexto: O Brasil tem adotado IA generativa em ritmo acelerado, com aplicações em fintechs, saúde, varejo e indústria. Solicito: faça uma análise completa com dados reais da pesquisa web. Inclua: (1) taxa de adoção por setor com métricas e gráfico de barras, (2) principais casos de uso com tabela comparativa, (3) investimento anual projetado com timeline de crescimento, (4) ranking das empresas que mais utilizam IA com indicadores de maturidade. Use fontes como FGV, Brasscom e McKinsey. Apresente tudo em blocos visuais organizados.">IA nas Empresas</button>' +
      '<button class="bnx-suggestion-chip" data-prompt="Cenário: Comparativo de custos entre provedores de nuvem (AWS, Azure, GCP). Contexto: Empresas brasileiras buscam otimizar gastos com infraestrutura cloud. Solicito: pesquisa web detalhada com (1) tabela comparativa de preços de instâncias similares (2 vCPU, 8GB RAM), (2) métricas de custo por região (US-East, São Paulo), (3) gráfico de tendência de preços nos últimos 12 meses, (4) custos adicionais de transferência de dados e serviços inclusos. Use dados de preços públicos oficiais de cada provedor. Destaque o provedor mais custo-benefício para cada cenário.">Custos de Cloud</button>' +
      '<button class="bnx-suggestion-chip" data-prompt="Cenário: Energia solar no Brasil. Contexto: O Brasil é um dos líderes mundiais em energia solar, com crescimento exponencial nos últimos 5 anos. Solicito: pesquisa web com dados oficiais da ANEEL e ABSOLAR para apresentar (1) capacidade instalada acumulada com gráfico de evolução anual (linha do tempo), (2) ranking dos estados com maior geração com gráfico de barras, (3) investimento total e geração de empregos com métricas, (4) projeção para 2026-2030 com tabela de crescimento esperado. Inclua comparativo com outras fontes renováveis (eólica, hidrelétrica).">Energia Solar Brasil</button>' +
      '<button class="bnx-suggestion-chip" data-prompt="Cenário: Análise de dados financeiros. Contexto: Extraia e analise dados reais da pesquisa web sobre um dos seguintes temas: (a) mercado de criptomoedas com preços e volumes, (b) indicadores macroeconômicos do Brasil (IPCA, SELIC, PIB), (c) desempenho de ações de empresas brasileiras, (d) fluxo de investimento estrangeiro. Solicito: apresente um dashboard completo com (1) métricas principais com indicadores de variação, (2) gráfico de tendência, (3) tabela com dados comparativos, (4) análise de cenários com cards informativos. Use fontes como BCB, IBGE, B3.">Análise Financeira</button>' +
      '<button class="bnx-suggestion-chip" data-prompt="Cenário: Indicadores de saúde no Brasil. Contexto: O sistema de saúde brasileiro enfrenta desafios de eficiência e qualidade. Solicito: pesquisa web com dados oficiais do DataSUS, ANS e OMS para criar (1) painel de indicadores hospitalares com métricas de ocupação de leitos, tempo médio de espera por especialidade e taxa de satisfação, (2) gráfico comparativo entre regiões (Norte, Nordeste, Sudeste, Sul, Centro-Oeste), (3) tabela com ranking dos melhores hospitais por estado, (4) timeline de evolução dos indicadores nos últimos 5 anos. Destaque as principais tendências e gargalos.">Indicadores Hospitalares</button>' +
      '<button class="bnx-suggestion-chip" data-prompt="Cenário: Mercado de veículos elétricos no Brasil. Contexto: A mobilidade elétrica está em expansão no país, com novas montadoras e incentivos fiscais. Solicito: pesquisa web com dados da ABVE e ANFAVEA para gerar (1) gráfico de vendas por marca e por ano (2022-2025), (2) tabela comparativa dos 10 modelos mais vendidos com preços, autonomia e tempo de recarga, (3) mapa de infraestrutura de recarga por estado com métricas, (4) timeline de marco regulatório e incentivos fiscais. Inclua comparativo com países líderes (Noruega, China, EUA).">Veículos Elétricos</button>' +
      '<button class="bnx-suggestion-chip" data-prompt="Cenário: Mercado de trabalho em tecnologia no Brasil. Contexto: O setor de TI brasileiro é um dos que mais cresce, com escassez de talentos e salários competitivos. Solicito: pesquisa web com dados de pesquisas salariais (Catho, Glassdoor, LinkedIn) para criar (1) tabela de salários por cargo e nível (júnior, pleno, sênior) com valores em R$, (2) gráfico das 10 habilidades mais demandadas com taxa de empregabilidade, (3) métricas de empregabilidade por região e porte de empresa, (4) timeline de contratações por trimestre nos últimos 2 anos. Destaque as tendências para 2025-2026.">Mercado de TI Brasil</button>' +
      '</div></div>';
    dom.chatInner.querySelectorAll('.bnx-suggestion-chip').forEach(function (chip) {
      chip.addEventListener('click', function () {
        const prompt = chip.dataset.prompt;
        if (prompt && dom.input) { dom.input.value = prompt; dom.input.focus(); dom.input.style.height = 'auto'; dom.input.style.height = Math.min(dom.input.scrollHeight, 140) + 'px'; }
      });
    });
  }

  // ── API Call ───────────────────────────────────────────────────────────

  // ── SSE Streaming sendMessage ──────────────────────────────────────────

  async function sendMessage(message) {
    if (state.isProcessing || !message.trim()) return;
    state.isProcessing = true;
    if (dom.sendBtn) dom.sendBtn.disabled = true;

    const welcome = dom.chatInner && dom.chatInner.querySelector('.bnx-welcome');
    if (welcome) welcome.remove();

    renderMessage('user', message);
    state.messages.push({ role: 'user', content: message });
    if (dom.input) { dom.input.value = ''; dom.input.style.height = 'auto'; }
    updateSendButton();
    updateCharCount();
    renderLoading();

    // SSE state
    var fullText = '';
    var responseContext = {};
    var msgEl = null;
    var bubbleEl = null;
    var vbContainerEl = null;
    var bodyEl = null;
    var timeEl = null;
    var sourcesRendered = false;
    // O(n) streaming cache: HTML dos parágrafos completos já renderizados
    var _streamParaCache = [];   // array de strings HTML (um por parágrafo completo)
    var _streamParaCacheKeys = []; // texto bruto correspondente (para invalidação)

    // Renderiza markdown com cache de blocos completos — O(n) em vez de O(n²)
    function renderStreamingMarkdown(text) {
      var paras = text.split(/\n\n/);
      if (paras.length <= 1) {
        // Parágrafo único ainda incompleto — nada a cachear
        return simpleMarkdown(autoCloseMarkdown(text));
      }
      // Parágrafos completos: tudo exceto o último
      var completedParas = paras.slice(0, paras.length - 1);
      var pendingPara = paras[paras.length - 1];
      // Atualiza cache somente para parágrafos novos ou modificados
      var htmlParts = [];
      for (var i = 0; i < completedParas.length; i++) {
        if (_streamParaCacheKeys[i] !== completedParas[i]) {
          _streamParaCache[i] = simpleMarkdown(completedParas[i]);
          _streamParaCacheKeys[i] = completedParas[i];
        }
        htmlParts.push(_streamParaCache[i]);
      }
      // Truncar cache se parágrafos foram removidos (improvável, mas seguro)
      _streamParaCache.length = completedParas.length;
      _streamParaCacheKeys.length = completedParas.length;
      // Último parágrafo: sempre re-renderiza pois está incompleto
      if (pendingPara) {
        htmlParts.push(simpleMarkdown(autoCloseMarkdown(pendingPara)));
      }
      return htmlParts.join('');
    }

    function ensureMessageEl() {
      if (msgEl) return;
      // Create agent message container (without VB skeleton — we'll add lazily)
      msgEl = document.createElement('div');
      msgEl.className = 'bnx-message agent';
      msgEl.dataset.id = generateId();

      var avatar = document.createElement('div');
      avatar.className = 'bnx-message-avatar';
      var img = document.createElement('img');
      img.src = 'assets/logo.png'; img.alt = 'Bravonix';
      avatar.appendChild(img);
      msgEl.appendChild(avatar);

      bodyEl = document.createElement('div');
      bodyEl.className = 'bnx-message-body';

      bubbleEl = document.createElement('div');
      bubbleEl.className = 'bnx-message-bubble';
      bodyEl.appendChild(bubbleEl);

      timeEl = document.createElement('div');
      timeEl.className = 'bnx-message-time';
      timeEl.textContent = getTimestamp();
      bodyEl.appendChild(timeEl);

      msgEl.appendChild(bodyEl);

      if (dom.chatInner) dom.chatInner.appendChild(msgEl);
    }

    function handleSSEEvent(eventName, data) {
      if (eventName === 'thinking') {
        updateThinkingStep(data.step, data.status || 'active', data.label || '', data.elapsed_ms);

      } else if (eventName === 'response_context') {
        responseContext = data || {};
        if (typeof BRAVONIX_VB !== 'undefined' && BRAVONIX_VB.setColorScheme && data.color_scheme) {
          BRAVONIX_VB.setColorScheme(data.color_scheme);
        }

      } else if (eventName === 'token') {
        ensureMessageEl();
        if (data.text) {
          // Remover newlines iniciais do token para evitar triple-newline
          var tokenText = data.text.replace(/^\n+/, '');
          if (tokenText) {
            fullText += (fullText ? '\n\n' : '') + tokenText;
          }
          bubbleEl.innerHTML = renderStreamingMarkdown(fullText);
          scrollToBottom();
        }

      } else if (eventName === 'visual_blocks') {
        ensureMessageEl();
        // Remove any existing VB container
        if (!vbContainerEl) {
          vbContainerEl = document.createElement('div');
          vbContainerEl.className = 'bnx-visual-blocks';
          // Insert before time element
          if (timeEl && timeEl.parentNode === bodyEl) {
            bodyEl.insertBefore(vbContainerEl, timeEl);
          } else {
            bodyEl.appendChild(vbContainerEl);
          }
        }
        if (typeof BRAVONIX_VB !== 'undefined') {
          BRAVONIX_VB.renderBlocks(data, vbContainerEl, responseContext);
        }
        scrollToBottom();

      } else if (eventName === 'sources') {
        if (!sourcesRendered && Array.isArray(data) && data.length > 0 && msgEl) {
          ensureMessageEl();
          var srcEl = renderSources(data);
          if (srcEl && timeEl && timeEl.parentNode === bodyEl) {
            bodyEl.insertBefore(srcEl, timeEl);
          } else if (srcEl) {
            bodyEl.appendChild(srcEl);
          }
          sourcesRendered = true;
          scrollToBottom();
        }

      } else if (eventName === 'done') {
        state.conversationId = data.conversation_id || state.conversationId;
        // Renderização final completa (sem auto-close — texto já completo)
        if (bubbleEl && fullText) {
          bubbleEl.innerHTML = simpleMarkdown(fullText);
        } else if (bubbleEl) {
          // Sem texto — apenas blocks visuais; esconder bubble vazio
          bubbleEl.style.display = 'none';
        }
        // Limpar cache de streaming
        _streamParaCache = [];
        _streamParaCacheKeys = [];
        state.messages.push({ role: 'assistant', content: fullText });
        finalizeThinkingPanel(data.total_ms);

        if (!msgEl && !fullText) {
          renderMessage('agent', 'Resposta processada.', null, null, [], responseContext);
        }

        state.isProcessing = false;
        if (dom.sendBtn) dom.sendBtn.disabled = false;
        if (dom.input) dom.input.focus();
        updateSendButton();
        scrollToBottom();
      }
    }

    try {
      const response = await fetch(API_BASE + '/api/agent/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({
          message: message,
          conversation_id: state.conversationId,
          context: { mode: 'general' },
        }),
      });

      if (response.status === 401) {
        removeLoading();
        state.isAuthorized = false;
        renderMessage('agent', '**Sess&atilde;o expirada.** Fa&ccedil;a a valida&ccedil;&atilde;o do token novamente.');
        renderTokenGate();
        state.isProcessing = false;
        if (dom.sendBtn) dom.sendBtn.disabled = false;
        return;
      }

      if (!response.ok) throw new Error('Erro HTTP ' + response.status);

      // Parse SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      var buffer = '';
      var eventName = '';
      var dataLines = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        var lines = buffer.split('\n');
        buffer = lines.pop(); // keep incomplete last line

        for (var i = 0; i < lines.length; i++) {
          var line = lines[i];
          if (line.startsWith('event: ')) {
            eventName = line.slice(7).trim();
            dataLines = [];
          } else if (line.startsWith('data: ')) {
            dataLines.push(line.slice(6));
          } else if (line === '') {
            if (eventName && dataLines.length) {
              try {
                var parsed = JSON.parse(dataLines.join('\n'));
                handleSSEEvent(eventName, parsed);
              } catch (e) {
                // ignore malformed event
              }
            }
            eventName = '';
            dataLines = [];
          }
        }
      }

    } catch (err) {
      removeLoading();
      state.isProcessing = false;
      if (dom.input) dom.input.focus();
      updateSendButton();
      renderMessage('agent', '**Erro:** ' + (err.message || 'Erro de conex&atilde;o.') + '\n\nVerifique se o servidor backend est&aacute; rodando.');
      if (dom.chatInner) {
        const banner = document.createElement('div');
        banner.className = 'bnx-error-banner';
        banner.innerHTML = '<span class="bnx-error-banner-icon">&#9888;</span><span>' + (err.message || 'Erro de conex&atilde;o') + '</span>';
        dom.chatInner.appendChild(banner);
        scrollToBottom();
      }
    }
  }

  function normalizeSources(sources) {
    if (!Array.isArray(sources)) return [];
    var seen = {};
    return sources.map(function (source) {
      if (!source) return null;
      if (typeof source === 'string') {
        return { title: source, url: source, domain: source.replace(/^https?:\/\//, '').split('/')[0] };
      }
      var url = source.url || source.href || source.link || '';
      var title = source.title || source.name || source.label || url;
      var domain = source.domain || (url ? url.replace(/^https?:\/\//, '').split('/')[0].replace(/^www\./, '') : '');
      return { title: title, url: url, domain: domain };
    }).filter(function (source) {
      if (!source || !source.url || !/^https?:\/\//.test(source.url)) return false;
      if (seen[source.url]) return false;
      seen[source.url] = true;
      return true;
    });
  }

  function renderSources(sources) {
    var normalized = normalizeSources(sources);
    if (!normalized.length) return document.createDocumentFragment();

    var wrap = document.createElement('section');
    wrap.className = 'bnx-sources';
    wrap.setAttribute('aria-label', 'Fontes utilizadas');

    var header = document.createElement('div');
    header.className = 'bnx-sources-title';
    header.textContent = 'Fontes';
    wrap.appendChild(header);

    var list = document.createElement('ol');
    list.className = 'bnx-sources-list';
    normalized.forEach(function (source) {
      var item = document.createElement('li');
      var link = document.createElement('a');
      link.href = source.url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = source.title || source.domain || source.url;
      item.appendChild(link);
      if (source.domain) {
        var domain = document.createElement('span');
        domain.className = 'bnx-source-domain';
        domain.textContent = source.domain;
        item.appendChild(domain);
      }
      list.appendChild(item);
    });
    wrap.appendChild(list);
    return wrap;
  }

  // ── Progressive Message Rendering ──────────────────────────────────────

  function renderMessageProgressive(type, content, sources) {
    var msgEl = document.createElement('div');
    msgEl.className = 'bnx-message ' + type;
    msgEl.dataset.id = generateId();

    var avatar = document.createElement('div');
    avatar.className = 'bnx-message-avatar';
    if (type === 'user') {
      avatar.textContent = 'U';
    } else {
      var img = document.createElement('img');
      img.src = 'assets/logo.png';
      img.alt = 'Bravonix';
      avatar.appendChild(img);
    }
    msgEl.appendChild(avatar);

    var body = document.createElement('div');
    body.className = 'bnx-message-body';

    var bubble = document.createElement('div');
    bubble.className = 'bnx-message-bubble';
    bubble.innerHTML = simpleMarkdown(content);
    body.appendChild(bubble);

    // Visual blocks container (filled progressively)
    var vbContainer = document.createElement('div');
    vbContainer.className = 'bnx-visual-blocks bnx-loading-blocks';
    // Skeleton placeholders while blocks load
    for (var si = 0; si < 3; si++) {
      var skel = document.createElement('div');
      skel.className = 'bnx-skeleton bnx-skeleton-block';
      skel.style.cssText = 'height:' + (60 + si * 20) + 'px;width:' + (90 - si * 15) + '%;';
      vbContainer.appendChild(skel);
    }
    body.appendChild(vbContainer);

    if (sources && sources.length > 0 && type === 'agent') {
      body.appendChild(renderSources(sources));
    }

    var time = document.createElement('div');
    time.className = 'bnx-message-time';
    time.textContent = getTimestamp();
    body.appendChild(time);
    msgEl.appendChild(body);

    if (dom.chatInner) {
      dom.chatInner.appendChild(msgEl);
      scrollToBottom();
    }
    return msgEl;
  }

  // ── Input ──────────────────────────────────────────────────────────────

  function handleSubmit() {
    if (dom.input) { const m = dom.input.value.trim(); if (m) sendMessage(m); }
  }

  // ── Simple Markdown ────────────────────────────────────────────────────

  // ── Markdown → prose HTML renderer ────────────────────────────────────────
  // Renders LLM-generated markdown to clean, friendly HTML.
  // Strips common LLM artifacts (orphan ```, stray **, lone #).
  // Security: HTML-escapes input before processing.

  // Fecha marcadores markdown incompletos durante streaming para evitar artefatos visuais
  function autoCloseMarkdown(text) {
    var s = text;
    // Strip code blocks/inline code antes de contar marcadores (evita falsos positivos)
    var noCode = s.replace(/```[\s\S]*?```/g, '').replace(/`[^`]*`/g, '');
    // Conta ** (bold)
    var boldCount = (noCode.match(/\*\*/g) || []).length;
    if (boldCount % 2 !== 0) s += '**';
    // Conta * simples: remove TODOS os multi-star sequences (**, ***, ****) antes de contar
    // Isso evita falso positivo com *** (bold+italic) onde a remoção de ** deixa um * orfão
    var noCode2 = s.replace(/```[\s\S]*?```/g, '').replace(/`[^`]*`/g, '');
    var singleStars = (noCode2.replace(/\*{2,}/g, '').match(/\*/g) || []).length;
    if (singleStars % 2 !== 0) s += '*';
    // Fecha `inline code` se ímpar (sem fences abertas)
    var fenceCount = (s.match(/```/g) || []).length;
    if (fenceCount % 2 === 0) {
      var backtickCount = (s.replace(/```/g, '').match(/`/g) || []).length;
      if (backtickCount % 2 !== 0) s += '`';
    }
    return s;
  }

  function simpleMarkdown(text) {
    if (!text) return '';

    // 1. HTML-escape raw input (XSS prevention)
    var s = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // 2. Strip LLM control/special tokens (Llama, WatsonX, etc.) — AGGRESSIVE
    // Remove tokens com ou sem espacos internos
    s = s.replace(/\[\/?\s*s\s*\]/gi, '');
    s = s.replace(/\[\/?\s*INST\s*\]/gi, '');
    s = s.replace(/\[\/?\s*SYS\s*\]/gi, '');
    s = s.replace(/<<\/?SYS>>/g, '');
    s = s.replace(/<\/?s>/g, '');
    s = s.replace(/<\|[^|]*\|>/g, '');
    s = s.replace(/\[SYSTEM\].*?\[\/SYSTEM\]/gi, '');
    // Trim apos remocao de tokens no inicio/fim
    s = s.trim();

    // 3. Strip LLM artifacts: orphan backtick fences (unclosed ```)
    s = s.replace(/```[\w]*\s*$/gm, ''); // trailing fence at end of line
    s = s.replace(/^```[\w]*\s*$/gm, ''); // opening fence without close (will be paired next)

    // 3. Fenced code blocks — render BEFORE inline code
    s = s.replace(/```([\w]*)\n([\s\S]*?)```/g, function (_, lang, code) {
      var cls = lang ? ' class="lang-' + lang + '"' : '';
      return '<pre class="bnx-code-block"><code' + cls + '>' + code.trim() + '</code></pre>';
    });

    // 4. Inline code
    s = s.replace(/`([^`\n]+)`/g, '<code class="bnx-inline-code">$1</code>');

    // 5. Bold (handles ** text ** with spaces)
    s = s.replace(/\*\*\s*([^*\n]+?)\s*\*\*/g, '<strong>$1</strong>');
    // 6. Italic
    s = s.replace(/\*([^*\n]+)\*/g, '<em>$1</em>');

    // 7. Links [text](url)
    s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    // Auto-link bare URLs
    s = s.replace(/(^|[\s(])(https?:\/\/[^\s<)"]+)/g, '$1<a href="$2" target="_blank" rel="noopener noreferrer">$2</a>');

    // 8. HR
    s = s.replace(/^---+$/gm, '<hr class="bnx-hr">');

    // 9. Headings → styled divs (avoid h1–h3 breaking chat flow)
    s = s.replace(/^#{4,6}\s+(.+)$/gm, '<p class="bnx-h4">$1</p>');
    s = s.replace(/^###\s+(.+)$/gm,    '<p class="bnx-h3">$1</p>');
    s = s.replace(/^##\s+(.+)$/gm,     '<p class="bnx-h2">$1</p>');
    s = s.replace(/^#\s+(.+)$/gm,      '<p class="bnx-h1">$1</p>');

    // 9.5 Normalize double-newlines between adjacent table rows
    // (tokens streamed individually get joined with \n\n, breaking table detection)
    s = s.replace(/(\|[^\n]*)\n{2,}(\s*\|)/g, '$1\n$2');

    // 10. Markdown Tables — parse pipe tables BEFORE paragraph splitting
    // Format: | Header | Header |
    //         |--------|--------|
    //         | Cell   | Cell   |
    var tableRegex = /((?:^\s*\|.+\|(?:\n\s*\|.+\|)+)+)/gm;
    s = s.replace(tableRegex, function(match) {
      var lines = match.trim().split('\n').filter(function(l) { return l.trim(); });
      if (lines.length < 2) return match; // Not a valid table

      // Filter out separator lines (lines containing only -, :, |, spaces)
      var dataLines = lines.filter(function(l) {
        var trimmed = l.trim();
        // Remove leading/trailing pipes for check
        var content = trimmed.replace(/^\||\|$/g, '').trim();
        // Separator line has only dashes/colons
        return !/^[-:|\s]*$/.test(content);
      });

      if (dataLines.length < 1) return match;

      var headerLine = dataLines[0];
      var bodyLines = dataLines.slice(1);

      // Parse header cells (split by | and filter empty)
      var headers = headerLine.split('|').filter(function(h) { return h.trim(); });
      if (headers.length === 0) return match;

      // Parse header
      var headerHtml = '<thead><tr class="bnx-table-row bnx-table-header">';
      headers.forEach(function(h) {
        headerHtml += '<th class="bnx-table-cell bnx-table-header-cell">' + h.trim() + '</th>';
      });
      headerHtml += '</tr></thead>';

      // Parse body
      var bodyHtml = '<tbody>';
      bodyLines.forEach(function(row) {
        var cells = row.split('|').filter(function(c) { return c.trim(); });
        if (cells.length > 0) {
          bodyHtml += '<tr class="bnx-table-row">';
          cells.forEach(function(cell) {
            bodyHtml += '<td class="bnx-table-cell">' + cell.trim() + '</td>';
          });
          bodyHtml += '</tr>';
        }
      });
      bodyHtml += '</tbody>';

      return '\n\n<div class="bnx-table-responsive"><table class="bnx-markdown-table">' + headerHtml + bodyHtml + '</table></div>\n\n';
    });

    // 11. Lists — collect consecutive lines
    // Unordered
    s = s.replace(/^[-*+]\s+(.+)$/gm, '<li>$1</li>');
    // Ordered
    s = s.replace(/^(\d+)[.)]\s+(.+)$/gm, '<li>$2</li>');
    // Wrap consecutive <li> groups (but not inside tables)
    s = s.replace(/((?:<li>.*?<\/li>\n?)+)/g, function (m) {
      return '<ul class="bnx-list">' + m + '</ul>';
    });

    // 11. Blockquote
    s = s.replace(/^&gt;\s*(.+)$/gm, '<blockquote class="bnx-quote">$1</blockquote>');

    // 12. Paragraphs — split on double newlines
    var blocks = s.split(/\n{2,}/);
    s = blocks.map(function (block) {
      var trimmed = block.trim();
      if (!trimmed) return '';
      // Already a block element — don't wrap (includes table)
      if (/^<(pre|ul|ol|blockquote|hr|p\s|h[1-6]|table|div)/i.test(trimmed)) return trimmed;
      // Single newlines within paragraph → <br>
      return '<p class="bnx-p">' + trimmed.replace(/\n/g, '<br>') + '</p>';
    }).filter(Boolean).join('\n');

    // 13. Clean up double-wrapped block tags
    s = s.replace(/<p[^>]*>\s*(<(?:pre|ul|ol|blockquote|hr)[^>]*>)/g, '$1');
    s = s.replace(/(<\/(?:pre|ul|ol|blockquote|hr)>)\s*<\/p>/g, '$1');
    s = s.replace(/<p[^>]*>\s*<\/p>/g, '');

    return s;
  }

  // ── Performance: Debounced Resize (Chart.js instances) ─────────────────

  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      if (typeof BRAVONIX_VB !== 'undefined' && Array.isArray(BRAVONIX_VB.chartInstances)) {
        BRAVONIX_VB.chartInstances.forEach(function (inst) {
          // Verificar que o canvas ainda está no DOM antes de redimensionar
          if (inst && typeof inst.resize === 'function' &&
              inst.canvas && inst.canvas.parentNode) {
            try { inst.resize(); } catch (e) { /* chart destroyed, ignore */ }
          }
        });
      }
    }, 250);
  }, { passive: true });

  // ── Init Flow ──────────────────────────────────────────────────────────

  async function initChat() {
    renderWelcome();
    await checkStatus();

    // Scroll event for FAB visibility
    if (dom.chat) {
      dom.chat.addEventListener('scroll', updateScrollButton, { passive: true });
    }

    // Scroll-to-bottom FAB click
    if (dom.scrollBottom) {
      dom.scrollBottom.addEventListener('click', function () {
        if (dom.chat) dom.chat.scrollTo({ top: dom.chat.scrollHeight, behavior: 'smooth' });
      });
    }

    // Send button
    if (dom.sendBtn) dom.sendBtn.addEventListener('click', handleSubmit);

    // Input handlers
    if (dom.input) {
      dom.input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); }
        if (e.key === 'Escape') { dom.input.value = ''; dom.input.style.height = 'auto'; updateSendButton(); }
      });
      dom.input.addEventListener('input', function () {
        dom.input.style.height = 'auto';
        dom.input.style.height = Math.min(dom.input.scrollHeight, 140) + 'px';
        updateSendButton();
        updateCharCount();
      });
    }

    // Theme toggle
    if (dom.themeBtn) dom.themeBtn.addEventListener('click', toggleTheme);

    // New conversation (single listener)
    if (dom.newBtn) {
      dom.newBtn.addEventListener('click', function () {
        if (confirm('Nova conversa? A conversa atual sera perdida.')) clearChat();
      });
    }

    // Global keyboard shortcuts
    document.addEventListener('keydown', function (e) {
      if (e.ctrlKey && e.key === 'Enter') handleSubmit();
    });

    // Offline detection
    window.addEventListener('online', function () {
      if (dom.offlineBanner) dom.offlineBanner.hidden = true;
      if (dom.statusDot) { dom.statusDot.className = 'bnx-status-dot online'; dom.statusDot.title = 'Conectado'; }
    });
    window.addEventListener('offline', function () {
      if (dom.offlineBanner) dom.offlineBanner.hidden = false;
      if (dom.statusDot) { dom.statusDot.className = 'bnx-status-dot offline'; dom.statusDot.title = 'Offline'; }
    });

    console.log('[Bravonix] Chat initialized');
  }

  function updateSendButton() {
    if (!dom.sendBtn || !dom.input) return;
    dom.sendBtn.disabled = !dom.input.value.trim();
  }

  function updateCharCount() {
    if (!dom.charCount || !dom.input) return;
    var len = dom.input.value.length;
    dom.charCount.textContent = len + '/10000';
    dom.charCount.style.color = len > 9000 ? 'var(--bnx-warning)' : '';
  }

  async function init() {
    cacheDom();
    initTheme();

    // Check for existing session token
    const existingToken = getCookie(SESSION_COOKIE);
    if (existingToken) {
      try {
        const res = await fetch(API_BASE + '/api/access/status', {
          headers: { 'Cookie': SESSION_COOKIE + '=' + encodeURIComponent(existingToken) },
          credentials: 'same-origin',
        });
        if (res.ok) {
          state.accessToken = existingToken;
          state.isAuthorized = true;
          initChat();
          return;
        }
      } catch (_) { }
    }

    // Try development auto-login (Docker/local)
    try {
      const devRes = await fetch(API_BASE + '/api/access/dev-token');
      if (devRes.ok) {
        const devData = await devRes.json();
        if (devData.valid && devData.session_token) {
          setCookie(SESSION_COOKIE, devData.session_token, 1);
          state.accessToken = devData.session_token;
          state.isAuthorized = true;
          initChat();
          return;
        }
      }
    } catch (_) { }

    // No valid token → show token gate
    renderTokenGate();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
