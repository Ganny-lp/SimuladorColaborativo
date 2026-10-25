'use strict';
const JSONBIN_API_KEY = __JSONBIN_API_KEY__;
const JSONBIN_BIN_ID  = __JSONBIN_BIN_ID__;
let SYS = __MODEL_JSON__;
const EPOCH = __EPOCH__;
const FOCUS = __FOCUS_JSON__;

/* ════════════════════════════════════════════════════════════════════════════
 * Diagrama de laços causais.
 *
 * Arquitetura (por que ele é fluido):
 *  - Nós e arestas vivem em #world, em coordenadas do "mundo". Pan e zoom são só um
 *    CSS transform nesse elemento: nenhuma aresta é recalculada ao navegar.
 *  - Arrastar um nó reposiciona apenas aquele nó e recalcula só as arestas ligadas a ele.
 *  - Pointer Events unificam mouse, toque e caneta (inclui pinça com dois dedos).
 *  - Estado de navegação (pan/zoom/seleção) e edições não salvas sobrevivem aos reruns do
 *    Streamlit via sessionStorage; o iframe pode ser recriado sem o usuário perder nada.
 * ════════════════════════════════════════════════════════════════════════════ */

/* ── utilidades ── */
const $  = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const SVGNS = 'http://www.w3.org/2000/svg';
const REDUCE_MOTION = matchMedia('(prefers-reduced-motion: reduce)').matches;
const HAS_CLOUD = !!(JSONBIN_API_KEY && JSONBIN_BIN_ID);

const CATS = [
  { name: 'Estado',    key: 'estado',    hint: 'Acumula valor entre os ciclos' },
  { name: 'Equação',   key: 'equacao',   hint: 'Calculada a partir de outras variáveis' },
  { name: 'Parâmetro', key: 'parametro', hint: 'Constante do modelo' },
  { name: 'Ambiente',  key: 'ambiente',  hint: 'Fator externo, fora do seu controle' },
  { name: 'Input',     key: 'input',     hint: 'Decisão tomada na simulação' },
];
const catKey = name => (CATS.find(c => c.name === name) || CATS[0]).key;
const ic = (id, cls = '') => `<svg class="ic ${cls}" aria-hidden="true"><use href="#i-${id}"/></svg>`;

const KEYS = { view: 'lumina.cld.view', draft: 'lumina.cld.draft', focus: 'lumina.cld.focus' };
const store = {
  get(k) { try { return JSON.parse(sessionStorage.getItem(k)); } catch (e) { return null; } },
  set(k, v) { try { sessionStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* storage indisponível */ } },
  del(k) { try { sessionStorage.removeItem(k); } catch (e) { /* idem */ } },
};
const debounce = (fn, ms) => { let t = 0; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };

/* ── estado ── */
const S = { tool: 'select', sel: null, hover: null, linkSrc: null, off: new Set(), dirty: false,
            panel: true, fitted: false, touched: false, measured: false };
const V = { x: 0, y: 0, k: 1 };
const el = {
  viewport: $('#viewport'), world: $('#world'), nodes: $('#nodes'), edges: $('#edge-layer'),
  side: $('#side'), panel: $('#panel-content'), status: $('#status'), statusText: $('#status-text'),
  hint: $('#hint'), empty: $('#empty'), legend: $('#legend'), zoomVal: $('#z-val'), toasts: $('#toasts'),
  btnSave: $('#btn-save'), btnPanel: $('#btn-panel'),
};
const nodeEls = new Map();      // id → elemento
const dims = new Map();         // id → {w,h} medidos
const edgeObjs = [];            // {lk,g,path,t}
const adj = new Map();          // id → [edgeObj]

/* ── normalização e rascunho ── */
(function normalize() {
  SYS = SYS || {};
  SYS.nodes = SYS.nodes || {};
  SYS.links = SYS.links || [];
})();
(function restoreDraft() {
  const d = store.get(KEYS.draft);
  if (!d || d.epoch !== EPOCH || !d.sys || !d.sys.nodes) return;
  for (const [id, n] of Object.entries(d.sys.nodes)) if (SYS.nodes[id]) n.val = SYS.nodes[id].val;   // valores sempre frescos
  SYS = d.sys; SYS.links = SYS.links || [];
  S.dirty = true;
})();
(function ensureCoords() {
  let i = 0;
  for (const n of Object.values(SYS.nodes)) {
    if (typeof n.x !== 'number' || typeof n.y !== 'number') { n.x = 90 + (i % 8) * 150; n.y = 90 + Math.floor(i / 8) * 80; }
    i++;
  }
})();

/* ── mundo ↔ tela ── */
const vpRect = () => el.viewport.getBoundingClientRect();
function toWorld(cx, cy) { const r = vpRect(); return { x: (cx - r.left - V.x) / V.k, y: (cy - r.top - V.y) / V.k }; }
function dimsOf(id) {
  const d = dims.get(id);
  if (d && d.w > 0) return d;
  return { w: String(id).length * 7.4 + 44, h: 30 };    // estimativa até a primeira medição (iframe oculto)
}

