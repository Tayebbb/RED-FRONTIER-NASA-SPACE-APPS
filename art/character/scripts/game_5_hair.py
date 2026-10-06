"""
game_5_hair.py - final hair pass (hair only): natural hair mass + a small set of hair cards, game-ready.

Run:  blender -b art/character/source/RF01_Engineer_GAME.blend --python art/character/scripts/game_5_hair.py

Replaces GAME_Hair (and adds GAME_HairCards); nothing else in the character changes.
  Mass: same short professional shape, but the surface is broken into flow-aligned clumps of two sizes with
        irregular spacing (no regular grooves), a noise-broken hairline with softer temples, darker roots and
        lighter clump crests baked into a 1K colour map, plus a 1K normal map.
  Cards: ~160 alpha-clipped strand cards rooted along the hairline (front, temples, sideburns, nape) and scattered
        over the top and crown, lying on the mass along the hair direction to soften the edge and break the
        silhouette. Double-sided, alpha clip (glTF MASK).
Both are bound rigidly to the Head bone.
"""
import bpy, bmesh, sys, os, math, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import importlib, rf01_sdf, rf01_body, rf01_head_v4
for m in (rf01_sdf, rf01_body, rf01_head_v4):
    importlib.reload(m)
from rf01_sdf import mesh_sparse, project, Prim, Field
from rf01_body import build

TEXG = os.path.join(ROOT, 'textures', 'game')
T0 = time.time()
RNG = np.random.default_rng(11)
def log(*a):
    print(f'[{time.time() - T0:7.1f}s]', *a, flush=True)

H0 = np.array([0.0, 0.0, 1.683])
HEAD_C = np.array([0.0, 0.005, 1.700])


