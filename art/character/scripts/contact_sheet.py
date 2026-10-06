"""contact_sheet.py - tile review renders into one labelled sheet (system Python + Pillow).

python art/character/scripts/contact_sheet.py <out.png> <cols> <tile_px> img1.png img2.png ...
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont

out, cols, tile = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = sys.argv[4:]
rows = (len(files) + cols - 1) // cols
lab = 34
sheet = Image.new('RGB', (cols * tile, rows * (tile + lab)), (24, 24, 26))
try:
    font = ImageFont.truetype('bahnschrift.ttf', 22)
except Exception:
    font = ImageFont.load_default()
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB')
    im.thumbnail((tile, tile))
    x, y = (i % cols) * tile, (i // cols) * (tile + lab)
    sheet.paste(im, (x + (tile - im.width) // 2, y + lab))
    d.text((x + 10, y + 6), os.path.splitext(os.path.basename(f))[0].replace('turntable_', ''), fill=(220, 220, 220),
           font=font)
sheet.save(out)
print('sheet', out, sheet.size)
