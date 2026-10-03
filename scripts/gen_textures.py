"""
gen_textures.py - procedural texture set for the Red Frontier facility (system Python: numpy + PIL).

Writes PNGs to D:/RedFrontier/textures/{surfaces,screens,decals}. Everything here is a plain
image so it survives glTF export and works unchanged in Godot (no Blender-only nodes).
Normal maps are OpenGL convention (+Y), which both Blender and Godot 4 expect.

Run:  python scripts/gen_textures.py
"""
import os, math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = r"D:\RedFrontier\textures"
for d in ('surfaces', 'screens', 'decals'): os.makedirs(os.path.join(ROOT, d), exist_ok=True)
rng = np.random.default_rng(7)

# palette (sRGB)
NAVY_BG, GRID, CYAN, WHITE, ORANGE, AMBER, GRAPHITE = (8, 17, 31), (22, 40, 62), (116, 182, 255), (231, 236, 245), (240, 122, 69), (227, 169, 40), (43, 46, 51)
FONT = r"C:\Windows\Fonts\bahnschrift.ttf"          # DIN-derived: clean, technical, aerospace

def font(size, style='SemiBold'):
    f = ImageFont.truetype(FONT, size)
    try: f.set_variation_by_name(style)
    except Exception: pass
    return f

def save(img, sub, name):
    p = os.path.join(ROOT, sub, name); img.save(p); return p

# ----------------------------------------------------------------- tileable noise
def noise(size, cells, octaves=4, persistence=0.5):
    out = np.zeros((size, size), np.float32); amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = cells * 2 ** o
        g = rng.random((c, c)).astype(np.float32)
        big = np.tile(g, (3, 3))
        im = Image.fromarray((big * 255).astype(np.uint8)).resize((size * 3, size * 3), Image.BICUBIC)
        out += amp * (np.asarray(im, np.float32)[size:2 * size, size:2 * size] / 255.0)
        tot += amp; amp *= persistence
    return out / tot

def normal_from_height(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    n = np.dstack((-dx, dy, np.ones_like(h)))          # +Y up (OpenGL)
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8))

def to_img(a): return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