def smooth01(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


# ------------------------------------------------------------------------------------------- noise
def _hash(ix, iy, iz, seed):
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
    h = h & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def vnoise(q, seed=0):
    """Value noise in [0,1] at points q (N,3) (unit cell = 1)."""
    f = np.floor(q); t = q - f; i = f.astype(np.int64)
    w = t * t * (3 - 2 * t)
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                h = _hash(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, seed)
                wx = w[:, 0] if dx else 1 - w[:, 0]; wy = w[:, 1] if dy else 1 - w[:, 1]; wz = w[:, 2] if dz else 1 - w[:, 2]
                out = out + h * wx * wy * wz
    return out


def head(p):
    return np.stack([p[:, 0], -p[:, 1], p[:, 2] - H0[2]], 1)


# ------------------------------------------------------------------------------------------- hair direction
def flow(p):
    """Unit hair direction (world) on the scalp: top combed back from a side part on his left, sides down-back,
    crown radiating, back and nape down."""
    hx, hy, hz = head(p).T
    ax = np.abs(hx)
    part = 0.028
    a = smooth01(part - 0.004, part + 0.004, hx)
    top = np.stack([(1 - a) * -0.30 + a * 0.80, (1 - a) * -1.0 + a * -0.45, a * -0.30], 1)
    side = np.stack([np.sign(hx) * 0.15, np.full_like(hx, -0.45), np.full_like(hx, -1.0)], 1)
    crown = head(p) - np.array([0.010, -0.060, 0.105])
    down = np.tile(np.array([0.0, -0.15, -1.0]), (len(p), 1))
    wt = smooth01(0.045, 0.085, hz) * (1 - smooth01(0.05, 0.068, ax))
    ws = smooth01(0.045, 0.065, ax) * (1 - wt)
    wb = smooth01(-0.02, -0.06, hy) * (1 - ws)
    wc = np.exp(-np.sum((head(p) - np.array([0.010, -0.060, 0.105])) ** 2, 1) / 0.025 ** 2)
    f = top * (wt * (1 - wb))[:, None] + side * ws[:, None] + down * (wb * (1 - wc))[:, None] + crown * (wc * 8)[:, None]
    f += 1e-6
    fw = np.stack([f[:, 0], -f[:, 1], f[:, 2]], 1)                    # head -> world
    n = p - HEAD_C; n /= np.linalg.norm(n, axis=1)[:, None]
    fw -= n * np.sum(fw * n, 1)[:, None]
    return fw / np.maximum(np.linalg.norm(fw, axis=1), 1e-9)[:, None], n


# ------------------------------------------------------------------------------------------- scalp mask
def scalp_mask(p, soft=0.007):
    hx, hy, hz = head(p).T
    ax = np.abs(hx)
    yc = [-0.12, -0.08, -0.05, 0.0, 0.05, 0.12]; zc = [-0.085, -0.080, -0.060, 0.0, 0.074, 0.074]
    ys = [-0.12, -0.045, -0.030, 0.012, 0.020, 0.035, 0.050, 0.12]
    zs = [-0.070, -0.050, 0.026, 0.024, -0.004, 0.040, 0.080, 0.095]
    b = smooth01(0.03, 0.065, ax)
    zmin = (1 - b) * np.interp(hy, yc, zc) + b * np.interp(hy, ys, zs)
    zmin += 0.25 * np.maximum(ax - 0.03, 0) * smooth01(0.03, 0.06, hy)
    # irregular, not geometric: low-frequency wobble along the line + fine breakup
    zmin += 0.0030 * (vnoise(p / 0.014, 5) - 0.5) * 2 + 0.0012 * (vnoise(p / 0.004, 6) - 0.5) * 2
    s = soft * (1 + 0.6 * smooth01(0.035, 0.06, ax) * smooth01(0.02, 0.05, hy))          # softer temples
    return smooth01(0.0, s, hz - zmin)


def clumps(p, f):
    """Two scales of flow-aligned clumps (irregular), in [0,1] (1 = crest)."""
    def aniso(along, across):
        proj = np.sum(p * f, 1)[:, None] * f
        return (p - proj) / across + proj / along
    q1 = aniso(0.070, 0.0180); q2 = aniso(0.026, 0.0060)
    c1 = 1 - np.abs(2 * vnoise(q1, 1) - 1)
    c2 = 1 - np.abs(2 * vnoise(q2, 2) - 1)
    return c1, c2


def thickness(p):
    hx, hy, hz = head(p).T
    ax = np.abs(hx)
    T = np.interp(hz, [-0.09, -0.05, 0.0, 0.04, 0.08, 0.12], [0.0018, 0.0030, 0.0046, 0.0074, 0.0100, 0.0110])
    T *= 1 - 0.40 * smooth01(0.055, 0.075, ax) * (1 - smooth01(0.04, 0.08, hz))         # sides closer to the skull
    T += 0.0012 * smooth01(0.0, 0.05, hy) * smooth01(0.05, 0.09, hz)
    T *= 1 + 0.22 * (vnoise(p / 0.022, 3) - 0.5) * 2 * smooth01(0.04, 0.08, hz)           # lumpy top silhouette
    f, n = flow(p)
    c1, c2 = clumps(p, f)
    m = scalp_mask(p, soft=0.004)                    # irregular edge
    hy_ = head(p)[:, 1]
    taper = scalp_mask(p, soft=0.009 + 0.010 * smooth01(0.02, 0.05, hy_))   # soft edge, wider at the front: no ledge
    t = (T + 0.0007 * (c1 - 0.5)) * taper            # gentle large clumps only; strand detail is in the textures
    return np.maximum(t * m, 0.0), m, c1, c2


class HairMass(Prim):
    def __init__(self, body):
        self.body = body; self.c = H0 + np.array([0, 0.0, 0.03]); self.r = 0.2

    def d(self, p):
        b = self.body._eval_chunk(p, p.min(0), p.max(0), 1.0)
        t, m, _, _ = thickness(p)
        d = np.maximum(b - t, -(b - 0.0004))
        return np.maximum(d, 0.0006 - t)


# ------------------------------------------------------------------------------------------- textures
def card_texture(path, w=1024, h=512, variants=4):
    """Strand-clump atlas: 4 variants side by side; v = 0 root (soft, sparse), v = 1 tip (tapered)."""
    img = np.zeros((h, w, 4), np.float32)
    cw = w // variants
    yy = np.arange(h)[:, None] / h
    for k in range(variants):
        rng = np.random.default_rng(100 + k)
        for _ in range(320):
            x0 = rng.uniform(0.06, 0.94) * cw; drift = (0.5 * cw - x0) * rng.uniform(0.15, 0.45); bend = rng.uniform(-0.05, 0.05) * cw
            v_end = rng.uniform(0.55, 1.0); width = rng.uniform(1.6, 3.0)
            t = np.linspace(0, v_end, 400)
            xs = k * cw + x0 + drift * t + bend * np.sin(np.pi * t)
            ys = (t * (h - 1)).astype(int)
            shade = rng.uniform(0.65, 1.35)
            for xi, yi, tt in zip(xs, ys, t):
                a = min(1.0, tt / 0.12) * (1 - (tt / v_end) ** 4)                 # fades in at the root, tapers
                x_int = int(xi)
                for dx in range(-2, 3):
                    xx = x_int + dx
                    if k * cw <= xx < (k + 1) * cw:
                        cov = max(0.0, 1 - abs(xi - xx) / width)
                        img[yi, xx, 3] = max(img[yi, xx, 3], a * cov)
                        img[yi, xx, :3] = np.array([0.050, 0.034, 0.024]) * shade
    img[..., :3] = np.where(img[..., 3:4] > 0, img[..., :3], np.array([0.03, 0.02, 0.015]))
    im = bpy.data.images.new('T_RF01_HairCards', w, h, alpha=True)
    im.pixels.foreach_set(img.ravel()); im.alpha_mode = 'STRAIGHT'
    im.filepath_raw = path; im.file_format = 'PNG'; im.save()
    return im


# ------------------------------------------------------------------------------------------- mesh helpers
def new_mesh(name, v, q):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(x) for x in v], [], [tuple(f) for f in q]); me.validate()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    me.shade_smooth()
    return me


