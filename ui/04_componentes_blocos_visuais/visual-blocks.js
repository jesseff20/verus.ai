/**
 * visual-blocks.js — Renderizador de blocos visuais Bravonix v2
 *
 * Suporta: text, card, metric, chart (Chart.js), table, panel,
 *          timeline, action_list, document_reference.
 *
 * Inspirado por C1/Thesys, OpenUI Lang e wandb/openui.
 */

const BRAVONIX_VB = (() => {
  'use strict';

  // ── SVG Icon Library (Lucide-style, 16×16 viewBox) ────────────────────────
  // All icons use stroke="currentColor" so they inherit button color.

  var IC = {
    // Action buttons
    copy:     '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="5.5" y="1.5" width="9" height="11" rx="1.5"/><path d="M3 4.5H2a1 1 0 00-1 1V14a1 1 0 001 1h8a1 1 0 001-1v-1"/></svg>',
    copyDone: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="2,8 6,12 14,4"/></svg>',
    download: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v8M4.5 7l3.5 4 3.5-4"/><path d="M2 13h12"/></svg>',
    expand:   '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2h4v4M6 14H2v-4"/><line x1="14" y1="2" x2="9" y2="7"/><line x1="2" y1="14" x2="7" y2="9"/></svg>',
    close:    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="3" x2="13" y2="13"/><line x1="13" y1="3" x2="3" y2="13"/></svg>',
    play:     '<svg viewBox="0 0 16 16" fill="currentColor" stroke="none"><polygon points="4,2 14,8 4,14"/></svg>',
    pause:    '<svg viewBox="0 0 16 16" fill="currentColor" stroke="none"><rect x="3" y="2" width="4" height="12" rx="1"/><rect x="9" y="2" width="4" height="12" rx="1"/></svg>',
    imgDown:  '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="1" width="14" height="14" rx="2"/><circle cx="5.5" cy="5.5" r="1.5"/><polyline points="1,11 5,7 8,10 11,7 15,11"/></svg>',
    csv:      '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="1" y="1" width="14" height="14" rx="2"/><line x1="1" y1="5.5" x2="15" y2="5.5"/><line x1="5.5" y1="5.5" x2="5.5" y2="15"/></svg>',
    // Status icons (for panels/cards)
    warn:     '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M8 1.5L14.5 13.5H1.5L8 1.5z"/><line x1="8" y1="6.5" x2="8" y2="9.5"/><circle cx="8" cy="11.5" r="0.5" fill="currentColor" stroke="none"/></svg>',
    error:    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="8" cy="8" r="6.5"/><line x1="8" y1="5" x2="8" y2="8.5"/><circle cx="8" cy="11" r="0.5" fill="currentColor" stroke="none"/></svg>',
    success:  '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="8" cy="8" r="6.5"/><polyline points="5,8.5 7,10.5 11,6"/></svg>',
    info:     '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="8" cy="8" r="6.5"/><line x1="8" y1="7" x2="8" y2="11"/><circle cx="8" cy="5" r="0.5" fill="currentColor" stroke="none"/></svg>',
    // Block type icons (for card headers)
    chart:    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="1" y="8" width="3" height="7" rx="1"/><rect x="6" y="5" width="3" height="10" rx="1"/><rect x="11" y="2" width="3" height="13" rx="1"/></svg>',
    table:    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="1" y="1" width="14" height="14" rx="2"/><line x1="1" y1="5.5" x2="15" y2="5.5"/><line x1="1" y1="9.5" x2="15" y2="9.5"/><line x1="5.5" y1="5.5" x2="5.5" y2="15"/></svg>',
    metric:   '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="8" cy="8" r="6.5"/><path d="M8 5v4l2.5 2"/></svg>',
    timeline: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="8" cy="8" r="2"/><line x1="1" y1="8" x2="6" y2="8"/><line x1="10" y1="8" x2="15" y2="8"/></svg>',
    sort:     '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><line x1="2" y1="4" x2="14" y2="4"/><line x1="4" y1="8" x2="12" y2="8"/><line x1="6" y1="12" x2="10" y2="12"/></svg>',
    sortAsc:  '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><line x1="2" y1="4" x2="10" y2="4"/><line x1="2" y1="8" x2="8" y2="8"/><line x1="2" y1="12" x2="6" y2="12"/><path d="M13 3v10M10 10l3 3 3-3"/></svg>',
    sortDesc: '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><line x1="2" y1="4" x2="10" y2="4"/><line x1="2" y1="8" x2="8" y2="8"/><line x1="2" y1="12" x2="6" y2="12"/><path d="M13 13V3M10 6l3-3 3 3"/></svg>',
  };

  // ── Prose renderer (LLM text → safe HTML, no heavy markdown) ─────────────
  // Used for card content, panel text, timeline descriptions.
  // Converts only: **bold**, *italic*, `code`, URLs → links.
  // Strips raw markdown artifacts that LLMs sometimes emit.
  function prosify(text) {
    if (!text || typeof text !== 'string') return '';
    // 1. Escape HTML
    var s = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    // 2. Strip LLM artifacts: orphan ``` blocks
    s = s.replace(/```[\w]*\n?/g, '').replace(/```/g, '');
    // 3. Strip orphan # headers — convert to plain text with emphasis
    s = s.replace(/^#{1,6}\s+(.+)$/gm, '<strong>$1</strong>');
    // 4. Bold and italic
    s = s.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
    // 5. Inline code
    s = s.replace(/`([^`\n]+)`/g, '<code class="bnx-inline-code">$1</code>');
    // 6. Auto-link URLs
    s = s.replace(/(https?:\/\/[^\s<>"]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" class="bnx-prose-link">$1</a>');
    // 7. Double newline → paragraph break, single → space
    s = s.replace(/\n\n+/g, '</p><p class="bnx-prose-p">').replace(/\n/g, ' ');
    // 8. Wrap in paragraph if needed
    if (!s.startsWith('<')) s = '<p class="bnx-prose-p">' + s + '</p>';
    return s;
  }

  // ── Color Schemes ──────────────────────────────────────────────────────────

  var COLOR_SCHEMES = {
    purple:  { primary: 'var(--bnx-purple)',   accent: 'var(--bnx-purple-bright)', bg: 'var(--bnx-purple-light)' },
    success: { primary: 'var(--bnx-success)',  accent: '#16A34A',                  bg: 'rgba(34,197,94,0.08)'   },
    warning: { primary: 'var(--bnx-warning)',  accent: '#D97706',                  bg: 'rgba(245,158,11,0.08)'  },
    danger:  { primary: 'var(--bnx-danger)',   accent: '#DC2626',                  bg: 'rgba(239,68,68,0.08)'   },
    info:    { primary: 'var(--bnx-info)',     accent: '#1D4ED8',                  bg: 'rgba(59,130,246,0.08)'  },
    neutral: { primary: 'var(--bnx-text-secondary)', accent: 'var(--bnx-text-tertiary)', bg: 'var(--bnx-bg-secondary)' },
  };

  var currentScheme = 'purple';

  function setColorScheme(scheme) {
    if (COLOR_SCHEMES[scheme]) {
      currentScheme = scheme;
    }
  }

  function applyColorScheme(container, scheme) {
    var s = COLOR_SCHEMES[scheme] || COLOR_SCHEMES.purple;
    container.style.setProperty('--bnx-scheme-primary', s.primary);
    container.style.setProperty('--bnx-scheme-accent', s.accent);
    container.style.setProperty('--bnx-scheme-bg', s.bg);
  }

  // ── State ──────────────────────────────────────────────────────────────────

  let chartInstances = [];
  let confettiCanvas = null;
  let confettiAnimId = null;

  // ── API ────────────────────────────────────────────────────────────────────

  function renderBlocks(blocks, container, context) {
    context = context || {};
    // Use layout_hint from blocks if available (C1-style), fallback to context
    var blockLayoutHint = blocks[0] && blocks[0].layout_hint ? blocks[0].layout_hint : 'auto';
    var layoutHint = context.layout_hint || blockLayoutHint || 'auto';
    var density = context.visual_density || 'normal';
    var isSimple = context.is_simple_response || false;

    // Apply color scheme from context
    if (context.color_scheme) {
      setColorScheme(context.color_scheme);
    }

    if (!blocks || !blocks.length) return;
    destroyCharts();
    chartInstances = [];
    var sorted = [].concat(blocks).sort(function(a, b) { return (b.priority || 0) - (a.priority || 0); });

    // Remove loading skeleton
    container.classList.remove('bnx-loading-blocks');
    container.innerHTML = '';

    // Simple response: render without card borders
    if (isSimple) {
      container.classList.add('bnx-simple-response');
    }

    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Determine stagger delay based on density
    var staggerDelay = 0.04;
    if (density === 'none' || reducedMotion) {
      staggerDelay = 0;
    } else if (density === 'minimal') {
      staggerDelay = 0.02;
    } else if (density === 'rich') {
      staggerDelay = 0.06;
    }

    // Animate function considering density
    function animateEl(el, i) {
      if (density === 'none' || reducedMotion) {
        // No animation
        return;
      }
      el.style.animationDelay = (i * staggerDelay) + 's';
      el.classList.add('bnx-animate-fade-up');
    }

    // Smart grouping by type
    var metrics = sorted.filter(function(b) { return b.type === 'metric'; });
    var charts = sorted.filter(function(b) { return b.type === 'chart'; });
    var tables = sorted.filter(function(b) { return b.type === 'table'; });
    var timelines = sorted.filter(function(b) { return b.type === 'timeline'; });

    // ── Layout: single ─────────────────────────────────────────────────────
    if (layoutHint === 'single') {
      sorted.forEach(function(block, i) {
        var el = renderBlock(block, i);
        if (el) {
          el.style.width = '100%';
          animateEl(el, i);
          container.appendChild(el);
        }
      });
      return;
    }

    // ── Layout: grid ──────────────────────────────────────────────────────
    if (layoutHint === 'grid') {
      var gridWrap = document.createElement('div');
      gridWrap.style.cssText = 'display:grid;grid-template-columns:1fr 1fr;gap:12px;';
      sorted.forEach(function(block, i) {
        var el = renderBlock(block, i);
        if (el) {
          var isWide = block.type === 'chart' || block.type === 'table' || block.type === 'timeline';
          if (isWide) el.style.gridColumn = '1 / -1';
          animateEl(el, i);
          gridWrap.appendChild(el);
        }
      });
      container.appendChild(gridWrap);
      return;
    }

    // ── Layout: dashboard ─────────────────────────────────────────────────
    if (layoutHint === 'dashboard') {
      var dashGrid = document.createElement('div');
      dashGrid.className = 'bnx-dashboard-grid';
      sorted.forEach(function(block, i) {
        var el = renderBlock(block, i);
        if (el) {
          animateEl(el, i);
          var isWide = block.type === 'chart' || block.type === 'table' || block.type === 'timeline' || block.type === 'interactive' || block.type === 'html';
          if (isWide) el.style.gridColumn = '1 / -1';
          dashGrid.appendChild(el);
        }
      });
      container.appendChild(dashGrid);
      return;
    }

    // ── Layout: narrative ─────────────────────────────────────────────────
    if (layoutHint === 'narrative') {
      var lastType = null;
      sorted.forEach(function(block, i) {
        if (block.type !== lastType) {
          var sep = document.createElement('div');
          sep.className = 'bnx-narrative-separator';
          var typeLabels = { metric: 'Métricas', chart: 'Visualizações', table: 'Dados', card: 'Informações', panel: 'Destaques', text: 'Texto', timeline: 'Linha do Tempo' };
          sep.textContent = typeLabels[block.type] || block.type;
          container.appendChild(sep);
          lastType = block.type;
        }
        var section = document.createElement('div');
        section.className = 'bnx-narrative-section';
        var el = renderBlock(block, i);
        if (el) {
          animateEl(el, i);
          section.appendChild(el);
          container.appendChild(section);
        }
      });
      return;
    }

    // ── Layout: tabs (C1-style dashboard) ─────────────────────────────────
    if (layoutHint === 'tabs' || (layoutHint === 'auto' && sorted.length >= 5)) {
      // Group blocks by type for tabs
      var groups = {};
      var typeLabels = {
        metric: 'Visão Geral',
        chart: 'Gráficos',
        table: 'Tabelas',
        timeline: 'Linha do Tempo',
        card: 'Informações',
        panel: 'Destaques',
        text: 'Texto',
        interactive: 'Interativo'
      };
      sorted.forEach(function(block) {
        var groupKey = block.type || 'card';
        if (!groups[groupKey]) {
          groups[groupKey] = [];
        }
        groups[groupKey].push(block);
      });

      // Create tab navigation
      var tabsNav = document.createElement('div');
      tabsNav.className = 'bnx-dashboard-tabs';
      var tabContents = {};
      var firstTab = true;

      // Create tabs and panels
      Object.keys(groups).forEach(function(groupKey) {
        var blocks = groups[groupKey];
        if (!blocks.length) return;

        var tabBtn = document.createElement('button');
        tabBtn.className = 'bnx-tab' + (firstTab ? ' active' : '');
        tabBtn.textContent = typeLabels[groupKey] || groupKey;
        tabBtn.dataset.tab = groupKey;
        tabBtn.onclick = function() {
          // Deactivate all tabs
          tabsNav.querySelectorAll('.bnx-tab').forEach(function(t) {
            t.classList.remove('active');
          });
          // Hide all contents
          Object.keys(tabContents).forEach(function(k) {
            tabContents[k].classList.remove('active');
          });
          // Activate selected
          tabBtn.classList.add('active');
          tabContents[groupKey].classList.add('active');
        };
        tabsNav.appendChild(tabBtn);

        // Create tab content panel
        var tabPanel = document.createElement('div');
        tabPanel.className = 'bnx-tab-content' + (firstTab ? ' active' : '');
        tabPanel.dataset.tab = groupKey;

        var panelGrid = document.createElement('div');
        panelGrid.className = 'bnx-tab-panel';

        blocks.forEach(function(block, i) {
          var el = renderBlock(block, i);
          if (el) {
            animateEl(el, i);
            var isWide = block.type === 'chart' || block.type === 'table' || block.type === 'timeline';
            if (isWide) el.style.gridColumn = '1 / -1';
            panelGrid.appendChild(el);
          }
        });

        tabPanel.appendChild(panelGrid);
        container.appendChild(tabPanel);
        tabContents[groupKey] = tabPanel;
        firstTab = false;
      });

      // Insert tabs nav at the beginning
      container.insertBefore(tabsNav, container.firstChild);
      return;
    }

    // ── Layout: auto (original logic) ─────────────────────────────────────

    // Dashboard grid: 4+ blocks — always use grid layout para coesão visual
    if (sorted.length >= 4) {
      var grid = document.createElement('div');
      grid.className = 'bnx-dashboard-grid';

      sorted.forEach(function(block, i) {
        var el = renderBlock(block, i);
        if (el) {
          animateEl(el, i);

          // Wide blocks span full width
          var isWide = block.type === 'chart' || block.type === 'table' || block.type === 'timeline' || block.type === 'interactive' || block.type === 'html';
          if (isWide) {
            el.style.gridColumn = '1 / -1';
          }
          grid.appendChild(el);
        }
      });
      container.appendChild(grid);
      return;
    }

    // Medium layout: 2-3 blocks
    if (sorted.length <= 3) {
      // Show each block as a full-width card, metrics side by side
      if (metrics.length >= 2) {
        var metricRow = document.createElement('div');
        metricRow.className = 'bnx-metrics-grid';
        metricRow.style.cssText = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:8px;';
        metrics.forEach(function(b, i) {
          var el = renderBlock(b, i);
          if (el) {
            animateEl(el, i);
            metricRow.appendChild(el);
          }
        });
        container.appendChild(metricRow);
      }

      // Non-metric blocks
      var remaining = sorted.filter(function(b) { return b.type !== 'metric'; });
      remaining.forEach(function(b, i) {
        var el = renderBlock(b, i);
        if (el) {
          animateEl(el, metrics.length + i);
          container.appendChild(el);
        }
      });

      // Single metric (not grouped)
      if (metrics.length === 1) {
        var singleMetric = renderBlock(metrics[0], 0);
        if (singleMetric) {
          animateEl(singleMetric, 0);
          container.insertBefore(singleMetric, container.firstChild);
        }
      }
      return;
    }

    // Default fallback: all blocks as-is
    sorted.forEach(function(b, i) {
      var el = renderBlock(b, i);
      if (el) {
        animateEl(el, i);
        container.appendChild(el);
      }
    });
  }

  // ── Color Helpers ──────────────────────────────────────────────────────────

  function getPurple(alpha) {
    // Use currentScheme's primary when possible (CSS variable)
    // For hex operations we still need a concrete color
    var scheme = COLOR_SCHEMES[currentScheme] || COLOR_SCHEMES.purple;
    // If scheme primary is a CSS var, fall back to theme-based hex for alpha ops
    var isPurpleScheme = currentScheme === 'purple';
    const theme = document.documentElement.getAttribute('data-theme');
    var base;
    if (isPurpleScheme) {
      base = theme === 'dark' ? '#8B5CF6' : '#7030A0';
    } else {
      // Map semantic schemes to concrete hex colors
      var schemeHex = {
        success: '#22C55E',
        warning: '#F59E0B',
        danger:  '#EF4444',
        info:    '#3B82F6',
        neutral: theme === 'dark' ? 'rgba(255,255,255,0.68)' : 'rgba(10,10,10,0.68)',
      };
      base = schemeHex[currentScheme] || (theme === 'dark' ? '#8B5CF6' : '#7030A0');
    }
    if (alpha !== undefined) {
      // For rgba-compatible colors, handle specially
      if (base.startsWith('rgba') || base.startsWith('rgb')) {
        return base;
      }
      return base + Math.round(alpha * 255).toString(16).padStart(2, '0');
    }
    return base;
  }

  function getChartColors(count) {
    const theme = document.documentElement.getAttribute('data-theme');
    const c = theme === 'dark'
      ? ['#8B5CF6', '#64748B', '#94A3B8', '#14B8A6', '#F59E0B', '#EF4444', '#38BDF8', '#A78BFA']
      : ['#7030A0', '#64748B', '#94A3B8', '#0F766E', '#B45309', '#B91C1C', '#0369A1', '#5B2EE0'];
    return c.slice(0, count || c.length);
  }

  // ── Simple Markdown Parser (for visual blocks content) ──────────────────────

  function markedParse(text) {
    if (!text) return '';
    var html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    html = html.replace(/\n\n/g, '<br><br>');
    html = html.replace(/\n/g, '<br>');
    return html;
  }

  // ── Safe Renderer Wrapper (Error Boundary) ──────────────────────────────────

  function safeRender(fn, block, fallbackMsg) {
    try {
      return fn(block);
    } catch (e) {
      console.error('[Bravonix] Render error:', block.type, e);
      const el = document.createElement('div');
      el.className = 'bnx-glass-card';
      el.style.cssText = 'padding:12px;border-left:3px solid var(--bnx-danger);';
      el.setAttribute('role', 'alert');
      el.innerHTML = `<div style="font-size:12px;font-weight:600;color:var(--bnx-danger);">[!] Erro ao renderizar</div>
        <div style="font-size:11px;color:var(--bnx-text-secondary);margin-top:4px;">${fallbackMsg || block.title || ''}</div>`;
      return el;
    }
  }

  function renderBlock(block, idx) {
    if (!block || !block.type) return null;
    const fn = {
      text: renderText,
      card: renderCard,
      metric: renderMetric,
      chart: renderChart,
      table: renderTable,
      panel: renderPanel,
      timeline: renderTimeline,
      interactive: renderInteractive,
      html: renderInteractive,
      action_list: renderActionList,
      document_reference: renderDocRef,
      form: renderForm,
      progress: renderProgress,
      comparison: renderComparison,
      tabs: renderTabs,
      kanban: renderKanban,
      gauge: renderGauge,
      funnel: renderFunnel,
      heatmap: renderHeatmap,
      sparkline: renderSparkline,
      treemap: renderTreemap,
    }[block.type];
    if (!fn) return null;
    return safeRender(fn, block, 'Falha ao processar este bloco.');
  }

  // ── Renderers ──────────────────────────────────────────────────────────────

  function renderText(block) {
    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:16px;font-size:14px;line-height:1.7;color:var(--bnx-text-primary);animation:bnx-fade-up 0.3s ease-out both;white-space:pre-wrap;';
    if (block.title) {
      const t = document.createElement('div');
      t.style.cssText = 'font-size:11px;color:var(--bnx-text-tertiary);text-transform:uppercase;letter-spacing:0.05em;font-weight:600;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid rgba(128,128,128,0.12);';
      t.textContent = block.title;
      el.appendChild(t);
    }
    var textContent = (typeof block.data === 'string' ? block.data
      : block.data?.content || block.data?.conteudo || block.data?.text || block.data?.message || block.data?.body) || block.description || '';
    if (textContent && textContent.trim()) {
      // Create a content div to avoid overwriting the title
      var contentDiv = document.createElement('div');
      contentDiv.style.cssText = 'font-size:14px;line-height:1.7;color:var(--bnx-text-primary);';
      contentDiv.innerHTML = markedParse(textContent);
      el.appendChild(contentDiv);
    } else {
      var fb = document.createElement('div');
      fb.style.cssText = 'padding:20px;text-align:center;color:var(--bnx-text-tertiary);font-size:13px;border:1px dashed rgba(128,128,128,0.2);border-radius:8px;';
      fb.innerHTML = '<span style="opacity:0.4;">&#9632;</span> <em>Bloco de texto</em>';
      el.appendChild(fb);
    }
    return el;
  }

  function renderCard(block) {
    var d = block.data || {};

    // Normalize: if block.data is a string, wrap it
    if (typeof d === 'string') { d = { conteudo: d }; }
    // Normalize: if block.data is an array, convert to items
    if (Array.isArray(d)) { d = { items: d }; }

    // Extract content from various possible fields
    var contentText = d.conteudo || d.content || d.text || d.description || d.body || d.message || '';
    // If block.description has content and no data content, use description
    if (!contentText && block.description && typeof block.description === 'string') {
      contentText = block.description;
    }

    var el = document.createElement('div');
    el.className = 'bnx-glass-card';
    // Status-based border
    var cardStatusColors = { positive: 'var(--bnx-success)', negative: 'var(--bnx-danger)', warning: 'var(--bnx-warning)', info: 'var(--bnx-info)' };
    var cardStatus = d.status || d.severity || '';
    var cardBorderColor = cardStatusColors[cardStatus] || getPurple();
    el.style.cssText = 'padding:16px;animation:bnx-fade-up 0.4s ease-out both;border-left:3px solid ' + cardBorderColor + ';';

    // Header with icon + title
    var header = document.createElement('div');
    header.style.cssText = 'display:flex;align-items:center;gap:10px;margin-bottom:10px;';

    var icon = document.createElement('div');
    icon.style.cssText = 'width:32px;height:32px;border-radius:8px;background:' + getPurple(0.12) + ';display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;';
    icon.textContent = block.icon || d.icon || ' ';
    header.appendChild(icon);

    var titleEl = document.createElement('div');
    titleEl.style.cssText = 'font-size:14px;font-weight:600;color:var(--bnx-text-primary);';
    titleEl.textContent = block.title || '';
    header.appendChild(titleEl);
    el.appendChild(header);

    // Content area — use prosify for safe HTML with basic formatting
    if (contentText) {
      var bodyDiv = document.createElement('div');
      bodyDiv.className = 'bnx-card-body';
      bodyDiv.style.cssText = 'font-size:13px;color:var(--bnx-text-primary);line-height:1.65;';
      bodyDiv.innerHTML = prosify(contentText);
      el.appendChild(bodyDiv);
    }

    // Key-value pairs for remaining data fields (skip content/conteudo/text fields)
    if (typeof d === 'object' && !Array.isArray(d)) {
      var skipKeys = { content:1, conteudo:1, text:1, description:1, body:1, message:1, icon:1, items:1 };
      var kvPairs = Object.keys(d).filter(function(k) { return !skipKeys[k]; });
      if (kvPairs.length > 0) {
        var kvDiv = document.createElement('div');
        kvDiv.style.cssText = 'margin-top:8px;display:flex;flex-direction:column;gap:4px;';
        kvPairs.forEach(function(key) {
          var val = d[key];
          if (val === null || val === undefined || val === '') return;
          if (typeof val === 'object') val = JSON.stringify(val);
          var row = document.createElement('div');
          row.style.cssText = 'display:flex;justify-content:space-between;padding:5px 0;font-size:12px;border-bottom:1px solid var(--bnx-rule);';
          var displayKey = key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ');
          row.innerHTML = '<span style="color:var(--bnx-text-secondary);font-weight:500;">' + displayKey + '</span>' +
            '<span style="color:var(--bnx-text-primary);font-weight:600;">' + val + '</span>';
          kvDiv.appendChild(row);
        });
        el.appendChild(kvDiv);
      }

      // If there are items, render them as a list
      if (d.items && Array.isArray(d.items) && d.items.length > 0) {
        var itemsDiv = document.createElement('div');
        itemsDiv.style.cssText = 'margin-top:8px;display:flex;flex-direction:column;gap:4px;';
        d.items.forEach(function(item) {
          var itemEl = document.createElement('div');
          itemEl.style.cssText = 'padding:6px 10px;background:var(--bnx-bg-secondary);border-radius:6px;font-size:12px;color:var(--bnx-text-secondary);';
          itemEl.textContent = typeof item === 'string' ? item : (item.label || item.title || item.name || JSON.stringify(item));
          itemsDiv.appendChild(itemEl);
        });
        el.appendChild(itemsDiv);
      }
    }

    makeExpandable(el, block);
    addCopyButton(el, (block.title || '') + (contentText ? ': ' + contentText : ''));
    addDownloadBtn(el, block);
    addTtsButton(el, block);
    el.setAttribute('role', 'figure');
    el.setAttribute('aria-label', block.title || 'Card');
    return el;
  }

  function renderMetric(block) {
    const d = block.data && typeof block.data === 'object' && !Array.isArray(block.data) ? block.data : {};
    const value = (d.value != null && d.value !== '') ? d.value : '—';
    const label = d.label || block.description || '';
    const delta = d.delta || '';
    const status = d.status || 'neutral';

    const statusColors = {
      positive: 'var(--bnx-success)',
      negative: 'var(--bnx-danger)',
      warning: 'var(--bnx-warning)',
      neutral: 'var(--bnx-text-secondary)',
    };

    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    var metricBorderColor = statusColors[status] || getPurple();
    el.style.cssText = 'padding:16px;text-align:center;display:flex;flex-direction:column;gap:2px;border-left:3px solid ' + metricBorderColor + ';';

    if (block.title) {
      const t = document.createElement('div');
      t.style.cssText = 'font-size:11px;color:var(--bnx-text-tertiary);text-transform:uppercase;letter-spacing:0.05em;font-weight:600;margin-bottom:4px;';
      t.textContent = block.title;
      el.appendChild(t);
    }

    const val = document.createElement('div');
    val.style.cssText = 'font-size:28px;font-weight:800;letter-spacing:-0.03em;color:var(--bnx-text-primary);font-feature-settings:"tnum";animation:bnx-metric-count 0.5s ease-out both;';
    // Animated counting effect for numeric values
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const numMatch = String(value).match(/^([^\d]*)?([\d,.]+)(.*)?$/);
    if (numMatch) {
      const prefix = numMatch[1] || '';
      const numStr = numMatch[2].replace(/,/g, '');
      const suffix = numMatch[3] || '';
      const targetNum = parseFloat(numStr);
      if (!isNaN(targetNum)) {
        if (prefersReducedMotion) {
          // No animation: set final value immediately
          val.textContent = prefix + targetNum.toLocaleString('pt-BR') + suffix;
        } else {
          val.textContent = prefix + '0' + suffix;
          const duration = 800;
          const startTime = performance.now();
          function animateCount(now) {
            const p = Math.min(1, (now - startTime) / duration);
            const ease = 1 - Math.pow(1 - p, 3);
            const current = Math.round(targetNum * ease);
            const formatted = current.toLocaleString('pt-BR');
            val.textContent = prefix + formatted + suffix;
            if (p < 1) requestAnimationFrame(animateCount);
          }
          requestAnimationFrame(animateCount);
        }
      } else {
        val.textContent = value;
      }
    } else {
      val.textContent = value;
    }
    el.appendChild(val);

    if (label) {
      const l = document.createElement('div');
      l.style.cssText = 'font-size:12px;color:var(--bnx-text-secondary);';
      l.textContent = label;
      el.appendChild(l);
    }

    // Gauge/radial indicator bar
    const statusPct = status === 'positive' ? 85 : status === 'warning' ? 50 : status === 'negative' ? 25 : 60;
    const gaugeContainer = document.createElement('div');
    gaugeContainer.style.cssText = 'width:100%;height:4px;background:var(--bnx-bg-tertiary);border-radius:2px;margin-top:6px;overflow:hidden;';
    const gaugeBar = document.createElement('div');
    if (prefersReducedMotion) {
      gaugeBar.style.cssText = `height:100%;border-radius:2px;width:${statusPct}%;background:${statusColors[status] || statusColors.neutral};transition:none;`;
    } else {
      gaugeBar.style.cssText = `height:100%;border-radius:2px;width:0%;background:${statusColors[status] || statusColors.neutral};transition:width 1s ease-out;`;
    }
    gaugeContainer.appendChild(gaugeBar);
    el.appendChild(gaugeContainer);
    // Animate gauge after render (skip if reduced motion)
    if (!prefersReducedMotion) {
      requestAnimationFrame(() => { gaugeBar.style.width = statusPct + '%'; });
    }

    if (delta) {
      const d = document.createElement('div');
      d.style.cssText = `font-size:12px;font-weight:600;color:${statusColors[status] || statusColors.neutral};margin-top:4px;`;
      d.textContent = delta;
      el.appendChild(d);
    }

    makeExpandable(el, block);
    addCopyButton(el, JSON.stringify({ value, label, delta, status }));
    addDownloadBtn(el, block);
    addTtsButton(el, block);
    el.setAttribute('role', 'figure');
    el.setAttribute('aria-label', block.title || 'Métrica');
    return el;
  }

  function renderChart(block) {
    var d = block.data || {};

    // Normalize chart type
    var chartType = (d.type || 'bar').toLowerCase();

    // Heatmap: delegate to dedicated renderer, converting chart data format
    if (chartType === 'heatmap') {
      var hmRows = [];
      if (d.datasets && d.datasets.length > 0) {
        hmRows = d.datasets.map(function(ds) {
          return { label: ds.label || '', values: Array.isArray(ds.data) ? ds.data : [] };
        });
      }
      return renderHeatmap({
        title: block.title,
        data: {
          columns: Array.isArray(d.labels) ? d.labels : [],
          xLabels: Array.isArray(d.labels) ? d.labels : [],
          rows: hmRows,
          matrix: hmRows.map(function(r) { return r.values; }),
        }
      });
    }

    // Treemap: delegate to dedicated renderer
    if (chartType === 'treemap' || chartType === 'tree') {
      return renderTreemap(block);
    }

    var validTypes = { bar:1, line:1, pie:1, donut:1, doughnut:1, radar:1, polarArea:1 };
    if (!validTypes[chartType]) chartType = 'bar';
    if (chartType === 'donut') chartType = 'doughnut';

    // Normalize labels
    var labels = d.labels || [];
    if (!Array.isArray(labels)) labels = [];
    labels = labels.map(function(l) { return String(l); });

    // Normalize datasets: ensure [{label, data}] format
    var datasets = d.datasets || [];
    if (!Array.isArray(datasets)) datasets = [];

    // If datasets is a flat array of numbers [10,20,30], wrap it
    if (datasets.length > 0 && typeof datasets[0] === 'number') {
      datasets = [{ label: block.title || 'Serie', data: datasets }];
    }

    // Ensure each dataset has label and data
    datasets = datasets.map(function(ds, i) {
      if (typeof ds === 'number') return { label: 'Serie ' + (i + 1), data: [ds] };
      return {
        label: ds.label || ds.name || ('Serie ' + (i + 1)),
        data: Array.isArray(ds.data) ? ds.data : (Array.isArray(ds.values) ? ds.values : []),
      };
    }).filter(function(ds) { return ds.data.length > 0; });

    if (chartType === 'pie' || chartType === 'doughnut') {
      var values = datasets.length === 1 ? datasets[0].data.map(function(v) { return Number(v); }) : [];
      var total = values.reduce(function(sum, v) { return sum + (isFinite(v) ? v : 0); }, 0);
      var validPartWhole = datasets.length === 1 && labels.length > 1 && labels.length <= 6 && total > 0 && values.every(function(v) { return isFinite(v) && v >= 0; });
      if (!validPartWhole) chartType = 'bar';
    }

    // Fallback: no valid chart data -> show as card with info
    if (!labels.length || !datasets.length) {
      var fb = { title: block.title, type: 'card', data: { conteudo: 'Dados insuficientes para gerar o gráfico. ' + (block.description || '') } };
      return renderCard(fb);
    }

    // Also accept flat values array as alternative
    if (!labels.length && d.values) {
      labels = d.values.map(function(_, i) { return 'Item ' + (i + 1); });
      datasets = [{ label: block.title || 'Valores', data: d.values }];
    }

    var el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:16px;animation:bnx-fade-up 0.3s ease-out both;';

    if (block.title) {
      var t = document.createElement('div');
      t.style.cssText = 'font-size:13px;font-weight:600;color:var(--bnx-text-primary);margin-bottom:12px;';
      t.textContent = block.title;
      el.appendChild(t);
    }

    // Accessible chart container
    var chartContainer = document.createElement('div');
    chartContainer.setAttribute('role', 'img');
    var ariaLabelParts = [block.title || 'Gráfico'];
    // Build a brief summary: first dataset, first 3 labels with values
    if (labels.length > 0 && datasets.length > 0) {
      var firstDs = datasets[0];
      var samplePairs = labels.slice(0, 3).map(function(lbl, i) {
        return lbl + ': ' + (firstDs.data[i] !== undefined ? firstDs.data[i] : '');
      });
      ariaLabelParts.push(samplePairs.join(', ') + (labels.length > 3 ? ' e mais ' + (labels.length - 3) + ' itens' : ''));
    }
    chartContainer.setAttribute('aria-label', ariaLabelParts.join('. '));
    el.appendChild(chartContainer);

    var canvas = document.createElement('canvas');
    canvas.style.cssText = 'max-height:280px;max-width:100%;';
    chartContainer.appendChild(canvas);

    // Hidden data table for screen readers
    var srTable = document.createElement('table');
    srTable.className = 'bnx-sr-only';
    srTable.setAttribute('aria-label', (block.title || 'Gráfico') + ' — dados');
    var srThead = document.createElement('thead');
    var srHeadRow = document.createElement('tr');
    var srThLabel = document.createElement('th');
    srThLabel.scope = 'col';
    srThLabel.textContent = 'Rótulo';
    srHeadRow.appendChild(srThLabel);
    datasets.forEach(function(ds) {
      var srTh = document.createElement('th');
      srTh.scope = 'col';
      srTh.textContent = ds.label || '';
      srHeadRow.appendChild(srTh);
    });
    srThead.appendChild(srHeadRow);
    srTable.appendChild(srThead);
    var srTbody = document.createElement('tbody');
    labels.forEach(function(lbl, rowIdx) {
      var srTr = document.createElement('tr');
      var srTdLabel = document.createElement('th');
      srTdLabel.scope = 'row';
      srTdLabel.textContent = lbl;
      srTr.appendChild(srTdLabel);
      datasets.forEach(function(ds) {
        var srTd = document.createElement('td');
        srTd.textContent = ds.data[rowIdx] !== undefined ? ds.data[rowIdx] : '';
        srTr.appendChild(srTd);
      });
      srTbody.appendChild(srTr);
    });
    srTable.appendChild(srTbody);
    el.appendChild(srTable);

    var colors = getChartColors(Math.max(datasets.length, labels.length));

    // Delay for DOM insertion before Chart.js init
    requestAnimationFrame(function () {
      try {
        var ctx = canvas.getContext('2d');
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        var gridColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
        var isPie = chartType === 'pie' || chartType === 'doughnut';
        var chartPrefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        var instance = new Chart(ctx, {
          type: chartType,
          data: {
            labels: labels,
            datasets: datasets.map(function(ds, i) {
              return {
                label: ds.label || '',
                data: ds.data || [],
                backgroundColor: isPie ? colors.slice(0, ds.data.length || colors.length) : (colors[i % colors.length] + '30'),
                borderColor: colors[i % colors.length],
                borderWidth: isPie ? 2 : 2,
                borderRadius: chartType === 'bar' ? 4 : 0,
                tension: chartType === 'line' ? 0.3 : 0,
                fill: chartType === 'line' ? false : undefined,
                pointRadius: chartType === 'line' ? 3 : undefined,
                pointHoverRadius: chartType === 'line' ? 6 : undefined,
              };
            }),
          },
          options: {
            responsive: true,
            maintainAspectRatio: true,
            animation: chartPrefersReducedMotion ? false : { duration: 800, easing: 'easeOutQuart' },
            plugins: {
              legend: {
                display: datasets.length > 1 || isPie,
                position: 'bottom',
                labels: {
                  color: isDark ? '#ccc' : '#666',
                  padding: 12,
                  font: { size: 11, family: 'Sora, system-ui, sans-serif' },
                  usePointStyle: true,
                  boxHeight: 6,
                },
              },
              tooltip: {
                backgroundColor: isDark ? 'rgba(0,0,0,0.85)' : 'rgba(255,255,255,0.95)',
                titleColor: isDark ? '#fff' : '#111',
                bodyColor: isDark ? '#ccc' : '#444',
                borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
                borderWidth: 1, cornerRadius: 8, padding: 10,
                titleFont: { size: 12, weight: '600' },
                bodyFont: { size: 11 },
              },
            },
            scales: !isPie ? {
              x: { grid: { color: gridColor }, ticks: { color: isDark ? '#999' : '#888', font: { size: 10 } } },
              y: { beginAtZero: true, grid: { color: gridColor }, ticks: { color: isDark ? '#999' : '#888', font: { size: 10 } } },
            } : undefined,
          },
        });
        chartInstances.push(instance);
      } catch (e) {
        console.error('[Bravonix] Chart render error:', e);
        // Show fallback text on error
        var errorDiv = document.createElement('div');
        errorDiv.style.cssText = 'padding:12px;text-align:center;color:var(--bnx-text-tertiary);font-size:12px;';
        errorDiv.textContent = 'Não foi possível renderizar o gráfico. Verifique os dados.';
        el.appendChild(errorDiv);
      }
    });

    makeExpandable(el, block);
    addCopyButton(el, block.title || 'Chart');
    addDownloadBtn(el, block);
    addChartCsvDownload(el, block, labels, datasets);
    el.setAttribute('role', 'figure');
    el.setAttribute('aria-label', block.title || 'Gráfico');
    return el;
  }

  function renderTable(block) {
    const d = block.data || {};
    const columns = d.columns || [];
    const rows = d.rows || [];

    if (!columns.length) {
      return renderText({ title: block.title, description: 'Tabela sem colunas', data: {} });
    }

    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:0;overflow:hidden;';

    // Table header with title + row count badge
    if (block.title || rows.length) {
      const header = document.createElement('div');
      header.style.cssText = 'display:flex;align-items:center;justify-content:space-between;padding:14px 16px 0;';
      if (block.title) {
        const t = document.createElement('div');
        t.style.cssText = 'font-size:13px;font-weight:600;color:var(--bnx-text-primary);display:flex;align-items:center;gap:6px;';
        var tableIcon = document.createElement('span');
        tableIcon.style.cssText = 'width:14px;height:14px;color:var(--bnx-text-tertiary);flex-shrink:0;';
        tableIcon.innerHTML = IC.table;
        t.appendChild(tableIcon);
        t.appendChild(document.createTextNode(block.title));
        header.appendChild(t);
      }
      if (rows.length > 0) {
        const badge = document.createElement('span');
        badge.style.cssText = 'font-size:10px;font-weight:600;color:var(--bnx-text-tertiary);background:var(--bnx-bg-secondary);' +
          'border-radius:4px;padding:2px 7px;font-family:var(--bnx-font-mono,monospace);';
        badge.textContent = rows.length + (rows.length === 1 ? ' linha' : ' linhas');
        header.appendChild(badge);
      }
      el.appendChild(header);
    }

    // Sort state
    var sortCol = null;
    var sortDir = 1; // 1=asc, -1=desc
    // currentRows rastreia a ordem atual (pós-sort) para que "Ver mais" respeite o sort
    var currentRows = rows.slice();

    function renderRows(sortedRows) {
      tbody.innerHTML = '';
      sortedRows.forEach(function(row, ri) {
        const tr = document.createElement('tr');
        tr.style.cssText = 'border-bottom:1px solid var(--bnx-rule);' + (ri % 2 === 1 ? 'background:var(--bnx-bg-secondary);' : '') + 'transition:background 0.15s ease;';
        columns.forEach(function(col) {
          const td = document.createElement('td');
          td.style.cssText = 'padding:9px 14px;color:var(--bnx-text-primary);font-size:12px;transition:color 0.15s;white-space:nowrap;max-width:240px;overflow:hidden;text-overflow:ellipsis;';
          var val = row[col.key] !== undefined ? String(row[col.key]) : '';
          td.textContent = val;
          td.title = val; // show full value on hover
          tr.appendChild(td);
        });
        tr.addEventListener('mouseenter', function() {
          tr.style.background = getPurple(0.07);
          tr.querySelectorAll('td').forEach(function(td) { td.style.color = 'var(--bnx-purple)'; });
        });
        tr.addEventListener('mouseleave', function() {
          tr.style.background = ri % 2 === 1 ? 'var(--bnx-bg-secondary)' : 'transparent';
          tr.querySelectorAll('td').forEach(function(td) { td.style.color = ''; });
        });
        tbody.appendChild(tr);
      });
    }

    const wrap = document.createElement('div');
    wrap.style.cssText = 'overflow-x:auto;padding:8px 0;';
    const table = document.createElement('table');
    table.setAttribute('role', 'table');
    table.style.cssText = 'width:100%;border-collapse:collapse;font-size:13px;';

    const thead = document.createElement('thead');
    const tr = document.createElement('tr');
    tr.style.cssText = 'border-bottom:2px solid ' + getPurple(0.15) + ';';
    columns.forEach(function(col, ci) {
      const th = document.createElement('th');
      th.style.cssText = 'padding:9px 14px;text-align:left;font-weight:600;font-size:11px;text-transform:uppercase;' +
        'letter-spacing:0.04em;color:var(--bnx-text-secondary);cursor:pointer;user-select:none;white-space:nowrap;';
      th.setAttribute('scope', 'col');
      th.setAttribute('aria-sort', 'none');

      var thContent = document.createElement('div');
      thContent.style.cssText = 'display:flex;align-items:center;gap:4px;';
      thContent.appendChild(document.createTextNode(col.label || col.key || ''));

      var sortIcon = document.createElement('span');
      sortIcon.style.cssText = 'width:12px;height:12px;color:var(--bnx-text-tertiary);flex-shrink:0;opacity:0.5;';
      sortIcon.innerHTML = IC.sort;
      thContent.appendChild(sortIcon);
      th.appendChild(thContent);

      th.addEventListener('mouseenter', function() { th.style.color = 'var(--bnx-purple)'; sortIcon.style.opacity = '1'; });
      th.addEventListener('mouseleave', function() {
        if (sortCol !== col.key) { th.style.color = ''; sortIcon.style.opacity = '0.5'; }
      });

      th.addEventListener('click', function() {
        if (sortCol === col.key) { sortDir *= -1; }
        else { sortCol = col.key; sortDir = 1; }
        // Update all sort icons
        thead.querySelectorAll('th').forEach(function(t) {
          t.style.color = '';
          var si = t.querySelector('span');
          if (si) { si.innerHTML = IC.sort; si.style.opacity = '0.5'; }
          t.setAttribute('aria-sort', 'none');
        });
        th.style.color = 'var(--bnx-purple)';
        sortIcon.innerHTML = sortDir === 1 ? IC.sortAsc : IC.sortDesc;
        sortIcon.style.opacity = '1';
        th.setAttribute('aria-sort', sortDir === 1 ? 'ascending' : 'descending');
        // Sort e atualiza currentRows para que "Ver mais" respeite a ordem
        currentRows = rows.slice().sort(function(a, b) {
          var av = a[col.key] !== undefined ? a[col.key] : '';
          var bv = b[col.key] !== undefined ? b[col.key] : '';
          var an = parseFloat(String(av).replace(/[^\d.-]/g, ''));
          var bn = parseFloat(String(bv).replace(/[^\d.-]/g, ''));
          if (!isNaN(an) && !isNaN(bn)) return (an - bn) * sortDir;
          return String(av).localeCompare(String(bv), 'pt-BR') * sortDir;
        });
        // Renderiza respeitando estado atual do "Ver mais"
        renderRows(showAllRows ? currentRows : currentRows.slice(0, TABLE_PAGE));
      });

      tr.appendChild(th);
    });
    thead.appendChild(tr);
    table.appendChild(thead);

    const TABLE_PAGE = 15;
    const tbody = document.createElement('tbody');
    var visibleRows = rows.length > TABLE_PAGE ? rows.slice(0, TABLE_PAGE) : rows;
    renderRows(visibleRows);
    table.appendChild(tbody);
    wrap.appendChild(table);
    el.appendChild(wrap);

    // Botão "Ver mais" quando tabela tem mais de TABLE_PAGE linhas
    if (rows.length > TABLE_PAGE) {
      var showAllRows = false;
      var verMaisWrap = document.createElement('div');
      verMaisWrap.style.cssText = 'text-align:center;padding:8px 0 4px;border-top:1px solid var(--bnx-rule);';
      var verMaisBtn = document.createElement('button');
      verMaisBtn.style.cssText = 'background:none;border:none;cursor:pointer;font-size:11px;font-weight:600;' +
        'color:var(--bnx-purple);padding:4px 12px;border-radius:6px;transition:background 0.15s;';
      verMaisBtn.textContent = 'Ver mais (+' + (rows.length - TABLE_PAGE) + ' linhas)';
      verMaisBtn.addEventListener('mouseenter', function() { verMaisBtn.style.background = getPurple(0.08); });
      verMaisBtn.addEventListener('mouseleave', function() { verMaisBtn.style.background = 'none'; });
      verMaisBtn.addEventListener('click', function() {
        showAllRows = !showAllRows;
        if (showAllRows) {
          renderRows(currentRows);
          verMaisBtn.textContent = 'Ver menos';
        } else {
          renderRows(currentRows.slice(0, TABLE_PAGE));
          verMaisBtn.textContent = 'Ver mais (+' + (rows.length - TABLE_PAGE) + ' linhas)';
        }
      });
      verMaisWrap.appendChild(verMaisBtn);
      el.appendChild(verMaisWrap);
    }
    makeExpandable(el, block);
    addCopyButton(el, block.title || 'Table');
    addDownloadBtn(el, block);
    addTableCsvDownload(el, block, columns, rows);
    el.setAttribute('role', 'figure');
    el.setAttribute('aria-label', block.title || 'Tabela');
    return el;
  }

  function renderPanel(block) {
    const d = block.data || {};
    const errorType = d.type === 'error';
    const warningType = d.type === 'warning';
    const successType = d.type === 'success';

    const el = document.createElement('div');
    if (errorType) {
      el.className = 'bnx-error-banner';
      el.style.cssText = 'animation:bnx-fade-in 0.3s ease-out both;';
      var errIcon = document.createElement('span');
      errIcon.className = 'bnx-error-banner-icon';
      errIcon.innerHTML = IC.error;
      var errText = document.createElement('span');
      errText.textContent = d.error || block.description || block.title || '';
      el.appendChild(errIcon);
      el.appendChild(errText);
    } else {
      el.className = 'bnx-glass-card';
      var panelBorderColor = warningType ? 'var(--bnx-warning)' : successType ? 'var(--bnx-success)' : getPurple();
      el.style.cssText = 'padding:16px;border-left:3px solid ' + panelBorderColor + ';';
      if (block.title) {
        const t = document.createElement('div');
        t.style.cssText = 'font-size:14px;font-weight:600;margin-bottom:8px;color:var(--bnx-text-primary);';
        t.textContent = block.title;
        el.appendChild(t);
      }
      const c = document.createElement('div');
      c.className = 'bnx-panel-body';
      c.style.cssText = 'font-size:13px;color:var(--bnx-text-secondary);line-height:1.65;';
      c.innerHTML = prosify(d.content || block.description || '');
      el.appendChild(c);
    }
    return el;
  }

  function renderTimeline(block) {
    const data = block.data;
    const items = Array.isArray(data) ? data : (data?.items || data?.events || []);
    if (!items.length) return renderText({ data: { content: 'Sem dados na timeline' } });

    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:16px;';

    if (block.title) {
      const t = document.createElement('div');
      t.style.cssText = 'font-size:13px;font-weight:600;margin-bottom:12px;color:var(--bnx-text-primary);';
      t.textContent = block.title;
      el.appendChild(t);
    }

    items.forEach((item, i) => {
      const itemEl = document.createElement('div');
      itemEl.style.cssText = 'display:flex;gap:12px;padding:0 0 16px 0;position:relative;animation:bnx-slide-right 0.3s ease-out both;animation-delay:' + (i * 0.06) + 's;';

      const dotLine = document.createElement('div');
      dotLine.style.cssText = 'display:flex;flex-direction:column;align-items:center;';
      const dot = document.createElement('div');
      dot.style.cssText = `width:28px;height:28px;border-radius:50%;background:${getPurple(0.12)};display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:${getPurple()};flex-shrink:0;`;
      dot.textContent = i + 1;
      dotLine.appendChild(dot);
      if (i < items.length - 1) {
        const line = document.createElement('div');
        line.style.cssText = 'width:2px;flex:1;background:var(--bnx-rule);margin:4px 0;';
        dotLine.appendChild(line);
      }
      itemEl.appendChild(dotLine);

      const content = document.createElement('div');
      content.style.cssText = 'flex:1;min-width:0;padding-top:3px;';

      const strong = document.createElement('div');
      strong.style.cssText = 'font-size:13px;font-weight:600;color:var(--bnx-text-primary);';
      strong.textContent = item.title || item.name || item.label || item.date || `Evento ${i + 1}`;
      content.appendChild(strong);

      const desc = document.createElement('div');
      desc.style.cssText = 'font-size:12px;color:var(--bnx-text-secondary);margin-top:2px;line-height:1.5;';
      desc.textContent = item.description || item.content || item.event || '';
      content.appendChild(desc);

      itemEl.appendChild(content);
      el.appendChild(itemEl);
    });

    makeExpandable(el, block);
    addCopyButton(el, block.title || 'Timeline');
    addDownloadBtn(el, block);
    el.setAttribute('role', 'figure');
    el.setAttribute('aria-label', block.title || 'Timeline');
    return el;
  }

  function renderActionList(block) {
    const data = block.data;
    const items = Array.isArray(data) ? data : (data?.items || data?.actions || []);

    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:12px;display:flex;flex-wrap:wrap;gap:8px;';

    if (items.length === 0 && block.data?.steps) {
      for (const step of block.data.steps) {
        const btn = document.createElement('button');
        btn.className = 'bnx-action-btn primary';
        btn.textContent = step;
        el.appendChild(btn);
      }
      return el;
    }

    for (const item of items) {
      const btn = document.createElement('button');
      const isPrimary = item.type === 'primary';
      btn.style.cssText = `padding:8px 16px;border-radius:8px;border:none;font-size:12px;font-weight:600;cursor:pointer;
        font-family:var(--bnx-font-sans);transition:all 0.2s;
        background:${isPrimary ? getPurple() : 'var(--bnx-bg-secondary)'};
        color:${isPrimary ? '#fff' : 'var(--bnx-text-primary)'};`;
      btn.textContent = item.label || item;
      btn.addEventListener('mouseenter', () => {
        btn.style.transform = 'translateY(-1px)';
        btn.style.boxShadow = 'var(--bnx-shadow)';
      });
      btn.addEventListener('mouseleave', () => {
        btn.style.transform = 'none';
        btn.style.boxShadow = 'none';
      });
      if (item.action) {
        btn.dataset.action = typeof item.action === 'string' ? item.action : JSON.stringify(item.action);
      }
      el.appendChild(btn);
    }

    return el;
  }

  function renderDocRef(block) {
    const doc = block.data || {};
    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = `padding:14px;border-left:3px solid ${getPurple()};`;

    const title = document.createElement('div');
    title.style.cssText = 'font-size:13px;font-weight:600;color:var(--bnx-text-primary);';
    title.textContent = block.title || 'Documento';
    el.appendChild(title);

    if (block.description) {
      const d = document.createElement('div');
      d.style.cssText = 'font-size:12px;color:var(--bnx-text-secondary);margin-top:2px;';
      d.textContent = block.description;
      el.appendChild(d);
    }

    if (doc.snippet) {
      const s = document.createElement('div');
      s.style.cssText = 'font-size:12px;color:var(--bnx-text-secondary);padding:8px;background:var(--bnx-bg-secondary);border-radius:6px;margin-top:8px;font-style:italic;';
      s.textContent = `"${doc.snippet}"`;
      el.appendChild(s);
    }

    return el;
  }

  // ── Interactive HTML ────────────────────────────────────────────────────────

  function renderInteractive(block) {
    const html = block.data?.content || block.description || '';
    if (!html) return renderText({ data: { content: 'Sem conteúdo interativo' } });

    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:0;overflow:hidden;position:relative;';

    if (block.title) {
      const t = document.createElement('div');
      t.style.cssText = 'font-size:13px;font-weight:600;padding:14px 16px 0;color:var(--bnx-text-primary);';
      t.textContent = block.title;
      el.appendChild(t);
    }

    const iframe = document.createElement('iframe');
    iframe.style.cssText = 'width:100%;border:none;display:block;';
    iframe.srcdoc = html;
    iframe.sandbox = 'allow-scripts allow-same-origin';
    iframe.loading = 'lazy';

    // Auto-resize iframe to content height
    iframe.addEventListener('load', () => {
      try {
        const h = iframe.contentWindow.document.documentElement.scrollHeight;
        iframe.style.height = h + 'px';
      } catch (e) {
        iframe.style.height = '300px';
      }
    });

    el.appendChild(iframe);
    makeExpandable(el, block);
    addCopyButton(el, block.title || 'Interactive');
    addDownloadBtn(el, block);
    el.setAttribute('role', 'figure');
    el.setAttribute('aria-label', block.title || 'Interactive');
    return el;
  }

  // ── Cleanup ────────────────────────────────────────────────────────────────

  // ── New C1 Components ─────────────────────────────────────────────────

  function renderForm(block) {
    const d = block.data || {};
    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:16px;animation:bnx-fade-up 0.4s ease-out both;';
    if (block.title) {
      const t = document.createElement('div');
      t.style.cssText = 'font-size:14px;font-weight:600;margin-bottom:12px;';
      t.textContent = block.title;
      el.appendChild(t);
    }
    // Parse fields from data
    var fields = [];
    if (typeof d.fields === 'string') {
      try { fields = JSON.parse(d.fields); } catch(e) { fields = d.fields.split(',').map(function(f) { return {label:f.trim(),type:'text',name:f.trim()}; }); }
    } else if (Array.isArray(d.fields)) {
      fields = d.fields;
    } else if (d.fields && typeof d.fields === 'object') {
      fields = Object.keys(d.fields).map(function(k) { return {label:d.fields[k],name:k,type:'text'}; });
    }
    if (fields.length === 0) {
      fields = [{label:'Campo',name:'campo',type:'text',placeholder:'Digite aqui...'}];
    }
    fields.forEach(function(f) {
      var fg = document.createElement('div');
      fg.style.cssText = 'margin-bottom:10px;';
      var lb = document.createElement('label');
      lb.style.cssText = 'display:block;font-size:12px;font-weight:500;margin-bottom:4px;color:var(--bnx-text-secondary);';
      lb.textContent = f.label || f.name || 'Campo';
      fg.appendChild(lb);
      if (f.type === 'select' || f.type === 'dropdown') {
        var sel = document.createElement('select');
        sel.style.cssText = 'width:100%;padding:8px 10px;border:1px solid var(--bnx-border,rgba(128,128,128,0.2));border-radius:6px;background:var(--bnx-bg-secondary);color:var(--bnx-text-primary);font-size:13px;';
        (f.options || ['Opcao 1','Opcao 2']).forEach(function(o) {
          var opt = document.createElement('option');
          opt.textContent = typeof o === 'object' ? o.label || o.value : o;
          sel.appendChild(opt);
        });
        fg.appendChild(sel);
      } else if (f.type === 'textarea') {
        var ta = document.createElement('textarea');
        ta.placeholder = f.placeholder || '';
        ta.style.cssText = 'width:100%;padding:8px 10px;border:1px solid var(--bnx-border,rgba(128,128,128,0.2));border-radius:6px;background:var(--bnx-bg-secondary);color:var(--bnx-text-primary);font-size:13px;min-height:60px;resize:vertical;';
        fg.appendChild(ta);
      } else {
        var inp = document.createElement('input');
        inp.type = f.type || 'text';
        inp.placeholder = f.placeholder || '';
        inp.style.cssText = 'width:100%;padding:8px 10px;border:1px solid var(--bnx-border,rgba(128,128,128,0.2));border-radius:6px;background:var(--bnx-bg-secondary);color:var(--bnx-text-primary);font-size:13px;';
        fg.appendChild(inp);
      }
      el.appendChild(fg);
    });
    var btn = document.createElement('button');
    btn.textContent = d.submitLabel || 'Enviar';
    btn.style.cssText = 'padding:8px 20px;background:var(--bnx-purple,#7030A0);color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;margin-top:4px;';
    el.appendChild(btn);
    return el;
  }

  function renderProgress(block) {
    const d = block.data || {};
    const value = Math.min(100, Math.max(0, parseFloat(d.value) || parseFloat(d.percent) || 0));
    const maxVal = parseFloat(d.max) || 100;
    const pct = Math.round((value / maxVal) * 100);
    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:16px;animation:bnx-fade-up 0.4s ease-out both;';
    if (block.title) {
      const t = document.createElement('div');
      t.style.cssText = 'font-size:12px;font-weight:600;margin-bottom:8px;color:var(--bnx-text-secondary);';
      t.textContent = block.title;
      el.appendChild(t);
    }
    // Percentage display
    const pctDiv = document.createElement('div');
    pctDiv.style.cssText = 'font-size:24px;font-weight:800;color:var(--bnx-text-primary);margin-bottom:6px;';
    pctDiv.textContent = pct + '%';
    el.appendChild(pctDiv);
    // Bar
    const barOuter = document.createElement('div');
    barOuter.style.cssText = 'width:100%;height:8px;background:var(--bnx-bg-tertiary,rgba(128,128,128,0.12));border-radius:4px;overflow:hidden;';
    const barInner = document.createElement('div');
    barInner.style.cssText = 'height:100%;width:0%;background:linear-gradient(90deg,var(--bnx-purple,#7030A0),var(--bnx-purple-light,#8B5CF6));border-radius:4px;transition:width 1s ease-out;';
    barOuter.appendChild(barInner);
    el.appendChild(barOuter);
    setTimeout(function() { barInner.style.width = pct + '%'; }, 100);
    if (d.label) {
      const lb = document.createElement('div');
      lb.style.cssText = 'font-size:12px;color:var(--bnx-text-tertiary);margin-top:6px;';
      lb.textContent = d.label;
      el.appendChild(lb);
    }
    return el;
  }

  function renderComparison(block) {
    const d = block.data || {};
    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:16px;animation:bnx-fade-up 0.4s ease-out both;';
    if (block.title) {
      const t = document.createElement('div');
      t.style.cssText = 'font-size:13px;font-weight:600;margin-bottom:10px;';
      t.textContent = block.title;
      el.appendChild(t);
    }
    var items = d.items || d.rows || [];
    if (typeof items === 'string') {
      try { items = JSON.parse(items); } catch(e) { items = items.split(',').map(function(x) { return {a:x,b:''}; }); }
    }
    if (items.length === 0) {
      var fb = document.createElement('div');
      fb.style.cssText = 'padding:12px;text-align:center;color:var(--bnx-text-tertiary);font-size:12px;';
      fb.textContent = d.description || 'Comparacao vazia';
      el.appendChild(fb);
      return el;
    }
    var grid = document.createElement('div');
    grid.style.cssText = 'display:grid;grid-template-columns:1fr 1fr;gap:8px;';
    items.forEach(function(item) {
      var a = typeof item === 'object' ? (item.a || item.left || item.name || '') : item;
      var b = typeof item === 'object' ? (item.b || item.right || item.value || '') : '';
      var ca = document.createElement('div');
      ca.style.cssText = 'padding:8px;background:var(--bnx-bg-secondary,rgba(128,128,128,0.06));border-radius:6px;font-size:13px;';
      ca.textContent = String(a);
      grid.appendChild(ca);
      var cb = document.createElement('div');
      cb.style.cssText = 'padding:8px;background:var(--bnx-bg-secondary,rgba(128,128,128,0.06));border-radius:6px;font-size:13px;color:var(--bnx-text-secondary);';
      cb.textContent = String(b);
      grid.appendChild(cb);
    });
    el.appendChild(grid);
    return el;
  }

  function renderTabs(block) {
    const d = block.data || {};
    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:16px;animation:bnx-fade-up 0.4s ease-out both;';
    var tabs = d.tabs || d.items || [];
    if (typeof tabs === 'string') {
      try { tabs = JSON.parse(tabs); } catch(e) { tabs = [{label:'Aba',content:tabs}]; }
    }
    if (tabs.length === 0) tabs = [{label:'Info',content:block.description || ''}];
    // Tab headers
    var header = document.createElement('div');
    header.style.cssText = 'display:flex;gap:4px;margin-bottom:10px;border-bottom:1px solid var(--bnx-border,rgba(128,128,128,0.15));padding-bottom:4px;';
    var contentDiv = document.createElement('div');
    contentDiv.style.cssText = 'font-size:13px;line-height:1.6;min-height:40px;';
    tabs.forEach(function(tab, idx) {
      var tb = document.createElement('button');
      tb.textContent = tab.label || tab.title || 'Aba ' + (idx+1);
      tb.style.cssText = 'padding:6px 12px;border:none;background:' + (idx === 0 ? 'var(--bnx-purple,rgba(112,48,160,0.12))' : 'transparent') + ';border-radius:6px 6px 0 0;font-size:12px;font-weight:' + (idx === 0 ? '600' : '400') + ';color:' + (idx === 0 ? 'var(--bnx-purple,#7030A0)' : 'var(--bnx-text-secondary)') + ';cursor:pointer;transition:all 0.2s;';
      tb.onclick = function() {
        header.querySelectorAll('button').forEach(function(b) { b.style.background = 'transparent'; b.style.fontWeight = '400'; b.style.color = 'var(--bnx-text-secondary)'; });
        tb.style.background = 'var(--bnx-purple,rgba(112,48,160,0.12))';
        tb.style.fontWeight = '600';
        tb.style.color = 'var(--bnx-purple,#7030A0)';
        contentDiv.innerHTML = markedParse(tab.content || tab.body || '');
      };
      header.appendChild(tb);
    });
    if (tabs[0]) contentDiv.innerHTML = markedParse(tabs[0].content || tabs[0].body || '');
    el.appendChild(header);
    el.appendChild(contentDiv);
    return el;
  }

  function renderKanban(block) {
    const d = block.data || {};
    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:16px;animation:bnx-fade-up 0.4s ease-out both;';
    if (block.title) {
      const t = document.createElement('div');
      t.style.cssText = 'font-size:13px;font-weight:600;margin-bottom:10px;';
      t.textContent = block.title;
      el.appendChild(t);
    }
    var columns = d.columns || d.items || [];
    if (typeof columns === 'string') { try { columns = JSON.parse(columns); } catch(e) { columns = []; } }
    if (columns.length === 0) columns = [{title:'A Fazer',cards:[{title:'Tarefa 1'}]},{title:'Feito',cards:[]}];
    var grid = document.createElement('div');
    grid.style.cssText = 'display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;';
    columns.forEach(function(col) {
      var colDiv = document.createElement('div');
      colDiv.style.cssText = 'background:var(--bnx-bg-secondary,rgba(128,128,128,0.06));border-radius:8px;padding:8px;';
      var colTitle = document.createElement('div');
      colTitle.style.cssText = 'font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;color:var(--bnx-text-tertiary);';
      colTitle.textContent = col.title || col.name || 'Coluna';
      colDiv.appendChild(colTitle);
      (col.cards || col.items || []).forEach(function(card) {
        var cd = document.createElement('div');
        cd.style.cssText = 'padding:6px 8px;margin-bottom:4px;background:var(--bnx-bg-card);border-radius:6px;font-size:12px;border-left:3px solid var(--bnx-purple,#7030A0);';
        cd.textContent = card.title || card.name || card.content || '';
        colDiv.appendChild(cd);
      });
      grid.appendChild(colDiv);
    });
    el.appendChild(grid);
    return el;
  }

  function renderGauge(block) {
    const d = block.data || {};
    const value = Math.min(100, Math.max(0, parseFloat(d.value) || 0));
    const maxVal = Math.max(1, Math.abs(parseFloat(d.max) || 100));
    const pct = Math.max(0, Math.min(100, Math.round((value / maxVal) * 100)));
    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:16px;text-align:center;animation:bnx-fade-up 0.4s ease-out both;';
    if (block.title) {
      const t = document.createElement('div');
      t.style.cssText = 'font-size:11px;color:var(--bnx-text-tertiary);text-transform:uppercase;letter-spacing:0.05em;font-weight:600;margin-bottom:8px;';
      t.textContent = block.title;
      el.appendChild(t);
    }
    // Simple SVG gauge
    var svgNS = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', '0 0 120 70');
    svg.style.cssText = 'width:120px;height:70px;display:block;margin:0 auto 8px;';
    // Background arc
    var bgArc = document.createElementNS(svgNS, 'path');
    var r = 50, cx = 60, cy = 60;
    var startA = Math.PI * 0.75;
    var endA = Math.PI * 2.25;
    function polarToCart(cx, cy, r, a) { return {x:cx + r * Math.cos(a), y:cy + r * Math.sin(a)}; }
    var p1 = polarToCart(cx, cy, r, startA);
    var p2 = polarToCart(cx, cy, r, endA);
    var dStr = 'M' + p1.x + ',' + p1.y + ' A' + r + ',' + r + ' 0 1,1 ' + p2.x + ',' + p2.y;
    bgArc.setAttribute('d', dStr);
    bgArc.setAttribute('fill', 'none');
    bgArc.setAttribute('stroke', 'rgba(128,128,128,0.12)');
    bgArc.setAttribute('stroke-width', '10');
    svg.appendChild(bgArc);
    // Value arc
    var valAngle = startA + (endA - startA) * (pct / 100);
    var vp2 = polarToCart(cx, cy, r, valAngle);
    var largeArc = (pct / 100) > 0.5 ? 1 : 0;
    var valArc = document.createElementNS(svgNS, 'path');
    valArc.setAttribute('d', 'M' + p1.x + ',' + p1.y + ' A' + r + ',' + r + ' 0 ' + largeArc + ',1 ' + vp2.x + ',' + vp2.y);
    valArc.setAttribute('fill', 'none');
    valArc.setAttribute('stroke', 'var(--bnx-purple,#7030A0)');
    valArc.setAttribute('stroke-width', '10');
    valArc.setAttribute('stroke-linecap', 'round');
    svg.appendChild(valArc);
    // Value text
    var vt = document.createElementNS(svgNS, 'text');
    vt.setAttribute('x', '60');
    vt.setAttribute('y', '58');
    vt.setAttribute('text-anchor', 'middle');
    vt.setAttribute('font-size', '18');
    vt.setAttribute('font-weight', '800');
    vt.setAttribute('fill', 'var(--bnx-text-primary)');
    vt.textContent = pct + '%';
    svg.appendChild(vt);
    el.appendChild(svg);
    if (d.label) {
      var lb = document.createElement('div');
      lb.style.cssText = 'font-size:12px;color:var(--bnx-text-tertiary);';
      lb.textContent = d.label;
      el.appendChild(lb);
    }
    return el;
  }

  function renderFunnel(block) {
    const d = block.data || {};
    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:16px;animation:bnx-fade-up 0.4s ease-out both;';
    if (block.title) {
      const t = document.createElement('div');
      t.style.cssText = 'font-size:13px;font-weight:600;margin-bottom:12px;color:var(--bnx-text-primary);';
      t.textContent = block.title;
      el.appendChild(t);
    }

    var stages = d.stages || d.items || d.steps || [];
    if (typeof stages === 'string') { try { stages = JSON.parse(stages); } catch(e) { stages = []; } }
    if (stages.length === 0) stages = [{label:'Visitantes',value:1000},{label:'Leads',value:400},{label:'Oportunidades',value:120},{label:'Conversao',value:40}];

    // Normalize values
    var stageData = stages.map(function(s) {
      return {
        label: s.label || s.name || s.stage || 'Etapa',
        value: parseFloat(s.value || s.count || s.total || 0) || 0,
        description: s.description || s.desc || '',
      };
    });

    var totalVal = stageData[0] ? stageData[0].value : 1;
    var maxVal = Math.max.apply(null, stageData.map(function(s) { return s.value; })) || 1;

    // Gradient colors for stages: from scheme primary (intense) to lighter
    var schemeColors = {
      purple:  ['#7030A0','#8B5CF6','#A78BFA','#C4B5FD'],
      success: ['#16A34A','#22C55E','#4ADE80','#86EFAC'],
      warning: ['#B45309','#D97706','#F59E0B','#FCD34D'],
      danger:  ['#B91C1C','#DC2626','#EF4444','#FCA5A5'],
      info:    ['#1D4ED8','#2563EB','#3B82F6','#93C5FD'],
      neutral: ['#374151','#6B7280','#9CA3AF','#D1D5DB'],
    };
    var gradColors = schemeColors[currentScheme] || schemeColors.purple;

    var funnelWrap = document.createElement('div');
    funnelWrap.className = 'bnx-funnel-wrap';
    funnelWrap.style.cssText = 'display:flex;flex-direction:column;gap:4px;';

    stageData.forEach(function(s, idx) {
      var widthPct = maxVal > 0 ? (s.value / maxVal) * 100 : 100;
      var conversionPct = idx > 0 && stageData[idx-1].value > 0
        ? Math.round((s.value / stageData[idx-1].value) * 100)
        : 100;
      var totalConvPct = totalVal > 0 ? Math.round((s.value / totalVal) * 100) : 100;
      var colorIdx = Math.min(idx, gradColors.length - 1);
      var color = gradColors[colorIdx];

      var stageEl = document.createElement('div');
      stageEl.className = 'bnx-funnel-stage';
      stageEl.style.cssText = 'display:flex;flex-direction:column;gap:2px;';

      // Drop-off indicator between stages
      if (idx > 0) {
        var dropoff = stageData[idx-1].value - s.value;
        var dropoffPct = stageData[idx-1].value > 0 ? Math.round((dropoff / stageData[idx-1].value) * 100) : 0;
        if (dropoffPct > 0) {
          var dropEl = document.createElement('div');
          dropEl.style.cssText = 'font-size:10px;color:var(--bnx-text-tertiary);text-align:center;padding:1px 0;';
          dropEl.textContent = '\u2193 ' + dropoffPct + '% saiu (' + dropoff.toLocaleString('pt-BR') + ')';
          funnelWrap.appendChild(dropEl);
        }
      }

      // Bar row
      var barRow = document.createElement('div');
      barRow.style.cssText = 'display:flex;align-items:center;gap:8px;';

      // Label
      var lb = document.createElement('div');
      lb.className = 'bnx-funnel-label';
      lb.style.cssText = 'font-size:12px;min-width:90px;max-width:90px;color:var(--bnx-text-secondary);text-overflow:ellipsis;overflow:hidden;white-space:nowrap;';
      lb.textContent = s.label;
      lb.title = s.label + (s.description ? ': ' + s.description : '');
      barRow.appendChild(lb);

      // Bar container (trapezoid effect via margin)
      var barContainer = document.createElement('div');
      barContainer.style.cssText = 'flex:1;display:flex;align-items:center;';

      var barOuter = document.createElement('div');
      barOuter.className = 'bnx-funnel-bar-outer';
      barOuter.style.cssText = 'width:100%;height:28px;background:var(--bnx-bg-secondary);border-radius:4px;overflow:hidden;position:relative;';

      var barInner = document.createElement('div');
      barInner.className = 'bnx-funnel-bar';
      barInner.style.cssText = 'height:100%;width:0%;background:' + color + ';border-radius:4px;transition:width 0.9s ease-out;opacity:0.85;';
      barInner.title = s.label + ': ' + s.value.toLocaleString('pt-BR') + ' (' + totalConvPct + '% do total)';

      barOuter.appendChild(barInner);
      barContainer.appendChild(barOuter);
      barRow.appendChild(barContainer);

      // Value + pct
      var valDiv = document.createElement('div');
      valDiv.style.cssText = 'display:flex;flex-direction:column;align-items:flex-end;min-width:64px;';

      var valNum = document.createElement('div');
      valNum.className = 'bnx-funnel-value';
      valNum.style.cssText = 'font-size:12px;font-weight:700;color:var(--bnx-text-primary);line-height:1.2;';
      valNum.textContent = s.value.toLocaleString('pt-BR');
      valDiv.appendChild(valNum);

      var pctEl = document.createElement('div');
      pctEl.className = 'bnx-funnel-pct';
      pctEl.style.cssText = 'font-size:10px;color:' + color + ';font-weight:600;';
      pctEl.textContent = (idx === 0 ? '100%' : conversionPct + '% step');
      valDiv.appendChild(pctEl);

      barRow.appendChild(valDiv);
      stageEl.appendChild(barRow);
      funnelWrap.appendChild(stageEl);

      // Animate bar after render
      setTimeout(function() { barInner.style.width = widthPct + '%'; }, 80 + idx * 100);
    });

    el.appendChild(funnelWrap);

    makeExpandable(el, block);
    addCopyButton(el, block.title || 'Funnel');
    el.setAttribute('role', 'figure');
    el.setAttribute('aria-label', block.title || 'Funil');
    return el;
  }

  function renderHeatmap(block) {
    const d = block.data || {};
    const el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:16px;animation:bnx-fade-up 0.4s ease-out both;overflow-x:auto;';
    if (block.title) {
      const t = document.createElement('div');
      t.style.cssText = 'font-size:13px;font-weight:600;margin-bottom:10px;color:var(--bnx-text-primary);';
      t.textContent = block.title;
      el.appendChild(t);
    }

    // Normalize data — support rows=[{label, values:[]}], matrix=[[]], or data=[[]]
    var matrix = [];
    var rowLabels = [];
    var colLabels = d.columns || d.xLabels || d.col_labels || [];

    if (d.rows && Array.isArray(d.rows) && d.rows.length > 0 && typeof d.rows[0] === 'object' && !Array.isArray(d.rows[0])) {
      // Format: rows = [{label, values:[]}]
      d.rows.forEach(function(r) {
        rowLabels.push(r.label || r.name || '');
        matrix.push(Array.isArray(r.values) ? r.values : Array.isArray(r.data) ? r.data : []);
      });
    } else {
      // Format: matrix=[[]] or rows=[[]]
      matrix = d.matrix || d.data || d.rows || [];
      if (typeof matrix === 'string') { try { matrix = JSON.parse(matrix); } catch(e) { matrix = [[0]]; } }
      if (!Array.isArray(matrix) || matrix.length === 0) matrix = [[0]];
    }

    // Collect all numeric values for scale
    var allVals = [];
    matrix.forEach(function(row) {
      if (Array.isArray(row)) row.forEach(function(v) { var n = parseFloat(v); if (!isNaN(n)) allVals.push(n); });
    });
    var minVal = allVals.length ? Math.min.apply(null, allVals) : 0;
    var maxVal = allVals.length ? Math.max.apply(null, allVals) : 1;
    var range = maxVal - minVal || 1;

    // Scheme-based colors for heatmap cells
    var heatSchemeColors = {
      purple:  { r1:112, g1:48,  b1:160, r2:139, g2:92,  b2:246 },
      success: { r1:34,  g1:197, b1:94,  r2:22,  g2:163, b2:74  },
      warning: { r1:245, g1:158, b1:11,  r2:217, g2:119, b2:6   },
      danger:  { r1:239, g1:68,  b1:68,  r2:220, g2:38,  b2:38  },
      info:    { r1:59,  g1:130, b1:246, r2:29,  g2:78,  b2:216 },
      neutral: { r1:107, g1:114, b1:128, r2:75,  g2:85,  b2:99  },
    };
    var hc = heatSchemeColors[currentScheme] || heatSchemeColors.purple;

    var numCols = matrix[0] ? matrix[0].length : 1;

    // Column headers
    if (colLabels.length > 0) {
      var headerRow = document.createElement('div');
      var headerPrefix = rowLabels.length > 0 ? 'display:grid;grid-template-columns:80px repeat(' + numCols + ',1fr);gap:3px;margin-bottom:3px;' : 'display:grid;grid-template-columns:repeat(' + numCols + ',1fr);gap:3px;margin-bottom:3px;';
      headerRow.style.cssText = headerPrefix;
      if (rowLabels.length > 0) {
        var emptyCorner = document.createElement('div');
        headerRow.appendChild(emptyCorner);
      }
      colLabels.forEach(function(lbl) {
        var th = document.createElement('div');
        th.className = 'bnx-heatmap-col-label';
        th.style.cssText = 'font-size:10px;font-weight:600;text-align:center;color:var(--bnx-text-tertiary);padding:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;';
        th.textContent = lbl;
        th.title = lbl;
        headerRow.appendChild(th);
      });
      el.appendChild(headerRow);
    }

    // Grid wrapper
    var gridWrap = document.createElement('div');
    gridWrap.className = 'bnx-heatmap-grid';
    var gridCols = rowLabels.length > 0 ? '80px repeat(' + numCols + ',1fr)' : 'repeat(' + numCols + ',1fr)';
    gridWrap.style.cssText = 'display:grid;grid-template-columns:' + gridCols + ';gap:3px;';

    matrix.forEach(function(row, rowIdx) {
      if (!Array.isArray(row)) return;

      // Row label
      if (rowLabels.length > rowIdx) {
        var rl = document.createElement('div');
        rl.style.cssText = 'font-size:11px;color:var(--bnx-text-secondary);display:flex;align-items:center;padding-right:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:80px;';
        rl.textContent = rowLabels[rowIdx];
        rl.title = rowLabels[rowIdx];
        gridWrap.appendChild(rl);
      }

      row.forEach(function(val) {
        var v = parseFloat(val);
        var isNum = !isNaN(v);
        var intensity = isNum ? (v - minVal) / range : 0;
        var r = Math.round(hc.r1 + (hc.r2 - hc.r1) * intensity);
        var g = Math.round(hc.g1 + (hc.g2 - hc.g1) * intensity);
        var b = Math.round(hc.b1 + (hc.b2 - hc.b1) * intensity);
        var alpha = 0.15 + 0.7 * intensity;

        var cell = document.createElement('div');
        cell.className = 'bnx-heatmap-cell';
        var fontSize = numCols > 8 ? '9px' : numCols > 5 ? '10px' : '11px';
        cell.style.cssText = 'padding:5px 3px;text-align:center;border-radius:3px;font-size:' + fontSize + ';font-weight:600;'
          + 'color:' + (intensity > 0.6 ? '#fff' : 'var(--bnx-text-primary)') + ';'
          + 'background:rgba(' + r + ',' + g + ',' + b + ',' + alpha + ');'
          + 'transition:transform 0.15s ease;cursor:default;';
        cell.textContent = isNum ? (Number.isInteger(v) ? v : v.toFixed(1)) : String(val);
        cell.title = (colLabels[row.indexOf ? row.indexOf(val) : 0] || '') + ': ' + (isNum ? v : val);

        cell.addEventListener('mouseenter', function() { cell.style.transform = 'scale(1.08)'; cell.style.zIndex = '1'; });
        cell.addEventListener('mouseleave', function() { cell.style.transform = ''; cell.style.zIndex = ''; });

        gridWrap.appendChild(cell);
      });
    });
    el.appendChild(gridWrap);

    // Legend / scale bar
    var legend = document.createElement('div');
    legend.className = 'bnx-heatmap-legend';
    legend.style.cssText = 'margin-top:10px;display:flex;align-items:center;gap:8px;';

    var legendLabel1 = document.createElement('span');
    legendLabel1.style.cssText = 'font-size:10px;color:var(--bnx-text-tertiary);';
    legendLabel1.textContent = minVal.toLocaleString('pt-BR');
    legend.appendChild(legendLabel1);

    var scaleBar = document.createElement('div');
    scaleBar.style.cssText = 'flex:1;height:8px;border-radius:4px;background:linear-gradient(90deg,rgba('
      + hc.r1 + ',' + hc.g1 + ',' + hc.b1 + ',0.15),rgba(' + hc.r2 + ',' + hc.g2 + ',' + hc.b2 + ',0.85));';
    legend.appendChild(scaleBar);

    var legendLabel2 = document.createElement('span');
    legendLabel2.style.cssText = 'font-size:10px;color:var(--bnx-text-tertiary);';
    legendLabel2.textContent = maxVal.toLocaleString('pt-BR');
    legend.appendChild(legendLabel2);

    el.appendChild(legend);

    makeExpandable(el, block);
    addCopyButton(el, block.title || 'Heatmap');
    el.setAttribute('role', 'figure');
    el.setAttribute('aria-label', block.title || 'Mapa de calor');
    return el;
  }

  function renderTreemap(block) {
    var d = block.data || {};
    var labels = Array.isArray(d.labels) ? d.labels : [];
    var datasets = Array.isArray(d.datasets) ? d.datasets : [];
    var rawValues = datasets.length > 0 && Array.isArray(datasets[0].data)
      ? datasets[0].data : [];

    // Build items from labels + values
    var items = labels.map(function(l, i) {
      return { label: String(l), value: Number(rawValues[i]) || 1 };
    }).filter(function(it) { return it.value > 0; });

    if (!items.length) {
      return renderCard({ title: block.title, type: 'card',
        data: { conteudo: 'Dados insuficientes para o treemap.' + (block.description ? ' ' + block.description : '') } });
    }

    // Sort descending by value
    items.sort(function(a, b) { return b.value - a.value; });
    var total = items.reduce(function(s, it) { return s + it.value; }, 0);

    var PALETTE = [
      '#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6',
      '#06b6d4','#f97316','#84cc16','#ec4899','#6366f1',
      '#14b8a6','#f43f5e','#a3e635','#fb923c','#818cf8',
    ];

    var el = document.createElement('div');
    el.className = 'bnx-glass-card';
    el.style.cssText = 'padding:16px;animation:bnx-fade-up 0.3s ease-out both;';

    if (block.title) {
      var t = document.createElement('div');
      t.className = 'bnx-card-header';
      t.innerHTML = '<span class="bnx-card-icon">' + IC.chart + '</span>' +
        '<span class="bnx-card-title">' + esc(block.title) + '</span>';
      el.appendChild(t);
    }

    var wrap = document.createElement('div');
    wrap.setAttribute('role', 'figure');
    wrap.setAttribute('aria-label', block.title || 'Treemap');
    wrap.style.cssText = 'display:flex;flex-wrap:wrap;gap:3px;min-height:160px;' +
      'border-radius:8px;overflow:hidden;margin-top:10px;';

    items.forEach(function(it, i) {
      var pct = (it.value / total) * 100;
      var cell = document.createElement('div');
      cell.style.cssText =
        'box-sizing:border-box;flex-grow:' + it.value + ';' +
        'flex-shrink:1;flex-basis:' + Math.max(pct * 0.9, 6) + '%;' +
        'min-width:56px;min-height:56px;' +
        'background:' + PALETTE[i % PALETTE.length] + ';' +
        'border-radius:4px;display:flex;flex-direction:column;' +
        'align-items:center;justify-content:center;padding:6px;' +
        'cursor:default;transition:opacity 0.15s;';
      cell.title = it.label + ': ' + it.value.toLocaleString('pt-BR') + ' (' + pct.toFixed(1) + '%)';
      cell.onmouseenter = function() { cell.style.opacity = '0.82'; };
      cell.onmouseleave = function() { cell.style.opacity = '1'; };

      var nameEl = document.createElement('div');
      nameEl.style.cssText = 'color:#fff;font-weight:600;font-size:0.72rem;' +
        'text-align:center;word-break:break-word;line-height:1.3;' +
        'text-shadow:0 1px 3px rgba(0,0,0,0.5);max-width:100%;overflow:hidden;';
      nameEl.textContent = it.label;

      var valEl = document.createElement('div');
      valEl.style.cssText = 'color:rgba(255,255,255,0.88);font-size:0.65rem;' +
        'margin-top:3px;text-shadow:0 1px 2px rgba(0,0,0,0.4);white-space:nowrap;';
      valEl.textContent = it.value.toLocaleString('pt-BR') + ' (' + pct.toFixed(1) + '%)';

      cell.appendChild(nameEl);
      cell.appendChild(valEl);
      wrap.appendChild(cell);
    });

    el.appendChild(wrap);
    makeExpandable(el, block);
    addCopyButton(el, block.title || 'Treemap');
    return el;
  }

  function renderSparkline(block) {
    const d = block.data || {};
    const el = document.createElement('div');
    el.className = 'bnx-glass-card bnx-sparkline-wrapper';
    el.style.cssText = 'padding:16px;animation:bnx-fade-up 0.4s ease-out both;';

    if (block.title) {
      const t = document.createElement('div');
      t.style.cssText = 'font-size:11px;color:var(--bnx-text-tertiary);text-transform:uppercase;letter-spacing:0.05em;font-weight:600;margin-bottom:6px;';
      t.textContent = block.title;
      el.appendChild(t);
    }

    // Normalize values — accept array or object with {values, trend}
    var values = d.values || d.data || d;
    var trendHint = d.trend || null; // 'up'|'down'|'stable'

    if (typeof values === 'string') { try { values = JSON.parse(values); } catch(e) { values = values.split(',').map(Number); } }
    if (typeof values === 'object' && !Array.isArray(values)) {
      // d itself is the data object
      trendHint = values.trend || trendHint;
      values = values.values || values.data || [];
    }
    if (!Array.isArray(values) || values.length === 0) values = [0, 10, 5, 20, 15, 25];

    var nums = values.map(Number).filter(function(v) { return !isNaN(v); });
    if (nums.length === 0) nums = [0, 10, 5, 20, 15, 25];

    var firstVal = nums[0];
    var lastVal = nums[nums.length - 1];
    var changePct = firstVal !== 0 ? Math.round(((lastVal - firstVal) / Math.abs(firstVal)) * 100) : 0;

    // Auto-detect trend if not specified
    if (!trendHint) {
      if (changePct > 2) trendHint = 'up';
      else if (changePct < -2) trendHint = 'down';
      else trendHint = 'stable';
    }

    var trendColors = { up: 'var(--bnx-success)', down: 'var(--bnx-danger)', stable: 'var(--bnx-text-tertiary)' };
    var trendIcons  = { up: '\u2197', down: '\u2198', stable: '\u2192' };
    var lineColor   = trendColors[trendHint] || getPurple();

    // Chart.js sparkline (no axes, no labels, no legend)
    if (typeof Chart !== 'undefined') {
      var canvasWrap = document.createElement('div');
      canvasWrap.style.cssText = 'position:relative;height:60px;width:100%;';
      var canvas = document.createElement('canvas');
      canvas.style.cssText = 'display:block;max-height:60px;';
      canvasWrap.appendChild(canvas);
      el.appendChild(canvasWrap);

      var prefRM = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var schemeColor = getPurple();

      requestAnimationFrame(function() {
        try {
          var ctx = canvas.getContext('2d');
          var instance = new Chart(ctx, {
            type: 'line',
            data: {
              labels: nums.map(function(_, i) { return i; }),
              datasets: [{
                data: nums,
                borderColor: lineColor,
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 3,
                tension: 0.4,
                fill: true,
                backgroundColor: function(context) {
                  var c = context.chart.ctx;
                  var gradient = c.createLinearGradient(0, 0, 0, 60);
                  gradient.addColorStop(0, lineColor.replace('var(--bnx-success)', '#22C55E')
                    .replace('var(--bnx-danger)', '#EF4444')
                    .replace('var(--bnx-text-tertiary)', '#9CA3AF') + '40');
                  gradient.addColorStop(1, 'transparent');
                  return gradient;
                },
              }],
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              animation: prefRM ? false : { duration: 600 },
              plugins: { legend: { display: false }, tooltip: { enabled: true, callbacks: {
                label: function(ctx) { return ctx.parsed.y.toLocaleString('pt-BR'); }
              }}},
              scales: {
                x: { display: false },
                y: { display: false },
              },
            },
          });
          chartInstances.push(instance);
        } catch(e) {
          console.error('[Bravonix] Sparkline chart error:', e);
        }
      });
    } else {
      // SVG fallback
      var mn = Math.min.apply(null, nums);
      var mx = Math.max.apply(null, nums);
      var rng = mx - mn || 1;
      var w = 200, h = 50;
      var svgNS = 'http://www.w3.org/2000/svg';
      var svg = document.createElementNS(svgNS, 'svg');
      svg.setAttribute('viewBox', '0 0 ' + w + ' ' + h);
      svg.style.cssText = 'width:100%;height:50px;display:block;';
      var pts = nums.map(function(v, i) {
        var x = nums.length > 1 ? (i / (nums.length - 1)) * w : w / 2;
        var y = h - ((v - mn) / rng) * (h - 6) - 3;
        return x + ',' + y;
      });
      var polyline = document.createElementNS(svgNS, 'polyline');
      polyline.setAttribute('points', pts.join(' '));
      polyline.setAttribute('fill', 'none');
      polyline.setAttribute('stroke', getPurple());
      polyline.setAttribute('stroke-width', '2');
      polyline.setAttribute('stroke-linecap', 'round');
      polyline.setAttribute('stroke-linejoin', 'round');
      polyline.style.strokeDasharray = '1000';
      polyline.style.strokeDashoffset = '1000';
      svg.appendChild(polyline);
      el.appendChild(svg);
      setTimeout(function() { polyline.style.strokeDashoffset = '0'; polyline.style.transition = 'stroke-dashoffset 1s ease-out'; }, 200);
    }

    // Bottom row: last value + trend arrow
    var bottomRow = document.createElement('div');
    bottomRow.style.cssText = 'display:flex;align-items:baseline;gap:8px;margin-top:6px;';

    var lastValEl = document.createElement('div');
    lastValEl.style.cssText = 'font-size:22px;font-weight:800;color:var(--bnx-text-primary);line-height:1;';
    lastValEl.textContent = lastVal.toLocaleString('pt-BR');
    bottomRow.appendChild(lastValEl);

    var trendEl = document.createElement('div');
    trendEl.className = 'bnx-sparkline-trend';
    trendEl.style.cssText = 'font-size:13px;font-weight:700;color:' + trendColors[trendHint] + ';display:flex;align-items:center;gap:2px;';
    trendEl.textContent = trendIcons[trendHint] + ' ' + (changePct >= 0 ? '+' : '') + changePct + '%';
    bottomRow.appendChild(trendEl);

    el.appendChild(bottomRow);
    return el;
  }


  // ── CSV Download Helpers ───────────────────────────────────────────────────

  function slugify(str) {
    return (str || 'dados').toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'dados';
  }

  function todayStr() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }

  function triggerCsvDownload(csvContent, filename) {
    var BOM = '\uFEFF'; // UTF-8 BOM for Excel compatibility
    var blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    setTimeout(function() { URL.revokeObjectURL(url); }, 2000);
  }

  function addTableCsvDownload(el, block, columns, rows) {
    var btn = document.createElement('button');
    btn.innerHTML = IC.csv + '<span style="font-size:9px;font-weight:700;font-family:var(--bnx-font-mono,monospace);margin-left:3px;letter-spacing:0.03em;">CSV</span>';
    btn.title = 'Baixar como CSV';
    btn.setAttribute('aria-label', 'Baixar tabela como CSV');
    btn.style.cssText = 'position:absolute;top:8px;right:136px;height:28px;padding:0 7px;border:none;border-radius:6px;' +
      'background:rgba(112,48,160,0.1);color:#7030A0;cursor:pointer;display:flex;gap:2px;' +
      'align-items:center;justify-content:center;opacity:0;transition:opacity 0.2s;z-index:2;';
    el.appendChild(btn);
    el.addEventListener('mouseenter', function() { btn.style.opacity = '1'; });
    el.addEventListener('mouseleave', function() { btn.style.opacity = '0'; });

    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      try {
        // Header row
        var headerCells = columns.map(function(col) {
          var val = col.label || col.key || '';
          return '"' + String(val).replace(/"/g, '""') + '"';
        });
        var csvLines = [headerCells.join(',')];

        // Data rows
        rows.forEach(function(row) {
          var cells = columns.map(function(col) {
            var val = row[col.key] !== undefined ? row[col.key] : '';
            return '"' + String(val).replace(/"/g, '""') + '"';
          });
          csvLines.push(cells.join(','));
        });

        // Footer with metadata
        var now = new Date();
        var source = block.data && block.data.source ? block.data.source : null;
        var footerParts = ['Exportado em: ' + now.toLocaleString('pt-BR')];
        if (source) footerParts.push('Fonte: ' + source);
        csvLines.push('"' + footerParts.join(' | ') + '"');

        var filename = slugify(block.title) + '-' + todayStr() + '.csv';
        triggerCsvDownload(csvLines.join('\r\n'), filename);

        btn.innerHTML = IC.copyDone;
        btn.style.background = 'var(--bnx-success)';
        btn.style.color = '#fff';
        setTimeout(function() { btn.innerHTML = IC.csv + '<span style="font-size:9px;font-weight:700;font-family:var(--bnx-font-mono,monospace);margin-left:3px;">CSV</span>'; btn.style.background = ''; btn.style.color = ''; }, 1500);
      } catch (err) {
        console.error('[Bravonix] CSV export error:', err);
        btn.innerHTML = IC.close;
        btn.style.color = 'var(--bnx-danger)';
        setTimeout(function() { btn.innerHTML = IC.csv + '<span style="font-size:9px;font-weight:700;font-family:var(--bnx-font-mono,monospace);margin-left:3px;">CSV</span>'; btn.style.color = ''; }, 1500);
      }
    });
  }

  function addChartCsvDownload(el, block, labels, datasets) {
    var btn = document.createElement('button');
    btn.innerHTML = IC.csv + '<span style="font-size:9px;font-weight:700;font-family:var(--bnx-font-mono,monospace);margin-left:3px;letter-spacing:0.03em;">CSV</span>';
    btn.title = 'Baixar dados do gráfico como CSV';
    btn.setAttribute('aria-label', 'Baixar dados do gráfico como CSV');
    btn.style.cssText = 'position:absolute;top:8px;right:136px;height:28px;padding:0 7px;border:none;border-radius:6px;' +
      'background:rgba(112,48,160,0.1);color:#7030A0;cursor:pointer;display:flex;gap:2px;' +
      'align-items:center;justify-content:center;opacity:0;transition:opacity 0.2s;z-index:2;';
    el.appendChild(btn);
    el.addEventListener('mouseenter', function() { btn.style.opacity = '1'; });
    el.addEventListener('mouseleave', function() { btn.style.opacity = '0'; });

    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      try {
        // Header: Label, Dataset1, Dataset2...
        var headerCells = ['"Label"'].concat(datasets.map(function(ds) {
          return '"' + String(ds.label || '').replace(/"/g, '""') + '"';
        }));
        var csvLines = [headerCells.join(',')];

        // Data rows: label, value1, value2...
        labels.forEach(function(lbl, i) {
          var cells = ['"' + String(lbl).replace(/"/g, '""') + '"'].concat(
            datasets.map(function(ds) {
              var v = ds.data[i] !== undefined ? ds.data[i] : '';
              return '"' + String(v).replace(/"/g, '""') + '"';
            })
          );
          csvLines.push(cells.join(','));
        });

        var filename = slugify(block.title) + '-dados-' + todayStr() + '.csv';
        triggerCsvDownload(csvLines.join('\r\n'), filename);

        btn.innerHTML = IC.copyDone;
        btn.style.background = 'var(--bnx-success)';
        btn.style.color = '#fff';
        setTimeout(function() { btn.innerHTML = IC.csv + '<span style="font-size:9px;font-weight:700;font-family:var(--bnx-font-mono,monospace);margin-left:3px;">CSV</span>'; btn.style.background = ''; btn.style.color = ''; }, 1500);
      } catch (err) {
        console.error('[Bravonix] Chart CSV export error:', err);
        btn.innerHTML = IC.close;
        btn.style.color = 'var(--bnx-danger)';
        setTimeout(function() { btn.innerHTML = IC.csv + '<span style="font-size:9px;font-weight:700;font-family:var(--bnx-font-mono,monospace);margin-left:3px;">CSV</span>'; btn.style.color = ''; }, 1500);
      }
    });
  }

  function destroyCharts() {
    chartInstances.forEach(c => {
      try { if (c && typeof c.destroy === 'function') c.destroy(); }
      catch(e) { console.warn('[Bravonix] Chart destroy error:', e.message); }
    });
    chartInstances = [];
    if (confettiAnimId) { cancelAnimationFrame(confettiAnimId); confettiAnimId = null; }
    if (confettiCanvas) { confettiCanvas.remove(); confettiCanvas = null; }
  }

  // ── Fullscreen Modal ───────────────────────────────────────────────────────

  function _mkActionBtn(iconSvg, title, rightOffset) {
    var btn = document.createElement('button');
    btn.innerHTML = iconSvg;
    btn.title = title;
    btn.setAttribute('aria-label', title);
    btn.style.cssText = 'position:absolute;top:8px;right:' + rightOffset + 'px;width:28px;height:28px;border:none;' +
      'border-radius:6px;background:' + getPurple(0.1) + ';color:' + getPurple() + ';cursor:pointer;' +
      'display:flex;align-items:center;justify-content:center;opacity:0;transition:opacity 0.2s;z-index:2;padding:5px;';
    return btn;
  }

  function makeExpandable(el, block) {
    const toggle = _mkActionBtn(IC.expand, 'Expandir', 8);
    el.style.position = 'relative';
    el.appendChild(toggle);
    el.addEventListener('mouseenter', () => toggle.style.opacity = '1');
    el.addEventListener('mouseleave', () => toggle.style.opacity = '0');

    toggle.addEventListener('click', (e) => {
      e.stopPropagation();
      const overlay = document.createElement('div');
      overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.6);' +
        'backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;' +
        'animation:bnx-fade-in 0.2s ease-out;';

      const modal = document.createElement('div');
      modal.style.cssText = 'background:var(--bnx-bg-card);border-radius:16px;max-width:90vw;max-height:90vh;' +
        'overflow:auto;padding:24px;position:relative;box-shadow:0 20px 60px rgba(0,0,0,0.3);' +
        'animation:bnx-scale-in 0.25s ease-out;min-width:400px;';

      const close = document.createElement('button');
      close.innerHTML = IC.close;
      close.setAttribute('aria-label', 'Fechar');
      close.title = 'Fechar';
      close.style.cssText = 'position:absolute;top:12px;right:12px;width:32px;height:32px;border:none;' +
        'border-radius:8px;background:var(--bnx-bg-secondary);cursor:pointer;padding:7px;' +
        'display:flex;align-items:center;justify-content:center;color:var(--bnx-text-primary);z-index:1;';
      close.addEventListener('click', () => { overlay.remove(); document.body.style.overflow = ''; });
      modal.appendChild(close);

      const clone = el.cloneNode(true);
      const origToggle = clone.querySelector('button');
      if (origToggle) origToggle.remove();
      clone.style.animation = 'none';
      clone.style.position = 'static';
      clone.style.margin = '0';
      modal.appendChild(clone);

      overlay.addEventListener('click', (ev) => {
        if (ev.target === overlay) { overlay.remove(); document.body.style.overflow = ''; }
      });
      // Keyboard: Escape to close
      overlay.addEventListener('keydown', (ev) => {
        if (ev.key === 'Escape') { overlay.remove(); document.body.style.overflow = ''; }
      });
      close.focus();
      overlay.appendChild(modal);
      document.body.appendChild(overlay);
      document.body.style.overflow = 'hidden';

      // Re-create charts inside modal if needed
      const canvases = clone.querySelectorAll('canvas');
      canvases.forEach((c, i) => {
        const origCanvas = el.querySelectorAll('canvas')[i];
        if (origCanvas && origCanvas.__chart) {
          const ctx = c.getContext('2d');
          const newChart = new Chart(ctx, origCanvas.__chart.config);
          c.__chart = newChart;
        }
      });
    });
  }

  // ── Text-to-Speech ───────────────────────────────────────────────────────────

  function addTtsButton(el, block) {
    if (!window.speechSynthesis) return;
    const btn = _mkActionBtn(IC.play, 'Ouvir conteúdo', 104);
    btn.setAttribute('aria-label', 'Ouvir conteúdo do bloco');
    el.appendChild(btn);
    el.addEventListener('mouseenter', () => btn.style.opacity = '1');
    el.addEventListener('mouseleave', () => btn.style.opacity = '0');

    let speaking = false;
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (speaking) {
        window.speechSynthesis.cancel();
        speaking = false;
        btn.innerHTML = IC.play;
        btn.style.background = '';
        btn.style.color = '';
        return;
      }
      const text = block.title + '. ' + (
        typeof block.data === 'string' ? block.data
          : (block.data && (block.data.conteudo || block.data.content)) || block.description || ''
      );
      if (!text.trim()) return;
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'pt-BR';
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.onstart  = () => { speaking = true;  btn.innerHTML = IC.pause; btn.style.background = 'var(--bnx-danger)'; btn.style.color = '#fff'; };
      utterance.onend    = () => { speaking = false; btn.innerHTML = IC.play;  btn.style.background = ''; btn.style.color = ''; };
      utterance.onerror  = () => { speaking = false; btn.innerHTML = IC.play;  btn.style.background = ''; btn.style.color = ''; };
      try {
        window.speechSynthesis.speak(utterance);
      } catch (ttsErr) {
        speaking = false;
        btn.innerHTML = IC.play;
        btn.style.background = '';
        btn.style.color = '';
        console.warn('[Bravonix] TTS speak() error:', ttsErr.message);
      }
    });
  }

  // ── Download as PNG ─────────────────────────────────────────────────────────

  function addDownloadBtn(el, block) {
    const btn = _mkActionBtn(IC.imgDown, 'Exportar como imagem', 72);
    el.appendChild(btn);
    el.addEventListener('mouseenter', () => btn.style.opacity = '1');
    el.addEventListener('mouseleave', () => btn.style.opacity = '0');
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      html2canvas(el, { backgroundColor: null, scale: 2, useCORS: true, logging: false }).then(canvas => {
        const a = document.createElement('a');
        a.download = (block.title || 'bravonix-block').replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.png';
        a.href = canvas.toDataURL('image/png');
        a.click();
        btn.innerHTML = IC.copyDone;
        btn.style.background = 'var(--bnx-success)';
        btn.style.color = '#fff';
        setTimeout(() => { btn.innerHTML = IC.imgDown; btn.style.background = ''; btn.style.color = ''; }, 1500);
      }).catch(() => {
        btn.innerHTML = IC.close;
        btn.style.color = 'var(--bnx-danger)';
        setTimeout(() => { btn.innerHTML = IC.imgDown; btn.style.color = ''; }, 1500);
      });
    });
  }

  // ── Copy Button ─────────────────────────────────────────────────────────────

  function addCopyButton(el, text) {
    const btn = _mkActionBtn(IC.copy, 'Copiar', 40);
    el.style.position = 'relative';
    el.appendChild(btn);
    el.addEventListener('mouseenter', () => btn.style.opacity = '1');
    el.addEventListener('mouseleave', () => btn.style.opacity = '0');
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      navigator.clipboard.writeText(text).then(() => {
        btn.innerHTML = IC.copyDone;
        btn.style.background = 'var(--bnx-success)';
        btn.style.color = '#fff';
        setTimeout(() => { btn.innerHTML = IC.copy; btn.style.background = ''; btn.style.color = ''; }, 1500);
      }).catch(() => {});
    });
  }

  // ── Confetti ────────────────────────────────────────────────────────────────

  function fireConfetti(count) {
    if (!confettiCanvas) {
      confettiCanvas = document.createElement('canvas');
      confettiCanvas.style.cssText = 'position:fixed;inset:0;z-index:9998;pointer-events:none;';
      document.body.appendChild(confettiCanvas);
    }
    confettiCanvas.width = window.innerWidth;
    confettiCanvas.height = window.innerHeight;

    const ctx = confettiCanvas.getContext('2d');
    const particles = [];
    const colors = ['#7030A0','#8B5CF6','#A78BFA','#22C55E','#F59E0B','#EC4899'];

    for (let i = 0; i < (count || 40); i++) {
      particles.push({
        x: Math.random() * confettiCanvas.width,
        y: -20 - Math.random() * 100,
        w: 6 + Math.random() * 6,
        h: 4 + Math.random() * 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        vx: (Math.random() - 0.5) * 4,
        vy: 2 + Math.random() * 4,
        rot: Math.random() * 360,
        rv: (Math.random() - 0.5) * 8,
        opacity: 1,
      });
    }

    let frame = 0;
    const maxFrames = 120;

    function draw() {
      frame++;
      if (frame > maxFrames) {
        ctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
        confettiAnimId = null;
        return;
      }
      ctx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
      const fadeOut = frame > maxFrames * 0.6 ? 1 - (frame - maxFrames * 0.6) / (maxFrames * 0.4) : 1;
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.05;
        p.rot += p.rv;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rot * Math.PI) / 180);
        ctx.globalAlpha = Math.max(0, fadeOut);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
        ctx.restore();
      }
      confettiAnimId = requestAnimationFrame(draw);
    }
    draw();
  }

  // ── Markdown Parser Aprimorado ───────────────────────────────────────────

  function markedParse(text) {
    if (!text) return '';
    let html = text
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/\n/g, '\n'); // normalize

    // Code blocks (must come before inline code)
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
      `<pre><code class="language-${lang || 'text'}">${code.trim()}</code></pre>`);

    // Tables: | col1 | col2 | ... |
    html = html.replace(/^\|(.+)\|\s*$/gm, (_, row) => {
      const cells = row.split('|').map(c => c.trim()).filter(c => c);
      // Separator row (---|---)
      if (cells.every(c => /^[-:\s]+$/.test(c))) return '';
      return `<tr>${cells.map(c => {
        const isHeader = html.match(/^\|.+\|\s*$/m);
        return `<td>${c}</td>`;
      }).join('')}</tr>`;
    });
    html = html.replace(/(<tr>.*<\/tr>\n?)+/g, '<table><tbody>$&</tbody></table>');

    // Horizontal rules
    html = html.replace(/^(?:---|\*\*\*|___)\s*$/gm, '<hr>');

    // Blockquotes
    html = html.replace(/^&gt;\s?(.+)$/gm, '<blockquote>$1</blockquote>');

    // Headers
    html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

    // Inline code (after code blocks)
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold and italic
    html = html.replace(/\*\*\*([^*]+)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>');
    html = html.replace(/_([^_]+)_/g, '<em>$1</em>');

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener">$1</a>');

    // Images
    html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g,
      '<img src="$2" alt="$1" style="max-width:100%;border-radius:8px;margin:8px 0;">');

    // Ordered lists: 1. item
    let olIndex = 0;
    html = html.replace(/^(\d+)\.\s+(.+)$/gm, (_, num, item) => {
      const tag = num === '1' || !olIndex ? '<ol>' : '';
      olIndex = parseInt(num);
      return `${tag}<li value="${num}">${item}</li>`;
    });
    html = html.replace(/((?:<li value=.*?<\/li>\n?)+)/g, (m) => {
      if (!m.includes('<ol>')) return '<ol>' + m + '</ol>';
      return m;
    });

    // Unordered lists
    html = html.replace(/^[\s]*[-*+]\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/((?:<li>.*?<\/li>\n?)+)/g, '<ul>$1</ul>');

    // Paragraphs - wrap remaining text
    const blockTags = '(?:table|tbody|tr|td|th|thead|ul|ol|li|pre|code|h[1-4]|hr|blockquote)';
    // First, close any remaining open blocks and wrap paragraph text
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/^(.+)$/gm, m => {
      const s = m.trim();
      if (!s) return '';
      if (/^<\//.test(s) || /^<[a-z]/i.test(s)) return m;
      return `<p>${s}</p>`;
    });

    // Clean up empty paragraphs and nested paragraphs
    html = html.replace(/<p><\/p>/g, '');
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<\/p>\s*<p>/g, '</p><p>');

    return html;
  }

  // ── Compare Mode ────────────────────────────────────────────────────────────

  let compareMode = false;
  let compareSelection = [];

  function toggleCompare() {
    compareMode = !compareMode;
    compareSelection = [];
    document.querySelectorAll('.bnx-visual-blocks .bnx-glass-card, .bnx-dashboard-grid .bnx-glass-card').forEach(el => {
      el.classList.toggle('bnx-compare-mode', compareMode);
      el.classList.remove('bnx-compare-selected');
    });
    return compareMode;
  }

  // Add click-to-compare to blocks when in compare mode
  document.addEventListener('click', (e) => {
    const block = e.target.closest('.bnx-glass-card');
    if (!block || !compareMode) return;
    e.stopPropagation();

    if (block.classList.contains('bnx-compare-selected')) {
      block.classList.remove('bnx-compare-selected');
      compareSelection = compareSelection.filter(el => el !== block);
    } else if (compareSelection.length < 2) {
      block.classList.add('bnx-compare-selected');
      compareSelection.push(block);
    }

    if (compareSelection.length === 2) {
      // Show comparison overlay
      const overlay = document.createElement('div');
      overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.6);backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;animation:bnx-fade-in 0.2s ease-out;';
      const modal = document.createElement('div');
      modal.style.cssText = 'background:var(--bnx-bg-card);border-radius:16px;padding:24px;max-width:95vw;max-height:90vh;overflow:auto;box-shadow:0 20px 60px rgba(0,0,0,0.3);min-width:600px;';
      modal.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;"><h2 style="font-size:18px;font-weight:700;">Comparar Blocos</h2><button id="bnx-compare-close" style="width:32px;height:32px;border:none;border-radius:8px;background:var(--bnx-bg-secondary);cursor:pointer;font-size:16px;">x</button></div>';
      const grid = document.createElement('div');
      grid.style.cssText = 'display:grid;grid-template-columns:1fr 1fr;gap:16px;';
      compareSelection.forEach(el => {
        const clone = el.cloneNode(true);
        clone.querySelectorAll('button').forEach(b => b.remove());
        clone.style.animation = 'none';
        clone.style.position = 'static';
        clone.style.margin = '0';
        // Re-create charts in clone
        const origCanvases = el.querySelectorAll('canvas');
        const cloneCanvases = clone.querySelectorAll('canvas');
        origCanvases.forEach((oc, i) => {
          if (oc.__chart && cloneCanvases[i]) {
            try { new Chart(cloneCanvases[i].getContext('2d'), oc.__chart.config); } catch(e) {}
          }
        });
        grid.appendChild(clone);
      });
      modal.appendChild(grid);
      overlay.appendChild(modal);
      document.body.appendChild(overlay);
      document.body.style.overflow = 'hidden';

      overlay.querySelector('#bnx-compare-close').addEventListener('click', () => { overlay.remove(); document.body.style.overflow = ''; });
      overlay.addEventListener('click', (ev) => { if (ev.target === overlay) { overlay.remove(); document.body.style.overflow = ''; } });

      // Reset compare mode
      compareMode = false;
      compareSelection = [];
      document.querySelectorAll('.bnx-compare-mode').forEach(el => el.classList.remove('bnx-compare-mode', 'bnx-compare-selected'));
    }
  });

  // ── Public API ─────────────────────────────────────────────────────────────

  return { renderBlocks, renderBlock, destroyCharts, renderInteractive, fireConfetti, makeExpandable, toggleCompare, chartInstances, setColorScheme, applyColorScheme, COLOR_SCHEMES };
})();
