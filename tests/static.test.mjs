// Checks on the built site in public/: every work has its page, PDF, cover and search data,
// the API accepts exactly the published works, and old addresses redirect to pages that exist.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { SLUGS } from '../lib/slugs.js';

const pub = p => new URL('../public/' + p, import.meta.url);
const read = p => readFileSync(pub(p), 'utf8');

test('the API slug list matches the published work pages', () => {
  const pages = readdirSync(pub('books')).filter(d => existsSync(pub(`books/${d}/index.html`))).sort();
  assert.deepEqual([...SLUGS].sort(), pages);
  assert.equal(new Set(SLUGS).size, SLUGS.length, 'no duplicate slugs');
});

test('every work has a PDF, a search index and a sitemap entry', () => {
  const sitemap = read('sitemap.xml');
  for (const s of SLUGS) {
    const html = read(`books/${s}/index.html`);
    assert.ok(existsSync(pub(`pdfs/${s}.pdf`)), `pdf for ${s}`);
    assert.ok(sitemap.includes(`/books/${s}/`), `sitemap has ${s}`);
    assert.match(html, new RegExp(`citation_pdf_url" content="https://mjalameellibrary.com/pdfs/${s}.pdf"`), `scholar tag for ${s}`);
  }
  const indexes = readdirSync(pub('data/search')).filter(f => f.endsWith('.json'));
  assert.equal(indexes.length, SLUGS.length, 'one search index per work');
  for (const f of indexes) {
    const pages = JSON.parse(read('data/search/' + f));
    assert.ok(Array.isArray(pages) && pages.length > 0, `${f} has pages`);
    for (const [p, t] of pages) assert.ok(Number.isInteger(p) && p > 0 && typeof t === 'string', `${f} page ${p}`);
  }
});

test('page anchors in the contents point inside each PDF', () => {
  for (const s of SLUGS) {
    const html = read(`books/${s}/index.html`);
    const ar = (html.match(/<dd>([٠-٩]+) صفحة،/) || [])[1];
    assert.ok(ar, `${s} shows its page count`);
    const total = +ar.replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));
    for (const m of html.matchAll(/#p(\d+)"/g)) assert.ok(+m[1] >= 1 && +m[1] <= total, `${s} #p${m[1]} within ${total}`);
  }
});

test('old addresses redirect to pages that exist', () => {
  for (const line of read('_redirects').trim().split('\n')) {
    const [, to] = line.split(/\s+/);
    const path = to.split('#')[0].replace(/^\//, '');
    assert.ok(path === '' || existsSync(pub(path.endsWith('/') ? path + 'index.html' : path)), `${line}`);
  }
});

test('pages carry no inline scripts, so the strict content security policy holds', () => {
  const headers = read('_headers');
  assert.match(headers, /Content-Security-Policy: default-src 'self'; script-src 'self'[^;]*;/);
  for (const p of ['index.html', 'library/index.html', 'author/index.html', 'admin/index.html', ...SLUGS.map(s => `books/${s}/index.html`)]) {
    const html = read(p);
    const inline = [...html.matchAll(/<script(?![^>]*\bsrc=)(?![^>]*type="application\/(?:ld\+)?json")[^>]*>/g)];
    assert.equal(inline.length, 0, `inline script in ${p}`);
    assert.doesNotMatch(html, /\son[a-z]+="/, `inline event handler in ${p}`);
  }
});