/* ═══════════════ construção ═══════════════ */
function buildNodes() {
  el.nodes.replaceChildren(); nodeEls.clear();
  for (const [id, nd] of Object.entries(SYS.nodes)) {
    const n = document.createElement('div');
    n.className = 'cld-node'; n.dataset.id = id; n.dataset.cat = catKey(nd.cat);
    n.tabIndex = 0; n.setAttribute('role', 'button'); n.setAttribute('aria-label', `${id}, ${nd.cat}`);
    n.innerHTML = `<span class="node-box"><i class="cdot"></i><span>${esc(id)}</span></span>`;
    n.style.left = nd.x + 'px'; n.style.top = nd.y + 'px';
    el.nodes.appendChild(n); nodeEls.set(id, n);
  }
  el.empty.hidden = nodeEls.size > 0;
}
function measureNodes() {
  let ok = false;
  nodeEls.forEach((n, id) => { const w = n.offsetWidth; if (w > 0) { dims.set(id, { w, h: n.offsetHeight }); ok = true; } });
  S.measured = ok;
  return ok;
}
function svgEl(tag, attrs = {}) { const e = document.createElementNS(SVGNS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; }
function buildEdges() {
  el.edges.replaceChildren(); edgeObjs.length = 0; adj.clear();
  for (const lk of SYS.links) {
    if (!SYS.nodes[lk.from] || !SYS.nodes[lk.to] || lk.from === lk.to) continue;
    const neg = lk.sign === '-';
    const g = svgEl('g', { class: 'edge-g ' + (neg ? 'neg' : 'pos') });
    const path = svgEl('path', { class: 'edge' });
    const t = svgEl('g', { class: 'sign' });
    const pill = svgEl('g', { class: 'pill' });
    const circle = svgEl('circle', { r: 8 });
    const txt = svgEl('text'); txt.textContent = neg ? '−' : '+';
    pill.append(circle, txt); t.append(pill); g.append(path, t); el.edges.append(g);
    const e = { lk, g, path, t };
    edgeObjs.push(e);
    for (const id of [lk.from, lk.to]) { if (!adj.has(id)) adj.set(id, []); adj.get(id).push(e); }
    layoutEdge(e);
  }
}
function rectEdge(c, d, dx, dy, pad) {   // ponto onde a direção (dx,dy) sai do retângulo do nó
  const hw = d.w / 2 + pad, hh = d.h / 2 + pad;
  const t = Math.min(dx ? hw / Math.abs(dx) : Infinity, dy ? hh / Math.abs(dy) : Infinity, 1);
  return { x: c.x + dx * t, y: c.y + dy * t };
}
function layoutEdge(e) {
  const a = SYS.nodes[e.lk.from], b = SYS.nodes[e.lk.to];
  const da = dimsOf(e.lk.from), db = dimsOf(e.lk.to);
  const dx = b.x - a.x, dy = b.y - a.y, dist = Math.hypot(dx, dy) || 1;
  const ux = dx / dist, uy = dy / dist, bend = Math.min(46, dist * .2);
  const cx = (a.x + b.x) / 2 - uy * bend, cy = (a.y + b.y) / 2 + ux * bend;    // sentidos opostos se separam sozinhos
  const p1 = rectEdge(a, da, cx - a.x, cy - a.y, 3), p2 = rectEdge(b, db, cx - b.x, cy - b.y, 8);
  e.path.setAttribute('d', `M${p1.x.toFixed(1)},${p1.y.toFixed(1)} Q${cx.toFixed(1)},${cy.toFixed(1)} ${p2.x.toFixed(1)},${p2.y.toFixed(1)}`);
  const lx = .25 * p1.x + .5 * cx + .25 * p2.x, ly = .25 * p1.y + .5 * cy + .25 * p2.y;
  e.t.setAttribute('transform', `translate(${lx.toFixed(1)} ${ly.toFixed(1)})`);
}
const layoutAllEdges = () => edgeObjs.forEach(layoutEdge);

function rebuild() {
  buildNodes(); measureNodes(); buildEdges(); applyCats(); applyFocus(); renderPanel();
}

/* ═══════════════ destaque, categorias ═══════════════ */
function applyFocus() {
  const f = S.hover || S.sel;
  el.world.classList.toggle('has-focus', !!f);
  const mine = f ? new Set(adj.get(f) || []) : null;
  const near = new Set(f ? [f] : []);
  mine && mine.forEach(e => { near.add(e.lk.from); near.add(e.lk.to); });
  edgeObjs.forEach(e => e.g.classList.toggle('hl', !!mine && mine.has(e)));
  nodeEls.forEach((n, id) => {
    n.classList.toggle('near', near.has(id));
    n.classList.toggle('sel', id === S.sel);
    n.classList.toggle('src', id === S.linkSrc);
  });
}
function applyCats() {
  const off = id => S.off.has(catKey((SYS.nodes[id] || {}).cat));
  nodeEls.forEach((n, id) => n.classList.toggle('off', off(id)));
  edgeObjs.forEach(e => e.g.classList.toggle('off', off(e.lk.from) || off(e.lk.to)));
}
function renderLegend() {
  el.legend.innerHTML = CATS.map(c =>
    `<button type="button" class="lg" data-cat="${c.key}" aria-pressed="${!S.off.has(c.key)}" title="${esc(c.hint)}. Clique para ocultar/mostrar."><i class="cdot"></i>${c.name}</button>`).join('');
}
el.legend.addEventListener('click', e => {
  const b = e.target.closest('.lg'); if (!b) return;
  const k = b.dataset.cat;
  S.off.has(k) ? S.off.delete(k) : S.off.add(k);
  b.setAttribute('aria-pressed', String(!S.off.has(k)));
  applyCats();
});

/* ═══════════════ navegação (pan / zoom / ajuste) ═══════════════ */
let paintRaf = 0, animRaf = 0;
function paintView() {
  cancelAnimationFrame(paintRaf);
  paintRaf = requestAnimationFrame(() => {
    el.world.style.transform = `translate(${V.x}px,${V.y}px) scale(${V.k})`;
    const s = el.viewport.style;
    s.setProperty('--k', V.k.toFixed(4)); s.setProperty('--x', V.x.toFixed(1) + 'px'); s.setProperty('--y', V.y.toFixed(1) + 'px');
    el.zoomVal.textContent = Math.round(V.k * 100) + '%';
    el.viewport.classList.toggle('low-zoom', V.k < .45);
  });
  saveViewSoon();
}
const saveViewSoon = debounce(() => store.set(KEYS.view, { x: V.x, y: V.y, k: V.k, sel: S.sel, touched: S.touched }), 250);

function animateTo(t, ms = 320) {
  cancelAnimationFrame(animRaf);
  if (REDUCE_MOTION || ms <= 0) { Object.assign(V, t); paintView(); return; }
  const s = { ...V }, t0 = performance.now();
  const step = now => {
    const p = clamp((now - t0) / ms, 0, 1), e = 1 - Math.pow(1 - p, 3);
    V.x = s.x + (t.x - s.x) * e; V.y = s.y + (t.y - s.y) * e; V.k = s.k + (t.k - s.k) * e;
    paintView();
    if (p < 1) animRaf = requestAnimationFrame(step);
  };
  animRaf = requestAnimationFrame(step);
}
function zoomAt(k, cx, cy) {
  k = clamp(k, .15, 2.5);
  V.x = cx - (cx - V.x) * (k / V.k); V.y = cy - (cy - V.y) * (k / V.k); V.k = k;
  S.touched = true; paintView();
}
function zoomBy(f) { const r = vpRect(); cancelAnimationFrame(animRaf); zoomAt(V.k * f, r.width / 2, r.height / 2); }

function fit({ animate = true } = {}) {
  const r = vpRect();
  if (r.width < 80 || r.height < 80) return false;
  const ids = Object.keys(SYS.nodes);
  if (!ids.length) { Object.assign(V, { x: r.width / 2, y: r.height / 2, k: 1 }); paintView(); return true; }
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (const id of ids) {
    const n = SYS.nodes[id], d = dimsOf(id);
    x0 = Math.min(x0, n.x - d.w / 2); x1 = Math.max(x1, n.x + d.w / 2);
    y0 = Math.min(y0, n.y - d.h / 2); y1 = Math.max(y1, n.y + d.h / 2);
  }
  const padX = 36, padTop = 44, padBottom = r.width < 520 ? 100 : 70;
  const bw = Math.max(x1 - x0, 1), bh = Math.max(y1 - y0, 1);
  const k = clamp(Math.min((r.width - 2 * padX) / bw, (r.height - padTop - padBottom) / bh), .2, 1.15);
  const t = { k, x: (r.width - bw * k) / 2 - x0 * k, y: padTop + (r.height - padTop - padBottom - bh * k) / 2 - y0 * k };
  animate ? animateTo(t) : (Object.assign(V, t), paintView());
  S.fitted = true; S.touched = false;
  return true;
}
function centerOn(id, minK = .85) {
  const n = SYS.nodes[id]; if (!n) return;
  const r = vpRect(), k = Math.max(V.k, minK);
  S.touched = true;
  animateTo({ k, x: r.width / 2 - n.x * k, y: r.height / 2 - n.y * k });
}

/* ═══════════════ ponteiros: arrastar nó, mover fundo, pinça ═══════════════ */
const ptrs = new Map();
let gesture = null;

el.viewport.addEventListener('pointerdown', e => {
  if (e.pointerType === 'mouse' && e.button !== 0 && e.button !== 1) return;
  cancelAnimationFrame(animRaf);
  ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
  try { el.viewport.setPointerCapture(e.pointerId); } catch (err) { /* ok */ }
  if (ptrs.size === 2) {
    const [a, b] = [...ptrs.values()];
    gesture = { type: 'pinch', d: Math.hypot(a.x - b.x, a.y - b.y) || 1, k: V.k };
    return;
  }
  const nodeEl = e.target.closest('.cld-node');
  if (nodeEl && !nodeEl.classList.contains('off')) {
    const id = nodeEl.dataset.id, w = toWorld(e.clientX, e.clientY);
    gesture = { type: 'node', id, sx: e.clientX, sy: e.clientY, ox: w.x - SYS.nodes[id].x, oy: w.y - SYS.nodes[id].y,
                moved: false, canDrag: S.tool === 'select' };
  } else {
    gesture = { type: 'pan', sx: e.clientX, sy: e.clientY, vx: V.x, vy: V.y, moved: false };
  }
});

el.viewport.addEventListener('pointermove', e => {
  if (!ptrs.has(e.pointerId)) {                       // sem botão pressionado: só realce por hover
    if (e.pointerType === 'touch') return;
    const n = e.target.closest && e.target.closest('.cld-node');
    const id = n && !n.classList.contains('off') ? n.dataset.id : null;
    if (id !== S.hover) { S.hover = id; applyFocus(); }
    return;
  }
  ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
  if (!gesture) return;
  if (gesture.type === 'pinch') {
    if (ptrs.size < 2) return;
    const [a, b] = [...ptrs.values()], r = vpRect();
    zoomAt(gesture.k * (Math.hypot(a.x - b.x, a.y - b.y) / gesture.d), (a.x + b.x) / 2 - r.left, (a.y + b.y) / 2 - r.top);
    return;
  }
  const dx = e.clientX - gesture.sx, dy = e.clientY - gesture.sy;
  if (!gesture.moved && Math.hypot(dx, dy) < 4) return;
  gesture.moved = true;
  if (gesture.type === 'pan') {
    V.x = gesture.vx + dx; V.y = gesture.vy + dy; S.touched = true;
    el.viewport.classList.add('panning'); paintView();
  } else if (gesture.canDrag) {
    const w = toWorld(e.clientX, e.clientY);
    nodeEls.get(gesture.id).classList.add('dragging');
    moveNode(gesture.id, w.x - gesture.ox, w.y - gesture.oy);
  }
});

function endPointer(e) {
  ptrs.delete(e.pointerId);
  const g = gesture;
  if (g && g.type === 'pinch') { if (ptrs.size < 2) gesture = null; return; }
  gesture = null; el.viewport.classList.remove('panning');
  if (!g) return;
  if (g.type === 'node') {
    nodeEls.get(g.id)?.classList.remove('dragging');
    if (g.moved && g.canDrag) markDirty(); else if (!g.moved) activateNode(g.id);
  } else if (g.type === 'pan' && !g.moved && e.type === 'pointerup') {
    if (S.tool === 'link' && S.linkSrc) { S.linkSrc = null; showHint(HINT_LINK); applyFocus(); }
    else deselect();
  }
}
el.viewport.addEventListener('pointerup', endPointer);
el.viewport.addEventListener('pointercancel', endPointer);
el.viewport.addEventListener('pointerleave', () => { if (S.hover && !ptrs.size) { S.hover = null; applyFocus(); } });
el.viewport.addEventListener('wheel', e => {
  e.preventDefault(); cancelAnimationFrame(animRaf);
  const dy = e.deltaY * (e.deltaMode === 1 ? 33 : e.deltaMode === 2 ? 400 : 1), r = vpRect();
  zoomAt(V.k * Math.exp(-dy * (e.ctrlKey ? .012 : .0018)), e.clientX - r.left, e.clientY - r.top);
}, { passive: false });

function moveNode(id, x, y) {
  const n = SYS.nodes[id]; n.x = Math.round(x); n.y = Math.round(y);
  const d = nodeEls.get(id); d.style.left = n.x + 'px'; d.style.top = n.y + 'px';
  (adj.get(id) || []).forEach(layoutEdge);
}

/* teclado nos nós */
el.nodes.addEventListener('keydown', e => {
  const n = e.target.closest('.cld-node'); if (!n) return;
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); activateNode(n.dataset.id); }
  else if (e.key.startsWith('Arrow') && S.tool === 'select') {
    e.preventDefault();
    const step = e.shiftKey ? 40 : 10, n0 = SYS.nodes[n.dataset.id];
    moveNode(n.dataset.id, n0.x + (e.key === 'ArrowRight' ? step : e.key === 'ArrowLeft' ? -step : 0),
                          n0.y + (e.key === 'ArrowDown' ? step : e.key === 'ArrowUp' ? -step : 0));
    markDirty();
  }
});
el.nodes.addEventListener('focusin', e => { const n = e.target.closest('.cld-node'); if (n && !ptrs.size) { S.hover = n.dataset.id; applyFocus(); } });
el.nodes.addEventListener('focusout', () => { if (S.hover && !ptrs.size) { S.hover = null; applyFocus(); } });