# =========================================================================== SURFACES
def floor_epoxy(size=2048):
    """Sealed epoxy concrete, one tile = 4.4 x 4.4 m (matches the hangar column grid), saw-cut joint on the edge."""
    m = noise(size, 4, 5)                                  # broad mottling
    speck = (rng.random((size, size)) > 0.9965).astype(np.float32)
    speck = np.asarray(Image.fromarray((speck * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), np.float32) / 255
    base = 0.50 + (m - 0.5) * 0.10 - speck * 0.08 + (noise(size, 64, 2) - 0.5) * 0.03
    joint = np.zeros((size, size), np.float32); w = 3
    joint[:w, :] = joint[-w:, :] = joint[:, :w] = joint[:, -w:] = 1.0
    col = np.dstack((base * 0.98, base * 1.0, base * 1.03))  # very slightly cool grey
    col[joint > 0] *= 0.45
    save(to_img(col), 'surfaces', 'T_Floor_Epoxy_BaseColor.png')
    rough = 0.30 + (noise(size, 8, 4) - 0.5) * 0.16 + speck * 0.2 + joint * 0.4
    save(to_img(rough), 'surfaces', 'T_Floor_Epoxy_Roughness.png')
    h = -joint * 1.0 + (noise(size, 128, 2) - 0.5) * 0.02
    save(normal_from_height(h, 2.0), 'surfaces', 'T_Floor_Epoxy_Normal.png')

def grate(size=512):
    """Cable-trench cover: slotted steel, tile = 0.3 x 0.3 m."""
    h = np.zeros((size, size), np.float32)
    for i in range(6):
        y0 = int((i + 0.5) * size / 6 - size / 40)
        h[y0:y0 + size // 20, size // 10: size - size // 10] = -1.0
    h = np.asarray(Image.fromarray(((h + 1) * 127).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 127 - 1
    base = 0.42 + (noise(size, 8, 3) - 0.5) * 0.06
    col = np.dstack([base] * 3); col[h < -0.5] = 0.05
    save(to_img(col), 'surfaces', 'T_Grate_BaseColor.png')
    save(normal_from_height(h, 3.0), 'surfaces', 'T_Grate_Normal.png')

def roof_deck(size=1024):
    """Profiled steel roof deck, ribs every 0.25 m, tile = 1 m."""
    x = np.linspace(0, 4 * 2 * math.pi, size, endpoint=False)
    h = np.tile(np.clip(np.sin(x) * 1.6, -1, 1), (size, 1)).astype(np.float32)
    save(normal_from_height(h, 1.5), 'surfaces', 'T_RoofDeck_Normal.png')

def brushed(size=1024):
    """Directional brushing for brushed-metal roughness."""
    n = rng.random((size // 8, size)).astype(np.float32)
    im = Image.fromarray((n * 255).astype(np.uint8)).resize((size, size), Image.BILINEAR)
    a = np.asarray(im, np.float32) / 255
    save(to_img(0.32 + (a - 0.5) * 0.12), 'surfaces', 'T_Brushed_Roughness.png')

# ============================================================================ SCREENS
def screen_base(w, h, title, sub=None):
    im = Image.new('RGB', (w, h), NAVY_BG); d = ImageDraw.Draw(im)
    for x in range(0, w, 40): d.line([(x, 0), (x, h)], fill=(12, 24, 40))
    for y in range(0, h, 40): d.line([(0, y), (w, y)], fill=(12, 24, 40))
    d.rectangle([0, 0, w, 70], fill=(10, 22, 40)); d.line([(0, 70), (w, 70)], fill=GRID, width=2)
    d.rectangle([28, 22, 36, 48], fill=ORANGE)                          # identity tab
    d.text((52, 16), title, font=font(36), fill=WHITE)
    if sub: d.text((w - 28, 24), sub, font=font(22, 'Regular'), fill=CYAN, anchor='ra')
    return im, d

def option_cards(d, labels, sel, x0, y0, w, h, gap=18):
    cw = (w - gap * (len(labels) - 1)) / len(labels)
    for i, lab in enumerate(labels):
        x = x0 + i * (cw + gap); on = i == sel
        d.rounded_rectangle([x, y0, x + cw, y0 + h], 10, outline=ORANGE if on else GRID, width=4 if on else 2, fill=(14, 30, 52) if on else NAVY_BG)
        d.text((x + cw / 2, y0 + h / 2), lab, font=font(26), fill=WHITE if on else CYAN, anchor='mm')

def bar(d, x, y, w, h, frac, label, col=CYAN):
    d.rectangle([x, y, x + w, y + h], outline=GRID, width=2)
    d.rectangle([x + 3, y + 3, x + 3 + (w - 6) * frac, y + h - 3], fill=col)
    d.text((x, y - 30), label, font=font(22, 'Regular'), fill=CYAN)

def screens():
    W, H = 1024, 640
    im, d = screen_base(W, H, 'POWER SYSTEMS', 'power | battery | thermal')
    option_cards(d, ['SOLAR', 'LARGE SOLAR', 'NUCLEAR'], 2, 40, 100, W - 80, 90)
    pts = [(60 + i * 9, 470 - 120 * max(0, math.sin(i / 100 * math.pi)) - 20) for i in range(101)]
    d.line(pts, fill=CYAN, width=3); d.text((60, 300), 'OUTPUT PER SOL', font=font(22, 'Regular'), fill=CYAN)
    bar(d, 60, 540, 420, 36, 0.72, 'BATTERY  2 x 43 Ah'); bar(d, 540, 540, 420, 36, 0.35, 'THERMAL MARGIN', ORANGE)
    save(im, 'screens', 'T_Screen_Power.png')

    im, d = screen_base(W, H, 'SCIENCE PAYLOAD', '3 slots | mission style')
    for i, (lab, inst) in enumerate((('SLOT 1', 'CAMERA'), ('SLOT 2', 'LASER'), ('SLOT 3', 'ORGANICS'))):
        x = 40 + i * 322
        d.rounded_rectangle([x, 110, x + 300, 380], 12, outline=CYAN, width=2)
        d.text((x + 20, 125), lab, font=font(22, 'Regular'), fill=CYAN)
        d.text((x + 150, 260), inst, font=font(34), fill=WHITE, anchor='mm')
    option_cards(d, ['FIELD LAB  (analyze)', 'COLLECTOR  (cache)'], 1, 40, 430, W - 80, 90)
    bar(d, 40, 580, W - 80, 30, 0.64, 'PAYLOAD MASS  16.0 / 25 kg')
    save(im, 'screens', 'T_Screen_Science.png')

    im, d = screen_base(W, H, 'MOBILITY', 'wheels | computer / AutoNav')
    option_cards(d, ['STANDARD', 'REINFORCED', 'SELF-DRIVING'], 1, 40, 100, W - 80, 90)
    xs = np.arange(60, W - 60, 6); ys = 420 + np.cumsum(rng.normal(0, 3.2, xs.size)).clip(-70, 70)
    d.line(list(zip(xs.tolist(), ys.tolist())), fill=CYAN, width=3); d.text((60, 300), 'TERRAIN PROFILE  |  ROCK FIELD', font=font(22, 'Regular'), fill=CYAN)
    for i, cx in enumerate((300, 512, 724)):                              # rocker-bogie schematic
        d.ellipse([cx - 34, 520, cx + 34, 588], outline=WHITE, width=4)
    d.line([(300, 554), (420, 500), (512, 554)], fill=WHITE, width=4); d.line([(420, 500), (724, 554)], fill=WHITE, width=4)
    save(im, 'screens', 'T_Screen_Mobility.png')

    im, d = screen_base(W, H, 'COMMUNICATIONS', 'relay | direct-to-Earth')
    option_cards(d, ['UHF RELAY', 'RELAY + DIRECT-TO-EARTH'], 1, 40, 100, W - 80, 90)
    for k, a in enumerate((60, 40, 25)):
        pts = [(60 + i * 4, 400 + a * math.sin(i / (12 + k * 5))) for i in range(226)]
        d.line(pts, fill=CYAN if k else ORANGE, width=3)
    d.text((60, 300), 'LINK BUDGET  |  NEXT PASS 04:12', font=font(22, 'Regular'), fill=CYAN)
    bar(d, 60, 560, W - 120, 30, 0.55, 'DATA VOLUME PER SOL')
    save(im, 'screens', 'T_Screen_Comms.png')

    im, d = screen_base(W, H, 'MISSION CONFIGURATION', 'step 01')
    d.text((40, 100), 'LAUNCH VEHICLE', font=font(24, 'Regular'), fill=CYAN)
    for i, (nm, kg, usd) in enumerate((('MEDIUM', '900 kg', '$150M'), ('HEAVY', '1,100 kg', '$250M'))):
        x = 40 + i * 482; on = i == 1
        d.rounded_rectangle([x, 140, x + 460, 380], 14, outline=ORANGE if on else GRID, width=4 if on else 2, fill=(14, 30, 52) if on else NAVY_BG)
        d.text((x + 230, 200), nm, font=font(48), fill=WHITE, anchor='mm')
        d.text((x + 230, 275), f'payload limit  {kg}', font=font(28, 'Regular'), fill=CYAN, anchor='mm')
        d.text((x + 230, 330), f'budget  {usd}', font=font(28, 'Regular'), fill=CYAN, anchor='mm')
    bar(d, 40, 470, W - 80, 40, 0.0, 'ROVER MASS  0 / 1,100 kg'); bar(d, 40, 570, W - 80, 40, 0.38, 'BUDGET USED', ORANGE)
    save(im, 'screens', 'T_Screen_MissionConfig.png')

def dt_screen(lineart_path=None):
    """Digital Twin wall (2:1). Uses a line-art render of the real rover when available."""
    W, H = 2048, 1024
    im, d = screen_base(W, H, 'DIGITAL TWIN   |   RF-01', 'prediction model  |  awaiting run')
    if lineart_path and os.path.exists(lineart_path):
        la = Image.open(lineart_path).convert('L').resize((1100, 760))
        tint = Image.new('RGB', la.size, CYAN)
        im.paste(tint, (90, 150), la)
    for i, (lab, val, frac, col) in enumerate((('MASS', '1,025 / 1,100 kg', 0.93, ORANGE), ('POWER', '110 W nuclear', 0.6, CYAN),
                                               ('BUDGET', '$212M / $250M', 0.85, CYAN), ('RISK', 'MODERATE', 0.45, AMBER))):
        y = 190 + i * 170
        d.text((1300, y), lab, font=font(30, 'Regular'), fill=CYAN); d.text((1980, y), val, font=font(34), fill=WHITE, anchor='ra')
        d.rectangle([1300, y + 55, 1980, y + 85], outline=GRID, width=2); d.rectangle([1303, y + 58, 1303 + 674 * frac, y + 82], fill=col)
    d.rounded_rectangle([1300, 880, 1980, 960], 12, outline=ORANGE, width=4)
    d.text((1640, 920), 'RUN DIGITAL TWIN', font=font(36), fill=WHITE, anchor='mm')
    save(im, 'screens', 'T_Screen_DigitalTwin.png')

# ============================================================================= DECALS
def text_decal(name, body, size=180, color=WHITE, pad=24, style='SemiBold'):
    f = font(size, style)
    l, t, r, b = f.getbbox(body)
    im = Image.new('RGBA', (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l, pad - t), body, font=f, fill=color)
    save(im, 'decals', f'T_Decal_{name}.png'); return im.size

def step_badge(n):
    s = 512; im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([16, 16, s - 16, s - 16], outline=ORANGE + (255,), width=26)
    d.text((s / 2, s / 2 + 8), f'{n:02d}', font=font(230, 'Bold'), fill=WHITE + (255,), anchor='mm')
    save(im, 'decals', f'T_Decal_Step{n:02d}.png')

def hazard(name, w=1024, h=128, stripe=64):
    im = Image.new('RGBA', (w, h), AMBER + (255,)); d = ImageDraw.Draw(im)
    for x in range(-h, w + h, stripe * 2):
        d.polygon([(x, h), (x + stripe, h), (x + stripe + h, 0), (x + h, 0)], fill=(24, 24, 26, 255))
    save(im, 'decals', f'T_Decal_{name}.png')

def turntable_ring(s=2048):
    """Degree ring painted on the turntable: tick every 5 deg, label every 30 deg."""
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    R = s / 2 - 20
    for a in range(0, 360, 5):
        r = math.radians(a); L = 70 if a % 30 == 0 else 34; W = 8 if a % 30 == 0 else 4
        d.line([(c + math.cos(r) * (R - L), c + math.sin(r) * (R - L)), (c + math.cos(r) * R, c + math.sin(r) * R)], fill=(43, 46, 51, 235), width=W)
        if a % 30 == 0:
            tr = R - 120
            d.text((c + math.cos(r) * tr, c + math.sin(r) * tr), f'{(90 - a) % 360:03d}', font=font(44), fill=(43, 46, 51, 235), anchor='mm')
    save(im, 'decals', 'T_Decal_TurntableRing.png')

def insignia(s=1024):
    """Red Frontier mark: Mars disc, horizon line, ascending chevron."""
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    d.ellipse([60, 60, s - 60, s - 60], outline=WHITE + (255,), width=34)
    d.pieslice([150, 150, s - 150, s - 150], 180, 360, fill=ORANGE + (255,))
    d.rectangle([150, c - 8, s - 150, c + 14], fill=WHITE + (255,))
    d.line([(c - 170, c - 60), (c, c - 230), (c + 170, c - 60)], fill=WHITE + (255,), width=40, joint='curve')
    save(im, 'decals', 'T_Decal_Insignia.png')

# ===================================================================== POLISH PASS
def floor_wear(s=1024):
    """Very light traffic wear: soft darkening with fine scratch arcs. Alpha tops out ~0.2."""
    m = noise(s, 3, 4); fine = noise(s, 48, 2)
    yy, xx = np.mgrid[0:s, 0:s] / s - 0.5
    fall = np.clip(1 - (np.sqrt(xx ** 2 + yy ** 2) / 0.5) ** 1.6, 0, 1)            # fades out at the edges
    a = np.clip((m - 0.42) * 1.4, 0, 1) * fall * 0.16 + np.clip(fine - 0.6, 0, 1) * fall * 0.12
    im = Image.new('RGBA', (s, s)); arr = np.zeros((s, s, 4), np.float32)
    arr[..., :3] = (56, 58, 61); arr[..., 3] = a * 255
    im = Image.fromarray(arr.astype(np.uint8), 'RGBA'); d = ImageDraw.Draw(im)
    for _ in range(26):                                                                # scratch arcs
        cx, cy, r = rng.uniform(0.25, 0.75) * s, rng.uniform(0.25, 0.75) * s, rng.uniform(0.1, 0.4) * s
        a0 = rng.uniform(0, 360); d.arc([cx - r, cy - r, cx + r, cy + r], a0, a0 + rng.uniform(8, 30), fill=(70, 72, 75, 34), width=1)
    save(im, 'decals', 'T_Decal_FloorWear.png')

def scuffs(w=1024, h=256):
    """Cart-wheel scuffs: two faint parallel streaks."""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for y in (h * 0.3, h * 0.7):
        for k in range(5):
            dy = rng.normal(0, 4)
            d.line([(30, y + dy), (w - 30, y + dy + rng.normal(0, 6))], fill=(40, 42, 45, 22), width=int(rng.integers(3, 9)))
    save(im.filter(ImageFilter.GaussianBlur(2.5)), 'decals', 'T_Decal_Scuffs.png')

ATLAS_CELLS = [  # name, kind, text
    *[(f'PORT_P{i}', 'plate', f'SERVICE PORT  P{i}\n28 V DC  |  DATA') for i in range(1, 7)],
    ('CAUTION_LIVE', 'caution', 'CAUTION\nLIVE CONNECTOR'),
    *[(f'HATCH_H{i}', 'plate', f'MAINT ACCESS  H-0{i}\nNO STEP') for i in range(1, 4)],
    ('LOAD', 'plate', 'TURNTABLE\nLOAD LIMIT 1,500 kg'),
    ('INSPECT', 'sticker', 'QC\n09/26'),
    *[(f'EQ0{i}', 'plate', f'EQ-0{i}\n{n}') for i, n in enumerate(('POWER DIST.', 'DATA RACK', 'COOLANT', 'TOOLING', 'SPARES'), 1)],
    ('GROUND', 'plate', 'ESD GROUND POINT\nconnect before service'),
    ('CRANE_SWL', 'plate', 'SWL  10 t'),
    ('TORQUE', 'plate', 'TORQUE CHECKED\n45 Nm'),
]

def service_atlas(S=2048, cols=4, rows=8):
    """All small service labels in one texture (one material in Godot). Writes a JSON UV map."""
    import json
    cw, ch = S // cols, S // rows
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); uv = {}
    for idx, (name, kind, body) in enumerate(ATLAS_CELLS):
        cx, cy = (idx % cols) * cw, (idx // cols) * ch
        box = [cx + 10, cy + 10, cx + cw - 10, cy + ch - 10]
        if kind == 'plate':
            d.rounded_rectangle(box, 14, fill=(36, 39, 43, 240), outline=(200, 205, 212, 255), width=4)
            d.multiline_text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), body, font=font(46), fill=WHITE + (255,), anchor='mm', align='center', spacing=10)
        elif kind == 'caution':                         # drawn in its own cell image so stripes cannot bleed
            bw, bh = box[2] - box[0], box[3] - box[1]
            cell = Image.new('RGBA', (bw, bh), AMBER + (255,)); cd = ImageDraw.Draw(cell)
            for x in range(-60, bw + 60, 48):
                cd.polygon([(x, bh), (x + 24, bh), (x + 64, bh - 40), (x + 40, bh - 40)], fill=(24, 24, 26, 255))
            cd.multiline_text((bw / 2, 70), body, font=font(46, 'Bold'), fill=(24, 24, 26, 255), anchor='mm', align='center', spacing=6)
            im.alpha_composite(cell, (box[0], box[1]))
        elif kind == 'sticker':
            r = (ch - 30) / 2; mx, my = cx + cw / 2, cy + ch / 2
            d.ellipse([mx - r, my - r, mx + r, my + r], fill=(236, 238, 240, 255), outline=(43, 46, 51, 255), width=6)
            d.multiline_text((mx, my), body, font=font(52, 'Bold'), fill=(43, 46, 51, 255), anchor='mm', align='center')
        uv[name] = [cx / S, 1 - (cy + ch) / S, (cx + cw) / S, 1 - cy / S]     # u0, v0, u1, v1 (Blender UV, v up)
    save(im, 'decals', 'T_Decal_ServiceAtlas.png')
    json.dump({'cell_aspect': cw / ch, 'cells': uv}, open(os.path.join(ROOT, 'decals', 'T_Decal_ServiceAtlas.json'), 'w'), indent=1)

if __name__ == '__main__':
    floor_wear(); scuffs(); service_atlas()
    floor_epoxy(); grate(); roof_deck(); brushed()
    screens(); dt_screen(os.path.join(ROOT, 'screens', 'rover_lineart.png'))
    for n in range(1, 7): step_badge(n)
    hazard('Hazard'); turntable_ring(); insignia()
    for name, body in (('POWER', 'POWER'), ('SCIENCE', 'SCIENCE'), ('MOBILITY', 'MOBILITY'), ('COMMS', 'COMMS'),
                       ('MissionConfig', 'MISSION CONFIGURATION'), ('DigitalTwin', 'DIGITAL TWIN'),
                       ('EngineeringHangar', 'ENGINEERING HANGAR'), ('FlightOps', 'FLIGHT OPERATIONS'),
                       ('MissionControl', 'MISSION CONTROL'), ('WorkBay', 'RF-01  WORK BAY'), ('RF01', 'RF-01')):
        text_decal(name, body)
    text_decal('NoStep', 'NO STEP', 120, GRAPHITE + (255,))
    text_decal('Caution', 'CAUTION  ROTATING PLATFORM', 120, GRAPHITE + (255,))
    for i in range(1, 6): text_decal(f'ColumnH{i}', f'H{i}', 200, WHITE)
    for name, body in (('Dec_POWER', 'power  |  battery  |  thermal'), ('Dec_SCIENCE', '3 instrument slots  |  mission style'),
                       ('Dec_MOBILITY', 'wheels  |  computer / AutoNav'), ('Dec_COMMS', 'communications'),
                       ('Dec_MissionConfig', 'launch vehicle  |  payload limit  |  budget')):
        text_decal(name, body, 80, (200, 210, 222), style='Regular')
    print('TEXTURES_OK', sum(len(f) for _, _, f in os.walk(ROOT)))
