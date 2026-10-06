"""
game_1_meshes.py - game production stage 1: refined head/hands into the master, bake sources, low-poly game meshes.

Run:  blender -b art/character/source/RF01_Engineer_MASTER.blend --python art/character/scripts/game_1_meshes.py

1. RF01_Body in the MASTER gets the CP4 head/hands (rf01_head_v4) at 2 mm; MASTER is saved (still high-res).
2. Bake sources: skin shader on the master body (lips, eyebrows, hairline, nails), a high-res hair mass (HIGH_Hair).
3. Game meshes (collection GAME) are decimated copies with UVs:
   GAME_Skin (head+neck+hands only), GAME_Jacket/Trousers/Shoes (single layer; thickness added after baking),
   GAME_Hair, GAME_Eyes, GAME_ChestMark, GAME_BackMark, GAME_Patch, GAME_Badge, GAME_Wrist, GAME_Proxy (full
   body, only for skin weights). Saved as source/RF01_Engineer_GAME.blend.
"""
import bpy, bmesh, sys, os, time, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import importlib, rf01_sdf, rf01_body, rf01_head_v4
for m in (rf01_sdf, rf01_body, rf01_head_v4):
    importlib.reload(m)
from rf01_sdf import mesh_sparse, project, Prim, Field
from rf01_body import build, HeadSpace, eye_centres, EYE_R

MASTER = os.path.join(ROOT, 'source', 'RF01_Engineer_MASTER.blend')
GAME = os.path.join(ROOT, 'source', 'RF01_Engineer_GAME.blend')
TEXG = os.path.join(ROOT, 'textures', 'game'); os.makedirs(TEXG, exist_ok=True)
T0 = time.time()
def log(*a):
    print(f'[{time.time() - T0:7.1f}s]', *a, flush=True)


# ------------------------------------------------------------------------------------------- helpers
def verts_np(me):
    a = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', a); return a.reshape(-1, 3)


def relax(me, v, field, iters=3, lam=0.45):
    e = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get('vertices', e); e = e.reshape(-1, 2)
    for _ in range(iters):
        acc = np.zeros_like(v); cnt = np.zeros(len(v))
        np.add.at(acc, e[:, 0], v[e[:, 1]]); np.add.at(acc, e[:, 1], v[e[:, 0]])
        np.add.at(cnt, e[:, 0], 1); np.add.at(cnt, e[:, 1], 1)
        v = v + lam * (acc / np.maximum(cnt, 1)[:, None] - v)
        v = project(field, v, iters=3)
    return v


def new_mesh(name, v, q):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(x) for x in v], [], [tuple(f) for f in q]); me.validate()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    me.shade_smooth()
    return me


def ctx(ob):
    return dict(active_object=ob, object=ob, selected_objects=[ob], selected_editable_objects=[ob])


def apply_mods(ob):
    for m in list(ob.modifiers):
        with bpy.context.temp_override(**ctx(ob)):
            bpy.ops.object.modifier_apply(modifier=m.name)


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def decimate(ob, target):
    n = tris(ob)
    if n <= target:
        return
    m = ob.modifiers.new('Decimate', 'DECIMATE'); m.decimate_type = 'COLLAPSE'
    m.ratio = target / n; m.use_collapse_triangulate = True
    with bpy.context.temp_override(**ctx(ob)):
        bpy.ops.object.modifier_apply(modifier=m.name)


def copy_object(src, name, coll, apply=False):
    ob = src.copy(); ob.data = src.data.copy(); ob.name = name; ob.data.name = name
    ob.parent = None; ob.matrix_world = src.matrix_world.copy()
    coll.objects.link(ob)
    if not apply:
        for m in list(ob.modifiers):
            ob.modifiers.remove(m)
    else:
        apply_mods(ob)
    return ob


def smart_uv(ob, margin=0.004, angle=66):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.select_set(False)


def keep_faces(ob, keep_mask):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    dead = [f for f, k in zip(bm.faces, keep_mask) if not k]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.to_mesh(ob.data); bm.free(); ob.data.update()


def face_centres(ob):
    c = np.empty(len(ob.data.polygons) * 3); ob.data.polygons.foreach_get('center', c); return c.reshape(-1, 3)