/* ═══════════════ seleção e ferramentas ═══════════════ */
const HINT_LINK = 'Ligar: clique na variável de origem e depois na de destino (Esc cancela)';
const isNarrow = () => window.innerWidth < 720;

function activateNode(id) {
  if (S.tool === 'link') return linkClick(id);
  selectNode(id);
}
function selectNode(id, { center = false } = {}) {
  if (!SYS.nodes[id]) return;
  S.sel = id; applyFocus(); renderPanel();
  if (!S.panel || isNarrow()) setPanel(true);
  if (center) centerOn(id);
  saveViewSoon();
}
function deselect() {
  if (!S.sel) return;
  S.sel = null; applyFocus(); renderPanel();
  if (isNarrow()) setPanel(false);
  saveViewSoon();
}
function linkClick(id) {
  if (!S.linkSrc) { S.linkSrc = id; showHint(`Origem: ${id}. Agora clique no destino.`); applyFocus(); }
  else if (S.linkSrc === id) { S.linkSrc = null; showHint(HINT_LINK); applyFocus(); }
  else openLinkDialog(S.linkSrc, id);
}
function setTool(t) {
  S.tool = t; S.linkSrc = null;
  $$('button[data-tool]').forEach(b => { const on = b.dataset.tool === t; b.classList.toggle('active', on); b.setAttribute('aria-pressed', String(on)); });
  el.viewport.dataset.tool = t;
  t === 'link' ? showHint(HINT_LINK) : hideHint();
  applyFocus();
}
function showHint(msg) { el.hint.textContent = msg; el.hint.hidden = false; }
function hideHint() { el.hint.hidden = true; }

