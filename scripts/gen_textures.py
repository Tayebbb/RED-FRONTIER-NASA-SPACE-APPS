"""
gen_textures.py - procedural texture set for the Red Frontier facility (system Python: numpy + PIL).

Writes PNGs to textures/{surfaces,screens,decals}. Everything here is a plain
image so it survives glTF export and works unchanged in Godot (no Blender-only nodes).
Normal maps are OpenGL convention (+Y), which both Blender and Godot 4 expect.

Run:  python scripts/gen_textures.py
"""
import os, sys, math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "textures")
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
def noise(size, cells, octaves=4, persistence=0.5, r=None):
    r = r or rng
    out = np.zeros((size, size), np.float32); amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = cells * 2 ** o
        g = r.random((c, c)).astype(np.float32)
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
def screen_base(w, h, title, sub=None, s=1.0):
    """Navy UI page: grid, header bar, orange identity tab. s scales the chrome for large walls."""
    im = Image.new('RGB', (w, h), NAVY_BG); d = ImageDraw.Draw(im); g, hb = round(40 * s), round(70 * s)
    for x in range(0, w, g): d.line([(x, 0), (x, h)], fill=(12, 24, 40))
    for y in range(0, h, g): d.line([(0, y), (w, y)], fill=(12, 24, 40))
    d.rectangle([0, 0, w, hb], fill=(10, 22, 40)); d.line([(0, hb), (w, hb)], fill=GRID, width=max(2, round(2 * s)))
    d.rectangle([round(28 * s), round(22 * s), round(36 * s), round(48 * s)], fill=ORANGE)   # identity tab
    d.text((round(52 * s), round(16 * s)), title, font=font(round(36 * s)), fill=WHITE)
    if sub: d.text((w - round(28 * s), round(24 * s)), sub, font=font(round(22 * s), 'Regular'), fill=CYAN, anchor='ra')
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
    # Phase 5 - Mission Control (appended, so the Hangar's cells keep their UVs)
    *[(f'POS_{k}', 'plate', f'{k}\n{n}') for k, n in (('FLIGHT', 'flight director'), ('TRAJECTORY', 'cruise navigation'),
        ('EDL', 'entry  |  descent  |  landing'), ('SURFACE', 'surface operations'), ('POWER', 'power  |  thermal'),
        ('TELECOM', 'relay  |  direct-to-Earth'), ('SCIENCE', 'payload operations'), ('MOBILITY', 'drive  |  AutoNav'))],
    ('EQ11', 'plate', 'EQ-11\nGROUND DATA'), ('EQ12', 'plate', 'EQ-12\nNETWORK'),
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

# ================================================================ PHASE 5: MISSION CONTROL
# Same UI language as the Hangar screens. The decisions made upstream (vehicle, site, build)
# reappear here as confirmations: Mission Control adds no new decision except the launch.
rng5 = np.random.default_rng(21)                     # own stream: regenerating these never shifts Hangar textures
RUST = (150, 72, 48)                                 # Mars body in diagrams (not UI orange)

def access_floor(size=1024, tiles=4):
    """Raised access floor, 0.6 m tiles: one texture = 2.4 m. Per-tile tone shift, fine joints."""
    t = size // tiles
    tone = np.kron(rng5.normal(0, 0.012, (tiles, tiles)), np.ones((t, t))).astype(np.float32)
    base = 0.36 + tone + (noise(size, 8, 3, r=rng5) - 0.5) * 0.03 + (noise(size, 96, 2, r=rng5) - 0.5) * 0.02
    joint = np.zeros((size, size), np.float32)
    for k in range(tiles):
        a = k * t
        joint[a:a + 2, :] = 1.0; joint[:, a:a + 2] = 1.0
        joint[(a - 2) % size:(a - 2) % size + 2, :] = np.maximum(joint[(a - 2) % size:(a - 2) % size + 2, :], 0.5)
    col = np.dstack((base * 0.98, base * 1.0, base * 1.03)); col[joint >= 1] *= 0.35
    save(to_img(col), 'surfaces', 'T_Floor_Access_BaseColor.png')
    save(to_img(0.55 + (noise(size, 16, 3, r=rng5) - 0.5) * 0.1 + joint * 0.3), 'surfaces', 'T_Floor_Access_Roughness.png')
    save(normal_from_height(-joint, 1.5), 'surfaces', 'T_Floor_Access_Normal.png')

def pill(d, xy, text, size, col=CYAN, fill=(14, 30, 52), w=3):
    x0, y0, x1, y1 = xy
    d.rounded_rectangle(xy, (y1 - y0) // 2, outline=col, width=w, fill=fill)
    d.text(((x0 + x1) / 2, (y0 + y1) / 2), text, font=font(size), fill=WHITE, anchor='mm')

def label_value(d, x, x2, y, lab, val, s=1.0):
    d.text((x, y), lab, font=font(round(24 * s), 'Regular'), fill=CYAN)
    d.text((x2, y - round(3 * s)), val, font=font(round(28 * s)), fill=WHITE, anchor='ra')

def bar2(d, x, y, w, h, frac, col=CYAN):
    d.rectangle([x, y, x + w, y + h], outline=GRID, width=2); d.rectangle([x + 3, y + 3, x + 3 + (w - 6) * frac, y + h - 3], fill=col)

def transfer_diagram(d, cx, cy, r1, r2, s=1.0):
    """Sun, Earth and Mars orbits, Hohmann transfer (upper half), craft marker."""
    d.ellipse([cx - 9 * s, cy - 9 * s, cx + 9 * s, cy + 9 * s], fill=(255, 214, 140))
    for r in (r1, r2): d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GRID, width=round(3 * s))
    a, c = (r1 + r2) / 2, (r2 - r1) / 2; b = math.sqrt(r1 * r2); ex = cx + c
    pts = [(ex - a * math.cos(t), cy - b * math.sin(t)) for t in np.linspace(0, math.pi, 90)]
    for i in range(0, len(pts) - 1, 2): d.line([pts[i], pts[i + 1]], fill=CYAN, width=round(4 * s))
    ea, ma = (cx - r1, cy), (cx + r2, cy)
    d.ellipse([ea[0] - 13 * s, ea[1] - 13 * s, ea[0] + 13 * s, ea[1] + 13 * s], fill=(70, 140, 220))
    d.ellipse([ma[0] - 11 * s, ma[1] - 11 * s, ma[0] + 11 * s, ma[1] + 11 * s], fill=RUST)
    k = pts[28]; d.ellipse([k[0] - 7 * s, k[1] - 7 * s, k[0] + 7 * s, k[1] + 7 * s], fill=WHITE)
    return ea, ma

