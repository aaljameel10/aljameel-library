// Comment moderation page (/admin/).
const toAr = n => String(n).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
const esc = s => String(s || '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const TITLES = JSON.parse(document.getElementById('titles').textContent || '{}');
let status = 'pending';
async function api(path, opts) {
  const r = await fetch('/api/admin/' + path, { headers: { 'content-type': 'application/json' }, credentials: 'same-origin', ...opts });
  const j = await r.json().catch(() => ({}));
  if (r.status === 401) { show(false); throw new Error(j.error || 'سجّل الدخول أولاً.'); }
  if (!r.ok) throw new Error(j.error || 'حدث خطأ. أعد المحاولة.');
  return j;
}
function show(loggedIn) { document.getElementById('login').hidden = loggedIn; document.getElementById('panel').hidden = !loggedIn; }
async function load() {
  const list = document.getElementById('list');
  list.innerHTML = '<p class="note">جارٍ التحميل…</p>';
  let data;
  try { data = await api('comments?status=' + status); } catch (e) { list.innerHTML = ''; return; }
  show(true);
  document.querySelectorAll('[data-n]').forEach(el => el.textContent = '(' + toAr(data.counts[el.dataset.n] || 0) + ')');
  document.querySelectorAll('[data-status]').forEach(b => b.setAttribute('aria-pressed', b.dataset.status === status));
  if (!data.comments.length) { list.innerHTML = '<p class="note">' + (status === 'pending' ? 'لا توجد تعليقات جديدة بانتظار المراجعة.' : 'لا توجد تعليقات منشورة بعد.') + '</p>'; return; }
  list.innerHTML = data.comments.map(c => `
    <article class="card" data-id="${c.id}">
      <p class="meta"><a href="/books/${esc(c.slug)}/" target="_blank" rel="noopener">${esc(TITLES[c.slug] || c.slug)}</a> ، ${esc(c.created)}</p>
      <p><strong>${esc(c.name)}</strong></p>
      <p class="body">${esc(c.body)}</p>
      <label class="sr" for="r${c.id}">ردّ المكتبة</label>
      <textarea id="r${c.id}" rows="2" placeholder="ردّ اختياري يظهر تحت التعليق">${esc(c.reply)}</textarea>
      <div class="acts">
        ${status === 'pending' ? '<button class="btn" data-act="approve">اعتماد ونشر</button>' : '<button class="btn" data-act="approve">حفظ الرد</button><button class="btn ghost" data-act="hide">إخفاء من الموقع</button>'}
        <button class="btn ghost" data-act="delete" data-confirm="0">حذف</button>
      </div>
    </article>`).join('');
}
document.getElementById('list').addEventListener('click', async e => {
  const b = e.target.closest('[data-act]'); if (!b) return;
  const card = b.closest('[data-id]'), id = +card.dataset.id;
  if (b.dataset.act === 'delete' && b.dataset.confirm === '0') { b.dataset.confirm = '1'; b.textContent = 'اضغط مرة أخرى لتأكيد الحذف'; return; }
  b.disabled = true;
  try { await api('comments', { method: 'POST', body: JSON.stringify({ id, action: b.dataset.act, reply: card.querySelector('textarea').value.trim() || null }) }); load(); }
  catch (err) { b.disabled = false; b.textContent = err.message; }
});
document.querySelectorAll('[data-status]').forEach(b => b.addEventListener('click', () => { status = b.dataset.status; load(); }));
document.getElementById('logout').addEventListener('click', async () => { await fetch('/api/admin/logout', { method: 'POST' }); show(false); });
document.getElementById('login').addEventListener('submit', async e => {
  e.preventDefault();
  const m = document.getElementById('login-msg'); m.textContent = '';
  try { await api('login', { method: 'POST', body: JSON.stringify({ password: document.getElementById('pw').value }) }); document.getElementById('pw').value = ''; load(); }
  catch (err) { m.textContent = err.message; }
});
load().catch(() => show(false));
fetch('/api/admin/comments?status=pending', { credentials: 'same-origin' }).then(r => { if (r.status === 401 || r.status === 503) show(false); });
