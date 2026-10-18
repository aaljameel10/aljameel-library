// Admin API for comment moderation. Protected by the ADMIN_PASSWORD secret set in Cloudflare.
// POST /api/admin/login   {password}           -> sets a 30-day session cookie
// POST /api/admin/logout
// GET  /api/admin/comments?status=pending|approved
// POST /api/admin/comments {id, action: approve|hide|delete, reply?}
import { db, json, isAdmin, makeSession } from '../../../lib/api.js';

export async function onRequest({ request, env, params }) {
  const action = (params.action || []).join('/');
  if (!env.ADMIN_PASSWORD) return json({ error: 'لم تُضبط كلمة مرور الإدارة بعد في إعدادات Cloudflare.' }, 503);

  if (action === 'login' && request.method === 'POST') {
    const { password } = await request.json().catch(() => ({}));
    if (password !== env.ADMIN_PASSWORD) {
      await new Promise(r => setTimeout(r, 800));
      return json({ error: 'كلمة المرور غير صحيحة.' }, 401);
    }
    return json({ ok: true }, 200, { 'set-cookie': `lib_admin=${await makeSession(env)}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=2592000` });
  }
  if (action === 'logout') return json({ ok: true }, 200, { 'set-cookie': 'lib_admin=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0' });

  if (!(await isAdmin(request, env))) return json({ error: 'سجّل الدخول أولاً.' }, 401);
  const d = await db(env);

  if (action === 'comments' && request.method === 'GET') {
    const status = new URL(request.url).searchParams.get('status') === 'approved' ? 'approved' : 'pending';
    const { results } = await d.prepare('SELECT id, slug, name, body, created, reply FROM comments WHERE status = ? ORDER BY id DESC LIMIT 500').bind(status).all();
    const counts = await d.prepare("SELECT status, COUNT(*) AS c FROM comments GROUP BY status").all();
    return json({ comments: results, counts: Object.fromEntries(counts.results.map(r => [r.status, r.c])) });
  }
  if (action === 'comments' && request.method === 'POST') {
    const { id, action: act, reply } = await request.json().catch(() => ({}));
    if (!Number.isInteger(id)) return json({ error: 'طلب غير صالح.' }, 400);
    if (act === 'approve') await d.prepare("UPDATE comments SET status = 'approved', reply = COALESCE(?, reply) WHERE id = ?").bind(reply ? String(reply).slice(0, 2000) : null, id).run();
    else if (act === 'hide') await d.prepare("UPDATE comments SET status = 'pending' WHERE id = ?").bind(id).run();
    else if (act === 'delete') await d.prepare('DELETE FROM comments WHERE id = ?').bind(id).run();
    else return json({ error: 'طلب غير صالح.' }, 400);
    return json({ ok: true });
  }
  return json({ error: 'غير موجود.' }, 404);
}