def mc_main():
    """Front wall, 8:3. Left trajectory | centre countdown + status | right confirmed configuration."""
    W, H, s = 2400, 900, 1.9
    im, d = screen_base(W, H, 'RED FRONTIER   |   MISSION CONTROL', 'launch window open  |  pad 39A', s)
    top = round(70 * s)
    for x in (800, 1600): d.line([(x, top + 30), (x, H - 120)], fill=GRID, width=3)
    d.text((60, top + 40), 'TRAJECTORY   EARTH  >  MARS', font=font(38, 'Regular'), fill=CYAN)
    ea, ma = transfer_diagram(d, 400, 520, 175, 265, 1.4)
    d.text((ea[0] - 10, ea[1] + 26), 'EARTH', font=font(28), fill=WHITE, anchor='ma')
    d.text((ma[0] - 10, ma[1] + 26), 'MARS', font=font(28), fill=WHITE, anchor='ma')
    d.text((400, H - 175), 'transfer  205 days   |   arrival  Ls 34', font=font(30, 'Regular'), fill=CYAN, anchor='mm')
    d.text((1200, top + 70), 'COUNTDOWN', font=font(40, 'Regular'), fill=CYAN, anchor='mm')
    d.text((1200, top + 215), 'T - 00:02:18', font=font(150), fill=WHITE, anchor='mm')
    d.text((1200, top + 385), 'MISSION STATUS', font=font(40, 'Regular'), fill=CYAN, anchor='mm')
    pill(d, [1030, top + 430, 1370, top + 540], 'GO', 84)
    d.text((1200, H - 175), 'LAUNCH VEHICLE  HEAVY   |   CONFIRMED', font=font(32, 'Regular'), fill=CYAN, anchor='mm')
    x, x2 = 1660, 2340
    d.text((x, top + 40), 'RF-01   FLIGHT CONFIGURATION', font=font(38, 'Regular'), fill=CYAN)
    d.rounded_rectangle([x, top + 100, x2, top + 200], 14, outline=ORANGE, width=5, fill=(14, 30, 52))
    d.text((x + 30, top + 150), 'HEAVY', font=font(56), fill=WHITE, anchor='lm')
    d.text((x2 - 30, top + 150), 'payload limit  1,100 kg', font=font(30, 'Regular'), fill=CYAN, anchor='rm')
    rows = (('ROVER MASS', '1,025 / 1,100 kg', 0.93, CYAN), ('BUDGET', '$212M / $250M', 0.85, CYAN), ('RISK', 'MODERATE', 0.45, AMBER))
    for i, (lab, val, frac, col) in enumerate(rows):
        y = top + 250 + i * 105
        label_value(d, x, x2, y, lab, val, 1.25); bar2(d, x, y + 45, x2 - x, 26, frac, col)
    label_value(d, x, x2, H - 190, 'LANDING', 'SITE B  |  PRECISION', 1.25)
    names = ('RANGE', 'WEATHER', 'VEHICLE', 'RF-01', 'TELECOM', 'FLIGHT')
    pw = (W - 120 - 5 * 24) / 6
    for i, n in enumerate(names):
        x0 = 60 + i * (pw + 24)
        d.rounded_rectangle([x0, H - 95, x0 + pw, H - 35], 30, outline=GRID, width=3, fill=(10, 22, 40))
        d.text((x0 + 34, H - 65), n, font=font(30, 'Regular'), fill=CYAN, anchor='lm')
        d.text((x0 + pw - 34, H - 65), 'GO', font=font(32), fill=WHITE, anchor='rm')
    save(im, 'screens', 'T_Screen_MC_Main.png')

POSITIONS = ('FLIGHT', 'TRAJECTORY', 'EDL', 'SURFACE', 'POWER', 'TELECOM', 'SCIENCE', 'MOBILITY')

def mc_side_panels():
    W, H = 600, 1246                                                    # 1.3 x 2.7 m portrait
    im, d = screen_base(W, H, 'GO / NO-GO', 'poll', 1.15)
    for i, n in enumerate(POSITIONS):
        y = 130 + i * 118
        d.line([(36, y + 100), (W - 36, y + 100)], fill=GRID, width=2)
        d.text((40, y + 50), n, font=font(40), fill=WHITE, anchor='lm')
        pill(d, [W - 190, y + 22, W - 40, y + 80], 'GO', 36)
    d.text((W / 2, H - 70), 'POLL COMPLETE   8 / 8', font=font(32, 'Regular'), fill=CYAN, anchor='mm')
    save(im, 'screens', 'T_Screen_MC_GoNoGo.png')

    im, d = screen_base(W, H, 'READINESS', 'risk', 1.15)
    cx, cy, R = W / 2, 470, 220                                           # risk gauge: low -> high, needle at moderate
    for k in range(60):
        a0, a1 = 180 + k * 3, 180 + k * 3 + 2.2
        col = CYAN if k < 30 else (AMBER if k < 48 else (200, 70, 60))
        d.arc([cx - R, cy - R, cx + R, cy + R], a0, a1, fill=col, width=34)
    a = math.radians(180 + 0.58 * 180)
    d.line([(cx, cy), (cx + math.cos(a) * (R - 50), cy + math.sin(a) * (R - 50))], fill=WHITE, width=8)
    d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=WHITE)
    d.text((cx, cy + 60), 'MODERATE', font=font(56), fill=WHITE, anchor='mm')
    checks = ('mass within payload limit', 'power margin positive', 'landing site reachable', 'budget within cap', 'digital twin prediction run')
    for i, c in enumerate(checks):
        y = 640 + i * 82
        d.rounded_rectangle([40, y, 82, y + 42], 6, outline=CYAN, width=3)
        d.line([(49, y + 22), (59, y + 33), (75, y + 10)], fill=WHITE, width=5)
        d.text((104, y + 21), c, font=font(30, 'Regular'), fill=WHITE, anchor='lm')
    d.rounded_rectangle([40, H - 170, W - 40, H - 60], 14, outline=ORANGE, width=5)
    d.text((W / 2, H - 115), 'ACCEPT RISK & LAUNCH', font=font(40), fill=WHITE, anchor='mm')
    save(im, 'screens', 'T_Screen_MC_Readiness.png')

