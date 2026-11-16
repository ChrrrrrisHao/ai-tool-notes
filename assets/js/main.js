/* =========================================================
   AI 工具學習筆記站 — 全站唯一互動腳本
   - 依 <body data-page> 決定要做什麼：home | note | components
   - 筆記 metadata 一律從 data/notes.json 讀取（唯一來源）
   - 新增分類時，要同步修改 CATEGORIES（見 AGENTS.md 第 10 節 D）
   ========================================================= */
(() => {
  'use strict';

  const CATEGORIES = {
    tool: '工具',
    concept: '概念',
    skill: '技巧',
    workflow: '流程',
  };
  const LEVELS = { 1: '入門', 2: '進階', 3: '深入' };

  const body = document.body;
  const ROOT = body.dataset.root || './';
  const PAGE = body.dataset.page || '';

  /* ---------- helpers ---------- */
  const $ = (sel, el = document) => el.querySelector(sel);
  const $$ = (sel, el = document) => Array.from(el.querySelectorAll(sel));
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));

  async function loadNotes() {
    const res = await fetch(ROOT + 'data/notes.json', { cache: 'no-cache' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    return (data.notes || [])
      .filter((n) => !n.draft)
      .sort((a, b) => a.order - b.order);
  }

  const levelHTML = (lv) => `
    <span class="level level--${lv}" title="難度：${esc(LEVELS[lv] || '')}">
      <span class="level__dots" aria-hidden="true"><i></i><i></i><i></i></span>${esc(LEVELS[lv] || '')}
    </span>`;

  /* ---------- theme toggle ---------- */
  function initTheme() {
    const btn = $('[data-theme-toggle]');
    if (!btn) return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const current = () => document.documentElement.dataset.theme || (mq.matches ? 'dark' : 'light');
    const sync = () => btn.setAttribute('aria-label', current() === 'dark' ? '切換為淺色模式' : '切換為深色模式');
    sync();
    btn.addEventListener('click', () => {
      const next = current() === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = next;
      try { localStorage.setItem('theme', next); } catch (e) { /* ignore */ }
      sync();
    });
    mq.addEventListener?.('change', sync);
  }

  /* ---------- home ---------- */
  async function initHome() {
    const grid = $('#note-grid');
    const search = $('#note-search');
    const chipsEl = $('#category-filters');
    const empty = $('#empty-state');
    if (!grid) return;

    let notes;
    try {
      notes = await loadNotes();
    } catch (err) {
      grid.innerHTML = `<p class="load-error">讀不到 <code>data/notes.json</code>。
        如果你是直接雙擊開檔，請改用 <code>python -m http.server 8000</code> 再開 <code>http://localhost:8000</code>。</p>`;
      console.warn('[notes] load failed:', err);
      return;
    }

    // stats
    const setText = (id, v) => { const el = $(id); if (el) el.textContent = v; };
    setText('#stat-notes', notes.length);
    setText('#stat-cats', new Set(notes.map((n) => n.category)).size);
    setText('#stat-minutes', notes.reduce((s, n) => s + (n.minutes || 0), 0));

    // state from URL
    const params = new URLSearchParams(location.search);
    let cat = CATEGORIES[params.get('cat')] ? params.get('cat') : 'all';
    let q = params.get('q') || '';
    if (search) search.value = q;

    // chips
    const counts = notes.reduce((m, n) => ((m[n.category] = (m[n.category] || 0) + 1), m), {});
    const chipDefs = [['all', '全部', notes.length], ...Object.entries(CATEGORIES).map(([k, v]) => [k, v, counts[k] || 0])];
    chipsEl.innerHTML = chipDefs.map(([k, label, c]) =>
      `<button type="button" class="chip" data-cat="${k}" aria-pressed="${k === cat}">${esc(label)}<span class="chip__count">${c}</span></button>`
    ).join('');

    const cardHTML = (n) => `
      <a class="card card--${esc(n.category)}" href="${ROOT}notes/${esc(n.slug)}/">
        <span class="card__tape" aria-hidden="true"></span>
        <span class="tag tag--${esc(n.category)}">${esc(CATEGORIES[n.category] || n.category)}</span>
        <h3 class="card__title">${esc(n.title)}</h3>
        <p class="card__summary">${esc(n.summary)}</p>
        <div class="card__meta">
          ${levelHTML(n.level)}
          <span>${esc(n.minutes)} 分鐘</span>
          <span>更新 ${esc(n.updated)}</span>
        </div>
        <ul class="card__tags">${(n.tags || []).map((t) => `<li>#${esc(t)}</li>`).join('')}</ul>
      </a>`;

    const render = () => {
      const kw = q.trim().toLowerCase();
      const list = notes.filter((n) => {
        if (cat !== 'all' && n.category !== cat) return false;
        if (!kw) return true;
        const hay = [n.title, n.summary, n.slug, ...(n.tags || []), CATEGORIES[n.category]].join(' ').toLowerCase();
        return hay.includes(kw);
      });
      grid.innerHTML = list.map(cardHTML).join('');
      if (empty) empty.hidden = list.length > 0;
      $$('.chip', chipsEl).forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.cat === cat)));
      const url = new URL(location.href);
      cat === 'all' ? url.searchParams.delete('cat') : url.searchParams.set('cat', cat);
      kw ? url.searchParams.set('q', q.trim()) : url.searchParams.delete('q');
      history.replaceState(null, '', url);
    };

    chipsEl.addEventListener('click', (e) => {
      const b = e.target.closest('.chip');
      if (!b) return;
      cat = b.dataset.cat;
      render();
    });
    search?.addEventListener('input', () => { q = search.value; render(); });
    render();
  }

  /* ---------- note page ---------- */
  async function initNoteMeta() {
    const slug = body.dataset.slug;
    const metaEl = $('#note-meta');
    const pager = $('#pager');
    if (!slug) return;

    let notes;
    try {
      notes = await loadNotes();
    } catch (err) {
      console.warn('[notes] load failed:', err);
      return;
    }
    const i = notes.findIndex((n) => n.slug === slug);
    if (i < 0) return;
    const n = notes[i];

    if (metaEl) {
      metaEl.innerHTML = `
        <a class="tag tag--${esc(n.category)}" href="${ROOT}index.html?cat=${esc(n.category)}">${esc(CATEGORIES[n.category] || n.category)}</a>
        ${levelHTML(n.level)}
        <span>約 ${esc(n.minutes)} 分鐘</span>
        <span>更新 ${esc(n.updated)}</span>
        <ul class="note-meta__tags">${(n.tags || []).map((t) => `<li>${esc(t)}</li>`).join('')}</ul>`;
    }

    const crumb = $('#crumb-cat');
    if (crumb) {
      crumb.textContent = CATEGORIES[n.category] || n.category;
      crumb.href = `${ROOT}index.html?cat=${encodeURIComponent(n.category)}`;
    }

    if (pager) {
      const prev = notes[i - 1];
      const next = notes[i + 1];
      pager.innerHTML = [
        prev ? `<a class="pager__prev" href="${ROOT}notes/${esc(prev.slug)}/"><small>← 上一篇</small>${esc(prev.title)}</a>` : '',
        next ? `<a class="pager__next" href="${ROOT}notes/${esc(next.slug)}/"><small>下一篇 →</small>${esc(next.title)}</a>` : '',
      ].join('');
    }
  }

  /* ---------- shared: TOC ---------- */
  function initToc() {
    const toc = $('#toc-list');
    if (!toc) return;
    const heads = $$('.note-body .note-section > h2').filter((h) => h.parentElement.id);
    toc.innerHTML = heads.map((h) =>
      `<li><a href="#${h.parentElement.id}">${esc(h.textContent.trim())}</a></li>`
    ).join('');
    const links = $$('a', toc);
    if (!links.length) return;
    const sections = heads.map((h) => h.parentElement);
    let ticking = false;
    const update = () => {
      ticking = false;
      const line = window.innerHeight * 0.3;
      let idx = 0;
      sections.forEach((s, i) => { if (s.getBoundingClientRect().top <= line) idx = i; });
      const h = document.documentElement;
      if (h.scrollTop + h.clientHeight >= h.scrollHeight - 4) idx = sections.length - 1;
      links.forEach((a, i) => a.classList.toggle('is-active', i === idx));
    };
    document.addEventListener('scroll', () => {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  /* ---------- shared: copy buttons ---------- */
  function initCopy() {
    $$('pre.code').forEach((pre) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'copy-btn';
      btn.textContent = '複製';
      btn.addEventListener('click', async () => {
        const text = pre.querySelector('code')?.innerText ?? pre.innerText;
        try {
          await navigator.clipboard.writeText(text);
          btn.textContent = '已複製';
          btn.classList.add('is-done');
        } catch (e) {
          btn.textContent = '請手動選取';
        }
        setTimeout(() => { btn.textContent = '複製'; btn.classList.remove('is-done'); }, 1600);
      });
      pre.appendChild(btn);
    });
  }

  /* ---------- shared: quiz ---------- */
  function initQuiz() {
    const quizzes = $$('.quiz[data-answer]');
    if (!quizzes.length) return;
    const scoreEl = $('#quiz-score');
    let answered = 0;
    let correct = 0;
    const updateScore = () => {
      if (scoreEl) scoreEl.textContent = answered ? `目前答對 ${correct} / ${quizzes.length} 題` : '';
    };
    quizzes.forEach((qz) => {
      const ans = qz.dataset.answer;
      qz.addEventListener('click', (e) => {
        const btn = e.target.closest('button[data-option]');
        if (!btn || qz.classList.contains('is-answered')) return;
        const ok = btn.dataset.option === ans;
        $$('button[data-option]', qz).forEach((b) => {
          b.disabled = true;
          if (b.dataset.option === ans) b.classList.add('is-correct');
        });
        if (!ok) btn.classList.add('is-wrong');
        qz.classList.add('is-answered');
        answered += 1;
        if (ok) correct += 1;
        updateScore();
      });
    });
    updateScore();
  }

  /* ---------- shared: reading progress ---------- */
  function initProgress() {
    const bar = $('#progress');
    if (!bar) return;
    const onScroll = () => {
      const h = document.documentElement;
      const max = h.scrollHeight - h.clientHeight;
      bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + '%';
    };
    document.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---------- boot ---------- */
  initTheme();
  const year = $('#year');
  if (year) year.textContent = new Date().getFullYear();

  initCopy();
  if (PAGE === 'home') initHome();
  if (PAGE === 'note') initNoteMeta();
  if (PAGE === 'note' || PAGE === 'components') {
    initToc();
    initQuiz();
    initProgress();
  }
})();
