// Book page: accessible tabs and copy-citation buttons.
const tabs = [...document.querySelectorAll('[role=tab]')];
function select(tab, focus) {
  tabs.forEach(t => {
    const on = t === tab;
    t.setAttribute('aria-selected', on);
    t.tabIndex = on ? 0 : -1;
    document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
  });
  if (focus) tab.focus();
}
tabs.forEach((t, i) => {
  t.addEventListener('click', () => select(t));
  t.addEventListener('keydown', e => {
    const d = e.key === 'ArrowLeft' ? 1 : e.key === 'ArrowRight' ? -1 : 0; // RTL
    if (d) { e.preventDefault(); select(tabs[(i + d + tabs.length) % tabs.length], true); }
  });
});
document.querySelectorAll('[data-copy]').forEach(b => b.addEventListener('click', async () => {
  const text = document.getElementById(b.dataset.copy).innerText;
  try { await navigator.clipboard.writeText(text); b.textContent = 'نُسخ التوثيق'; }
  catch { b.textContent = 'حدّد النص وانسخه يدوياً'; }
  setTimeout(() => (b.textContent = b.dataset.label), 2500);
}));
document.querySelectorAll('[data-share]').forEach(b => b.addEventListener('click', async () => {
  const data = { title: document.title, url: location.href.split('#')[0] };
  if (navigator.share) { try { await navigator.share(data); } catch {} }
  else { try { await navigator.clipboard.writeText(data.url); b.textContent = 'نُسخ الرابط'; setTimeout(() => (b.textContent = b.dataset.label), 2500); } catch {} }
}));