def mc_wall_screens(lineart_path):
    W, H = 1280, 720
    im, d = screen_base(W, H, 'RF-01   BUILD SHEET', 'from the digital twin', 1.2)
    if lineart_path and os.path.exists(lineart_path):
        la = Image.open(lineart_path).convert('L').resize((620, 430))
        im.paste(Image.new('RGB', la.size, CYAN), (30, 160), la)
    rows = (('SCIENCE', 'camera  |  laser  |  organics'), ('POWER', 'nuclear  110 W'), ('MOBILITY', 'reinforced wheels'),
            ('COMMS', 'relay + direct-to-Earth'), ('MASS', '1,025 kg'))
    for i, (k, v) in enumerate(rows):
        y = 170 + i * 92
        d.text((700, y), k, font=font(26, 'Regular'), fill=CYAN); d.text((700, y + 34), v, font=font(34), fill=WHITE)
        d.line([(700, y + 82), (W - 40, y + 82)], fill=GRID, width=2)
    save(im, 'screens', 'T_Screen_MC_Rover.png')

    im, d = screen_base(W, H, 'LANDING   |   JEZERO REGION', 'precision landing', 1.2)
    top = 84; mh = H - top - 20
    z = noise(512, 5, 4, r=rng5); z = np.asarray(Image.fromarray((z * 255).astype(np.uint8)).resize((W - 40, mh), Image.BICUBIC), np.float32) / 255
    lv = (np.floor(z * 14) % 2).astype(np.float32)
    edge = (np.abs(np.diff(lv, axis=0, prepend=lv[:1])) + np.abs(np.diff(lv, axis=1, prepend=lv[:, :1]))) > 0
    m = np.zeros((mh, W - 40, 3), np.uint8); m[:] = NAVY_BG; m[edge] = (34, 66, 98)
    im.paste(Image.fromarray(m), (20, top)); d = ImageDraw.Draw(im)
    for nm, (x, y, col, w) in {'A': (300, 300, CYAN, 3), 'B': (640, 420, ORANGE, 6), 'C': (960, 260, AMBER, 3)}.items():
        rx, ry = (120, 60) if nm != 'B' else (70, 36)                      # precision landing shrinks the ellipse
        d.ellipse([x - rx, y - ry, x + rx, y + ry], outline=col, width=w)
        d.text((x, y), nm, font=font(48), fill=WHITE, anchor='mm')
    d.text((640, H - 60), 'SITE B   |   ellipse 7.7 x 6.6 km   |   delta front', font=font(30, 'Regular'), fill=WHITE, anchor='mm')
    save(im, 'screens', 'T_Screen_MC_Landing.png')

def mc_ops_atlas():
    """All operator monitors in one texture (2 x 2 cells, 16:9) so 16 monitors share one material."""
    CW, CH = 1024, 576; atlas = Image.new('RGB', (2 * CW, 2 * CH))
    im, d = screen_base(CW, CH, 'TELEMETRY', 'live')
    for k, (lab, col) in enumerate((('BUS VOLTAGE', CYAN), ('AVIONICS TEMP', AMBER), ('DOWNLINK RATE', CYAN))):
        y0 = 110 + k * 150
        d.text((40, y0), lab, font=font(22, 'Regular'), fill=CYAN)
        ys = y0 + 80 + (np.cumsum(rng5.normal(0, 2.4, 230)) * 0.35).clip(-45, 45)
        d.line(list(zip(np.linspace(40, CW - 40, 230).tolist(), ys.tolist())), fill=col, width=3)
    atlas.paste(im, (0, 0))
    im, d = screen_base(CW, CH, 'SUBSYSTEMS', 'nominal')
    for i in range(9):
        y = 100 + i * 50
        d.text((40, y), ('BATT A', 'BATT B', 'RTG OUT', 'HEATER 1', 'HEATER 2', 'UHF', 'X-BAND', 'CPU A', 'CPU B')[i], font=font(26, 'Regular'), fill=CYAN)
        for j in range(3): d.text((470 + j * 190, y), f'{rng5.uniform(10, 99):.1f}', font=font(28), fill=WHITE, anchor='ra')
    atlas.paste(im, (CW, 0))
    im, d = screen_base(CW, CH, 'CRUISE', 'trajectory')
    transfer_diagram(d, 512, 330, 115, 175)
    atlas.paste(im, (0, CH))
    im, d = screen_base(CW, CH, 'POWER DISTRIBUTION', 'bus A | bus B')
    boxes = [(80, 150), (80, 330), (420, 240), (760, 130), (760, 240), (760, 350), (760, 460)]
    for (x, y) in boxes[3:]: d.line([(560, 265), (760, y + 25)], fill=GRID, width=3)
    for (x, y) in boxes[:2]: d.line([(220, y + 25), (420, 265)], fill=GRID, width=3)
    for i, (x, y) in enumerate(boxes):
        d.rounded_rectangle([x, y, x + 140, y + 50], 8, outline=CYAN, width=2, fill=(14, 30, 52))
        d.text((x + 70, y + 25), ('RTG', 'BATT', 'PDU', 'SCI', 'MOB', 'COMM', 'HEAT')[i], font=font(24), fill=WHITE, anchor='mm')
    atlas.paste(im, (CW, CH))
    save(atlas, 'screens', 'T_Screen_MC_OpsAtlas.png')

def mc_launch_console():
    W, H = 1024, 380
    im, d = screen_base(W, H, 'LAUNCH AUTHORITY', 'final confirmation')
    for i, (k, v) in enumerate((('VEHICLE', 'HEAVY'), ('SITE', 'B  |  PRECISION'), ('RISK', 'MODERATE'))):
        y = 110 + i * 80
        d.text((40, y), k, font=font(24, 'Regular'), fill=CYAN); d.text((40, y + 30), v, font=font(32), fill=AMBER if k == 'RISK' else WHITE)
    d.rounded_rectangle([470, 120, W - 40, H - 50], 18, outline=ORANGE, width=6, fill=(14, 30, 52))
    d.text(((470 + W - 40) / 2, 210), 'ACCEPT RISK', font=font(52), fill=WHITE, anchor='mm')
    d.text(((470 + W - 40) / 2, 275), '& LAUNCH', font=font(52), fill=WHITE, anchor='mm')
    save(im, 'screens', 'T_Screen_MC_Launch.png')

def mission_control_set():
    access_floor()
    mc_main(); mc_side_panels(); mc_ops_atlas(); mc_launch_console()
    mc_wall_screens(os.path.join(ROOT, 'screens', 'rover_lineart.png'))
    text_decal('LaunchAuthority', 'LAUNCH AUTHORITY', 140)
    service_atlas()