def set_attr(me, name, vals):
    a = me.attributes.get(name) or me.attributes.new(name, 'FLOAT', 'POINT')
    a.data.foreach_set('value', np.asarray(vals, np.float32))


def smooth01(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


# ------------------------------------------------------------------------------------------- hair / scalp
H0 = np.array([0.0, 0.0, 1.683])


def head_space(p):
    """world -> head space (x left, y forward, z up from eye level)"""
    return np.stack([p[:, 0], -p[:, 1], p[:, 2] - H0[2]], 1)


def scalp_mask(p, soft=0.006):
    hx, hy, hz = head_space(p).T
    ax = np.abs(hx)
    yc = [-0.12, -0.08, -0.05, 0.0, 0.05, 0.12]; zc = [-0.085, -0.080, -0.060, 0.0, 0.074, 0.074]
    ys = [-0.12, -0.045, -0.030, 0.012, 0.020, 0.035, 0.050, 0.12]
    zs = [-0.070, -0.050, 0.026, 0.024, -0.004, 0.040, 0.080, 0.095]
    zmin_c = np.interp(hy, yc, zc); zmin_s = np.interp(hy, ys, zs)
    b = smooth01(0.03, 0.065, ax)
    zmin = (1 - b) * zmin_c + b * zmin_s
    zmin += 0.25 * np.maximum(ax - 0.03, 0) * smooth01(0.03, 0.06, hy)                # temple recession
    return smooth01(0.0, soft, hz - zmin)


def hair_thickness(p):
    hx, hy, hz = head_space(p).T
    ax = np.abs(hx)
    T = np.interp(hz, [-0.09, -0.05, 0.0, 0.04, 0.08, 0.12], [0.0020, 0.0032, 0.0050, 0.0080, 0.0105, 0.0115])
    T *= 1 - 0.35 * smooth01(0.055, 0.075, ax) * (1 - smooth01(0.04, 0.08, hz))         # tidy sides
    T += 0.0022 * smooth01(0.0, 0.05, hy) * smooth01(0.05, 0.09, hz)                     # front lift
    # groove texture following the combing direction: back on top, down-and-back on the sides, down at the back
    g_top = np.sin(2 * np.pi * hx / 0.0065 + 0.8 * np.sin(2 * np.pi * hy / 0.045))
    g_side = np.sin(2 * np.pi * (hz + 0.35 * hy) / 0.0055)
    g_back = np.sin(2 * np.pi * hx / 0.006 + 0.5 * np.sin(2 * np.pi * hz / 0.03))
    ws = smooth01(0.045, 0.065, ax); wb = smooth01(0.0, -0.05, hy) * (1 - ws)
    g = (1 - ws) * (1 - wb) * g_top + ws * g_side + wb * g_back
    part = np.exp(-((hx - 0.028) / 0.0025) ** 2) * smooth01(-0.03, 0.02, hy) * smooth01(0.06, 0.09, hz)
    m = scalp_mask(p)
    return np.maximum(T * m + 0.00065 * g * m - 0.0018 * part, 0.0)


class HairPrim(Prim):
    """Hair mass: the shell between the scalp (+0.4 mm) and scalp + thickness."""
    def __init__(self, body):
        self.body = body; self.c = H0 + np.array([0, 0.0, 0.03]); self.r = 0.2

    def d(self, p):
        b = self.body._eval_chunk(p, p.min(0), p.max(0), 1.0)
        t = hair_thickness(p)
        d = np.maximum(b - t, -(b - 0.0004))
        return np.maximum(d, 0.0006 - t)


# ------------------------------------------------------------------------------------------- skin masks
def skin_masks(field, v, J):
    """Per-vertex masks for the review/game skin: lips, eyebrows, scalp, nails, warmth."""
    hv = head_space(v)
    hx, hy, hz = hv.T
    out = {}
    lips = [prim for op, prim, k, tag, ph in field.ops if tag.startswith(('upper lip', 'lower lip'))]
    d = np.full(len(v), 1.0)
    for pr in lips:
        d = np.minimum(d, pr.d(v))
    out['rf_lips'] = smooth01(0.0014, 0.0003, d) * (hy > 0.06)
    # eyebrows (painted): arch per side, right one 0.8 mm higher (matches the asymmetry warp)
    brow = np.zeros(len(v))
    for s, dz in ((1, 0.0), (-1, 0.0008)):
        x = s * hx
        t = np.clip((x - 0.012) / 0.044, 0, 1)
        zc = 0.0265 + 0.0075 * np.sin(np.pi * np.clip(t * 1.15, 0, 1)) - 0.003 * t + dz
        half = 0.0046 - 0.0028 * t
        inside = smooth01(-0.0006, 0.0006, half - np.abs(hz - zc)) * smooth01(0.010, 0.014, x) * smooth01(0.058, 0.052, x)
        strokes = 0.78 + 0.22 * np.sin(2 * np.pi * (x * 1.0 + (hz - zc) * 0.6) / 0.0011)
        brow = np.maximum(brow, inside * strokes * (hy > 0.05))
    out['rf_brow'] = brow
    out['rf_scalp'] = scalp_mask(v, soft=0.010)
    nails = [prim for op, prim, k, tag, ph in field.ops if 'nail' in tag]
    d = np.full(len(v), 1.0)
    for pr in nails:
        d = np.minimum(d, pr.d(v))
    out['rf_nails'] = smooth01(0.0006, 0.0, d)
    warm = np.zeros(len(v))
    for c, r in (((0.0, 0.112, -0.038), 0.012), ((0.038, 0.070, -0.035), 0.016), ((-0.038, 0.070, -0.035), 0.016),
                 ((0.080, -0.010, -0.012), 0.022), ((-0.080, -0.010, -0.012), 0.022)):
        warm = np.maximum(warm, np.exp(-np.sum((hv - np.array(c)) ** 2, 1) / (r * r)))
    out['rf_warm'] = warm
    return out


def skin_material():
    m = bpy.data.materials.get('MAT_RF_SkinBake') or bpy.data.materials.new('MAT_RF_SkinBake')
    m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    for n in list(N):
        if n.type not in ('BSDF_PRINCIPLED', 'OUTPUT_MATERIAL'):
            N.remove(n)
    b = N['Principled BSDF']; b.inputs['Roughness'].default_value = 0.5
    col = None
    base = (0.560, 0.355, 0.262)
    for key, c in (('rf_warm', (0.560, 0.290, 0.215)), ('rf_scalp', (0.085, 0.060, 0.048)), ('rf_lips', (0.420, 0.190, 0.160)),
                   ('rf_brow', (0.028, 0.020, 0.016)), ('rf_nails', (0.640, 0.450, 0.400))):
        at = N.new('ShaderNodeAttribute'); at.attribute_name = key
        mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.use_clamp = True
        mul.inputs[1].default_value = 0.45 if key == 'rf_warm' else 1.0
        L.new(at.outputs['Fac'], mul.inputs[0])
        mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'
        L.new(mul.outputs[0], mix.inputs['Factor'])
        if col is None:
            mix.inputs['A'].default_value = (*base, 1)
        else:
            L.new(col, mix.inputs['A'])
        mix.inputs['B'].default_value = (*c, 1)
        col = mix.outputs['Result']
    L.new(col, b.inputs['Base Color'])
    m.diffuse_color = (*base, 1)
    return m


# ------------------------------------------------------------------------------------------- eyes
def make_eye_image(path, s=512):
    """Sclera + dark-hazel iris + pupil on a planar map (centre = cornea apex)."""
    yy, xx = (np.mgrid[0:s, 0:s] + 0.5) / s * 2 - 1
    r = np.sqrt(xx ** 2 + yy ** 2); a = np.arctan2(yy, xx)
    ir = 0.49                                    # iris radius in map units (map spans the eyeball radius)
    pr = 0.15
    sclera = np.stack([0.80 - 0.05 * r, 0.76 - 0.07 * r, 0.72 - 0.07 * r], -1)
    fib = 0.5 + 0.5 * np.sin(a * 60 + 3 * np.sin(a * 7)) * np.cos(a * 23)
    rr = np.clip(r / ir, 0, 1)
    iris = np.stack([0.20 - 0.10 * rr + 0.04 * fib, 0.115 - 0.06 * rr + 0.025 * fib, 0.050 - 0.025 * rr + 0.01 * fib], -1)
    iris *= (1 - 0.55 * smooth01(0.80, 1.0, rr))[..., None]                           # limbal ring
    iris += (0.06 * np.exp(-((rr - 0.42) / 0.10) ** 2))[..., None] * np.array([1.0, 0.75, 0.35])  # collarette
    img = np.where((r < ir)[..., None], iris, sclera)
    img = np.where((r < pr)[..., None], np.array([0.01, 0.01, 0.012]), img)
    rgba = np.concatenate([img, np.ones((s, s, 1))], -1)
    im = bpy.data.images.new('T_RF01_Eye', s, s); im.pixels.foreach_set(np.clip(rgba[::-1], 0, 1).astype(np.float32).ravel())
    im.filepath_raw = path; im.file_format = 'PNG'; im.save()
    return im


def make_eyes(coll):
    cs, r = eye_centres()
    me = bpy.data.meshes.new('GAME_Eyes'); bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    for c in cs:
        res = bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=14, radius=r * 0.995)
        vs = res['verts']
        for v in vs:
            v.co = (v.co.x + c[0], v.co.y + c[1], v.co.z + c[2])
        # planar UV on the front hemisphere (-Y): the cornea apex maps to the UV centre
        for f in {f for v in vs for f in v.link_faces}:
            for lp in f.loops:
                q = lp.vert.co - __import__('mathutils').Vector(c)
                lp[uv].uv = (0.5 + q.x / (2 * r), 0.5 + q.z / (2 * r)) if q.y < 0 else (0.02, 0.5)
    bm.to_mesh(me); bm.free(); me.shade_smooth()
    ob = bpy.data.objects.new('GAME_Eyes', me); coll.objects.link(ob)
    return ob


