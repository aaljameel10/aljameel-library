"""Static site generator for the Al-Jameel library.

Reads the content files in ../library/content and writes a complete static site to dist/.
Run:  python3 build.py
"""
import html, json, os, re, shutil, subprocess
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, '..', 'library')
C = os.path.join(LIB, 'content')
DIST = os.environ.get('DIST') or os.path.join(HERE, 'dist')
SITE = 'https://mjalameellibrary.com'

THEMES = {
    'sira': 'السيرة النبوية ومجتمع المدينة',
    'yahud': 'النبي ﷺ واليهود وأهل الذمة',
    'madi': 'الحياة اليومية في العهد النبوي',
    'hadara': 'التعليم والحضارة الإسلامية',
}
THEME_SHORT = {'sira': 'السيرة ومجتمع المدينة', 'yahud': 'النبي ﷺ واليهود', 'madi': 'الحياة اليومية', 'hadara': 'التعليم والحضارة'}
TYPES = {'book': 'كتاب', 'research': 'بحث محكّم', 'article': 'مقال نقدي'}
TYPES_PL = {'all': 'الكل', 'book': 'كتب', 'research': 'أبحاث محكّمة', 'article': 'مقالات'}
AUTHOR = 'د. محمد بن فارس الجميل'

e = html.escape
ar = lambda n: str(n).translate(str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩'))


def load(name, default):
    p = os.path.join(C, name)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else default


def pdf_pages(path):
    try:
        out = subprocess.run(['pdfinfo', path], capture_output=True, text=True).stdout
        return int(re.search(r'Pages:\s+(\d+)', out).group(1))
    except Exception:
        return 0


def works():
    base = load('base.json', [])
    toc, research, summ = load('toc.json', {}), load('research.json', {}), load('summaries.json', {})
    cites = load('cite.json', {})
    out = []
    for w in base:
        i = w['id']
        w = dict(w)
        t, r, s = toc.get(i, {}), research.get(i, {}), summ.get(i, {})
        w['toc'] = t.get('items', [])
        w['offset'] = t.get('offset', 0)
        w['edition'] = t.get('meta') or r.get('venue', '')
        w['pages_range'] = r.get('pages', '')
        w['cite'] = cites.get(i, {'kind': 'unknown'})
        w['summary'] = s.get('summary', '')
        w['findings'] = s.get('findings', [])
        w['quotes'] = s.get('quotes') or ([s['quote']] if s.get('quote') else [])
        w['pdf'] = f'/pdfs/{w["slug"]}.pdf'
        for folder in ('web', 'fixed', 'pdfs'):   # web = re-encoded heavy scans, fixed = upright copies, pdfs = originals
            w['_src'] = os.path.join(LIB, folder, f'{i}.pdf')
            if os.path.exists(w['_src']):
                break
        w['npages'] = pdf_pages(w['_src'])
        w['mb'] = round(os.path.getsize(w['_src']) / 1048576, 1) if os.path.exists(w['_src']) else 0
        w['cover'] = f'/covers/{w["slug"]}.webp' if os.path.exists(os.path.join(LIB, 'covers', f'{i}.webp')) else ''
        out.append(w)
    return out


STAR = '<svg class="{cls}" viewBox="0 0 40 40" fill="none" stroke="{c}" stroke-width="1.4" aria-hidden="true"><rect x="8" y="8" width="24" height="24"/><rect x="8" y="8" width="24" height="24" transform="rotate(45 20 20)"/><circle cx="20" cy="20" r="3.2"/></svg>'
MARK = '<svg class="brand-mark" viewBox="0 0 44 44" aria-hidden="true"><rect width="44" height="44" rx="4" fill="#13233A"/><g fill="none" stroke="#D9B26A" stroke-width="1.6"><rect x="12" y="12" width="20" height="20"/><rect x="12" y="12" width="20" height="20" transform="rotate(45 22 22)"/></g><circle cx="22" cy="22" r="3" fill="#D9B26A"/></svg>'
ICON = {
    'read': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 5h7a3 3 0 0 1 3 3v12a2 2 0 0 0-2-2H2z"/><path d="M22 5h-7a3 3 0 0 0-3 3v12a2 2 0 0 1 2-2h8z"/></svg>',
    'down': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v12"/><path d="M7 10l5 5 5-5"/><path d="M5 21h14"/></svg>',
    'search': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>',
    'next': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>',
    'prev': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>',
    'full': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>',
}


def cover(w, lg=False, link=True):
    inner = (f'<span class="c-top"><span>{e(TYPES[w["type"]])}</span><span>{ar(w["year"])}</span></span>'
             f'<span>{STAR.format(cls="c-star", c="#D9B26A")}<span class="c-title">{e(w["title"])}</span></span>'
             f'<span class="c-author">محمد بن فارس الجميل</span>')
    cls = f'cover t-{w["theme"]}' + (' lg' if lg else '')
    if link:
        return f'<a class="{cls}" href="/books/{w["slug"]}/" aria-label="{e(w["title"])}" tabindex="-1">{inner}</a>'
    return f'<div class="{cls}" aria-hidden="true">{inner}</div>'


def page(path, title, desc, body, current='', extra_head='', scripts='', og_image='/og.jpg', jsonld=None):
    url = SITE + path
    nav = [('/', 'الرئيسية', 'home'), ('/library/', 'المكتبة', 'library'),
           ('/library/?type=research', 'الأبحاث المحكّمة', 'research'), ('/author/', 'عن المؤلف', 'author')]
    navh = ''.join(f'<a href="{h}"{" aria-current=page" if k == current else ""}>{t}</a>' for h, t, k in nav)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ''
    full_title = title if 'مكتبة' in title and current == 'home' else f'{title} | مكتبة د. محمد الجميل'
    return f'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:locale" content="ar_SA">
<meta property="og:site_name" content="مكتبة الدكتور محمد بن فارس الجميل">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#13233A">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/fonts/ibm-plex-sans-arabic-arabic-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/amiri-arabic-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts.css">
<link rel="stylesheet" href="/assets/site.css">
{extra_head}{ld}
</head>
<body>
<a class="sr" href="#main">تخطَّ إلى المحتوى</a>
<header class="site-head"><div class="wrap">
<a class="brand" href="/">{MARK}<span class="brand-name">مكتبة الدكتور محمد الجميل<span class="brand-sub">السيرة النبوية والتاريخ الإسلامي</span></span></a>
<nav class="nav" aria-label="القائمة الرئيسية">{navh}</nav>
</div></header>
<main id="main">
{body}
</main>
<footer class="site-foot">
<div class="wrap">
<div><h2>مكتبة الدكتور محمد الجميل</h2><p>كتب الدكتور محمد بن فارس الجميل وأبحاثه المحكّمة في السيرة النبوية والتاريخ الإسلامي، متاحة للقراءة والتحميل مجاناً لأغراض البحث والتعلّم.</p></div>
<div><h3>تصفّح</h3><ul><li><a href="/library/">المكتبة كاملة</a></li><li><a href="/library/?type=book">الكتب</a></li><li><a href="/library/?type=research">الأبحاث المحكّمة</a></li><li><a href="/author/">عن المؤلف</a></li></ul></div>
<div><h3>التواصل</h3><ul><li>الرياض، المملكة العربية السعودية</li><li><a href="mailto:maljameel47@gmail.com">maljameel47@gmail.com</a></li><li><a href="https://x.com/dr_mjameel" target="_blank" rel="noopener me">حسابه على منصة X</a></li></ul></div>
</div>
<div class="wrap foot-base">© {ar(date.today().year)} مكتبة الدكتور محمد بن فارس الجميل. حقوق النشر محفوظة للمؤلف وناشري الطبعات الأصلية.</div>
</footer>
{scripts}
</body>
</html>'''


def work_card(w):
    sub = f'<p class="sub">{e(w["subtitle"])}</p>' if w['subtitle'] else ''
    pub = f'<p class="pub">{e(TYPES[w["type"]])}، {ar(w["year"])}م' + (f'، {e(w["publisher"])}' if w['publisher'] else '') + '</p>'
    return (f'<article class="work" data-id="{w["id"]}">{cover(w)}'
            f'<h3><a href="/books/{w["slug"]}/">{e(w["title"])}</a></h3>{sub}{pub}'
            f'<div class="acts"><a class="btn" href="/books/{w["slug"]}/#p1">اقرأ</a>'
            f'<a class="btn ghost" href="{w["pdf"]}" download data-dl="{w["slug"]}" aria-label="تحميل {e(w["title"])} بصيغة PDF">{ICON["down"]}PDF</a></div>'
            f'<p class="pub" data-count-wrap hidden>مرات التحميل: <span data-count="{w["slug"]}:download"></span></p></article>')


def citation(w):
    t = w['title'] + (f': {w["subtitle"]}' if w['subtitle'] and not w['subtitle'].startswith('(') else (f' {w["subtitle"]}' if w['subtitle'] else ''))
    if w['type'] == 'book':
        pub = w['publisher'] or ''
        return f'الجميل، محمد بن فارس. {t}. {pub}، {ar(w["year"])}م.'
    venue = w['edition'] or w['publisher']
    if not venue:   # publication venue not documented: cite title and year only
        return f'الجميل، محمد بن فارس. «{t}». {ar(w["year"])}م.'
    pr = f'، {w["pages_range"]}' if w['pages_range'] else ''
    return f'الجميل، محمد بن فارس. «{t}». {venue}{pr}.'.replace('..', '.')


VIDEOS = [
    {'mp4': '/media/hubasha.mp4', 'poster': '/media/hubasha.jpg',
     'title': 'سوق حُباشة: حيث تاجر النبي ﷺ لخديجة رضي الله عنها قبل الإسلام',
     'note': 'يتحدث الدكتور الجميل عن سوق حُباشة في ديار قبائل بارق، الذي باع فيه النبي ﷺ واشترى لخديجة رضي الله عنها قبل الإسلام. من لقاء على قناة الزاهرة.'},
    {'yt': 'xeZ7R3uBWQs', 'title': 'هل تمت تصفية يهود بني قريظة في المدينة؟',
     'note': 'لقاء على قناة الزاهرة.', 'book': 'prophet-jews'},
    {'yt': 'FnA1EkcuKJM', 'title': 'هل كان إجلاء اليهود من المدينة بقرار من الرسول ﷺ؟',
     'note': 'لقاء على قناة الزاهرة.', 'book': 'prophet-jews-expulsion'},
    {'yt': 'O01Dt5CxHV8', 'title': 'عام الوفود وآخر غزوة غزاها الرسول ﷺ: ماذا كان اسمها وإلى أين وجهتها؟',
     'note': 'لقاء على قناة الزاهرة.', 'book': 'ghazwat-usra'},
    {'yt': 'yY-IxGi09x8', 'title': 'بيوت النبي ﷺ وحجراته', 'book': 'prophet-houses',
     'note': 'لقاء يتحدث فيه الدكتور الجميل عن بيوت النبي ﷺ وحجراته.'},
]
PLAY = '<span class="play"><span><svg width="26" height="26" viewBox="0 0 24 24" fill="#fff" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg></span></span>'
YT_JS = '<script type="module" src="/assets/yt.js"></script>'


def video_html(v):
    if v.get('mp4'):
        player = (f'<div class="video"><video controls preload="none" playsinline poster="{v["poster"]}" aria-label="{e(v["title"])}">'
                  f'<source src="{v["mp4"]}" type="video/mp4"></video></div>')
    else:
        player = (f'<div class="video" data-yt="{v["yt"]}"><button type="button" aria-label="شغّل لقاء: {e(v["title"])}">'
                  f'<img src="https://img.youtube.com/vi/{v["yt"]}/hqdefault.jpg" alt="" loading="lazy">{PLAY}</button></div>')
    more = ''
    if v.get('book') and v['book'] in TITLE_OF:
        more = f' <a href="/books/{v["book"]}/">اقرأ المزيد في «{e(TITLE_OF[v["book"]])}»</a>'
    return f'<figure class="talk">{player}<figcaption><h3>{e(v["title"])}</h3><p>{e(v["note"])}{more}</p></figcaption></figure>'


def cite_styles(w):
    """APA 7 and Chicago (bibliography) entries built only from the documented fields in cite.json.
    Returns [(label, html)]; italics mark the journal or book title, as each style requires."""
    c, y = w['cite'], w['cite'].get('year') or w['year']
    sub = w['subtitle'] or ''
    title = c.get('title') or (w['title'] + (f' {sub}' if sub.startswith('(') else f': {sub}' if sub else ''))
    i = lambda t: f'<i>{e(t)}</i>'
    author_apa, author_chi = 'الجميل، م. ف.', 'الجميل، محمد بن فارس.'
    if c.get('original_author'):
        last, first = c['original_author']
        author_apa, author_chi = f'{last}، {first[0]}.', f'{last}، {first}.'
    tr_apa = ' (م. ف. الجميل، مترجم)' if c.get('original_author') else ''
    tr_chi = ' ترجمة محمد بن فارس الجميل.' if c.get('original_author') else ''
    k = c['kind']
    if k == 'article':
        vol, iss, pg = c.get('volume'), c.get('issue'), c.get('pages')
        loc_apa = (f'، {vol}' + (f'({iss})' if iss else '') if vol else (f'، العدد {iss}' if iss else '')) + (f'، {pg}' if pg else '')
        apa = f'{e(author_apa)} ({y}). {e(title)}{e(tr_apa)}. {i(c["journal"])}{e(loc_apa)}.'
        loc_chi = (f' {vol}' if vol else '') + (f'، العدد {iss}' if iss else '')
        chi = f'{e(author_chi)} «{e(title)}».{e(tr_chi)} {i(c["journal"])}{e(loc_chi)} ({y})' + (f': {e(pg)}' if pg else '') + '.'
    elif k == 'chapter':
        apa = f'{e(author_apa)} ({y}). {e(title)}. في {i(c["book"])} (ص. {e(c["pages"])}). {e(c["publisher"])}.'
        chi = f'{e(author_chi)} «{e(title)}». في {i(c["book"])}، {e(c["pages"])}. {e(c["publisher"])}، {y}.'
    elif k == 'book':
        ed_apa = f' (ط. {c["edition"]})' if c.get('edition') else ''
        ser = f' ({e(c["series"])})' if c.get('series') else ''
        apa = f'{e(author_apa)} ({y}). {i(title)}{e(ed_apa)}{ser}. {e(c["publisher"])}.'
        ed_chi = f' ط. {c["edition"]}.' if c.get('edition') else ''
        ser_chi = f' {e(c["series"])}.' if c.get('series') else ''
        chi = f'{e(author_chi)} {i(title)}.{e(ed_chi)}{ser_chi} {e(c["place"])}: {e(c["publisher"])}، {y}.'
    else:   # publication venue not documented: author, year and title only
        apa = f'{e(author_apa)} ({y}). {i(title)}.'
        chi = f'{e(author_chi)} {i(title)}. {y}.'
    return [('APA (الإصدار السابع)', apa), ('شيكاغو', chi)]


def build_home(W):
    by = {w['id']: w for w in W}
    latest = sorted(W, key=lambda w: -w['year'])[:4]
    feat = by['30001']
    topics = ['يهود المدينة', 'الهجرة إلى الحبشة', 'أزواج النبي', 'اللباس', 'بيت عائشة']
    themes = ''
    for k, name in THEMES.items():
        ws = [w for w in W if w['theme'] == k]
        lis = ''.join(f'<li>{e(w["title"])}</li>' for w in sorted(ws, key=lambda w: -w['year'])[:4])
        themes += (f'<a class="theme" href="/library/?theme={k}"><span class="swatch t-{k}"></span>'
                   f'<h3>{e(name)}</h3><span class="n">{ar(len(ws))} مؤلفات</span><ul>{lis}</ul></a>')
    tl = [('١٣٦٧هـ', 'المولد في محافظة الزلفي'), ('١٩٨٥م', 'الدكتوراه من جامعة ميشيغان، وبدء التدريس في جامعة الملك سعود'),
          ('١٩٨٩م', 'أقدم أبحاثه في المكتبة: «الخواتم الإسلامية في القرنين الأول والثاني الهجريين» و«المكتبات العربية في العصر العباسي»'),
          ('٢٠٠٢م', 'كتاب «النبي ﷺ ويهود المدينة» عن مركز الملك فيصل للبحوث والدراسات الإسلامية'),
          ('٢٠١٢م', 'جائزة الملك سلمان لدراسات تاريخ الجزيرة العربية عن كتاب «بيوت النبي ﷺ وحجراتها»'),
          ('٢٠١٣م', 'التقاعد من جامعة الملك سعود'),
          ('٢٠١٧م', 'جائزة الملك سلمان التقديرية للمتميزين في خدمة تاريخ الجزيرة العربية'),
          ('٢٠٢١م', 'صدور «موالي رسول الله ﷺ وأزواجه وخدمهم من النساء»')]
    tlh = ''.join(f'<li><span class="y">{y}</span><span>{e(t)}</span></li>' for y, t in tl)
    q = by['22']['quotes'][-1] if by['22']['quotes'] else None
    quote = (f'<section class="sec sand"><div class="wrap quote">{STAR.format(cls="star", c="#8A5F17")}'
             f'<blockquote>«{e(q["t"])}»</blockquote><cite>من كتاب «نساء حول النبي ﷺ»، {e(q["p"])}. '
             f'<a href="/books/{by["22"]["slug"]}/">اقرأ الكتاب</a></cite></div></section>') if q else ''
    feat_text = feat['summary'] or 'دراسة لبيوت النبي ﷺ وحجراتها ومواقعها وصفتها، تتخذ من بيت عائشة أنموذجاً، وتتناول أثاث البيوت ومتاعها ومعاش النبي ﷺ وأزواجه.'
    body = f'''
<section class="hero"><div class="wrap">
<div>
<p class="hero-role">أستاذ تاريخ الحضارة الإسلامية في جامعة الملك سعود سابقاً</p>
<h1>محمد بن فارس الجميل</h1>
<p class="hero-lead">أكثر من ثلاثين عاماً من البحث في السيرة النبوية والحياة اليومية في المدينة المنورة، مجموعة هنا في مكتبة واحدة. اقرأ الكتب كاملة، أو حمّلها، أو ابحث في نصوصها.</p>
<form class="search" role="search" action="/library/" method="get">
<label class="sr" for="hq">ابحث في المكتبة</label>
<input id="hq" name="q" type="search" placeholder="ابحث في العناوين ونصوص الكتب، مثلاً: الهجرة إلى الحبشة">
<button class="btn" type="submit">{ICON["search"]}بحث</button>
</form>
<div class="chips"><span>جرّب:</span>{"".join(f'<a class="chip" href="/library/?q={e(t)}">{e(t)}</a>' for t in topics)}</div>
</div>
<figure class="portrait"><img src="/img/portrait.jpg" alt="الدكتور محمد بن فارس الجميل" width="400" height="500">
<figcaption>حائز على جائزة الملك سلمان لدراسات تاريخ الجزيرة العربية عامي ٢٠١٢ و٢٠١٧م</figcaption></figure>
</div></section>

<section class="facts" aria-label="المكتبة بالأرقام"><div class="wrap"><dl>
<div><dt>كتاباً وبحثاً متاحة كاملة</dt><dd>{ar(len(W))}</dd></div>
<div><dt>صفحة قابلة للبحث</dt><dd>{ar(f"{sum(w['npages'] for w in W):,}".replace(",", "٬"))}</dd></div>
<div><dt>سنوات النشر</dt><dd>{ar(min(w["year"] for w in W))}–{ar(max(w["year"] for w in W))}</dd></div>
<div><dt>مرتان: جائزة الملك سلمان</dt><dd>٢٠١٢ و٢٠١٧</dd></div>
</dl></div></section>

<section class="sec band feature"><div class="wrap">
<div>{cover(feat, lg=True, link=False)}</div>
<div>
<p class="feature-kicker">الكتاب الفائز بجائزة الملك سلمان ٢٠١٢م</p>
<h2>{e(feat["title"])}</h2>
<p>{e(feat_text)}</p>
<p class="meta">{e(feat["publisher"])}، ١٤٣١هـ / ٢٠١٠م</p>
<div class="actions"><a class="btn gold" href="/books/{feat["slug"]}/#p1">{ICON["read"]}اقرأ الكتاب</a><a class="btn light" href="/books/{feat["slug"]}/">عن الكتاب</a></div>
</div>
</div></section>

<section class="sec"><div class="wrap">
<div class="sec-head"><div><h2>تصفّح حسب الموضوع</h2><p>{ar(len(W))} عنواناً في أربعة محاور</p></div><a class="link" href="/library/">المكتبة كاملة</a></div>
<div class="themes">{themes}</div>
</div></section>

<section class="sec" style="padding-top:0"><div class="wrap">
<div class="sec-head"><h2>أحدث المؤلفات</h2><a class="link" href="/library/">كل المؤلفات</a></div>
<div class="shelf">{"".join(work_card(w) for w in latest)}</div>
</div></section>

{quote}

<section class="sec" id="talks"><div class="wrap">
<div class="sec-head"><h2>لقاءات مصوّرة</h2></div>
<div class="talks">{"".join(video_html(v) for v in VIDEOS)}</div>
</div></section>

<section class="sec"><div class="wrap split">
<div><h2 style="font-size:38px">عن المؤلف</h2>
<p style="margin-top:14px;color:var(--text-2)">من مواليد محافظة الزلفي. درس في جامعة الملك سعود ثم في جامعتي إنديانا وميشيغان، ودرّس التاريخ والحضارة الإسلامية في جامعة الملك سعود من ١٩٨٥ حتى ٢٠١٣م. له كتب في السيرة النبوية وأكثر من عشرين بحثاً محكّماً.</p>
<p style="margin-top:14px"><a class="link" href="/author/">السيرة الذاتية الكاملة</a></p></div>
<ol class="timeline">{tlh}</ol>
</div></section>'''
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "مكتبة الدكتور محمد بن فارس الجميل", "url": SITE + '/', "inLanguage": "ar",
          "potentialAction": {"@type": "SearchAction", "target": SITE + "/library/?q={q}", "query-input": "required name=q"},
          "about": {"@type": "Person", "name": "محمد بن فارس الجميل", "jobTitle": "أستاذ التاريخ والحضارة الإسلامية", "affiliation": "جامعة الملك سعود"}}
    return page('/', 'مكتبة الدكتور محمد بن فارس الجميل: كتب السيرة النبوية والتاريخ الإسلامي',
                'كتب الدكتور محمد بن فارس الجميل وأبحاثه المحكّمة في السيرة النبوية وتاريخ المدينة المنورة والحضارة الإسلامية، للقراءة والتحميل والبحث في نصوصها.',
                body, 'home', jsonld=ld, scripts='<script type="module" src="/assets/stats.js"></script>' + YT_JS)


def build_library(W):
    data = [{k: w[k] for k in ('id', 'slug', 'title', 'subtitle', 'type', 'year', 'theme', 'publisher')} for w in W]
    types = ''.join(f'<button type="button" class="pill" data-type-btn="{k}" aria-pressed="{str(k == "all").lower()}">{v} <span class="n"></span></button>' for k, v in TYPES_PL.items())
    themes = '<button type="button" class="pill" data-theme-btn="all" aria-pressed="true">كل المحاور</button>' + ''.join(
        f'<button type="button" class="pill" data-theme-btn="{k}" aria-pressed="false"><span class="dot t-{k}"></span>{e(v)}</button>' for k, v in THEME_SHORT.items())
    body = f'''
<section class="page-title"><div class="wrap">
<nav class="crumbs" aria-label="مسار التصفح"><a href="/">الرئيسية</a> / المكتبة</nav>
<h1>المكتبة</h1>
<p>كل كتب الدكتور محمد الجميل وأبحاثه المحكّمة من {ar(min(w["year"] for w in W))} إلى {ar(max(w["year"] for w in W))}م. ابحث في العناوين أو في نصوص الكتب نفسها، واقرأ أي عمل هنا أو حمّله مجاناً.</p>
</div></section>
<section class="wrap" aria-label="البحث والتصفية">
<form id="lib-form" class="controls" role="search">
<div class="row">
<label class="sr" for="q">ابحث في المكتبة</label>
<input id="q" type="search" placeholder="ابحث في العناوين والمجلات ونصوص الكتب" autocomplete="off">
<label class="sr" for="sort">ترتيب</label>
<select id="sort"><option value="new">الأحدث أولاً</option><option value="old">الأقدم أولاً</option><option value="title">حسب العنوان</option></select>
</div>
<label class="toggle"><input id="deep" type="checkbox" checked> ابحث أيضاً داخل نصوص الكتب</label>
<div class="row" role="group" aria-label="النوع"><span class="lbl">النوع</span>{types}</div>
<div class="row" role="group" aria-label="المحور"><span class="lbl">المحور</span>{themes}</div>
</form>
<div class="status"><span id="count" aria-live="polite"></span><button type="button" id="reset" class="pill" hidden>مسح البحث والتصفية</button></div>
<div id="hits" class="hits" aria-live="polite"></div>
<div id="empty" class="empty" hidden><h2>لا توجد عناوين مطابقة</h2><p>جرّب كلمة أخرى أو امسح التصفية.</p></div>
<div id="grid" class="shelf" style="margin-bottom:96px">{"".join(work_card(w) for w in W)}</div>
</section>
<script type="application/json" id="works-data">{json.dumps(data, ensure_ascii=False)}</script>'''
    return page('/library/', 'المكتبة: كل الكتب والأبحاث', 'تصفّح كتب الدكتور محمد بن فارس الجميل وأبحاثه المحكّمة، وابحث في نصوصها، واقرأها أو حمّلها مجاناً.',
                body, 'library', scripts='<script type="module" src="/assets/library.js"></script><script type="module" src="/assets/stats.js"></script>')


def toc_html(w):
    if not w['toc']:
        return ''
    lis = ''
    for item in w['toc']:
        t, p = item[0], item[1]
        is_sub = bool(re.match(r'^[أبج]\s*-', t)) or (w['id'] == '14' and bool(re.match(r'^[١-٩]\s*-', t)))
        subcls = ' class="sub"' if is_sub else ''
        pdfp = item[2] if len(item) > 2 else int(p) + w['offset']
        lis += f'<li{subcls}><a href="#p{pdfp}" data-open-reader="{pdfp}">{e(t)}</a><span class="pg">{ar(p)}</span></li>'
    return f'<ol class="toc">{lis}</ol><p class="note">فهرس الكتاب كما ورد في طبعته، والأرقام أرقام صفحات الطبعة. اضغط أي عنوان لفتحه في القارئ.</p>'


def scholar_meta(w):
    """Highwire Press tags read by Google Scholar (one work per page, PDF on the same site)."""
    west = lambda t: t.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))
    title = w['title'] + (f': {w["subtitle"]}' if w['subtitle'] and not w['subtitle'].startswith('(') else (f' {w["subtitle"]}' if w['subtitle'] else ''))
    m = [('citation_title', title), ('citation_author', 'الجميل، محمد بن فارس'), ('citation_author_institution', 'جامعة الملك سعود'),
         ('citation_publication_date', str(w['year'])), ('citation_language', 'ar'),
         ('citation_pdf_url', SITE + w['pdf']), ('citation_abstract_html_url', f'{SITE}/books/{w["slug"]}/')]
    if w['type'] == 'book':
        if w['publisher']:
            m.append(('citation_publisher', w['publisher']))
    else:
        venue = w['edition'] or w['publisher']
        if venue:
            v = venue.split('»: ', 1)[1] if venue.startswith('«') and '»: ' in venue else venue
            conf = 'مداولات' in v or 'اللقاء' in v or 'ندوة' in v
            m.append(('citation_conference_title' if conf else 'citation_journal_title', v.split('، ')[0]))
        pr = re.findall(r'\d+', west(w['pages_range'] or ''))
        if len(pr) == 2:
            m += [('citation_firstpage', pr[0]), ('citation_lastpage', pr[1])]
    return ''.join(f'<meta name="{k}" content="{e(v)}">' for k, v in m)


def build_book(w, W):
    related = [x for x in W if x['theme'] == w['theme'] and x['id'] != w['id']][:4]
    tabs, panels = [], []

    def add(key, label, content):
        if not content:
            return
        tabs.append((key, label))
        panels.append((key, content))

    about = ''
    if w['summary']:
        about = f'<p>{e(w["summary"])}</p>'
        if w['findings']:
            about += '<h2 style="font-size:26px;margin-top:30px">أبرز ما انتهى إليه</h2><ul class="findings">' + ''.join(f'<li>{e(f)}</li>' for f in w['findings']) + '</ul>'
    add('about', 'نبذة' if w['type'] != 'book' else 'نبذة عن الكتاب', about)
    add('toc', 'الفهرس', toc_html(w))
    if w['quotes']:
        qs = ''.join(f'<figure class="excerpt"><blockquote>«{e(q["t"])}»</blockquote><figcaption>{e(q.get("p", ""))}' +
                     (f' <a href="#p{q["pdf"]}" data-open-reader="{q["pdf"]}">افتح الصفحة</a>' if q.get('pdf') else '') + '</figcaption></figure>' for q in w['quotes'])
        add('quotes', 'مقتطفات', qs)
    cite = citation(w)
    styles = ''.join(f'<p class="cite-label">{e(lbl)}</p><div class="cite-box" id="cite-{n}">{html_}</div>'
                     f'<button class="btn ghost" type="button" data-copy="cite-{n}" data-label="نسخ التوثيق">نسخ التوثيق</button>'
                     for n, (lbl, html_) in enumerate(cite_styles(w)))
    gap = ('<p class="note">لم تُذكر بيانات النشر لهذا العمل في الملف، فاقتصر التوثيق على المؤلف والعنوان والسنة.</p>'
           if w['cite']['kind'] == 'unknown' else '')
    add('cite', 'التوثيق', f'<p class="cite-label">التوثيق العربي</p><div class="cite-box" id="cite-ar">{e(cite)}</div>'
        f'<button class="btn ghost" type="button" data-copy="cite-ar" data-label="نسخ التوثيق">نسخ التوثيق</button>' + styles + gap +
        f'<p class="note">رابط هذه الصفحة: <span dir="ltr">{SITE}/books/{w["slug"]}/</span></p>')

    tabh = ''.join(f'<button class="tab" role="tab" id="tab-{k}" aria-controls="panel-{k}" aria-selected="{str(i == 0).lower()}" tabindex="{0 if i == 0 else -1}">{e(l)}</button>' for i, (k, l) in enumerate(tabs))
    panh = ''.join(f'<div class="panel" role="tabpanel" id="panel-{k}" aria-labelledby="tab-{k}"{"" if i == 0 else " hidden"}>{c}</div>' for i, (k, c) in enumerate(panels))

    facts = [('المؤلف', AUTHOR)]
    if w['publisher']:
        facts.append(('الناشر' if w['type'] == 'book' else 'نُشر في', w['publisher']))
    facts.append(('سنة النشر', f'{ar(w["year"])}م'))
    if w['edition'] and w['type'] == 'book':
        facts.append(('بيانات الطبعة المرفوعة', w['edition']))
    elif w['edition']:
        facts.append(('بيانات النشر', w['edition'] + (f'، {w["pages_range"]}' if w['pages_range'] else '')))
    if w.get('license'):
        facts.append(('مصدر الملف', w['license']))
    facts.append(('الملف', f'{ar(w["npages"])} صفحة، {ar(w["mb"])} ميجابايت'))
    ltr = lambda t: re.sub(r'((?:ISBN|ردمك)\s*)([0-9X][0-9X\- ]+[0-9X])', r'\1<bdi dir="ltr">\2</bdi>', e(t))
    counts = (f'<div data-count-wrap hidden><dt>مرات القراءة في الموقع</dt><dd data-count="{w["slug"]}:read"></dd></div>'
              f'<div data-count-wrap hidden><dt>مرات التحميل</dt><dd data-count="{w["slug"]}:download"></dd></div>')
    facth = ''.join(f'<div><dt>{e(a)}</dt><dd>{ltr(b)}</dd></div>' for a, b in facts)
    orig = f'<img class="orig" src="{w["cover"]}" alt="الغلاف الأصلي: {e(w["title"])}" loading="lazy"><small>الغلاف الأصلي</small>' if w['cover'] else ''
    sub = f'<p class="subtitle">{e(w["subtitle"])}</p>' if w['subtitle'] else ''

    body = f'''
<section class="book-head"><div class="wrap">
<nav class="crumbs" aria-label="مسار التصفح"><a href="/">الرئيسية</a> / <a href="/library/">المكتبة</a> / <a href="/library/?theme={w["theme"]}">{e(THEME_SHORT[w["theme"]])}</a></nav>
<div class="book-grid">
<div class="book-covers">{cover(w, lg=True, link=False)}{orig}</div>
<div>
<div class="tags"><span class="tag">{e(TYPES[w["type"]])}</span><span class="tag">{e(THEMES[w["theme"]])}</span></div>
<h1>{e(w["title"])}</h1>{sub}
<dl class="facts-list">{facth}{counts}</dl>
<div class="book-actions">
<a class="btn" href="#reader" data-open-reader="0">{ICON["read"]}اقرأ هنا</a>
<a class="btn ghost" href="{w["pdf"]}" download data-dl="{w["slug"]}">{ICON["down"]}تحميل PDF</a>
<button class="btn ghost" type="button" data-share data-label="مشاركة">مشاركة</button>
</div>
</div></div>
</div></section>

<section style="background:var(--paper-2);border-block:1px solid var(--rule)"><div class="wrap">
<div class="tabs" role="tablist" aria-label="أقسام الصفحة">{tabh}</div>
{panh}
</div></section>

<section class="sec" id="reader" aria-label="قارئ الكتاب"><div class="wrap">
<h2 style="font-size:34px;margin-bottom:18px">اقرأ {"الكتاب" if w["type"] == "book" else "البحث"}</h2>
<div class="reader" data-reader data-pdf="{w["pdf"]}" data-slug="{w["slug"]}" tabindex="-1">
<div class="reader-bar">
<div class="grp">
<button class="rbtn" type="button" data-act="prev" aria-label="الصفحة السابقة">{ICON["prev"]}</button>
<label>صفحة <input type="number" min="1" value="1" aria-label="رقم الصفحة"> من <span data-total>{ar(w["npages"])}</span></label>
<button class="rbtn" type="button" data-act="next" aria-label="الصفحة التالية">{ICON["next"]}</button>
</div>
<div class="grp">
<button class="rbtn" type="button" data-act="out" aria-label="تصغير">−</button>
<button class="rbtn" type="button" data-act="in" aria-label="تكبير">+</button>
<button class="rbtn" type="button" data-act="full" aria-label="ملء الشاشة">{ICON["full"]}</button>
</div>
</div>
<div class="reader-stage"><div class="reader-msg"><p style="margin-bottom:18px">{ar(w["npages"])} صفحة. يُفتح الملف هنا دون تحميله كاملاً.</p><button class="btn gold" type="button" data-act="open">{ICON["read"]}ابدأ القراءة</button></div></div>
</div>
<p class="note">أسهم لوحة المفاتيح تقلّب الصفحات. يتذكّر الموقع آخر صفحة قرأتها في هذا المتصفح.</p>
</div></section>

<section class="sec" style="padding-top:0" aria-labelledby="c-title"><div class="wrap comments" data-comments="{w["slug"]}">
<h2 id="c-title" style="font-size:34px">تعليقات القرّاء <span class="c-count"></span></h2>
<ol class="c-list"><li class="c-empty">جارٍ تحميل التعليقات…</li></ol>
<form class="c-form" novalidate>
<h3>أضف تعليقاً أو سؤالاً</h3>
<p class="note" style="margin-top:0">تُراجَع التعليقات قبل نشرها. لا نطلب بريداً ولا تسجيلاً.</p>
<div class="c-row"><label for="c-name">الاسم</label><input id="c-name" name="name" required minlength="2" maxlength="60" autocomplete="name"></div>
<div class="c-row"><label for="c-body">التعليق</label><textarea id="c-body" name="body" required minlength="5" maxlength="2000" rows="5"></textarea></div>
<div class="c-hp" aria-hidden="true"><label for="c-web">موقعك</label><input id="c-web" name="website" tabindex="-1" autocomplete="off"></div>
<div class="c-row c-actions"><button class="btn" type="submit">أرسل التعليق</button><p class="c-msg" role="status" aria-live="polite"></p></div>
</form>
</div></section>

{f'<section class="sec" style="padding-top:0"><div class="wrap"><div class="sec-head"><h2>من المحور نفسه</h2><a class="link" href="/library/?theme={w["theme"]}">كل مؤلفات المحور</a></div><div class="shelf">{"".join(work_card(x) for x in related)}</div></div></section>' if related else ''}'''

    desc = (w['summary'][:150].rsplit(' ', 1)[0] + '…') if w['summary'] else f'{TYPES[w["type"]]} للدكتور محمد بن فارس الجميل: {w["title"]}. اقرأه أو حمّله مجاناً.'
    schema_type = 'Book' if w['type'] == 'book' else 'ScholarlyArticle'
    ld = {"@context": "https://schema.org", "@type": schema_type, "name": w['title'] + (f': {w["subtitle"]}' if w['subtitle'] else ''),
          "author": {"@type": "Person", "name": "محمد بن فارس الجميل"}, "inLanguage": "ar", "datePublished": str(w['year']),
          "url": f'{SITE}/books/{w["slug"]}/', "isAccessibleForFree": True}
    if w['publisher']:
        ld['publisher' if w['type'] == 'book' else 'isPartOf'] = {"@type": "Organization" if w['type'] == 'book' else "Periodical", "name": w['publisher']}
    return page(f'/books/{w["slug"]}/', w['title'], desc, body, 'library',
                scripts='<script type="module" src="/assets/book.js"></script><script type="module" src="/assets/reader.js"></script><script type="module" src="/assets/stats.js"></script><script type="module" src="/assets/comments.js"></script>',
                extra_head=scholar_meta(w) + '<link rel="modulepreload" href="/vendor/pdfjs/pdf.min.mjs">', jsonld=ld)


SOURCES = [
    {'title': 'السيرة الذاتية الرسمية للدكتور محمد بن فارس الجميل', 'by': 'جامعة الملك سعود، مواقع أعضاء هيئة التدريس',
     'url': 'https://faculty.ksu.edu.sa/ar/node/110437'},
    {'title': 'خبر فوزه بجائزة الأمير سلمان لدراسات تاريخ الجزيرة العربية عن كتاب «بيوت النبي ﷺ وحجراتها»', 'by': 'صحيفة الاقتصادية، ٧ مايو ٢٠١٢م',
     'url': 'https://www.aleqt.com/2012/05/07/article_654391.html',
     'archive': 'https://web.archive.org/web/20251031231211/https://www.aleqt.com/2012/05/07/article_654391.html'},
    {'title': 'عرض كتاب «أزواج النبي ﷺ: دراسة للعلاقة بين النبي وأزواجه»', 'by': 'صحيفة الجزيرة، ٥ مارس ٢٠١٤م',
     'url': 'https://www.al-jazirah.com/2014/20140305/cu2.htm',
     'archive': 'https://web.archive.org/web/20140806003750/http://www.al-jazirah.com:80/2014/20140305/cu2.htm'},
]


def sources_html():
    items = ''.join(
        f'<li><a href="{x["url"]}" target="_blank" rel="noopener">{e(x["title"])}</a>'
        f'<span class="src-by">{e(x["by"])}'
        + (f' · <a href="{x["archive"]}" target="_blank" rel="noopener">نسخة محفوظة</a>' if x.get('archive') else '')
        + '</span></li>' for x in SOURCES)
    return (f'<section class="sec" id="sources" style="padding-top:0"><div class="wrap"><div class="sources">'
            f'<h2>عنه في المصادر</h2><p class="note" style="margin-top:0">صفحات خارجية تتحدث عن الدكتور الجميل ومؤلفاته، تُفتح في نافذة جديدة.</p>'
            f'<ul class="src-list">{items}</ul></div></div></section>')


def build_author(W):
    bio = load('bio.json', {})
    li = lambda xs: ''.join(f'<li>{e(x)}</li>' for x in xs)
    body = f'''
<section class="page-title"><div class="wrap">
<nav class="crumbs" aria-label="مسار التصفح"><a href="/">الرئيسية</a> / عن المؤلف</nav>
<h1>الدكتور محمد بن فارس الجميل</h1>
<p>باحث سعودي في تاريخ الحضارة الإسلامية والسيرة النبوية، وأستاذ سابق في قسم التاريخ بجامعة الملك سعود.</p>
</div></section>
<section class="sec" style="padding-top:24px"><div class="wrap bio-grid">
<div>
<h2>السيرة</h2>
<p>وُلد في {e(bio.get("born", "محافظة الزلفي"))}. تلقى تعليمه الجامعي في جامعة الملك سعود ثم في الولايات المتحدة، وعمل {e(bio.get("career", ""))}. كتب في السيرة النبوية وفي الحياة اليومية والمادية في العهد النبوي، معتمداً في كثير من أبحاثه على كتب الحديث التسعة مصدراً للتاريخ الاجتماعي، وناقش مواقف المستشرقين من السيرة.</p>
<h2>التعليم</h2><ul class="plain-list">{li(bio.get("education", []))}</ul>
<h2>الجوائز</h2><ul class="plain-list">{li(bio.get("awards", []))}</ul>
<figure class="award-photo"><img src="/media/award-2017.jpg" alt="الدكتور محمد بن فارس الجميل يتسلّم جائزة الملك سلمان التقديرية من خادم الحرمين الشريفين الملك سلمان بن عبدالعزيز" width="400" height="307" loading="lazy">
<figcaption>الدكتور محمد بن فارس الجميل يتسلّم جائزة الملك سلمان التقديرية للمتميزين في خدمة تاريخ الجزيرة العربية من خادم الحرمين الشريفين الملك سلمان بن عبدالعزيز، ٢٠١٧م.</figcaption></figure>
<h2>المهام العلمية</h2><ul class="plain-list">{li(bio.get("roles", []))}</ul>
</div>
<div>
<figure class="portrait" style="margin-bottom:14px"><img src="/img/portrait.jpg" alt="الدكتور محمد بن فارس الجميل" width="400" height="500"></figure>
<p style="margin-bottom:28px"><a class="btn ghost" href="https://x.com/dr_mjameel" target="_blank" rel="noopener me">تابع الدكتور على منصة X</a></p>
<h2>لقاءات مصوّرة</h2>
<div class="talks one">{"".join(video_html(v) for v in VIDEOS)}</div>
</div>
</div></section>
{sources_html()}
{YT_JS}'''
    ld = {"@context": "https://schema.org", "@type": "Person", "name": "محمد بن فارس الجميل", "birthPlace": "الزلفي",
          "jobTitle": "أستاذ التاريخ والحضارة الإسلامية", "affiliation": {"@type": "CollegeOrUniversity", "name": "جامعة الملك سعود"},
          "alumniOf": ["جامعة الملك سعود", "Indiana University", "University of Michigan"], "url": SITE + '/author/',
          "sameAs": ["https://x.com/dr_mjameel"]}
    return page('/author/', 'عن الدكتور محمد بن فارس الجميل', 'سيرة الدكتور محمد بن فارس الجميل: تعليمه ومسيرته في جامعة الملك سعود وجوائزه ومؤلفاته في السيرة النبوية والتاريخ الإسلامي.',
                body, 'author', jsonld=ld)


PREVIEW = os.environ.get('PREVIEW') == '1'
GF = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=IBM+Plex+Sans+Arabic:wght@400;500;600&display=swap">'


def relativize(html_text, rel):
    """Preview build: rewrite root-absolute links to relative ones with explicit index.html,
    so the site works when hosted under any folder (e.g. as an artifact preview)."""
    depth = rel.count('/')
    pre = '../' * depth

    def fix(m):
        attr, url = m.group(1), m.group(2)
        path, sep, rest = re.match(r'([^?#]*)([?#]?)(.*)', url).groups()
        path = path.lstrip('/')
        if path == '' or path.endswith('/'):
            path += 'index.html'
        return f'{attr}="{pre}{path}{sep}{rest}"'
    out = re.sub(r'\b(href|src|action|data-pdf)="(/(?!/)[^"]*)"', fix, html_text)
    out = out.replace('<html lang="ar" dir="rtl">', '<html lang="ar" dir="rtl" data-preview>', 1)
    out = re.sub(r'<link rel="preload"[^>]+as="font"[^>]*>\n?', '', out)
    out = out.replace(f'<link rel="stylesheet" href="{pre}assets/fonts.css">', GF)
    out = re.sub(r'<div class="video" data-yt="([^"]+)">.*?</div>\n?<p class="note">',
                 r'<p><a class="btn ghost" href="https://www.youtube.com/watch?v=\1" target="_blank" rel="noopener">شاهد اللقاء على يوتيوب</a></p>\n<p class="note">', out, flags=re.S)
    return out


TITLE_OF = {}


def main():
    W = works()
    TITLE_OF.update({w['slug']: w['title'] for w in W})
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)

    def write(rel, text):
        p = os.path.join(DIST, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if PREVIEW and rel.endswith('.html'):
            text = relativize(text, rel)
        open(p, 'w', encoding='utf-8').write(text)

    write('index.html', build_home(W))
    write('library/index.html', build_library(W))
    write('author/index.html', build_author(W))
    for w in W:
        write(f'books/{w["slug"]}/index.html', build_book(w, W))
    write('404.html', page('/404', 'الصفحة غير موجودة', 'الصفحة المطلوبة غير موجودة.',
          '<section class="page-title"><div class="wrap"><h1>الصفحة غير موجودة</h1><p>ربما تغيّر رابطها. ابحث عن العنوان في <a href="/library/">المكتبة</a> أو عُد إلى <a href="/">الرئيسية</a>.</p></div></section>'))

    # assets
    shutil.copytree(os.path.join(HERE, 'src', 'assets'), os.path.join(DIST, 'assets'))
    pj = os.path.join(HERE, 'node_modules', 'pdfjs-dist', 'build')
    os.makedirs(os.path.join(DIST, 'vendor', 'pdfjs'))
    for f in ('pdf.min.mjs', 'pdf.worker.min.mjs'):
        # Raw control bytes only occur inside string literals in these files; escape them so
        # hosts that reject control characters in text files accept the library unchanged in behaviour.
        src = open(os.path.join(pj, f), encoding='utf-8').read()
        src = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', lambda m: '\\x%02x' % ord(m.group(0)), src)
        open(os.path.join(DIST, 'vendor', 'pdfjs', f), 'w', encoding='utf-8').write(src)
    fd = os.path.join(DIST, 'fonts'); os.makedirs(fd)
    for slug, ws in (('amiri', (400, 700)), ('ibm-plex-sans-arabic', (400, 500, 600))):
        for wt in ws:
            for sub in ('arabic', 'latin'):
                f = f'{slug}-{sub}-{wt}-normal.woff2'
                src = os.path.join(HERE, 'node_modules', '@fontsource', slug, 'files', f)
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(fd, f))
    write('favicon.svg', MARK.replace('class="brand-mark" ', 'xmlns="http://www.w3.org/2000/svg" '))

    # images, covers, pdfs, search data
    os.makedirs(os.path.join(DIST, 'img'))
    for src, dst in (('covers/profile.jpg', 'img/portrait.jpg'), ('og.jpg', 'og.jpg')):
        s = os.path.join(LIB, src) if not src.startswith('og') else os.path.join(HERE, 'src', src)
        if os.path.exists(s):
            shutil.copy(s, os.path.join(DIST, dst))
    md = os.path.join(LIB, 'media')
    if os.path.isdir(md):
        shutil.copytree(md, os.path.join(DIST, 'media'))
    os.makedirs(os.path.join(DIST, 'covers'))
    os.makedirs(os.path.join(DIST, 'pdfs'))
    os.makedirs(os.path.join(DIST, 'data', 'search'))
    for w in W:
        c = os.path.join(LIB, 'covers', f'{w["id"]}.webp')
        if os.path.exists(c):
            shutil.copy(c, os.path.join(DIST, 'covers', f'{w["slug"]}.webp'))
        if os.environ.get('NO_PDFS') != '1':
            shutil.copy(w['_src'], os.path.join(DIST, 'pdfs', f'{w["slug"]}.pdf'))
        s = os.path.join(LIB, 'site-data', 'search', f'{w["id"]}.json')
        if os.path.exists(s):
            shutil.copy(s, os.path.join(DIST, 'data', 'search', f'{w["id"]}.json'))

    # SEO files and redirects for old addresses
    urls = ['/', '/library/', '/author/'] + [f'/books/{w["slug"]}/' for w in W]
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
          ''.join(f'<url><loc>{SITE}{u}</loc></url>' for u in urls) + '</urlset>')
    write('robots.txt', f'User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {SITE}/sitemap.xml\n')
    write('admin/index.html', open(os.path.join(HERE, 'src', 'admin.html'), encoding='utf-8').read()
          .replace('/*TITLES*/{}', json.dumps({w['slug']: w['title'] for w in W}, ensure_ascii=False).replace('<', '\\u003c')))
    write('_redirects', '/library /library/ 301\n/author /author/ 301\n/biography /author/ 301\n/videos /#talks 301\n/gallery /author/ 301\n/photos /author/ 301\n' +
          ''.join(f'/books/{w["slug"]} /books/{w["slug"]}/ 301\n' for w in W))
    # Security headers for every page (tested with the PDF reader, fonts and the YouTube player), then caching rules.
    write('_headers', "/*\n  Content-Security-Policy: default-src 'self'; script-src 'self' https://static.cloudflareinsights.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://img.youtube.com; font-src 'self' data:; connect-src 'self' https://cloudflareinsights.com; media-src 'self'; worker-src 'self' blob:; frame-src https://www.youtube-nocookie.com; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'; upgrade-insecure-requests\n  Strict-Transport-Security: max-age=31536000; includeSubDomains\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()\n  X-Frame-Options: SAMEORIGIN\n/admin/*\n  Cache-Control: no-store\n  X-Robots-Tag: noindex\n/pdfs/*\n  Cache-Control: public, max-age=86400\n/media/*\n  Cache-Control: public, max-age=86400\n/data/*\n  Cache-Control: public, max-age=86400\n/assets/*\n  Cache-Control: public, max-age=3600\n")
    # The API accepts only these slugs; write them next to it so new works are never rejected.
    lib = os.path.join(os.path.dirname(os.path.abspath(DIST)), 'lib')
    if os.path.isdir(lib):
        open(os.path.join(lib, 'slugs.js'), 'w', encoding='utf-8').write(
            '// Generated by source/build.py. Do not edit by hand.\nexport const SLUGS = ' + json.dumps([w['slug'] for w in W], ensure_ascii=False) + ';\n')
    print('built', len(W), 'works into', DIST)


if __name__ == '__main__':
    main()
