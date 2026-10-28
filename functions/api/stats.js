// GET  /api/stats            -> { slug: { download: n, read: n }, ... }
// POST /api/stats {slug,kind} -> counts one read or download (once per visitor per work per day)
import { db, isSlug, json, who, today } from '../../lib/api.js';

const BOT = /HeadlessChrome|Lighthouse|PageSpeed|bot\/|crawl|spider|slurp|curl\/|wget|python-requests|playwright|puppeteer/i;

export async function onRequestGet({ env }) {
  const d = await db(env);
  const { results } = await d.prepare('SELECT slug, kind, n FROM counts').all();
  const out = {};
  for (const r of results) (out[r.slug] ??= {})[r.kind] = r.n;
  return json(out, 200, { 'cache-control': 'public, max-age=60' });
}

export async function onRequestPost({ request, env }) {
  let body;
  try { body = await request.json(); } catch { return json({ error: 'bad request' }, 400); }
  const { slug, kind } = body || {};
  if (!isSlug(slug) || !['read', 'download'].includes(kind)) return json({ error: 'bad request' }, 400);
  // Automated browsers and crawlers (including the site's own checks) are not counted.
  if (BOT.test(request.headers.get('user-agent') || '')) return json({ ok: true, counted: false });
  const d = await db(env);
  const key = `${today()}|${await who(request, env)}|${slug}|${kind}`;
  const first = await d.prepare('INSERT OR IGNORE INTO seen (key, day) VALUES (?, ?)').bind(key, today()).run();
  if (first.meta.changes) {
    await d.prepare('INSERT INTO counts (slug, kind, n) VALUES (?, ?, 1) ON CONFLICT(slug, kind) DO UPDATE SET n = n + 1')
      .bind(slug, kind).run();
    // keep the de-duplication table small
    await d.prepare('DELETE FROM seen WHERE day < ?').bind(today()).run();
  }
  return json({ ok: true });
}