function setPanel(open) {
  S.panel = open;
  el.side.classList.toggle('closed', !open);
  el.btnPanel.setAttribute('aria-pressed', String(open));
}

/* ═══════════════ painel de detalhes ═══════════════ */
function fmtVal(v) {
  if (typeof v !== 'number' || !isFinite(v)) return v == null ? '—' : esc(v);
  return v.toLocaleString('pt-BR', { maximumSignificantDigits: 6 });
}
function eqHtml(expr, self) {   // identificadores que são variáveis do modelo viram links
  let out = '', last = 0;
  for (const m of expr.matchAll(/[A-Za-z_][A-Za-z0-9_]*/g)) {
    out += esc(expr.slice(last, m.index));
    const t = m[0];
    out += SYS.nodes[t] && t !== self ? `<a href="#" class="eqv" data-act="goto" data-id="${esc(t)}">${esc(t)}</a>` : esc(t);
    last = m.index + t.length;
  }
  return out + esc(expr.slice(last));
}
function relList(items, otherKey) {
  return `<ul class="rels">${items.map(l => {
    const other = l[otherKey], neg = l.sign === '-';
    return `<li><button type="button" class="rel" data-act="goto" data-id="${esc(other)}" title="${esc(l.desc || '')}">
      <span class="sgn ${neg ? 'neg' : 'pos'}">${neg ? '−' : '+'}</span><span class="nm">${esc(other)}</span></button>
      <button type="button" class="rel-x" data-act="flip" data-from="${esc(l.from)}" data-to="${esc(l.to)}" title="Inverter o sinal" aria-label="Inverter o sinal">${ic('flip')}</button>
      <button type="button" class="rel-x" data-act="rmlink" data-from="${esc(l.from)}" data-to="${esc(l.to)}" title="Remover ligação" aria-label="Remover ligação">${ic('x')}</button></li>`;
  }).join('')}</ul>`;
}
function renderPanel() {
  const id = S.sel, nd = id && SYS.nodes[id];
  if (!nd) {
    el.panel.innerHTML = `<div class="ph"><div class="ico"></div><strong>Nenhuma variável selecionada</strong>
      <span>Clique em um nó para ver descrição, equação e relações.</span>
      <span>${Object.keys(SYS.nodes).length} variáveis · ${SYS.links.length} ligações</span></div>`;
    return;
  }
  const inc = SYS.links.filter(l => l.to === id), out = SYS.links.filter(l => l.from === id);
  const cat = CATS.find(c => c.name === nd.cat) || CATS[0];
  let h = `<span class="d-cat" data-cat="${cat.key}"><i class="cdot"></i>${esc(cat.name)}</span>
    <h2 class="d-name">${esc(id)}</h2><p class="d-desc">${esc(nd.desc || 'Sem descrição.')}</p>
    <div class="d-sec"><h3>Valor atual</h3><div class="d-val">${fmtVal(nd.val)}</div></div>`;
  if (nd.expr) h += `<div class="d-sec"><h3>Equação</h3><div class="d-eq">${eqHtml(nd.expr, id)}</div></div>`;
  if (inc.length) h += `<div class="d-sec"><h3>Causas <span class="n">${inc.length}</span></h3>${relList(inc, 'from')}</div>`;
  if (out.length) h += `<div class="d-sec"><h3>Efeitos <span class="n">${out.length}</span></h3>${relList(out, 'to')}</div>`;
  h += `<div class="d-actions">
    <button type="button" class="btn" data-act="edit" data-id="${esc(id)}">${ic('pencil')}Editar</button>
    <button type="button" class="btn" data-act="link" data-id="${esc(id)}">${ic('link')}Ligar a…</button>
    <button type="button" class="btn danger" data-act="del" data-id="${esc(id)}">${ic('trash')}Excluir</button></div>`;
  el.panel.innerHTML = h;
}
el.panel.addEventListener('click', e => {
  const b = e.target.closest('[data-act]'); if (!b) return;
  e.preventDefault();
  const { act, id, from, to } = b.dataset;
  if (act === 'goto') selectNode(id, { center: true });
  else if (act === 'edit') openNodeDialog(id);
  else if (act === 'link') openLinkDialog(id);
  else if (act === 'del') deleteNode(id);
  else if (act === 'rmlink') removeLink(from, to);
  else if (act === 'flip') flipLink(from, to);
});

