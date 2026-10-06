"""
gen_cp3_textures.py - Checkpoint 3 identity artwork for the RF-01 engineer (system Python + Pillow).

  python art/character/scripts/gen_cp3_textures.py

Writes art/character/textures/cp3/. Fictional Red Frontier programme branding only: no NASA marks, no real names.
The insignia reuses the facility mark (scripts/gen_textures.py: Mars disc, horizon, ascending chevron) so the
character matches the Digital Twin header and programme board.
"""
import os, math
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'textures', 'cp3')
os.makedirs(OUT, exist_ok=True)
FONT = r"C:\Windows\Fonts\bahnschrift.ttf"          # facility typeface (DIN family)

NAVY = (20, 28, 42)            # garment navy (matches the jacket dark panels)
NAVY_UI = (8, 17, 31)          # facility screen background
OFFWHITE = (226, 223, 214)     # facility warm off-white
ORANGE = (194, 80, 28)         # facility orange #C2501C (physical accents)
ORANGE_UI = (240, 122, 69)     # facility UI orange (screens only)
CYAN = (116, 182, 255)
GRAPHITE = (44, 47, 52)
GREY = (150, 152, 156)


def font(size, style='SemiBold'):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_name(style)
    except Exception:
        pass
    return f


def insignia(d, cx, cy, r, ring, disc, mark, w=None):
    """Red Frontier mark centred at (cx, cy), outer radius r."""
    w = w or max(2, int(r * 0.075))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ring, width=w)
    ri = r * 0.80
    d.pieslice([cx - ri, cy - ri, cx + ri, cy + ri], 180, 360, fill=disc)
    hh = max(2, int(r * 0.045))
    d.rectangle([cx - ri, cy - hh * 0.4, cx + ri, cy + hh], fill=mark)
    cw = max(2, int(r * 0.088))
    d.line([(cx - ri * 0.47, cy - ri * 0.17), (cx, cy - ri * 0.64), (cx + ri * 0.47, cy - ri * 0.17)], fill=mark,
           width=cw, joint='curve')


