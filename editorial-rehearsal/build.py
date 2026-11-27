import json
import re
from pathlib import Path
from PIL import Image, ImageDraw

PAYLOAD = re.compile(r'<script type="application/json" id="test-edition-data">(.*?)</script>', re.S)

ROOT = Path('dist')
ROUTE = 'rehearsal-2026-11-27'
SOURCE = ROOT / '2026-11-28'
DEST = ROOT / ROUTE


def draw_zeros(path):
    image = Image.new('RGB', (960, 540), '#111b2c')
    draw = ImageDraw.Draw(image)
    draw.text((90, 62), 'RIEMANN ZETA FUNCTION', fill='#e8edf5', font_size=30)
    draw.text((90, 105), 'First three nontrivial zeros with positive imaginary part', fill='#aebcce', font_size=19)
    draw.rectangle((255, 159, 665, 441), fill='#192b44', outline='#3b536f', width=2)
    draw.line((460, 159, 460, 441), fill='#f4c66e', width=3)
    draw.text((475, 166), 'critical line', fill='#f4c66e', font_size=17)
    for ordinate in (14.134725, 21.022040, 25.010858):
        y = round(441 - (ordinate - 10) * 15)
        draw.ellipse((453, y - 7, 467, y + 7), fill='#f4c66e')
        draw.text((479, y - 9), f'{ordinate:.4f}i', fill='#dbe6f6', font_size=17)
    for x, label in ((255, '0'), (453, '1/2'), (660, '1')):
        draw.text((x, 454), label, fill='#aebcce', font_size=20)
    draw.text((696, 448), 'Re(s)', fill='#aebcce', font_size=19)
    image.save(path, 'WEBP', quality=93)


def main():
    approved = json.loads(Path(__file__).with_name('edition.json').read_text(encoding='utf-8'))
    assert len(approved['items']) == 6
    (DEST / 'media').mkdir(parents=True, exist_ok=False)
    html = (SOURCE / 'index.html').read_text(encoding='utf-8')
    match = PAYLOAD.search(html)
    assert match and 'content="noindex, nofollow"' in html
    previous = {item['url']: item for item in json.loads(match[1])['items']}
    stories = []
    for item in approved['items']:
        image = item['image']
        if image['small'] == 'media/zeta-critical-line.webp':
            draw_zeros(DEST / image['small'])
        else:
            approved_image = previous[item['url']]['image']
            for field in ('alt', 'altEn', 'credit'):
                assert approved_image[field] == image[field]
            for size in ('small', 'large'):
                assert re.fullmatch(r'media/[a-z0-9-]+\.webp', approved_image[size])
                media = (SOURCE / approved_image[size]).read_bytes()
                assert media[:4] == b'RIFF' and media[8:12] == b'WEBP'
                (DEST / image[size]).write_bytes(media)
        stories.append(item)

    for name in ('app.js', 'reader-layout.css', 'reader-motion.css'):
        (DEST / name).write_bytes((SOURCE / name).read_bytes())
    edition = {'issue': approved['issue'], 'status': approved['status'], 'items': stories}
    data = json.dumps(edition, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    page = html[:match.start(1)] + data + html[match.end(1):]
    page = re.sub(r'<title>[^<]*</title>', '<title>DE∀I · 리허설 / Rehearsal</title>', page, count=1)
    page = re.sub(r'(<body\b[^>]*>)', r'\1<div role="note" style="text-align:center;padding:.65rem">DE∀I · 리허설 / Rehearsal</div>', page, count=1)
    (DEST / 'index.html').write_text(page, encoding='utf-8')
    print('Prepared 6 approved stories and 6 images for the standalone rehearsal.')


if __name__ == '__main__':
    main()