/* ═══════════════ edição do modelo ═══════════════ */
function structuralChange() { rebuild(); markDirty(); }
function deleteNode(id) {
  const node = SYS.nodes[id]; if (!node) return;
  const links = SYS.links.filter(l => l.from === id || l.to === id);
  SYS.links = SYS.links.filter(l => l.from !== id && l.to !== id);
  delete SYS.nodes[id];
  if (S.sel === id) S.sel = null;
  if (S.hover === id) S.hover = null;
  structuralChange();
  toast(`“${id}” excluído`, { action: { label: 'Desfazer', fn: () => {
    SYS.nodes[id] = node; SYS.links.push(...links); structuralChange(); selectNode(id); } } });
}
function removeLink(from, to) {
  const i = SYS.links.findIndex(l => l.from === from && l.to === to); if (i < 0) return;
  const [lk] = SYS.links.splice(i, 1);
  structuralChange();
  toast('Ligação removida', { action: { label: 'Desfazer', fn: () => { SYS.links.push(lk); structuralChange(); } } });
}
function flipLink(from, to) {
  const lk = SYS.links.find(l => l.from === from && l.to === to); if (!lk) return;
  lk.sign = lk.sign === '-' ? '+' : '-';
  structuralChange();
}

/* afastar sobreposições */
function tidy() {
  const ids = Object.keys(SYS.nodes);
  const before = Object.fromEntries(ids.map(id => [id, { x: SYS.nodes[id].x, y: SYS.nodes[id].y }]));
  const GAP = 14; let moved = false;
  for (let it = 0; it < 90; it++) {
    let any = false;
    for (let i = 0; i < ids.length; i++) for (let j = i + 1; j < ids.length; j++) {
      const a = SYS.nodes[ids[i]], b = SYS.nodes[ids[j]], da = dimsOf(ids[i]), db = dimsOf(ids[j]);
      const ox = (da.w + db.w) / 2 + GAP - Math.abs(a.x - b.x), oy = (da.h + db.h) / 2 + GAP - Math.abs(a.y - b.y);
      if (ox > 0 && oy > 0) {
        any = moved = true;
        if (ox < oy) { const s = a.x <= b.x ? -1 : 1; a.x += s * ox / 2; b.x -= s * ox / 2; }
        else { const s = a.y <= b.y ? -1 : 1; a.y += s * oy / 2; b.y -= s * oy / 2; }
      }
    }
    if (!any) break;
  }
  if (!moved) { toast('Nenhuma sobreposição encontrada'); return; }
  ids.forEach(id => { const n = SYS.nodes[id]; n.x = Math.round(n.x); n.y = Math.round(n.y);
    const d = nodeEls.get(id); d.style.left = n.x + 'px'; d.style.top = n.y + 'px'; });
  layoutAllEdges(); markDirty();
  toast('Nós afastados', { action: { label: 'Desfazer', fn: () => {
    ids.forEach(id => { if (SYS.nodes[id]) { SYS.nodes[id].x = before[id].x; SYS.nodes[id].y = before[id].y;
      const d = nodeEls.get(id); d.style.left = before[id].x + 'px'; d.style.top = before[id].y + 'px'; } });
    layoutAllEdges(); markDirty(); } } });
}