def verts_np(me):
    a = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', a); return a.reshape(-1, 3)


def ctx(ob):
    return dict(active_object=ob, object=ob, selected_objects=[ob], selected_editable_objects=[ob])


def decimate(ob, target):
    n = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    if n > target:
        m = ob.modifiers.new('Decimate', 'DECIMATE'); m.ratio = target / n; m.use_collapse_triangulate = True
        with bpy.context.temp_override(**ctx(ob)):
            bpy.ops.object.modifier_apply(modifier=m.name)


def smart_uv(ob):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004)
    bpy.ops.object.mode_set(mode='OBJECT'); ob.select_set(False)


def poisson(points, spacing, limit=None):
    """Greedy thinning to a minimum spacing (random order)."""
    idx = RNG.permutation(len(points)); chosen = []
    for i in idx:
        p = points[i]
        if all(np.linalg.norm(p - points[j]) >= spacing for j in chosen[-400:]):
            chosen.append(i)
            if limit and len(chosen) >= limit:
                break
    return points[chosen]


# ------------------------------------------------------------------------------------------- cards
def build_cards(mass_field, roots, length, width, lift, variants=4):
    """One 3-segment strip per root, following the hair direction over the mass surface."""
    V, F, UV, N = [], [], [], []
    for r, L, W, lf in zip(roots, length, width, lift):
        col = RNG.integers(variants); flip = RNG.random() < 0.5
        f, n = flow(r[None])
        f, n = f[0], n[0]
        side = np.cross(n, f); side /= np.linalg.norm(side)
        yaw = np.radians(RNG.uniform(-10, 10))
        f = f * np.cos(yaw) + side * np.sin(yaw); side = np.cross(n, f)
        rows = []
        p = r.copy()
        for s in range(4):
            t = s / 3
            centre = p
            seat = project(mass_field, centre[None], iters=6, max_step=0.01)[0]
            g = mass_field.grad(seat[None])[0]; g /= np.linalg.norm(g)
            c = seat + g * (0.0005 + lf * t ** 1.6)
            sd = np.cross(g, f); sd /= np.linalg.norm(sd)
            w = W * (1.0 - 0.35 * t)
            rows.append((c - sd * w / 2, c + sd * w / 2, g, t))
            # march along the surface
            ff, _ = flow(seat[None]); f = 0.6 * f + 0.4 * ff[0]
            f -= g * np.dot(f, g); f /= np.linalg.norm(f)
            p = seat + f * (L / 3)
        base = len(V)
        for a, b, g, t in rows:
            u0, u1 = (col + 0.08) / variants, (col + 0.92) / variants
            if flip:
                u0, u1 = u1, u0
            V += [a, b]; N += [g, g]; UV += [(u0, t), (u1, t)]
        for s in range(3):
            i = base + 2 * s
            F.append((i, i + 1, i + 3, i + 2))
    return np.array(V), F, np.array(UV), np.array(N)


