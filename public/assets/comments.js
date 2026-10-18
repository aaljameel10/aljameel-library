// Comments under a work: shows approved comments and sends new ones for the family's approval.
const API = new URL('../api/comments', import.meta.url).href;
const box = document.querySelector('[data-comments]');
if (box) {
  const slug = box.dataset.comments;
  const list = box.querySelector('.c-list'), form = box.querySelector('form'), msg = box.querySelector('.c-msg');
  const count = box.querySelector('.c-count');
  const opened = Date.now();
  const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const toAr = n => String(n).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
  const date = s => { try { return new Date(s.replace(' ', 'T') + 'Z').toLocaleDateString('ar-SA-u-ca-gregory', { year: 'numeric', month: 'long', day: 'numeric' }); } catch { return ''; } };

  fetch(`${API}?slug=${encodeURIComponent(slug)}`).then(r => r.ok ? r.json() : Promise.reject()).then(rows => {
    count.textContent = rows.length ? `(${toAr(rows.length)})` : '';
    list.innerHTML = rows.length ? rows.map(c => `<li class="c-item"><p class="c-head"><strong>${esc(c.name)}</strong> <span>${date(c.created)}</span></p><p class="c-body">${esc(c.body)}</p>${c.reply ? `<p class="c-reply"><strong>ردّ المكتبة:</strong> ${esc(c.reply)}</p>` : ''}</li>`).join('')
      : '<li class="c-empty">لا توجد تعليقات بعد. شاركنا رأيك أو سؤالك عن هذا العمل.</li>';
  }).catch(() => {
    list.innerHTML = '<li class="c-empty">التعليقات تعمل بعد نشر الموقع على نطاقه.</li>';
    form.hidden = true;
  });

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const btn = form.querySelector('button[type=submit]');
    const data = Object.fromEntries(new FormData(form));
    btn.disabled = true; msg.textContent = 'جارٍ الإرسال…'; msg.className = 'c-msg';
    try {
      const r = await fetch(API, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ ...data, slug, t: Date.now() - opened }) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.error || 'تعذّر الإرسال. أعد المحاولة بعد قليل.');
      form.reset();
      msg.textContent = 'وصل تعليقك، وسيظهر هنا بعد مراجعته. شكراً لك.';
      msg.className = 'c-msg ok';
    } catch (err) {
      msg.textContent = err.message; msg.className = 'c-msg err';
    } finally { btn.disabled = false; }
  });
}