/* ═══════════════ diálogos ═══════════════ */
function openDialog(d) { if (!d.open) d.showModal(); }
$$('dialog').forEach(d => {
  d.addEventListener('click', e => { if (e.target === d) d.close(); });
  $$('[data-close]', d).forEach(b => b.addEventListener('click', () => d.close()));
});
$('#dlg-link').addEventListener('close', () => { if (S.tool === 'link') setTool('select'); });

const nnCat = $('#nn-cat');
nnCat.innerHTML = CATS.map(c => `<option value="${c.name}">${c.name}</option>`).join('');
let editing = null;
const NAME_RE = /^[A-Za-z_][A-Za-z0-9_]*$/;
function openNodeDialog(id = null) {
  editing = id;
  const n = id ? SYS.nodes[id] : { cat: 'Estado', val: 0, expr: '', desc: '' };
  $('#dn-title').textContent = id ? 'Editar variável' : 'Novo nó';
  $('#dn-sub').textContent = id ? 'Altere os atributos da variável selecionada.' : 'Crie uma nova variável no sistema.';
  $('#nn-ok').textContent = id ? 'Salvar alterações' : 'Criar nó';
  $('#nn-name').value = id || ''; nnCat.value = n.cat; $('#nn-val').value = n.val ?? 0;
  $('#nn-eq').value = n.expr || ''; $('#nn-desc').value = id ? (n.desc || '') : '';
  setErr($('#nn-err'), $('#nn-name'), '');
  openDialog($('#dlg-node'));
  $('#nn-name').focus(); $('#nn-name').select();
}
function setErr(p, input, msg) { p.hidden = !msg; p.textContent = msg; input && input.classList.toggle('bad', !!msg); }
$('#f-node').addEventListener('submit', e => {
  e.preventDefault();
  const name = $('#nn-name').value.trim(), err = $('#nn-err'), input = $('#nn-name');
  if (!name) return setErr(err, input, 'Informe um nome.');
  if ((editing === null || name !== editing) && !NAME_RE.test(name))
    return setErr(err, input, 'Use letras, números e _ (sem espaços), começando por letra ou _.');
  if (name !== editing && SYS.nodes[name]) return setErr(err, input, `“${name}” já existe.`);
  const data = { cat: nnCat.value, val: parseFloat($('#nn-val').value) || 0, expr: $('#nn-eq').value.trim(),
                 desc: $('#nn-desc').value.trim() || 'Sem descrição.' };
  if (editing === null) {
    const c = toWorld(vpRect().left + vpRect().width / 2, vpRect().top + vpRect().height / 2), j = () => (Math.random() - .5) * 60;
    SYS.nodes[name] = { ...data, x: Math.round(c.x + j()), y: Math.round(c.y + j()) };
  } else {
    const nd = Object.assign(SYS.nodes[editing], data);
    if (name !== editing) {
      SYS.nodes[name] = nd; delete SYS.nodes[editing];
      SYS.links.forEach(l => { if (l.from === editing) l.from = name; if (l.to === editing) l.to = name; });
      const re = new RegExp(`\\b${editing}\\b`, 'g');           // mantém as equações que citavam o nome antigo
      let fixed = 0;
      for (const o of Object.values(SYS.nodes)) if (o.expr && re.test(o.expr)) { o.expr = o.expr.replace(re, name); fixed++; re.lastIndex = 0; }
      if (S.sel === editing) S.sel = name;
      if (fixed) toast(`Nome atualizado em ${fixed} equaç${fixed > 1 ? 'ões' : 'ão'}`);
    }
  }
  $('#dlg-node').close();
  structuralChange();
  selectNode(name, { center: editing === null });
});

function openLinkDialog(from, to = null) {
  const sel = $('#lk-to');
  $('#lk-from').value = from;
  sel.innerHTML = Object.keys(SYS.nodes).filter(n => n !== from).sort((a, b) => a.localeCompare(b))
    .map(n => `<option value="${esc(n)}">${esc(n)}</option>`).join('');
  if (to) sel.value = to;
  const ex = SYS.links.find(l => l.from === from && l.to === sel.value);
  $$('input[name="lk-sign"]').forEach(r => { r.checked = r.value === (ex ? ex.sign : '+'); });
  $('#lk-desc').value = ex && ex.desc ? ex.desc : '';
  setErr($('#lk-err'), null, '');
  openDialog($('#dlg-link'));
  (to ? $('#f-link button[type=submit]') : sel).focus();
}
$('#f-link').addEventListener('submit', e => {
  e.preventDefault();
  const from = $('#lk-from').value, to = $('#lk-to').value;
  const sign = $('input[name="lk-sign"]:checked').value;
  if (!from || !to || from === to) return setErr($('#lk-err'), null, 'Origem e destino devem ser diferentes.');
  const desc = $('#lk-desc').value.trim() || `${from} ${sign === '+' ? 'reforça' : 'reduz'} ${to}`;
  const ex = SYS.links.find(l => l.from === from && l.to === to);
  ex ? Object.assign(ex, { sign, desc }) : SYS.links.push({ from, to, sign, desc });
  $('#dlg-link').close();
  structuralChange();
});

