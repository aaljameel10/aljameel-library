"""Build a full-text search index from the OCR output.

Output: site-data/search/<id>.json = [[pdf_page, normalized_text], ...]
Normalization folds the spelling variants that trip up Arabic search
(hamza forms, ta marbuta, alef maqsura, diacritics, tatweel) and drops
lines that are mostly OCR noise.
"""
import json, os, re

DIAC = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭـ]')
NON = re.compile(r'[^ء-ي0-9a-zA-Z\s]')

KEEP = re.compile(r'[^\u0621-\u064A0-9a-zA-Z\s\u060C\u061B\u061F.,:;()«»"\-]')

def norm(t):
    """Display-ready text: diacritics, tatweel and stray symbols removed, spaces collapsed.
    Spelling variants are folded in the browser with a 1:1 character map, so offsets stay aligned."""
    t = DIAC.sub('', t)
    t = KEEP.sub(' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def good_line(l):
    ar = len(re.findall(r'[ء-ي]', l))
    return ar >= 6 and ar / max(1, len(l.replace(' ', ''))) > 0.6

def main(src='ocr', out='site-data/search'):
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    os.makedirs(out, exist_ok=True)
    total = 0
    for id_ in sorted(os.listdir(src)):
        pages = []
        for f in sorted(os.listdir(os.path.join(src, id_))):
            if not f.endswith('.txt'):
                continue
            raw = open(os.path.join(src, id_, f), encoding='utf-8').read()
            lines = [l for l in raw.splitlines() if good_line(l)]
            text = norm(' '.join(lines))
            if len(text) > 30:
                pages.append([int(f[:4]), text])
        json.dump(pages, open(os.path.join(out, f'{id_}.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
        size = os.path.getsize(os.path.join(out, f'{id_}.json'))
        total += size
        print(id_, len(pages), 'pages', round(size / 1024), 'KB')
    print('total', round(total / 1024 / 1024, 1), 'MB')

if __name__ == '__main__':
    main()