# ============================================================== PHASE 5: MARS INTELLIGENCE
# One terrain drives everything here: the relief table (height + colour), the map wall and the site screens.
# Table-local metres: x -2..2 (east), y -1.2..1.2 (north). Jezero-like: crater (D 45 km = 2.0 m on the table,
# 1 m = 22.5 km), inflow channel from the west, delta fan inside the breach, boulder field near site C.
rng6 = np.random.default_rng(33)
TW, TH = 1500, 900                                   # 5:3 like the 4.0 x 2.4 m table
CRATER, CR = (0.95, 0.05), 1.0
ENTRY_A = math.radians(150)
SITES = {'A': (-1.2, -0.5), 'B': (0.4, 0.6), 'C': (1.3, -0.5)}       # greybox site positions, table-local
ELLIPSE = (0.17, 0.145)                              # precision landing 7.7 x 6.6 km, semi-axes on the table
SITE_COL = {'A': CYAN, 'B': ORANGE, 'C': AMBER}       # B = the selected site, C = needs precision landing

def _grid():
    xs = np.linspace(-2, 2, TW); ys = np.linspace(1.2, -1.2, TH)       # image row 0 = north
    return np.meshgrid(xs, ys)

def blur(a, k):
    """Separable box blur x3 (~Gaussian), float precision, edges clamped."""
    for _ in range(3):
        for ax in (0, 1):
            p = np.pad(a, [(k, k) if i == ax else (0, 0) for i in (0, 1)], mode='edge'); c = np.cumsum(p, axis=ax, dtype=np.float64)
            c = np.concatenate([np.zeros_like(c.take([0], axis=ax)), c], axis=ax)
            n = a.shape[ax]; a = ((c.take(range(2 * k + 1, 2 * k + 1 + n), axis=ax) - c.take(range(0, n), axis=ax)) / (2 * k + 1)).astype(np.float32)
    return a