# ------------------------------------------------------------------------------------------- materials
def mass_bake_material():
    """Hair look evaluated per pixel at bake time: fine strands and larger clumps stretched along the hair
    direction (vertex attribute rf_flow), darker toward the hairline (rf_root). Colour -> base map,
    bump -> normal map."""
    m = bpy.data.materials.new('MAT_RF_HairBake'); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N['Principled BSDF']; b.inputs['Roughness'].default_value = 0.6
    geo = N.new('ShaderNodeNewGeometry')
    fl = N.new('ShaderNodeAttribute'); fl.attribute_name = 'rf_flow'
    root = N.new('ShaderNodeAttribute'); root.attribute_name = 'rf_root'
    dot = N.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
    L.new(geo.outputs['Position'], dot.inputs[0]); L.new(fl.outputs['Vector'], dot.inputs[1])
    along = N.new('ShaderNodeVectorMath'); along.operation = 'SCALE'
    L.new(fl.outputs['Vector'], along.inputs[0]); L.new(dot.outputs['Value'], along.inputs['Scale'])
    cross = N.new('ShaderNodeVectorMath'); cross.operation = 'SUBTRACT'
    L.new(geo.outputs['Position'], cross.inputs[0]); L.new(along.outputs['Vector'], cross.inputs[1])
    def stretched(across_m, along_m, seed_off):
        a = N.new('ShaderNodeVectorMath'); a.operation = 'SCALE'; a.inputs['Scale'].default_value = 1.0 / across_m
        L.new(cross.outputs['Vector'], a.inputs[0])
        c = N.new('ShaderNodeVectorMath'); c.operation = 'SCALE'; c.inputs['Scale'].default_value = 1.0 / along_m
        L.new(along.outputs['Vector'], c.inputs[0])
        add = N.new('ShaderNodeVectorMath'); add.operation = 'ADD'
        L.new(a.outputs['Vector'], add.inputs[0]); L.new(c.outputs['Vector'], add.inputs[1])
        off = N.new('ShaderNodeVectorMath'); off.operation = 'ADD'; off.inputs[1].default_value = (seed_off, seed_off * 2, 0)
        L.new(add.outputs['Vector'], off.inputs[0])
        nz = N.new('ShaderNodeTexNoise'); nz.noise_dimensions = '3D'
        nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = 1.5; nz.inputs['Roughness'].default_value = 0.5
        L.new(off.outputs['Vector'], nz.inputs['Vector'])
        return nz.outputs['Fac']
    strands = stretched(0.0019, 0.040, 3.1)
    clump = stretched(0.0085, 0.060, 7.7)
    sr = N.new('ShaderNodeMapRange'); sr.inputs['From Min'].default_value = 0.38; sr.inputs['From Max'].default_value = 0.62
    L.new(strands, sr.inputs['Value'])
    mix = N.new('ShaderNodeMath'); mix.operation = 'MULTIPLY_ADD'; mix.inputs[1].default_value = 0.6
    L.new(sr.outputs['Result'], mix.inputs[0])
    cw = N.new('ShaderNodeMath'); cw.operation = 'MULTIPLY'; cw.inputs[1].default_value = 0.4
    L.new(clump, cw.inputs[0]); L.new(cw.outputs[0], mix.inputs[2])
    rootmul = N.new('ShaderNodeMapRange'); rootmul.inputs['To Min'].default_value = 0.45; rootmul.inputs['To Max'].default_value = 1.0
    L.new(root.outputs['Fac'], rootmul.inputs['Value'])
    tone = N.new('ShaderNodeMath'); tone.operation = 'MULTIPLY'
    L.new(mix.outputs[0], tone.inputs[0]); L.new(rootmul.outputs['Result'], tone.inputs[1])
    ramp = N.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = (0.0050, 0.0036, 0.0028, 1)
    cr.elements[1].position = 1.0; cr.elements[1].color = (0.046, 0.032, 0.023, 1)
    e = cr.elements.new(0.45); e.color = (0.015, 0.0105, 0.0078, 1)
    L.new(tone.outputs[0], ramp.inputs['Fac']); L.new(ramp.outputs['Color'], b.inputs['Base Color'])
    bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.55; bump.inputs['Distance'].default_value = 0.0004
    L.new(mix.outputs[0], bump.inputs['Height']); L.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def game_hair_material(base_img, normal_img):
    m = bpy.data.materials.get('MAT_GAME_Hair')
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new('MAT_GAME_Hair'); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.62; b.inputs['Specular IOR Level'].default_value = 0.30
    t = N.new('ShaderNodeTexImage'); t.image = base_img; L.new(t.outputs['Color'], b.inputs['Base Color'])
    tn = N.new('ShaderNodeTexImage'); tn.image = normal_img
    nm = N.new('ShaderNodeNormalMap'); L.new(tn.outputs['Color'], nm.inputs['Color']); L.new(nm.outputs['Normal'], b.inputs['Normal'])
    return m, t, tn


