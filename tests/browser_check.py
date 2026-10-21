"""Open the main pages in a real browser and report script errors and security-policy violations.
Usage: BASE=http://localhost:8788 python3 tests/browser_check.py"""
import os, sys
from playwright.sync_api import sync_playwright

BASE = os.environ.get('BASE', 'http://localhost:8788')
checks = [
    ('/', None), ('/library/', None), ('/library/?q=سعد بن عبادة', '.hit, .result, mark'),
    ('/books/saqifa/#p12', 'canvas'), ('/books/north-hijaz-jews/#p31', 'canvas'),
    ('/books/prophet-houses/', None), ('/author/', 'video'), ('/admin/', '#pw'), ('/no-such-page', None),
]
bad = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for w in (390, 1366):
        pg = b.new_page(viewport={'width': w, 'height': 900})
        errs = []
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        for path, sel in checks:
            errs.clear()
            pg.goto(BASE + path, wait_until='load')
            ok_sel = True
            if sel:
                try: pg.wait_for_selector(sel, timeout=12000, state='attached')
                except Exception: ok_sel = False
            pg.wait_for_timeout(800)
            hscroll = pg.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
            # Expected: the 404 page itself, the admin API refusing a visitor who has not logged in,
            # and outside resources (YouTube thumbnails) when the test machine has no internet access.
            errs = [e for e in errs if not ('404' in e and path == '/no-such-page') and not ('401' in e and path == '/admin/')
                    and 'ERR_TUNNEL_CONNECTION_FAILED' not in e and 'ERR_NAME_NOT_RESOLVED' not in e]
            status = 'ok' if not errs and ok_sel and not hscroll else 'FAIL'
            bad += status != 'ok'
            print(f'{w:>4} {status:4} {path} {"(missing " + sel + ")" if not ok_sel else ""} {"(horizontal scroll)" if hscroll else ""} {errs[:3] if errs else ""}')
        pg.close()
    b.close()
sys.exit(1 if bad else 0)
