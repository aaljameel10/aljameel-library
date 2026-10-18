// In-page PDF reader built on pdf.js. One page at a time, RTL-aware keyboard,
// remembers the last page per work, and opens at #p=N links (from the contents and search).
import * as pdfjs from '../vendor/pdfjs/pdf.min.mjs';
pdfjs.GlobalWorkerOptions.workerSrc = new URL('../vendor/pdfjs/pdf.worker.min.mjs', import.meta.url).href;

const toAr = n => String(n).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);

for (const root of document.querySelectorAll('[data-reader]')) setup(root);

function setup(root) {
  const url = new URL(root.dataset.pdf, location.href).href, key = 'reader:' + root.dataset.slug;
  const stage = root.querySelector('.reader-stage');
  const input = root.querySelector('input[type=number]');
  const total = root.querySelector('[data-total]');
  let doc = null, page = 1, scale = 0, rendering = null, started = false;

  const store = {
    get() { try { return +localStorage.getItem(key) || 0; } catch { return 0; } },
    set(v) { try { localStorage.setItem(key, v); } catch {} }
  };

  let loadP = null;
  function load() {
    loadP ??= (async () => {
      stage.innerHTML = '<p class="reader-msg">جارٍ فتح الملف…</p>';
      try {
        doc = await pdfjs.getDocument({ url, disableAutoFetch: true, rangeChunkSize: 262144 }).promise;
        input.max = doc.numPages; total.textContent = toAr(doc.numPages);
      } catch (e) {
        stage.innerHTML = '<p class="reader-msg">تعذّر فتح الملف هنا. يمكنك تحميله بزر «تحميل PDF».</p>';
      }
    })();
    return loadP;
  }
  function start(p) { return go(p || (doc ? page : store.get()) || 1); }

  async function go(p) {
    if (!doc) { await load(); if (!doc) return; }
    page = Math.min(Math.max(1, p | 0), doc.numPages);
    input.value = page; store.set(page);
    const pg = await doc.getPage(page);
    const avail = Math.max(280, stage.clientWidth - 24);
    const base = pg.getViewport({ scale: 1 });
    const fit = Math.min(avail / base.width, 1.6);
    const vp = pg.getViewport({ scale: (scale || fit) * (window.devicePixelRatio || 1) });
    const canvas = document.createElement('canvas');
    canvas.width = vp.width; canvas.height = vp.height;
    canvas.style.width = (vp.width / (window.devicePixelRatio || 1)) + 'px';
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', 'صفحة ' + toAr(page));
    if (rendering) rendering.cancel();
    rendering = pg.render({ canvasContext: canvas.getContext('2d'), viewport: vp });
    try { await rendering.promise; } catch { return; }
    stage.replaceChildren(canvas);
    if (!started) { started = true; document.dispatchEvent(new CustomEvent('lib:read', { detail: { slug: root.dataset.slug } })); }
    if (!scale) scale = fit;
  }

  root.querySelector('[data-act=next]').onclick = () => go(page + 1);
  root.querySelector('[data-act=prev]').onclick = () => go(page - 1);
  root.querySelector('[data-act=in]').onclick = () => { scale = (scale || 1) * 1.2; go(page); };
  root.querySelector('[data-act=out]').onclick = () => { scale = (scale || 1) / 1.2; go(page); };
  root.querySelector('[data-act=full]').onclick = () => {
    if (document.fullscreenElement) document.exitFullscreen(); else root.requestFullscreen?.();
  };
  input.onchange = () => go(+input.value);
  root.addEventListener('keydown', e => {
    if (e.target === input) return;
    if (e.key === 'ArrowLeft') { e.preventDefault(); go(page + 1); }   // RTL: left = forward
    if (e.key === 'ArrowRight') { e.preventDefault(); go(page - 1); }
  });
  root.querySelector('[data-act=open]')?.addEventListener('click', () => start());
  document.querySelectorAll('[data-open-reader]').forEach(a => a.addEventListener('click', e => {
    const p = +a.dataset.openReader || 0;
    start(p);
  }));

  const m = location.hash.match(/^#p(\d+)$/);
  if (m) { root.scrollIntoView(); start(+m[1]); }
  window.addEventListener('hashchange', () => {
    const h = location.hash.match(/^#p(\d+)$/); if (h) { root.scrollIntoView(); start(+h[1]); }
  });
}