def card_material(img):
    m = bpy.data.materials.new('MAT_GAME_HairCards'); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.60; b.inputs['Specular IOR Level'].default_value = 0.30
    t = N.new('ShaderNodeTexImage'); t.image = img
    L.new(t.outputs['Color'], b.inputs['Base Color'])
    gt = N.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.45   # alpha clip (glTF MASK)
    L.new(t.outputs['Alpha'], gt.inputs[0]); L.new(gt.outputs[0], b.inputs['Alpha'])
    m.use_backface_culling = False
    return m


def bind_head(ob, arm):
    for g in list(ob.vertex_groups):
        ob.vertex_groups.remove(g)
    g = ob.vertex_groups.new(name='Head'); g.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
    mw = ob.matrix_world.copy(); ob.parent = arm; ob.matrix_world = mw
    mod = ob.modifiers.new('Armature', 'ARMATURE'); mod.object = arm


# ------------------------------------------------------------------------------------------- main
def main():
    arm = bpy.data.objects['RF01_Armature']
    game = bpy.data.collections['GAME']; src = bpy.data.collections['BAKE_HIGH']
    for n in ('GAME_Hair', 'GAME_HairCards', 'HIGH_Hair'):
        if n in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[n])
    for n in ('T_GAME_Hair_BaseColor', 'T_GAME_Hair_Normal', 'T_RF01_HairCards'):
        if n in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[n])
    for n in ('MAT_GAME_HairCards', 'MAT_RF_HairBake'):
        if n in bpy.data.materials:
            bpy.data.materials.remove(bpy.data.materials[n])
    body, J = build(cp=4)
    log('hair mass (high)')
    mf = Field(); mf.add(HairMass(body)); mf.finalize()
    v, q = mesh_sparse(mf, H0 + np.array([-0.11, -0.16, -0.12]), H0 + np.array([0.11, 0.135, 0.15]), 0.0012,
                       log=log, reach=3.0)
    me = new_mesh('HIGH_Hair', v, q)
    hi = bpy.data.objects.new('HIGH_Hair', me); src.objects.link(hi)
    c = np.empty(len(me.polygons) * 3); me.polygons.foreach_get('center', c); c = c.reshape(-1, 3)
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    inner = body.eval(c) <= 0.0009
    bmesh.ops.delete(bm, geom=[f for f, k in zip(bm.faces, inner) if k], context='FACES'); bm.to_mesh(me); bm.free()
    hv = verts_np(me)
    t, m, c1, c2 = thickness(hv)
    fv, _ = flow(hv)
    a = me.attributes.new('rf_flow', 'FLOAT_VECTOR', 'POINT'); a.data.foreach_set('vector', fv.astype(np.float32).ravel())
    a = me.attributes.new('rf_root', 'FLOAT', 'POINT'); a.data.foreach_set('value', smooth01(0.0006, 0.006, t).astype(np.float32))
    me.materials.append(mass_bake_material())
    hi.hide_render = True
    log(f'high hair {len(me.polygons)} faces')
    # low-poly mass, UV, bake
    low = hi.copy(); low.data = me.copy(); low.name = 'GAME_Hair'; low.data.name = 'GAME_Hair'
    for att in list(low.data.attributes):
        if att.name in ('rf_flow', 'rf_root'):
            low.data.attributes.remove(att)
    game.objects.link(low); low.hide_render = False; decimate(low, 3600); smart_uv(low)
    bimg = bpy.data.images.new('T_GAME_Hair_BaseColor', 2048, 2048)
    nimg = bpy.data.images.new('T_GAME_Hair_Normal', 2048, 2048); nimg.colorspace_settings.name = 'Non-Color'
    mat, tb, tn = game_hair_material(bimg, nimg)
    low.data.materials.clear(); low.data.materials.append(mat)
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 4
    for node, kind in ((tb, 'COLOR'), (tn, 'NORMAL')):
        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        hi.hide_set(False); hi.hide_render = False; hi.select_set(True); low.select_set(True)
        bpy.context.view_layer.objects.active = low; mat.node_tree.nodes.active = node
        kw = dict(use_selected_to_active=True, cage_extrusion=0.004, max_ray_distance=0.02, margin=8)
        if kind == 'COLOR':
            bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, **kw)
        else:
            bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', **kw)
    hi.hide_render = True
    for im in (bimg, nimg):
        im.filepath_raw = os.path.join(TEXG, im.name + '.png'); im.file_format = 'PNG'; im.save()
    log('mass baked')
    cards = None                                    # cards dropped: the textured mass reads better
    bind_head(low, arm)
    tri = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
    log(f'hair triangles: mass {tri(low)} (no cards)')
    bpy.ops.wm.save_mainfile()
    log('saved')


main()