def text_on_arc(img, text, cx, cy, radius, centre_deg, fnt, fill, inward=False, spacing=1.0):
    """Draw text along a circle (top arc reads clockwise, bottom arc reads counter-clockwise)."""
    widths = [fnt.getlength(ch) for ch in text]
    total = sum(widths) * spacing
    ang_total = total / radius
    a = math.radians(centre_deg) - (ang_total / 2 if not inward else -ang_total / 2)
    for ch, wch in zip(text, widths):
        step = wch * spacing / radius
        mid = a + (step / 2 if not inward else -step / 2)
        x, y = cx + radius * math.cos(mid), cy + radius * math.sin(mid)
        tile = Image.new('RGBA', (int(wch * 2 + 40), int(fnt.size * 2)), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((tile.width / 2, tile.height / 2), ch, font=fnt, fill=fill, anchor='mm')
        rot = -math.degrees(mid) - 90 if not inward else -math.degrees(mid) + 90
        tile = tile.rotate(rot, resample=Image.BICUBIC, expand=True)
        img.alpha_composite(tile, (int(x - tile.width / 2), int(y - tile.height / 2)))
        a += step if not inward else -step


# ------------------------------------------------------------------------------------------------ mission patch
def patch(s=2048):
    """Round RF-01 mission patch: navy field, Mars horizon, transfer trajectory, RF-01, ring text."""
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    d.ellipse([0, 0, s - 1, s - 1], fill=OFFWHITE + (255,))                         # merrowed edge (off-white)
    d.ellipse([34, 34, s - 35, s - 35], fill=ORANGE + (255,))                        # thin orange keyline
    d.ellipse([58, 58, s - 59, s - 59], fill=NAVY + (255,))                          # text ring field
    inner = s * 0.355
    d.ellipse([c - inner, c - inner, c + inner, c + inner], fill=(12, 19, 31, 255))  # inner field
    # Mars rising from the bottom of the inner field (clipped to the inner circle)
    field = Image.new('L', (s, s), 0); ImageDraw.Draw(field).ellipse([c - inner, c - inner, c + inner, c + inner], fill=255)
    mars = Image.new('RGBA', (s, s), (0, 0, 0, 0)); md = ImageDraw.Draw(mars)
    R = inner * 1.55; my = c + inner * 0.45 + R
    md.ellipse([c - R, my - R - R * 0.0, c + R, my + R], fill=(150, 62, 30, 255))
    md.ellipse([c - R * 0.98, my - R * 0.985, c + R * 0.98, my + R], fill=(172, 74, 34, 255))
    for (dx, dy, rr) in [(-0.35, 0.10, 0.07), (0.22, 0.06, 0.05), (0.05, 0.18, 0.09)]:   # faint terrain
        x, y = c + dx * inner, my - R + dy * inner + 30
        md.ellipse([x - rr * inner, y - rr * inner * 0.45, x + rr * inner, y + rr * inner * 0.45], fill=(140, 58, 28, 255))
    im.paste(mars, (0, 0), Image.composite(mars, Image.new('RGBA', (s, s)), field).split()[3])
    d = ImageDraw.Draw(im)
    # transfer trajectory: dashed curve from the spacecraft (left) over the title to the landing site (right)
    P0, P1, P2 = (c - 0.72 * inner, c + 0.06 * inner), (c + 0.42 * inner, c - 1.12 * inner), (c + 0.63 * inner, c + 0.57 * inner)
    pts = []
    for i in range(241):
        t = i / 240
        pts.append(((1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t * t * P2[0],
                    (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t * t * P2[1]))
    for i in range(6, 232, 12):
        d.line(pts[i:i + 7], fill=OFFWHITE + (255,), width=13)
    lx, ly = P2                                                                       # landing marker
    d.ellipse([lx - 26, ly - 26, lx + 26, ly + 26], fill=ORANGE + (255,), outline=OFFWHITE + (255,), width=8)
    sx, sy = P0                                                                       # spacecraft chevron
    d.line([(sx - 34, sy + 34), (sx + 6, sy - 18), (sx + 46, sy + 20)], fill=OFFWHITE + (255,), width=16, joint='curve')
    # RF-01
    d.text((c, c + 0.08 * inner), 'RF-01', font=font(int(s * 0.118), 'Bold'), fill=OFFWHITE + (255,), anchor='mm')
    d.rectangle([c - inner * 0.40, c + inner * 0.31, c + inner * 0.40, c + inner * 0.33], fill=ORANGE + (255,))
    # ring text
    rt = (inner + (s / 2 - 58)) / 2
    text_on_arc(im, 'RED FRONTIER', c, c, rt + 4, -90, font(int(s * 0.072), 'Bold'), OFFWHITE + (255,), spacing=1.18)
    text_on_arc(im, 'MISSION SYSTEMS', c, c, rt - 4, 90, font(int(s * 0.056), 'SemiBold'), OFFWHITE + (255,), inward=True,
                spacing=1.12)
    d = ImageDraw.Draw(im)
    for a in (180, 0):                                                                # separator dots
        x, y = c + rt * math.cos(math.radians(a)), c + rt * math.sin(math.radians(a))
        d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=ORANGE + (255,))
    im.save(os.path.join(OUT, 'T_RF01_MissionPatch.png'))


# ------------------------------------------------------------------------------------------------ chest identifier
def chest_mark(w=2800, h=640):
    """Left-chest identifier on the navy yoke: insignia + RED FRONTIER + MISSION RF-01 (embroidery colours)."""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = h * 0.42
    insignia(d, r + 20, h / 2, r, OFFWHITE + (255,), ORANGE + (255,), OFFWHITE + (255,))
    x0 = 2 * r + 90
    d.text((x0, h * 0.40), 'RED FRONTIER', font=font(int(h * 0.36), 'Bold'), fill=OFFWHITE + (255,), anchor='lm')
    d.text((x0 + 4, h * 0.78), 'MISSION  RF-01', font=font(int(h * 0.17), 'SemiBold'), fill=(196, 196, 192, 255),
           anchor='lm')
    im = im.crop(im.getbbox()); bw, bh = im.size
    pad = Image.new('RGBA', (bw + 40, bh + 40), (0, 0, 0, 0)); pad.paste(im, (20, 20))
    pad.save(os.path.join(OUT, 'T_RF01_ChestMark.png'))
    return pad.size


# ------------------------------------------------------------------------------------------------ back mark
def back_mark(s=1024):
    """Back-yoke mark: insignia over RF-01, off-white on navy (read from the third-person camera)."""
    im = Image.new('RGBA', (s, int(s * 1.25)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = s * 0.40
    insignia(d, s / 2, r + 20, r, OFFWHITE + (255,), ORANGE + (255,), OFFWHITE + (255,))
    d.text((s / 2, 2 * r + 150), 'RF-01', font=font(int(s * 0.20), 'Bold'), fill=OFFWHITE + (255,), anchor='mm')
    im.save(os.path.join(OUT, 'T_RF01_BackMark.png'))


# ------------------------------------------------------------------------------------------------ ID badge
def badge(w=1080, h=1720):
    """Facility ID card (CR80 portrait, 54 x 86 mm). No personal name: identifier MS-01, abstract portrait."""
    im = Image.new('RGBA', (w, h), (238, 236, 230, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 330], fill=NAVY + (255,))
    insignia(d, 150, 165, 105, OFFWHITE + (255,), ORANGE + (255,), OFFWHITE + (255,))
    d.text((290, 120), 'RED FRONTIER', font=font(92, 'Bold'), fill=OFFWHITE + (255,), anchor='lm')
    d.text((292, 215), 'PROGRAM  ·  FACILITY ACCESS', font=font(44), fill=(170, 180, 196, 255), anchor='lm')
    # slot punch
    d.rounded_rectangle([w / 2 - 90, 32, w / 2 + 90, 62], radius=15, fill=(10, 14, 22, 255))
    # abstract portrait area (no likeness): tonal panel with a neutral head/shoulder glyph
    px0, py0, px1, py1 = 90, 400, 520, 960
    d.rectangle([px0, py0, px1, py1], fill=(198, 202, 208, 255))
    d.ellipse([px0 + 140, py0 + 90, px1 - 140, py0 + 250], fill=(172, 177, 185, 255))
    d.rounded_rectangle([px0 + 60, py0 + 280, px1 - 60, py1 + 120], radius=120, fill=(172, 177, 185, 255))
    d.rectangle([px0, py1, px1, py1 + 140], fill=(238, 236, 230, 255))
    d.rectangle([px0, py0, px1, py1], outline=(160, 164, 170, 255), width=4)
    # role block
    d.text((580, 430), 'MISSION', font=font(66, 'Bold'), fill=NAVY + (255,), anchor='lm')
    d.text((580, 510), 'SYSTEMS', font=font(66, 'Bold'), fill=NAVY + (255,), anchor='lm')
    d.text((580, 590), 'ENGINEER', font=font(48), fill=(70, 80, 96, 255), anchor='lm')
    d.rectangle([580, 650, 990, 656], fill=ORANGE + (255,))
    d.text((580, 720), 'MISSION', font=font(36), fill=(110, 118, 130, 255), anchor='lm')
    d.text((580, 780), 'RF-01', font=font(84, 'Bold'), fill=NAVY + (255,), anchor='lm')
    d.text((580, 880), 'ID  MS-01', font=font(52, 'SemiBold'), fill=(70, 80, 96, 255), anchor='lm')
    # name field left abstract
    d.rectangle([90, 1040, 990, 1046], fill=(190, 192, 196, 255))
    for i, wd in enumerate([300, 220, 260]):
        d.rounded_rectangle([90, 1080 + i * 52, 90 + wd, 1108 + i * 52], radius=14, fill=(208, 210, 214, 255))
    # access zones
    d.text((90, 1290), 'ACCESS', font=font(38), fill=(110, 118, 130, 255), anchor='lm')
    for i, z in enumerate(['BRF', 'INT', 'ENG', 'MCC']):
        x = 260 + i * 182
        d.rounded_rectangle([x, 1262, x + 160, 1320], radius=10, outline=NAVY + (255,), width=4)
        d.text((x + 80, 1291), z, font=font(38, 'Bold'), fill=NAVY + (255,), anchor='mm')
    # code strip + orange access band
    import random
    rnd = random.Random(1)
    x = 90
    while x < 990:
        bw = rnd.choice([4, 6, 10, 14]); d.rectangle([x, 1380, x + bw, 1500], fill=(30, 34, 42, 255)); x += bw + rnd.choice([5, 8, 12])
    d.rectangle([0, h - 150, w, h], fill=ORANGE + (255,))
    d.text((w / 2, h - 75), 'MISSION OPERATIONS', font=font(54, 'Bold'), fill=(250, 244, 236, 255), anchor='mm')
    im.save(os.path.join(OUT, 'T_RF01_Badge.png'))


# ------------------------------------------------------------------------------------------------ wrist UI
def wrist_ui(w=960, h=600):
    """Wrist interface screen, facility UI rules: navy, faint grid, cyan info, orange = selected only."""
    im = Image.new('RGB', (w, h), NAVY_UI); d = ImageDraw.Draw(im)
    for x in range(0, w, 40):
        d.line([(x, 0), (x, h)], fill=(18, 32, 50))
    for y in range(0, h, 40):
        d.line([(0, y), (w, y)], fill=(18, 32, 50))
    d.text((36, 52), 'RF-01', font=font(64, 'Bold'), fill=(231, 236, 245), anchor='lm')
    d.text((w - 36, 52), 'MS-01', font=font(34), fill=CYAN, anchor='rm')
    d.rectangle([36, 96, w - 36, 99], fill=(40, 70, 104))
    rows = [('LANDING SITE', 'JEZERO  B'), ('BUILD', 'CONFIG 3'), ('DIGITAL TWIN', 'NOMINAL'), ('RISK', 'MODERATE')]
    for i, (k, v) in enumerate(rows):
        y = 150 + i * 92
        d.text((36, y), k, font=font(34), fill=CYAN, anchor='lm')
        d.text((w - 36, y), v, font=font(40, 'SemiBold'), fill=(231, 236, 245), anchor='rm')
    d.rounded_rectangle([36, h - 92, 300, h - 36], radius=8, outline=ORANGE_UI, width=4)
    d.text((168, h - 64), 'BRIEF', font=font(34, 'Bold'), fill=ORANGE_UI, anchor='mm')
    d.text((w - 36, h - 64), 'T-  00:42:10', font=font(40, 'SemiBold'), fill=CYAN, anchor='rm')
    im.save(os.path.join(OUT, 'T_RF01_WristUI.png'))


if __name__ == '__main__':
    patch(); cm = chest_mark(); back_mark(); badge(); wrist_ui()
    print('wrote', OUT, 'chest mark px', cm)