function askConfirm(title, text, okLabel) {
  return new Promise(resolve => {
    const d = $('#dlg-confirm');
    $('#dc-title').textContent = title; $('#dc-text').textContent = text; $('#dc-ok').textContent = okLabel;
    const done = () => { d.removeEventListener('close', done); resolve(d.returnValue === 'ok'); };
    d.returnValue = ''; d.addEventListener('close', done); openDialog(d);
  });
}

/* ═══════════════ avisos, estado e nuvem ═══════════════ */
function toast(msg, { action, type = 'info', ms = 6000 } = {}) {
  const t = document.createElement('div');
  t.className = 'toast ' + type; t.setAttribute('role', 'status');
  t.append(Object.assign(document.createElement('span'), { textContent: msg }));
  if (action) {
    const b = document.createElement('button'); b.type = 'button'; b.textContent = action.label;
    b.onclick = () => { action.fn(); t.remove(); }; t.append(b);
  }
  el.toasts.append(t);
  setTimeout(() => t.classList.add('out'), ms - 250); setTimeout(() => t.remove(), ms);
  while (el.toasts.children.length > 3) el.toasts.firstChild.remove();
}
function setStatus(state, text) { el.status.dataset.state = state; el.statusText.textContent = text; }
const persistDraft = debounce(() => { S.dirty ? store.set(KEYS.draft, { epoch: EPOCH, sys: SYS }) : store.del(KEYS.draft); }, 300);
function markDirty() { S.dirty = true; setStatus('dirty', 'Alterações não salvas'); persistDraft(); }
function markClean() { S.dirty = false; store.del(KEYS.draft); setStatus('idle', 'Sem alterações'); }

async function manualSave() {
  if (!HAS_CLOUD) return toast('Persistência não configurada (veja as Secrets).', { type: 'error' });
  setStatus('saving', 'Salvando…');
  try {
    const r = await fetch(`https://api.jsonbin.io/v3/b/${JSONBIN_BIN_ID}`, { method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'X-Master-Key': JSONBIN_API_KEY }, body: JSON.stringify(SYS) });
    if (!r.ok) throw new Error(r.status);
    S.dirty = false; store.del(KEYS.draft);
    setStatus('saved', 'Salvo');
    toast('Diagrama salvo. Use “Recarregar modelo” abaixo para levá-lo à simulação.');
    setTimeout(() => { if (el.status.dataset.state === 'saved') setStatus('idle', 'Sem alterações'); }, 3000);
  } catch (err) {
    setStatus('error', 'Falha ao salvar');
    toast(err instanceof TypeError ? 'Sem conexão com a nuvem.' : `Erro ao salvar (${err.message}).`, { type: 'error' });
  }
}
async function refreshFromCloud() {
  if (!HAS_CLOUD) return toast('Persistência não configurada (veja as Secrets).', { type: 'error' });
  if (S.dirty && !(await askConfirm('Descartar alterações?', 'Há edições não salvas neste diagrama. Recarregar da nuvem as substitui.', 'Descartar e recarregar'))) return;
  setStatus('saving', 'Carregando…');
  try {
    const r = await fetch(`https://api.jsonbin.io/v3/b/${JSONBIN_BIN_ID}/latest`, { headers: { 'X-Master-Key': JSONBIN_API_KEY } });
    if (!r.ok) throw new Error(r.status);
    const data = await r.json();
    if (!data.record || !data.record.nodes) throw new Error('formato');
    SYS = data.record; SYS.links = SYS.links || []; S.sel = null; S.linkSrc = null;
    markClean(); rebuild(); measureNodes(); layoutAllEdges(); fit();
    setStatus('saved', 'Recarregado');
    setTimeout(() => { if (el.status.dataset.state === 'saved') setStatus('idle', 'Sem alterações'); }, 3000);
  } catch (err) {
    setStatus('error', 'Falha ao carregar');
    toast('Não foi possível carregar o modelo da nuvem.', { type: 'error' });
  }
}

/* ═══════════════ busca ═══════════════ */
const sIn = $('#search-input'), sList = $('#search-results');
let sItems = [], sIdx = -1;
function renderSearch() {
  const q = sIn.value.trim().toLowerCase();
  if (!q) return closeSearch();
  const score = (id, n) => { const l = id.toLowerCase(); return l === q ? 4 : l.startsWith(q) ? 3 : l.includes(q) ? 2 : (n.desc || '').toLowerCase().includes(q) ? 1 : 0; };
  sItems = Object.entries(SYS.nodes).map(([id, n]) => ({ id, n, s: score(id, n) })).filter(x => x.s)
    .sort((a, b) => b.s - a.s || a.id.localeCompare(b.id)).slice(0, 8);
  sIdx = sItems.length ? 0 : -1;
  sList.innerHTML = sItems.length
    ? sItems.map((x, i) => `<li role="option" data-id="${esc(x.id)}" aria-selected="${i === 0}" data-cat="${catKey(x.n.cat)}"><i class="cdot"></i><b>${esc(x.id)}</b><small>${esc(x.n.cat)}</small></li>`).join('')
    : '<li class="none" role="option">Nenhuma variável encontrada</li>';
  sList.hidden = false; sIn.setAttribute('aria-expanded', 'true');
}
function closeSearch() { sList.hidden = true; sIn.setAttribute('aria-expanded', 'false'); sItems = []; sIdx = -1; }
function pickSearch(id) { closeSearch(); sIn.value = ''; sIn.blur(); selectNode(id, { center: true }); }
function markSearch(i) { sIdx = i; $$('li', sList).forEach((li, j) => li.setAttribute('aria-selected', String(j === i))); }
sIn.addEventListener('input', renderSearch);
sIn.addEventListener('focus', renderSearch);
sIn.addEventListener('blur', () => setTimeout(closeSearch, 120));
sIn.addEventListener('keydown', e => {
  if (e.key === 'ArrowDown' && sItems.length) { e.preventDefault(); markSearch((sIdx + 1) % sItems.length); }
  else if (e.key === 'ArrowUp' && sItems.length) { e.preventDefault(); markSearch((sIdx - 1 + sItems.length) % sItems.length); }
  else if (e.key === 'Enter' && sItems[sIdx]) { e.preventDefault(); pickSearch(sItems[sIdx].id); }
  else if (e.key === 'Escape') { sIn.value = ''; closeSearch(); sIn.blur(); }
});
sList.addEventListener('pointerdown', e => { const li = e.target.closest('li[data-id]'); if (li) { e.preventDefault(); pickSearch(li.dataset.id); } });