# ------------------------------------------------------------------------------------------- main
def main():
    master_body = bpy.data.objects['RF01_Body']
    root = bpy.data.objects['RF01_Character_ROOT']
    log('CP4 body field + 2 mm mesh')
    field, J = build(cp=4)
    v, q = mesh_sparse(field, (-0.75, -0.26, -0.01), (0.75, 0.26, 1.83), 0.002, log=log)
    me = new_mesh('RF01_Body', v, q)
    v = relax(me, verts_np(me), field, iters=3)
    me.vertices.foreach_set('co', v.ravel()); me.update()
    old = master_body.data
    for mat in old.materials:
        me.materials.append(mat)
    master_body.data = me; bpy.data.meshes.remove(old)
    # keep the CP1 review briefs mask so the master still renders the same under the clothing
    c = face_centres(master_body); z, x = c[:, 2], np.abs(c[:, 0])
    top = 0.992 - 0.012 * np.clip(c[:, 1] / 0.08, 0, 1); legc = 0.775 + 0.030 * np.clip((x - 0.04) / 0.10, 0, 1)
    me.polygons.foreach_set('material_index', ((z < top) & (z > legc) & (x < 0.22)).astype(np.int32)); me.update()
    masks = skin_masks(field, verts_np(me), J)
    for k, val in masks.items():
        set_attr(me, k, val)
    master_body['rf_stage'] = 'CP4 face/hands (pre-retopology)'
    log(f'master body: {len(me.polygons)} quads, height {verts_np(me)[:, 2].max():.4f}')
    bpy.ops.wm.save_as_mainfile(filepath=MASTER, compress=True)
    log('saved master', MASTER)

    # ---------------- bake sources
    src = bpy.data.collections.new('BAKE_HIGH'); bpy.context.scene.collection.children.link(src)
    hb = copy_object(master_body, 'HIGH_Skin', src)
    hb.data.materials.clear(); hb.data.materials.append(skin_material())
    log('hair mass (high)')
    hf = Field(); hf.add(HairPrim(field)); hf.finalize()
    hv, hq = mesh_sparse(hf, H0 + np.array([-0.11, -0.16, -0.12]), H0 + np.array([0.11, 0.135, 0.15]), 0.0012, log=log,
                         reach=3.0)
    hme = new_mesh('HIGH_Hair', hv, hq)
    hv = relax(hme, verts_np(hme), hf, iters=2, lam=0.4); hme.vertices.foreach_set('co', hv.ravel()); hme.update()
    hh = bpy.data.objects.new('HIGH_Hair', hme); src.objects.link(hh)
    # drop the inner (scalp-side) faces: keep the visible outer surface
    cc = face_centres(hh); dbody = field.eval(cc)
    keep_faces(hh, dbody > 0.0009)
    hair_mat = bpy.data.materials.new('MAT_RF_Hair'); hair_mat.use_nodes = True
    hbsdf = hair_mat.node_tree.nodes['Principled BSDF']
    hbsdf.inputs['Base Color'].default_value = (0.018, 0.012, 0.009, 1); hbsdf.inputs['Roughness'].default_value = 0.45
    hair_mat.diffuse_color = (0.018, 0.012, 0.009, 1)
    hme.materials.append(hair_mat)
    log(f'high hair: {len(hme.polygons)} faces')

    # ---------------- game meshes
    game = bpy.data.collections.new('GAME'); bpy.context.scene.collection.children.link(game)
    W, df = np.array(J['wrist.L']), np.array(J['_df'])
    gs = copy_object(master_body, 'GAME_Skin', game)
    cc = face_centres(gs)
    head = (cc[:, 2] > 1.43) & (np.abs(cc[:, 0]) < 0.115) & (cc[:, 1] < 0.11)
    hands = np.zeros(len(cc), bool)
    for s in (1, -1):
        mv = np.array([s, 1, 1])
        hands |= ((cc - W * mv) @ (df * mv) > -0.035) & (np.linalg.norm(cc - W * mv, axis=1) < 0.26)
    keep_faces(gs, head | hands)
    gs.data.materials.clear()
    # decimate head and hands separately (head keeps more detail)
    bm = bmesh.new(); bm.from_mesh(gs.data); bm.free()
    gh = copy_object(gs, 'tmp_head', game); keep_faces(gh, face_centres(gh)[:, 2] > 1.3); decimate(gh, 6500)
    gk = copy_object(gs, 'tmp_hands', game); keep_faces(gk, face_centres(gk)[:, 2] <= 1.3); decimate(gk, 3600)
    bpy.data.objects.remove(gs)
    with bpy.context.temp_override(active_object=gh, selected_editable_objects=[gh, gk], selected_objects=[gh, gk]):
        bpy.ops.object.join()
    gh.name = 'GAME_Skin'; gh.data.name = 'GAME_Skin'
    smart_uv(gh, margin=0.003)
    log(f'GAME_Skin {tris(gh)} tris')
    px = copy_object(master_body, 'GAME_Proxy', game); px.data.materials.clear(); decimate(px, 14000)
    hair = copy_object(hh, 'GAME_Hair', game); decimate(hair, 3600); smart_uv(hair, margin=0.004)
    hair.data.materials.clear(); hair.data.materials.append(hair_mat)
    for src_name, name, target in (('RF01_Jacket', 'GAME_Jacket', 9000), ('RF01_Trousers', 'GAME_Trousers', 6500),
                                   ('RF01_Shoes', 'GAME_Shoes', 5000)):
        ob = copy_object(bpy.data.objects[src_name], name, game)            # single layer: no Solidify yet
        decimate(ob, target); smart_uv(ob, margin=0.003)
        ob.data.materials.clear()
        log(f'{name} {tris(ob)} tris')
    for src_name, name, target in (('RF01_ChestMark', 'GAME_ChestMark', 360), ('RF01_BackMark', 'GAME_BackMark', 360),
                                   ('RF01_MissionPatch', 'GAME_Patch', 900), ('RF01_Badge', 'GAME_Badge', 400),
                                   ('RF01_WristInterface', 'GAME_Wrist', 1400)):
        ob = copy_object(bpy.data.objects[src_name], name, game, apply=True)
        decimate(ob, target)
        log(f'{name} {tris(ob)} tris')
    eyes = make_eyes(game)
    em = bpy.data.materials.new('MAT_RF_Eye'); em.use_nodes = True
    et = em.node_tree.nodes.new('ShaderNodeTexImage'); et.image = make_eye_image(os.path.join(TEXG, 'T_RF01_Eye.png'))
    em.node_tree.links.new(et.outputs['Color'], em.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    em.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.12
    eyes.data.materials.append(em)
    total = sum(tris(o) for o in game.objects if o.name != 'GAME_Proxy')
    log(f'game triangles (before garment thickness): {total}')
    for o in src.objects:
        o.hide_render = True
    bpy.ops.wm.save_as_mainfile(filepath=GAME, compress=True)
    log('saved', GAME)


main()