def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def mars_height():
    """0..1 relief (1.0 = 6 cm on the table). Deterministic from rng6."""
    X, Y = _grid()
    def fbm(cells, oct_):
        n = noise(1024, cells, oct_, r=rng6)
        return np.asarray(Image.fromarray((n * 65535).astype(np.uint16)).resize((TW, TH), Image.BICUBIC), np.float32) / 65535
    h = 0.42 + (fbm(3, 5) - 0.5) * 0.22 + (fbm(24, 3) - 0.5) * 0.04
    dx, dy = X - CRATER[0], Y - CRATER[1]; r = np.hypot(dx, dy) / CR; ang = np.arctan2(dy, dx)
    breach = 1 - 0.85 * np.exp(-((np.angle(np.exp(1j * (ang - ENTRY_A)))) / 0.16) ** 2)
    h += np.where(r < 1, -0.24 * (1 - smooth(0.82, 1.0, r)), 0)                         # flat floor, wall
    h += 0.30 * np.exp(-((r - 1) / 0.06) ** 2) * breach + np.where(r > 1, 0.08 * np.exp(-(r - 1) / 0.3), 0)
    ex, ey = CRATER[0] + CR * math.cos(ENTRY_A), CRATER[1] + CR * math.sin(ENTRY_A)
    path = ey + 0.06 * np.sin(X * 4.0) - 0.03 * (X - ex)                                 # inflow channel, west of the breach
    h -= 0.16 * np.exp(-((Y - path) / 0.035) ** 2) * (1 - smooth(ex - 0.02, ex + 0.12, X))           # fades out on the fan
    fx, fy = X - ex, Y - ey; fd = np.hypot(fx, fy); fa = np.arctan2(fy, fx)               # delta fan toward the crater centre
    toward = math.atan2(CRATER[1] - ey, CRATER[0] - ex)
    lobes = 0.28 * (1 + 0.12 * np.sin(fa * 9) + (fbm(12, 2) - 0.5) * 0.25)
    spread = 1 - smooth(0.7, 1.15, np.abs(np.angle(np.exp(1j * (fa - toward)))))       # soft fan sides, no straight edges
    h += 0.14 * spread * (1 - smooth(0.9, 1.0, r)) * smooth(0.0, 0.03, lobes - fd) * (1 - 0.35 * fd / 0.28)
    craters = [(rng6.uniform(-1.9, 1.9), rng6.uniform(-1.1, 1.1), rng6.uniform(0.025, 0.09)) for _ in range(26)]
    craters += [(SITES['C'][0] + rng6.normal(0, 0.12), SITES['C'][1] + rng6.normal(0, 0.09), rng6.uniform(0.008, 0.025)) for _ in range(40)]
    for cx, cy, cr in craters:
        if any(math.hypot(cx - sx, cy - sy) < 0.2 for k, (sx, sy) in SITES.items() if k != 'C'): continue
        q = np.hypot(X - cx, Y - cy) / cr
        h += np.where(q < 1, -0.06 * (1 - q ** 2), 0) * (cr / 0.06) ** 0.5 + 0.03 * np.exp(-((q - 1) / 0.25) ** 2) * (cr / 0.06) ** 0.5
    bould = (rng6.random((TH, TW)) > 0.9975) * np.exp(-np.hypot(X - SITES['C'][0], Y - SITES['C'][1]) ** 2 / 0.06)
    h += np.asarray(Image.fromarray((bould * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255 * 0.08
    return np.clip(h, 0, 1)

def mars_colour(h, contours=True):
    """Hypsometric rust tints + hillshade (light from NW); delta deposits lighter; fine contours."""
    lo, mid, hi, dust = np.array((62, 44, 38)), np.array((142, 78, 50)), np.array((192, 124, 80)), np.array((214, 168, 122))
    t = np.clip((h - 0.15) / 0.6, 0, 1)[..., None]
    col = np.where(t < 0.5, lo + (mid - lo) * (t / 0.5), mid + (hi - mid) * ((t - 0.5) / 0.5))
    gy, gx = np.gradient(h * 60)
    shade = np.clip(0.78 + (-gx + gy) * 0.55, 0.35, 1.25)[..., None]
    col = col * shade
    if h.shape != (TH, TW): return np.clip(col, 0, 255).astype(np.uint8)          # legend ramps: tint only
    X, Y = _grid()
    ex, ey = CRATER[0] + CR * math.cos(ENTRY_A), CRATER[1] + CR * math.sin(ENTRY_A)
    delta = np.exp(-(np.hypot(X - ex - 0.14, Y - ey + 0.08) / 0.2) ** 2)[..., None]
    col = col * (1 - 0.35 * delta) + dust * 0.35 * delta
    if contours:                                         # from a smoothed height, so plains noise never reads as cracks
        hs = blur(h, 6)
        c = np.abs((hs * 22) % 1 - 0.5) > 0.475
        col[c] = col[c] * 0.78
    return np.clip(col, 0, 255).astype(np.uint8)

def to_px(x, y, W=TW, H=TH, x0=0, y0=0):
    return (x0 + (x + 2) / 4 * W, y0 + (1.2 - y) / 2.4 * H)

def ellipse(d, x, y, rx, ry, col, width, sx, sy, ox=0, oy=0):
    cx, cy = to_px(x, y, sx, sy, ox, oy); ax, ay = rx / 4 * sx, ry / 2.4 * sy
    d.ellipse([cx - ax, cy - ay, cx + ax, cy + ay], outline=col, width=width)
    return cx, cy

def mars_table(h):
    Image.fromarray((h * 65535).astype(np.uint16)).save(os.path.join(ROOT, 'surfaces', 'T_MarsTable_Height.png'))
    save(Image.fromarray(mars_colour(h)), 'surfaces', 'T_MarsTable_BaseColor.png')

def intel_map_wall(h):
    W, H, s = 2580, 840, 1.6
    im, d = screen_base(W, H, 'JEZERO REGION   |   LANDING SURVEY', '18.4 N  77.5 E   |   orbital elevation model', s)
    top = round(70 * s) + 20; mh = H - top - 30; mw = round(mh * 5 / 3)
    im.paste(Image.fromarray(mars_colour(h)).resize((mw, mh), Image.LANCZOS), (30, top)); d = ImageDraw.Draw(im)
    for gx in range(1, 10): d.line([(30 + gx * mw / 10, top), (30 + gx * mw / 10, top + mh)], fill=(116, 182, 255), width=1)
    for gy in range(1, 6): d.line([(30, top + gy * mh / 6), (30 + mw, top + gy * mh / 6)], fill=(116, 182, 255), width=1)
    for k, (x, y) in SITES.items():
        cx, cy = ellipse(d, x, y, *ELLIPSE, SITE_COL[k], 5, mw, mh, 30, top)
        d.text((cx, cy - ELLIPSE[1] / 2.4 * mh - 26), k, font=font(44), fill=WHITE, anchor='mm')
    ex, ey = to_px(CRATER[0] + CR * math.cos(ENTRY_A) - 0.55, CRATER[1] + CR * math.sin(ENTRY_A) + 0.12, mw, mh, 30, top)
    d.text((ex, ey), 'NERETVA VALLIS', font=font(26, 'Regular'), fill=WHITE, anchor='mm')
    d.text(to_px(0.95, -0.75, mw, mh, 30, top), 'JEZERO CRATER', font=font(30), fill=WHITE, anchor='mm')
    d.line([(60, top + mh - 40), (60 + mw / 4 / 22.5 * 10, top + mh - 40)], fill=WHITE, width=5)
    d.text((60, top + mh - 72), '10 km', font=font(26, 'Regular'), fill=WHITE)
    x = 60 + mw
    d.text((x, top + 10), 'LAYER', font=font(34, 'Regular'), fill=CYAN)
    option_cards(d, ['ELEVATION', 'SLOPE', 'GEOLOGY'], 0, x, top + 60, W - x - 40, 80)
    d.text((x, top + 190), 'ELEVATION  (m, MOLA datum)', font=font(28, 'Regular'), fill=CYAN)
    grad = Image.fromarray(np.tile(mars_colour(np.linspace(0.1, 0.8, 600)[None, :].repeat(30, 0), False), (1, 1, 1)))
    im.paste(grad.resize((W - x - 40, 36)), (x, top + 235)); d = ImageDraw.Draw(im)
    d.text((x, top + 280), '-2,600', font=font(24, 'Regular'), fill=WHITE); d.text((W - 40, top + 280), '-1,900', font=font(24, 'Regular'), fill=WHITE, anchor='ra')
    rows = (('A', 'crater plains', 'standard or precision'), ('B', 'delta front', 'standard or precision'), ('C', 'crater floor, boulders', 'precision only'))
    for i, (k, where, need) in enumerate(rows):
        y = top + 350 + i * 120
        d.rounded_rectangle([x, y, x + 70, y + 70], 10, outline=SITE_COL[k], width=5)
        d.text((x + 35, y + 35), k, font=font(40), fill=WHITE, anchor='mm')
        d.text((x + 100, y + 4), where, font=font(34), fill=WHITE); d.text((x + 100, y + 44), need, font=font(26, 'Regular'), fill=AMBER if k == 'C' else CYAN)
    save(im, 'screens', 'T_Screen_Intel_Map.png')

def intel_site_screens(h):
    W, H = 1024, 640
    info = {'A': ('crater plains', 'standard or precision', 0.30, 0.15, 'smooth plains, little to sample'),
            'B': ('delta front', 'standard or precision', 0.92, 0.40, 'ancient river delta: best science'),
            'C': ('crater floor', 'precision landing only', 0.70, 0.78, 'boulder field: needs a tight ellipse')}
    colour = Image.fromarray(mars_colour(h))
    for k, (x, y) in SITES.items():
        where, need, sci, haz, note = info[k]
        im, d = screen_base(W, H, f'SITE {k}   |   {where.upper()}', 'selected' if k == 'B' else 'candidate')
        cx, cy = to_px(x, y); r = 120
        crop = colour.crop((cx - r * 1.4, cy - r, cx + r * 1.4, cy + r)).resize((440, 314), Image.LANCZOS)
        im.paste(crop, (30, 100)); d = ImageDraw.Draw(im)
        ax, ay = ELLIPSE[0] / 4 * TW * 440 / (r * 2.8), ELLIPSE[1] / 2.4 * TH * 314 / (r * 2)
        d.ellipse([250 - ax, 257 - ay, 250 + ax, 257 + ay], outline=SITE_COL[k], width=5)
        d.rectangle([30, 100, 470, 414], outline=GRID, width=2)
        d.text((30, 440), note, font=font(24, 'Regular'), fill=WHITE)
        bar(d, 510, 150, 470, 34, sci, 'SCIENCE VALUE')
        bar(d, 510, 250, 470, 34, haz, 'TERRAIN HAZARD', AMBER if haz > 0.6 else CYAN)
        d.text((510, 310), 'ELLIPSE', font=font(22, 'Regular'), fill=CYAN)
        d.text((510, 340), '7.7 x 6.6 km  precision', font=font(30), fill=WHITE)
        d.text((510, 380), '25 x 20 km  standard' if k != 'C' else 'standard: not reachable', font=font(26, 'Regular'), fill=CYAN if k != 'C' else AMBER)
        if k == 'C':
            d.rounded_rectangle([510, 470, W - 40, 540], 35, outline=AMBER, width=4)
            d.text(((510 + W - 40) / 2, 505), 'REQUIRES PRECISION LANDING', font=font(30), fill=WHITE, anchor='mm')
        elif k == 'B':
            d.rounded_rectangle([510, 470, W - 40, 540], 12, outline=ORANGE, width=5, fill=(14, 30, 52))
            d.text(((510 + W - 40) / 2, 505), 'SELECTED SITE', font=font(32), fill=WHITE, anchor='mm')
        else:
            d.text((510, 490), 'LANDING  ' + need, font=font(28, 'Regular'), fill=CYAN)
        d.text((30, H - 70), f'site {k}   |   {x * 22.5:+.0f} km E   {y * 22.5:+.0f} km N of map centre', font=font(22, 'Regular'), fill=CYAN)
        save(im, 'screens', f'T_Screen_Intel_Site{k}.png')

def intel_console():
    W, H = 1024, 356
    im, d = screen_base(W, H, 'LANDING SYSTEM', 'decide before the site')
    for i, (nm, ell, sites, cost) in enumerate((('STANDARD', 'ellipse 25 x 20 km', 'sites A, B', '+$0   +0 kg'),
                                                ('PRECISION  TRN', 'ellipse 7.7 x 6.6 km', 'sites A, B, C', '+$18M   +12 kg'))):
        x = 30 + i * 492; on = i == 1
        d.rounded_rectangle([x, 95, x + 470, 330], 14, outline=ORANGE if on else GRID, width=5 if on else 2, fill=(14, 30, 52) if on else NAVY_BG)
        d.text((x + 235, 140), nm, font=font(40), fill=WHITE, anchor='mm')
        for j, t in enumerate((ell, sites, cost)): d.text((x + 235, 200 + j * 40), t, font=font(26, 'Regular'), fill=CYAN, anchor='mm')
    save(im, 'screens', 'T_Screen_Intel_LandingSystem.png')

def intel_atlases(h):
    """Env wall screens (2 cells, one material) and analyst monitors (2 x 2 cells, one material)."""
    CW, CH = 1024, 558; env = Image.new('RGB', (2 * CW, CH))
    im, d = screen_base(CW, CH, 'ATMOSPHERE', 'dust forecast')
    tau = 0.45 + np.cumsum(rng6.normal(0, 0.01, 200)).clip(-0.2, 0.3)
    d.line(list(zip(np.linspace(60, CW - 60, 200).tolist(), (500 - tau * 300).tolist())), fill=CYAN, width=4)
    d.line([(60, 500 - 0.9 * 300), (CW - 60, 500 - 0.9 * 300)], fill=AMBER, width=2)
    d.text((60, 100), 'DUST OPACITY  tau', font=font(24, 'Regular'), fill=CYAN); d.text((CW - 60, 96), 'tau 0.6  |  GO', font=font(30), fill=WHITE, anchor='ra')
    d.text((CW - 60, 500 - 0.9 * 300 - 34), 'EDL limit 0.9', font=font(22, 'Regular'), fill=AMBER, anchor='ra')
    env.paste(im, (0, 0))
    im, d = screen_base(CW, CH, 'SEASON', 'arrival')
    cx, cy, R = 300, 320, 170
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=GRID, width=4)
    a = math.radians(-90 + 34)
    d.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + 34, fill=ORANGE, width=10)
    d.ellipse([cx + math.cos(a) * R - 12, cy + math.sin(a) * R - 12, cx + math.cos(a) * R + 12, cy + math.sin(a) * R + 12], fill=WHITE)
    d.text((cx, cy), 'Ls 34', font=font(64), fill=WHITE, anchor='mm')
    for i, (k, v) in enumerate((('season', 'northern spring'), ('surface temp', '-78 to -8 C'), ('pressure', '7.2 mbar'), ('local time at EDL', '15:40'))):
        d.text((560, 130 + i * 95), k, font=font(24, 'Regular'), fill=CYAN); d.text((560, 162 + i * 95), v, font=font(34), fill=WHITE)
    env.paste(im, (CW, 0)); save(env, 'screens', 'T_Screen_Intel_EnvAtlas.png')

    CW, CH = 1024, 576; ops = Image.new('RGB', (2 * CW, 2 * CH))
    im, d = screen_base(CW, CH, 'SLOPES', 'site B')
    for i, v in enumerate(np.abs(rng6.normal(0, 1, 24)).cumsum()[::-1] / 6):
        d.rectangle([60 + i * 38, 500 - min(v, 9) * 40, 88 + i * 38, 500], fill=CYAN if i < 15 else AMBER)
    d.text((60, 100), 'SLOPE DISTRIBUTION  (deg)', font=font(24, 'Regular'), fill=CYAN)
    ops.paste(im, (0, 0))
    im, d = screen_base(CW, CH, 'IMAGING', 'orbital mosaic')
    g = np.asarray(Image.fromarray(mars_colour(h, False)).convert('L').crop((500, 150, 1100, 487)).resize((CW - 60, CH - 110)))
    im.paste(Image.fromarray(g).convert('RGB'), (30, 90)); d = ImageDraw.Draw(im)
    for k in range(1, 6): d.line([(30 + k * (CW - 60) / 6, 90), (30 + k * (CW - 60) / 6, CH - 20)], fill=(116, 182, 255), width=1)
    ops.paste(im, (CW, 0))
    im, d = screen_base(CW, CH, 'ROCK ABUNDANCE', 'site C')
    rk = np.asarray(Image.fromarray((noise(256, 6, 3, r=rng6) * 255).astype(np.uint8)).resize((CW - 60, CH - 110)), np.float32) / 255
    heat = np.dstack((rk * 60, rk * 120 + 20, rk * 200 + 40)).astype(np.uint8)
    im.paste(Image.fromarray(heat), (30, 90)); ops.paste(im, (0, CH))
    im, d = screen_base(CW, CH, 'SITE COMPARISON', 'A | B | C')
    for j, k in enumerate('ABC'): d.text((420 + j * 200, 110), k, font=font(40), fill=WHITE, anchor='ma')
    for i, (lab, vals) in enumerate((('science', (0.30, 0.92, 0.70)), ('hazard', (0.15, 0.40, 0.78)), ('reach', (1.0, 1.0, 0.5)))):
        y = 200 + i * 110; d.text((40, y), lab.upper(), font=font(28, 'Regular'), fill=CYAN)
        for j, v in enumerate(vals): bar2(d, 340 + j * 200, y, 160, 30, v, AMBER if (lab == 'hazard' and v > 0.6) else CYAN)
    ops.paste(im, (CW, CH)); save(ops, 'screens', 'T_Screen_Intel_OpsAtlas.png')

def mars_intel_set():
    h = mars_height()
    mars_table(h); intel_map_wall(h); intel_site_screens(h); intel_console(); intel_atlases(h)
    text_decal('MarsIntel', 'MARS INTELLIGENCE', 140)
    text_decal('MarsTableScale', 'JEZERO CRATER   |   1 m = 22.5 km   |   relief x 2', 80, (200, 210, 222), style='Regular')
    for k in 'ABC': text_decal(f'Site{k}', k, 160)

# ================================================================== PHASE 5: BRIEFING
# The first room: the question, the constraints and the route. Every number here reappears later
# (payload limits and budget in the Hangar, site and landing system in Mars Intelligence).
rng7 = np.random.default_rng(47)
ROUTE = ('BRIEFING', 'MARS INTELLIGENCE', 'ENGINEERING HANGAR', 'MISSION CONTROL')

def mars_globe(D=640, lon0=70.0, lat0=12.0, mark=(18.4, 77.5)):
    """Orthographic Mars: procedural albedo, north cap, day-side shading, Jezero target. RGBA."""
    n = noise(512, 4, 5, r=rng7); n2 = noise(512, 16, 3, r=rng7)
    yy, xx = np.mgrid[0:D, 0:D] / (D / 2) - 1; rr = xx ** 2 + yy ** 2; inside = rr <= 1
    zz = np.sqrt(np.clip(1 - rr, 0, 1)); la0, lo0 = math.radians(lat0), math.radians(lon0)
    lat = np.arcsin(np.clip(-yy * math.cos(la0) + zz * math.sin(la0), -1, 1))
    lon = lo0 + np.arctan2(xx, zz * math.cos(la0) + yy * math.sin(la0))
    u = ((lon / (2 * math.pi)) % 1 * 511).astype(int); v = ((0.5 - lat / math.pi) * 511).astype(int)
    alb = n[v, u] * 0.8 + n2[v, u] * 0.2
    col = np.array((182, 104, 64)) * (0.75 + 0.35 * alb[..., None]) - np.array((60, 40, 30)) * (1 - smooth(0.38, 0.47, alb))[..., None]
    cap = smooth(math.radians(68), math.radians(78), lat)[..., None]
    col = col * (1 - cap) + np.array((236, 232, 226)) * cap
    shade = np.clip(0.25 + 0.85 * (xx * -0.45 + yy * -0.35 + zz * 0.82), 0.12, 1.1)[..., None]
    rgba = np.zeros((D, D, 4), np.uint8); rgba[..., :3] = np.clip(col * shade, 0, 255); rgba[..., 3] = inside * 255
    im = Image.fromarray(rgba); d = ImageDraw.Draw(im)
    la, lo = math.radians(mark[0]), math.radians(mark[1])                          # Jezero on the globe
    cx = math.cos(la) * math.sin(lo - lo0)                                         # orthographic projection
    py = math.sin(la) * math.cos(la0) - math.cos(la) * math.cos(lo - lo0) * math.sin(la0)
    mx, my = D / 2 + cx * D / 2, D / 2 - py * D / 2
    for r, w in ((26, 4), (44, 2)): d.ellipse([mx - r, my - r, mx + r, my + r], outline=CYAN + (255,), width=w)
    d.line([(mx + 44, my - 10), (mx + 150, my - 70)], fill=CYAN + (255,), width=3)
    return im, (mx + 150, my - 70)

def brief_main():
    W, H, s = 2048, 960, 1.45
    im, d = screen_base(W, H, 'MISSION:  RED FRONTIER   |   BRIEFING', 'program RF-01', s)
    top = round(70 * s)
    globe, tip = mars_globe(600)
    im.paste(globe, (60, top + 40), globe); d = ImageDraw.Draw(im)
    d.text((60 + tip[0] + 10, top + 40 + tip[1] - 22), 'JEZERO CRATER', font=font(32), fill=WHITE)
    d.text((60 + tip[0] + 10, top + 40 + tip[1] + 18), '18.4 N  77.5 E', font=font(26, 'Regular'), fill=CYAN)
    x = 820
    d.text((x, top + 50), 'OBJECTIVE', font=font(34, 'Regular'), fill=CYAN)
    d.text((x, top + 100), 'Land a rover in Jezero Crater and', font=font(56), fill=WHITE)
    d.text((x, top + 170), 'find out if Mars was ever alive.', font=font(56), fill=WHITE)
    d.text((x, top + 280), 'SCIENCE QUESTION', font=font(34, 'Regular'), fill=CYAN)
    d.text((x, top + 325), 'Did the river delta preserve signs of ancient life?', font=font(40, 'Regular'), fill=WHITE)
    d.text((x, top + 410), 'CONSTRAINTS', font=font(34, 'Regular'), fill=CYAN)
    for i, (k, v) in enumerate((('payload', '900 / 1,100 kg'), ('budget', '$150M / $250M'), ('window', '26 months'))):
        cx = x + i * 400
        d.rounded_rectangle([cx, top + 455, cx + 370, top + 545], 12, outline=GRID, width=3, fill=(10, 22, 40))
        d.text((cx + 22, top + 470), k, font=font(26, 'Regular'), fill=CYAN); d.text((cx + 22, top + 502), v, font=font(34), fill=WHITE)
    y0 = H - 150; bw = (W - 120 - 3 * 40) / 4                                       # the route through the facility
    for i, nm in enumerate(ROUTE):
        bx = 60 + i * (bw + 40); on = i == 0
        d.rounded_rectangle([bx, y0, bx + bw, y0 + 100], 14, outline=ORANGE if on else GRID, width=5 if on else 3, fill=(14, 30, 52) if on else NAVY_BG)
        d.text((bx + 28, y0 + 50), f'{i + 1:02d}', font=font(40), fill=ORANGE if on else CYAN, anchor='lm')
        d.text((bx + 100, y0 + 50), nm, font=font(32), fill=WHITE, anchor='lm')
        if i < 3: d.polygon([(bx + bw + 10, y0 + 38), (bx + bw + 30, y0 + 50), (bx + bw + 10, y0 + 62)], fill=CYAN)
    save(im, 'screens', 'T_Screen_Brief_Main.png')

def brief_table():
    W, H = 2048, 542                                                                   # 3.4 x 0.9 m table top
    im, d = screen_base(W, H, 'YOUR MISSION', 'read, then proceed')
    cards = (('THE QUESTION', ('Was Mars ever habitable?', 'Ancient lake + delta at Jezero')),
             ('YOUR DECISIONS', ('landing system  |  landing site', 'vehicle  |  payload  |  power  |  mobility  |  comms')),
             ('THE RULE', ('Design backwards from the science.', 'If a part never matters on Mars, cut it.')))
    cw = (W - 80 - 2 * 30) / 3
    for i, (t, lines) in enumerate(cards):
        x = 40 + i * (cw + 30)
        d.rounded_rectangle([x, 100, x + cw, 400], 14, outline=GRID, width=3, fill=(10, 22, 40))
        d.text((x + 30, 125), t, font=font(30, 'Regular'), fill=CYAN)
        for j, l in enumerate(lines): d.text((x + 30, 190 + j * 70), l, font=font(34 if j == 0 else 26, 'SemiBold' if j == 0 else 'Regular'), fill=WHITE)
    d.rounded_rectangle([W - 760, 430, W - 40, 515], 14, outline=ORANGE, width=5, fill=(14, 30, 52))
    d.text((W - 400, 472), 'PROCEED TO MARS INTELLIGENCE', font=font(36), fill=WHITE, anchor='mm')
    d.text((40, 472), 'step 01 of 04', font=font(28, 'Regular'), fill=CYAN, anchor='lm')
    save(im, 'screens', 'T_Screen_Brief_Table.png')

def brief_context():
    CW, CH = 1024, 569; atlas = Image.new('RGB', (2 * CW, CH))
    im, d = screen_base(CW, CH, 'WHY JEZERO', 'context')
    rows = (('crater', '45 km wide'), ('age', '3.5 billion years'), ('once', 'a lake fed by a river'), ('today', 'a preserved delta'))
    for i, (k, v) in enumerate(rows):
        y = 110 + i * 105
        d.text((50, y), k.upper(), font=font(26, 'Regular'), fill=CYAN); d.text((50, y + 36), v, font=font(40), fill=WHITE)
        d.line([(50, y + 92), (CW - 50, y + 92)], fill=GRID, width=2)
    atlas.paste(im, (0, 0))
    im, d = screen_base(CW, CH, 'TIMELINE', 'Earth to surface')
    steps = (('LAUNCH', 'window opens'), ('CRUISE', '205 days'), ('EDL', '7 minutes'), ('SURFACE', '1 Mars year'))
    for i, (k, v) in enumerate(steps):
        x = 80 + i * 230
        d.ellipse([x - 16, 290 - 16, x + 16, 290 + 16], outline=CYAN, width=4, fill=(14, 30, 52))
        if i < 3: d.line([(x + 20, 290), (x + 210, 290)], fill=GRID, width=4)
        d.text((x, 340), k, font=font(30), fill=WHITE, anchor='ma'); d.text((x, 380), v, font=font(24, 'Regular'), fill=CYAN, anchor='ma')
    d.text((50, 130), 'one mission, four rooms, one launch', font=font(30, 'Regular'), fill=WHITE)
    atlas.paste(im, (CW, 0)); save(atlas, 'screens', 'T_Screen_Brief_ContextAtlas.png')

def briefing_set():
    brief_main(); brief_table(); brief_context()
    text_decal('Briefing', 'MISSION BRIEFING', 140)
    text_decal('Program', 'RED FRONTIER PROGRAM', 160)
    text_decal('ProgramSub', 'design a rover   |   land it   |   find out if Mars was ever alive', 80, (200, 210, 222), style='Regular')

# ================================================================= PHASE 5: CORRIDORS
def corridor_strip():
    """Corridor 01 map strip (2.4 x 0.5 m): a band of the Jezero terrain already made for the Mars table,
    with the route label. Built from the existing image, so no new terrain is generated."""
    W, H = 2048, 426
    im = Image.new('RGB', (W, H), NAVY_BG); d = ImageDraw.Draw(im)
    src = Image.open(os.path.join(ROOT, 'surfaces', 'T_MarsTable_BaseColor.png')).convert('RGB')
    band = src.crop((0, 300, 1500, 600)).resize((W - 590, H - 60), Image.LANCZOS)
    im.paste(band, (560, 30))
    for k in range(1, 12): d.line([(560 + k * (W - 590) / 12, 30), (560 + k * (W - 590) / 12, 48)], fill=CYAN, width=2)
    d.rectangle([560, 30, W - 30, H - 30], outline=GRID, width=2)
    d.rectangle([30, 40, 38, 76], fill=ORANGE)
    d.text((56, 34), '02   MARS INTELLIGENCE', font=font(40), fill=WHITE)
    d.text((56, 100), 'Jezero region', font=font(30, 'Regular'), fill=CYAN)
    d.text((56, 140), 'landing system  |  landing site', font=font(28, 'Regular'), fill=CYAN)
    d.text((56, H - 80), '1 : 1,500,000', font=font(26, 'Regular'), fill=WHITE)
    save(im, 'screens', 'T_Screen_Corridor01_Strip.png')

if __name__ == '__main__' and "corridor" in sys.argv[1:]:
    corridor_strip(); print('TEXTURES_CORRIDOR_OK'); raise SystemExit
if __name__ == '__main__' and "brief" in sys.argv[1:]:
    briefing_set(); print('TEXTURES_BRIEF_OK'); raise SystemExit
if __name__ == '__main__' and "mc" in sys.argv[1:]:          # Phase 5 only: leaves the locked Hangar textures untouched
    mission_control_set(); print('TEXTURES_MC_OK'); raise SystemExit
if __name__ == '__main__' and "intel" in sys.argv[1:]:
    mars_intel_set(); print('TEXTURES_INTEL_OK'); raise SystemExit

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
    mission_control_set(); mars_intel_set(); briefing_set(); corridor_strip()
    print('TEXTURES_OK', sum(len(f) for _, _, f in os.walk(ROOT)))
