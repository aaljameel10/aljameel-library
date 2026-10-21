// Admin API for comment moderation. Protected by the ADMIN_PASSWORD secret set in Cloudflare.
// POST /api/admin/login   {password}           -> sets a 7-day session cookie (5 wrong tries per hour per visitor)
// POST /api/admin/logout
// GET  /api/admin/comments?status=pending|approved
// POST /api/admin/comments {id, action: approve|hide|delete, reply?}
import { db, json, isAdmin, makeSession, same, who, SESSION_DAYS } from '../../../lib/api.js';

const MAX_FAILS = 5, WINDOW = 3600e3;

export async function onRequest({ request, env, params }) {
  const action = (params.action || []).join('/');
  if (!env.ADMIN_PASSWORD) return json({ error: 'لم تُضبط كلمة مرور الإدارة بعد في إعدادات Cloudflare.' }, 503);

  // Admin actions only come from this site's own pages (blocks cross-site form posts).
  if (request.method === 'POST') {
    const origin = request.headers.get('origin');
    if (origin && new URL(origin).host !== new URL(request.url).host) return json({ error: 'طلب غير مسموح.' }, 403);
  }

  if (action === 'login' && request.method === 'POST') {
    const d = await db(env), h = await who(request, env), since = Date.now() - WINDOW;
    const { results } = await d.prepare('SELECT COUNT(*) AS c FROM login_fail WHERE who = ? AND at > ?').bind(h, since).all();
    if (results[0].c >= MAX_FAILS) return json({ error: 'محاولات خاطئة كثيرة. حاول مرة أخرى بعد ساعة.' }, 429);
    const { password } = await request.json().catch(() => ({}));
    if (typeof password !== 'string' || !(await same(password, env.ADMIN_PASSWORD))) {
      await d.batch([
        d.prepare('INSERT INTO login_fail (who, at) VALUES (?, ?)').bind(h, Date.now()),
        d.prepare('DELETE FROM login_fail WHERE at < ?').bind(Date.now() - 864e5),
      ]);
      await new Promise(r => setTimeout(r, 800));
      return json({ error: 'كلمة المرور غير صحيحة.' }, 401);
    }
    await d.prepare('DELETE FROM login_fail WHERE who = ?').bind(h).run();
    return json({ ok: true }, 200, { 'set-cookie': `lib_admin=${await makeSession(env)}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${SESSION_DAYS * 86400}` });
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
