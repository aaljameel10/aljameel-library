// Library page: filter by type and theme, sort, title search, and optional full-text search inside the books.
const PREVIEW = document.documentElement.hasAttribute('data-preview');
const bookUrl = (slug, p) => new URL(`../books/${slug}/${PREVIEW ? 'index.html' : ''}${p ? '#p' + p : ''}`, import.meta.url).href;
const works = JSON.parse(document.getElementById('works-data').textContent);
const $ = s => document.querySelector(s);
const toAr = n => String(n).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
const norm = t => t.replace(/[ؐ-ًؚ-ٰٟـ]/g, '')
  .replace(/[أإآٱ]/g, 'ا').replace(/ة/g, 'ه').replace(/ى/g, 'ي').replace(/ؤ/g, 'و').replace(/ئ/g, 'ي')
  .replace(/[^ء-ي0-9a-zA-Z\s]/g, ' ').replace(/\s+/g, ' ').trim();

// 1:1 fold (same length) so match offsets in folded text map straight back to the displayed text.
const FOLD = { 'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ة': 'ه', 'ى': 'ي', 'ؤ': 'و', 'ئ': 'ي' };
const fold = t => t.replace(/[أإآٱةىؤئ]/g, c => FOLD[c]).replace(/[^\u0621-\u064A0-9a-zA-Z]/g, ' ');
const params = new URLSearchParams(location.search);
const state = { q: params.get('q') || '', type: params.get('type') || 'all', theme: params.get('theme') || 'all',
  sort: params.get('sort') || 'new', deep: params.get('deep') !== '0' };

const qInput = $('#q'), sortSel = $('#sort'), deepBox = $('#deep');
qInput.value = state.q; sortSel.value = state.sort; deepBox.checked = state.deep;

const grid = $('#grid'), count = $('#count'), empty = $('#empty'), hitsBox = $('#hits'), reset = $('#reset');
const cards = new Map([...grid.children].map(el => [el.dataset.id, el]));

function sync() {
  const p = new URLSearchParams();
  if (state.q) p.set('q', state.q);
  if (state.type !== 'all') p.set('type', state.type);
  if (state.theme !== 'all') p.set('theme', state.theme);
  if (state.sort !== 'new') p.set('sort', state.sort);
  if (!state.deep) p.set('deep', '0');
  history.replaceState(null, '', location.pathname + (p.toString() ? '?' + p : ''));
}

function render() {
  const nq = norm(state.q);
  const base = works.filter(w => !nq || norm(w.title + ' ' + w.subtitle + ' ' + w.publisher).includes(nq));
  const list = base.filter(w => (state.type === 'all' || w.type === state.type) && (state.theme === 'all' || w.theme === state.theme));
  list.sort((a, b) => state.sort === 'old' ? a.year - b.year : state.sort === 'title' ? a.title.localeCompare(b.title, 'ar') : b.year - a.year);
  for (const el of cards.values()) el.hidden = true;
  for (const w of list) { const el = cards.get(w.id); el.hidden = false; grid.appendChild(el); }
  document.querySelectorAll('[data-type-btn]').forEach(b => {
    const t = b.dataset.typeBtn;
    b.setAttribute('aria-pressed', state.type === t);
    const n = base.filter(w => (t === 'all' || w.type === t) && (state.theme === 'all' || w.theme === state.theme)).length;
    b.querySelector('.n').textContent = '(' + toAr(n) + ')';
  });
  document.querySelectorAll('[data-theme-btn]').forEach(b => b.setAttribute('aria-pressed', state.theme === b.dataset.themeBtn));
  count.textContent = !state.q ? `العناوين المعروضة: ${toAr(list.length)} من ${toAr(works.length)}`
    : list.length ? `عناوين تطابق «${state.q}»: ${toAr(list.length)}` : `لا عنوان يطابق «${state.q}»`;
  empty.hidden = list.length > 0 || (state.deep && !!state.q);
  reset.hidden = !(state.q || state.type !== 'all' || state.theme !== 'all');
  sync();
  deepSearch();
}

/* ---- full text ---- */
// Each work's page texts load on demand, a few at a time, and stay in memory for later searches
// (the browser also keeps them for a day). Results appear as each work finishes loading.
const texts = new Map();   // work id -> Promise<[[page, text, folded], ...]>
function loadWork(w) {
  if (!texts.has(w.id)) {
    texts.set(w.id, fetch(new URL(`../data/search/${w.id}.json`, import.meta.url))
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(pages => pages.map(([p, t]) => [p, t, fold(t)]))
      .catch(() => { texts.delete(w.id); return null; }));   // null = failed this time; retried next search
  }
  return texts.get(w.id);
}
function esc(s) { return s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }
function findIn(pages, fq) {
  const snips = [];
  for (const [p, text, f] of pages) {
    const i = f.indexOf(fq);
    if (i < 0) continue;
    const a = Math.max(0, text.lastIndexOf(' ', Math.max(0, i - 70))), bb = text.indexOf(' ', Math.min(text.length, i + fq.length + 70));
    const b = bb < 0 ? text.length : bb;
    snips.push({ p, html: esc(text.slice(a, i)) + '<mark>' + esc(text.slice(i, i + fq.length)) + '</mark>' + esc(text.slice(i + fq.length, b)) });
  }
  return snips;
}

