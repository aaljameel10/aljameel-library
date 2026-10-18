// GET  /api/comments?slug=…  -> approved comments for one work, oldest first
// POST /api/comments {slug,name,body,website,t} -> stores a comment as "pending" until the family approves it
import { db, isSlug, json, who } from '../../lib/api.js';

const clean = s => String(s || '').replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g, '').trim();

export async function onRequestGet({ request, env }) {
  const slug = new URL(request.url).searchParams.get('slug');
  if (!isSlug(slug)) return json({ error: 'bad request' }, 400);
  const d = await db(env);
  const { results } = await d.prepare(
    "SELECT id, name, body, created, reply FROM comments WHERE slug = ? AND status = 'approved' ORDER BY id ASC LIMIT 300"
  ).bind(slug).all();
  return json(results);
}

export async function onRequestPost({ request, env }) {
  let b;
  try { b = await request.json(); } catch { return json({ error: 'تعذّر قراءة التعليق. أعد المحاولة.' }, 400); }
  const slug = b?.slug, name = clean(b?.name), body = clean(b?.body);
  // Spam traps: a hidden field people never fill, and a minimum time on the page.
  if (b?.website || (Number(b?.t) > 0 && Number(b.t) < 4000)) return json({ ok: true });
  if (!isSlug(slug)) return json({ error: 'طلب غير صالح.' }, 400);
  if (name.length < 2 || name.length > 60) return json({ error: 'اكتب اسماً من حرفين إلى ٦٠ حرفاً.' }, 400);
  if (body.length < 5 || body.length > 2000) return json({ error: 'اكتب تعليقاً من ٥ أحرف إلى ٢٠٠٠ حرف.' }, 400);
  if ((body.match(/https?:\/\//g) || []).length > 2) return json({ error: 'التعليق يحتوي روابط كثيرة.' }, 400);
  const d = await db(env);
  const h = await who(request, env);
  const { results } = await d.prepare(
    "SELECT COUNT(*) AS c FROM comments WHERE who = ? AND created > datetime('now', '-1 hour')"
  ).bind(h).all();
  if (results[0].c >= 5) return json({ error: 'أرسلت تعليقات كثيرة خلال ساعة. حاول لاحقاً.' }, 429);
  await d.prepare("INSERT INTO comments (slug, name, body, created, status, who) VALUES (?, ?, ?, datetime('now'), 'pending', ?)")
    .bind(slug, name, body, h).run();
  return json({ ok: true });
}
