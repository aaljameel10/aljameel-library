// Integration tests for the API. Run against a local server started with `npm run dev`
// and a throwaway ADMIN_PASSWORD in .dev.vars (never the real one):
//   BASE=http://localhost:8788 ADMIN_TEST_PASSWORD=... npm run test:api
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { SLUGS } from '../lib/slugs.js';

const BASE = process.env.BASE || 'http://localhost:8788';
const PW = process.env.ADMIN_TEST_PASSWORD;
const post = (path, body, headers = {}) => fetch(BASE + path, {
  method: 'POST', headers: { 'content-type': 'application/json', ...headers }, body: JSON.stringify(body),
});

test('stats accept every published work and reject unknown ones', async () => {
  for (const slug of SLUGS) assert.equal((await post('/api/stats', { slug, kind: 'read' })).status, 200, slug);
  assert.equal((await post('/api/stats', { slug: 'not-a-book', kind: 'download' })).status, 400);
  assert.equal((await post('/api/stats', { slug: SLUGS[0], kind: 'bogus' })).status, 400);
});

test('a visitor is counted once per work per day', async () => {
  const slug = SLUGS[SLUGS.length - 1];
  const count = async () => ((await (await fetch(BASE + '/api/stats')).json())[slug] || {}).download || 0;
  const before = await count();
  await post('/api/stats', { slug, kind: 'download' });
  await post('/api/stats', { slug, kind: 'download' });
  await post('/api/stats', { slug, kind: 'download' });
  assert.ok((await count()) - before <= 1);
});

test('comments are validated and held for approval', async () => {
  const slug = SLUGS[0];
  assert.equal((await post('/api/comments', { slug, name: 'ا', body: 'تعليق تجريبي', t: 9000 })).status, 400, 'short name');
  assert.equal((await post('/api/comments', { slug, name: 'قارئ', body: 'قص', t: 9000 })).status, 400, 'short body');
  assert.equal((await post('/api/comments', { slug, name: 'قارئ', body: 'x'.repeat(2001), t: 9000 })).status, 400, 'long body');
  assert.equal((await post('/api/comments', { slug: 'nope', name: 'قارئ', body: 'تعليق تجريبي', t: 9000 })).status, 400, 'bad slug');
  // Bots: a filled hidden field or a too-quick submit is accepted silently but never stored.
  const trap = '<script>alert(1)</script> فخ';
  assert.equal((await post('/api/comments', { slug, name: 'روبوت', body: trap, website: 'x', t: 9000 })).status, 200);
  assert.equal((await post('/api/comments', { slug, name: 'روبوت', body: trap })).status, 200);
  const ok = await post('/api/comments', { slug, name: 'قارئ تجريبي', body: 'تعليق تجريبي للاختبار', t: 9000 });
  assert.equal(ok.status, 200);
  const shown = await (await fetch(`${BASE}/api/comments?slug=${slug}`)).json();
  assert.ok(!shown.some(c => c.body === 'تعليق تجريبي للاختبار'), 'not public before approval');
});

test('admin endpoints refuse visitors without a session', async () => {
  assert.equal((await fetch(BASE + '/api/admin/comments?status=pending')).status, 401);
  assert.equal((await post('/api/admin/comments', { id: 1, action: 'delete' })).status, 401);
  assert.equal((await fetch(BASE + '/api/admin/comments', { headers: { cookie: 'lib_admin=9999999999999.forged' } })).status, 401);
  assert.equal((await post('/api/admin/login', { password: 'x' }, { origin: 'https://evil.example' })).status, 403, 'cross-site post');
});

test('admin login: right password works, repeated wrong ones are locked out', { skip: !PW && 'set ADMIN_TEST_PASSWORD' }, async () => {
  const good = await post('/api/admin/login', { password: PW });
  assert.equal(good.status, 200);
  const cookie = good.headers.get('set-cookie');
  assert.match(cookie, /HttpOnly/); assert.match(cookie, /Secure/); assert.match(cookie, /SameSite=Strict/); assert.match(cookie, /Max-Age=604800/);
  const session = cookie.split(';')[0];
  const list = await fetch(BASE + '/api/admin/comments?status=pending', { headers: { cookie: session } });
  assert.equal(list.status, 200);
  const pending = (await list.json()).comments.find(c => c.body === 'تعليق تجريبي للاختبار');
  if (pending) {
    assert.equal((await post('/api/admin/comments', { id: pending.id, action: 'approve', reply: 'شكراً' }, { cookie: session })).status, 200);
    const shown = await (await fetch(`${BASE}/api/comments?slug=${SLUGS[0]}`)).json();
    assert.ok(shown.some(c => c.id === pending.id && c.reply === 'شكراً'), 'visible after approval');
    assert.equal((await post('/api/admin/comments', { id: pending.id, action: 'delete' }, { cookie: session })).status, 200);
  }
  const codes = [];
  for (let i = 0; i < 6; i++) codes.push((await post('/api/admin/login', { password: 'wrong-' + i })).status);
  assert.deepEqual(codes, [401, 401, 401, 401, 401, 429]);
  assert.equal((await post('/api/admin/login', { password: PW })).status, 429, 'locked even with the right password');
});