let run = 0, timer = null;
function deepSearch() {
  clearTimeout(timer);
  const my = ++run;   // a newer search makes this one stop updating the page
  hitsBox.replaceChildren();
  const nq = norm(state.q);
  const fq = fold(nq);
  if (!state.deep || nq.length < 3) return;
  timer = setTimeout(async () => {
    const scope = works.filter(w => (state.type === 'all' || w.type === state.type) && (state.theme === 'all' || w.theme === state.theme));
    const results = [];
    let done = 0, failed = 0, frame = 0;
    const paint = final => {
      if (my !== run) return;
      const sorted = [...results].sort((a, b) => b.snips.length - a.snips.length);
      const totalPages = sorted.reduce((n, r) => n + r.snips.length, 0);
      const progress = final ? '' : `<p class="hits-note" role="status">جارٍ البحث في نصوص الكتب… بُحث في ${toAr(done)} من ${toAr(scope.length)}</p>`;
      const failNote = final && failed ? `<p class="hits-note">تعذّر تحميل نصوص ${toAr(failed)} من المؤلفات، فقد تكون النتائج ناقصة. أعد البحث بعد قليل.</p>` : '';
      if (!sorted.length) {
        hitsBox.innerHTML = progress + (final ? `<p class="hits-note">لم ترد «${esc(state.q)}» في نصوص الكتب. جرّب كلمة أقصر أو صيغة أخرى.</p>` + failNote : '');
        if (final) empty.hidden = grid.querySelector('.work:not([hidden])') !== null;
        return;
      }
      empty.hidden = true;
      hitsBox.innerHTML = progress + `<h2 class="sr">نتائج من داخل الكتب</h2><p class="hits-note"${final ? ' role="status"' : ''}>وردت «${esc(state.q)}» داخل النصوص في ${toAr(totalPages)} صفحة، وعدد المؤلفات التي وردت فيها: ${toAr(sorted.length)}${final ? '' : ' حتى الآن'}. النص مستخرج آلياً من الصفحات المصوّرة، فقد يفوته بعض المواضع.</p>` + failNote +
        sorted.map(r => `<article class="hit"><h3><a href="${bookUrl(r.w.slug)}">${esc(r.w.title)}</a></h3><ul class="snips">${
          r.snips.slice(0, 4).map(s => `<li>…${s.html}… <a href="${bookUrl(r.w.slug, s.p)}">صفحة الملف ${toAr(s.p)}</a></li>`).join('')
        }${r.snips.length > 4 ? `<li><a href="${bookUrl(r.w.slug)}">و${toAr(r.snips.length - 4)} مواضع أخرى</a></li>` : ''}</ul></article>`).join('');
    };
    const schedule = () => { if (!frame) frame = requestAnimationFrame(() => { frame = 0; paint(false); }); };
    paint(false);
    const queue = [...scope];
    const worker = async () => {
      for (let w; (w = queue.shift());) {
        const pages = await loadWork(w);
        if (my !== run) return;
        done++;
        if (!pages) failed++;
        else { const snips = findIn(pages, fq); if (snips.length) results.push({ w, snips }); }
        schedule();
      }
    };
    await Promise.all(Array.from({ length: 4 }, worker));
    if (my !== run) return;
    cancelAnimationFrame(frame); frame = 0;
    paint(true);
  }, 250);
}

/* ---- events ---- */
qInput.addEventListener('input', () => { state.q = qInput.value.trim(); render(); });
sortSel.addEventListener('change', () => { state.sort = sortSel.value; render(); });
deepBox.addEventListener('change', () => { state.deep = deepBox.checked; render(); });
document.querySelectorAll('[data-type-btn]').forEach(b => b.addEventListener('click', () => { state.type = b.dataset.typeBtn; render(); }));
document.querySelectorAll('[data-theme-btn]').forEach(b => b.addEventListener('click', () => { state.theme = b.dataset.themeBtn; render(); }));
reset.addEventListener('click', () => { Object.assign(state, { q: '', type: 'all', theme: 'all' }); qInput.value = ''; render(); qInput.focus(); });
$('#lib-form').addEventListener('submit', e => e.preventDefault());
render();
