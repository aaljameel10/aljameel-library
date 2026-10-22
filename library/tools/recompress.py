"""Re-encode heavy scanned PDFs as upright grayscale JPEG pages (200 dpi) so they stream fast."""
# Run from anywhere: python3 library/tools/recompress.py <id> ...  (writes web/<id>.pdf next to the originals)
import os as _os; _os.chdir(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
import os, subprocess, sys, tempfile
from PIL import Image
ids = sys.argv[1:]
for i in ids:
    src = f'fixed/{i}.pdf' if os.path.exists(f'fixed/{i}.pdf') else f'pdfs/{i}.pdf'
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(['pdftoppm', '-r', '150', '-gray', '-jpeg', '-jpegopt', 'quality=60', src, f'{d}/p'], check=True, stderr=subprocess.DEVNULL)
        files = sorted(os.listdir(d))
        ims = [Image.open(os.path.join(d, f)) for f in files]
        ims[0].save(f'web/{i}.pdf', save_all=True, append_images=ims[1:], resolution=150.0)
    print(i, round(os.path.getsize(src)/1e6,1), '->', round(os.path.getsize(f'web/{i}.pdf')/1e6,1), 'MB', len(files), 'pages')
