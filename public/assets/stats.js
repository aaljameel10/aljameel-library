// Read and download counters. Shows counts wherever [data-count] appears and records
// downloads (links with data-dl) and reads (the reader announces 'lib:read').
const API = new URL('../api/stats', import.meta.url).href;
const toAr = n => String(n).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);

function send(slug, kind) {
  const body = JSON.stringify({ slug, kind });
  try {
    if (navigator.sendBeacon) navigator.sendBeacon(API, new Blob([body], { type: 'application/json' }));
    else fetch(API, { method: 'POST', body, headers: { 'content-type': 'application/json' }, keepalive: true });
  } catch {}
}

document.addEventListener('click', e => {
  const a = e.target.closest('[data-dl]');
  if (a) send(a.dataset.dl, 'download');
});
document.addEventListener('lib:read', e => send(e.detail.slug, 'read'));

const targets = document.querySelectorAll('[data-count]');
if (targets.length) {
  fetch(API).then(r => r.ok ? r.json() : Promise.reject()).then(all => {
    targets.forEach(el => {
      const [slug, kind] = el.dataset.count.split(':');
      const n = all[slug]?.[kind] || 0;
      el.textContent = toAr(n);
      el.closest('[data-count-wrap]')?.removeAttribute('hidden');
    });
  }).catch(() => {});
}
