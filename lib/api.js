// Shared helpers for the library's small API (Cloudflare Pages Functions + D1).
// The database binding is named DB. Tables are created on first use, so no manual setup is needed.

const SLUGS = new Set([
  'women-around-prophet', 'mawali-rasul', 'mashahir-mawali', 'prophet-wives', 'ghazwat-usra',
  'prophet-jews-expulsion', 'prophet-houses', 'prophet-sham-trip', 'umar-dhimma-expulsion',
  'rasool-madina-critique', 'prophet-jews', 'islam-umar', 'ibn-alhaj-education', 'hijra-habasha',
  'andalus-education-terms', 'food-drink', 'women-jewelry', 'clothing', 'vessels', 'furnishings',
  'abbasid-libraries', 'islamic-rings',
]);

// Download counts carried over from the previous site, so the counters do not restart at zero.
const SEED = {
  'women-around-prophet': 6, 'mawali-rasul': 9, 'mashahir-mawali': 8, 'prophet-wives': 14,
  'prophet-jews-expulsion': 2, 'ghazwat-usra': 2, 'prophet-houses': 7, 'prophet-sham-trip': 3,
  'umar-dhimma-expulsion': 3, 'rasool-madina-critique': 2, 'prophet-jews': 1, 'islam-umar': 6,
  'ibn-alhaj-education': 0, 'hijra-habasha': 1, 'andalus-education-terms': 2, 'food-drink': 4,
  'women-jewelry': 3, 'clothing': 3, 'vessels': 6, 'furnishings': 5, 'abbasid-libraries': 4, 'islamic-rings': 8,
};

let ready = false;
export async function db(env) {
  if (!env.DB) throw new Error('DB binding missing');
  if (ready) return env.DB;
  await env.DB.batch([
    env.DB.prepare('CREATE TABLE IF NOT EXISTS counts (slug TEXT NOT NULL, kind TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (slug, kind))'),
    env.DB.prepare('CREATE TABLE IF NOT EXISTS seen (key TEXT PRIMARY KEY, day TEXT NOT NULL)'),
    env.DB.prepare(`CREATE TABLE IF NOT EXISTS comments (
      id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT NOT NULL, name TEXT NOT NULL, body TEXT NOT NULL,
      created TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', who TEXT, reply TEXT)`),
    env.DB.prepare('CREATE INDEX IF NOT EXISTS comments_slug ON comments (slug, status)'),
  ]);
  const { results } = await env.DB.prepare('SELECT COUNT(*) AS c FROM counts').all();
  if (!results[0].c) {
    await env.DB.batch(Object.entries(SEED).map(([s, n]) =>
      env.DB.prepare("INSERT OR IGNORE INTO counts (slug, kind, n) VALUES (?, 'download', ?)").bind(s, n)));
  }
  ready = true;
  return env.DB;
}

export const isSlug = s => SLUGS.has(s);

export function json(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...extra },
  });
}

// A one-way hash of the visitor's address, used only to stop repeat counting and comment flooding.
export async function who(request, env) {
  const ip = request.headers.get('cf-connecting-ip') || '0';
  const salt = env.ADMIN_PASSWORD || 'library';
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(salt + '|' + ip));
  return [...new Uint8Array(buf)].slice(0, 12).map(b => b.toString(16).padStart(2, '0')).join('');
}

export const today = () => new Date().toISOString().slice(0, 10);

/* ---- admin session: a signed cookie, valid for 30 days ---- */
async function sign(value, secret) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(value));
  return [...new Uint8Array(sig)].map(b => b.toString(16).padStart(2, '0')).join('');
}
export async function makeSession(env) {
  const exp = Date.now() + 30 * 864e5;
  return `${exp}.${await sign(String(exp), env.ADMIN_PASSWORD)}`;
}
export async function isAdmin(request, env) {
  if (!env.ADMIN_PASSWORD) return false;
  const m = (request.headers.get('cookie') || '').match(/(?:^|;\s*)lib_admin=([^;]+)/);
  if (!m) return false;
  const [exp, sig] = m[1].split('.');
  if (!exp || +exp < Date.now()) return false;
  return sig === await sign(exp, env.ADMIN_PASSWORD);
}