/* ═══════════════ barras e atalhos ═══════════════ */
$$('button[data-tool]').forEach(b => b.addEventListener('click', () => setTool(S.tool === b.dataset.tool && b.dataset.tool !== 'select' ? 'select' : b.dataset.tool)));
$('#btn-add').addEventListener('click', () => openNodeDialog());
$('#btn-empty-add').addEventListener('click', () => openNodeDialog());
$('#btn-save').addEventListener('click', manualSave);
$('#btn-reload').addEventListener('click', refreshFromCloud);
$('#btn-panel').addEventListener('click', () => setPanel(!S.panel));
$('#side-x').addEventListener('click', () => setPanel(false));
$('#z-in').addEventListener('click', () => zoomBy(1.25));
$('#z-out').addEventListener('click', () => zoomBy(1 / 1.25));
$('#z-fit').addEventListener('click', () => fit());
$('#z-tidy').addEventListener('click', tidy);

document.addEventListener('keydown', e => {
  if ($$('dialog').some(d => d.open)) return;
  const typing = ['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName);
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); sIn.focus(); return; }
  if (typing || e.ctrlKey || e.metaKey || e.altKey) return;
  const k = e.key.toLowerCase();
  if (k === 's') setTool('select');
  else if (k === 'l') setTool(S.tool === 'link' ? 'select' : 'link');
  else if (k === 'n') { e.preventDefault(); openNodeDialog(); }
  else if (k === 'f') fit();
  else if (k === 'p') setPanel(!S.panel);
  else if (k === '/') { e.preventDefault(); sIn.focus(); }
  else if (k === '+' || k === '=') zoomBy(1.25);
  else if (k === '-') zoomBy(1 / 1.25);
  else if (e.key === 'Delete' && S.sel) deleteNode(S.sel);
  else if (e.key === 'Escape') { if (S.tool === 'link') setTool('select'); else deselect(); }
});

/* ═══════════════ tamanho do iframe e primeira exibição ═══════════════ */
function fitFrameHeight() {
  try {
    const fe = window.frameElement; if (!fe) return;
    const ph = window.parent.innerHeight, pw = window.parent.innerWidth;
    const h = pw < 720 ? clamp(ph - 170, 460, 720) : clamp(ph - 300, 520, 980);
    if (fe.style.height !== h + 'px') {
      fe.style.height = h + 'px'; fe.setAttribute('height', h);
      // o Streamlit também fixa a altura do contêiner do elemento: acompanha, senão o iframe invade o que vem abaixo
      const box = fe.closest('[data-testid="stElementContainer"]') || fe.parentElement;
      if (box) box.style.setProperty('height', h + 'px', 'important');
    }
  } catch (e) { /* sem acesso ao pai: usa a altura definida pelo Python */ }
}
fitFrameHeight();
try { window.parent.addEventListener('resize', debounce(fitFrameHeight, 80)); } catch (e) { /* idem */ }

let firstShow = true;
function handleFocusRequest() {
  if (!FOCUS || !FOCUS.name || !SYS.nodes[FOCUS.name]) return false;
  if (store.get(KEYS.focus) === FOCUS.nonce) return false;      // cada pedido é atendido uma vez
  store.set(KEYS.focus, FOCUS.nonce);
  selectNode(FOCUS.name, { center: true });
  return true;
}
new ResizeObserver(() => {
  const r = vpRect();
  if (r.width < 80 || r.height < 80) return;                    // aba oculta: aguarda
  if (!S.measured && measureNodes()) layoutAllEdges();
  if (firstShow) {
    firstShow = false;
    const v = store.get(KEYS.view);
    if (v && v.touched && isFinite(v.x) && isFinite(v.k)) { Object.assign(V, { x: v.x, y: v.y, k: v.k }); S.touched = true; paintView(); S.fitted = true; }
    else fit({ animate: false });
    if (v && v.sel && SYS.nodes[v.sel]) selectNode(v.sel);
    handleFocusRequest();
  } else if (!S.touched) fit({ animate: false });               // sem navegação manual: mantém enquadrado ao redimensionar
}).observe(el.viewport);

if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => {
  if (measureNodes()) { layoutAllEdges(); if (!S.touched && S.fitted) fit({ animate: false }); }
});

/* ═══════════════ início ═══════════════ */
renderLegend();
setPanel(!isNarrow());
buildNodes(); buildEdges(); applyFocus(); renderPanel();
if (S.dirty) setStatus('dirty', 'Alterações não salvas');
el.btnSave.disabled = !HAS_CLOUD;
if (!HAS_CLOUD) el.btnSave.title = 'Configure o JSONBin nas Secrets para salvar';
window.addEventListener('resize', debounce(() => { if (isNarrow() && S.panel && !S.sel) setPanel(false); }, 120));
