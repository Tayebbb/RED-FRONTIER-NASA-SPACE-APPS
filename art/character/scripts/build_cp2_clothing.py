"""
build_cp2_clothing.py - Checkpoint 2: clothing blockout (jacket, trousers, shoes) added to the RF-01 master.

Run:
  blender -b art/character/source/RF01_Engineer_MASTER.blend --python art/character/scripts/build_cp2_clothing.py --
      [--quick] [--out PATH]

Opens the approved CP1 master, (re)builds the CLOTHING collection only, and saves. RF01_Body and RF01_Eyes are not
modified. --quick meshes at 5 mm and writes to --out (look-dev); default is 3 mm garments / 2 mm shoes.
"""
import bpy, bmesh, sys, os, time, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import importlib, rf01_sdf, rf01_body, rf01_clothing
for m in (rf01_sdf, rf01_body, rf01_clothing):
    importlib.reload(m)
from rf01_sdf import mesh_sparse, project
from rf01_clothing import build_all
from rf01_body import P

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
QUICK = '--quick' in argv
OUT = os.path.abspath(argv[argv.index('--out') + 1]) if '--out' in argv else bpy.data.filepath
H_GARMENT = 0.005 if QUICK else 0.003
H_SHOE = 0.004 if QUICK else 0.002
STAGE = int(argv[argv.index('--stage') + 1]) if '--stage' in argv else 2

T0 = time.time()
def log(*a):
    print(f'[{time.time() - T0:7.1f}s]', *a, flush=True)


# ------------------------------------------------------------------------------------------- mesh processing
def edges_of(q):
    e = np.concatenate([q[:, [0, 1]], q[:, [1, 2]], q[:, [2, 3]], q[:, [3, 0]]])
    return np.sort(e, 1)


def grad(fn, p, e=2.5e-4):
    k = np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], float)
    g = np.zeros_like(p)
    for kk in k:
        g += kk[None, :] * fn(p + e * kk)[:, None]
    return g / (4.0 * e)


def open_shell(G, v, q, h):
    """Delete the faces that lie on the clip caps; snap the new boundary onto the hem/cuff/collar curves."""
    c = v[q].mean(1)
    g = G['field'].eval(c); r = G['clip'](c)
    keep = ~(r > g)
    q = q[keep]
    used = np.unique(q); remap = -np.ones(len(v), np.int64); remap[used] = np.arange(len(used))
    v = v[used]; q = remap[q]
    e, cnt = np.unique(edges_of(q), axis=0, return_counts=True)
    bedges = e[cnt == 1]
    bverts = np.unique(bedges)
    # only edges on a real opening (clip ~ 0) are snapped; anything else is a stray hole -> filled
    on_clip = np.abs(G['clip'](v[bverts])) < 2.5 * h
    stray = bverts[~on_clip]
    bverts = bverts[on_clip]
    bedges = bedges[np.isin(bedges, bverts).all(1)]
    log(f'    caps removed: {int((~keep).sum())} faces; opening boundary {len(bverts)} verts; '
        f'stray hole verts {len(stray)} (left in place)')
    return v, q, bedges, bverts


def snap_boundary(G, v, bv, iters=8):
    """Move boundary vertices onto clip = 0 while staying on the garment surface."""
    clip, field = G['clip'], G['field']
    p = v[bv].copy()
    for _ in range(iters):
        r = clip(p); gr = grad(clip, p)
        st = (r / np.maximum((gr * gr).sum(1), 1e-9))[:, None] * gr
        ln = np.linalg.norm(st, axis=1)
        p -= st * np.minimum(1.0, 0.004 / np.maximum(ln, 1e-12))[:, None]
        p = project(field, p, iters=1, max_step=0.004)
    v[bv] = p
    return v


def relax(G, v, q, bedges, bverts, iters=3, lam=0.45):
    e = np.unique(edges_of(q), axis=0)
    isb = np.zeros(len(v), bool); isb[bverts] = True
    for _ in range(iters):
        acc = np.zeros_like(v); cnt = np.zeros(len(v))
        np.add.at(acc, e[:, 0], v[e[:, 1]]); np.add.at(acc, e[:, 1], v[e[:, 0]])
        np.add.at(cnt, e[:, 0], 1); np.add.at(cnt, e[:, 1], 1)
        nv = v + lam * (acc / np.maximum(cnt, 1)[:, None] - v)
        # boundary verts relax along the boundary loop only
        if len(bedges):
            accb = np.zeros_like(v); cb = np.zeros(len(v))
            np.add.at(accb, bedges[:, 0], v[bedges[:, 1]]); np.add.at(accb, bedges[:, 1], v[bedges[:, 0]])
            np.add.at(cb, bedges[:, 0], 1); np.add.at(cb, bedges[:, 1], 1)
            nv[isb] = v[isb] + lam * (accb[isb] / np.maximum(cb[isb], 1)[:, None] - v[isb])
        v = nv
        inner = ~isb
        v[inner] = project(G['field'], v[inner], iters=2, max_step=0.003)
        if len(bverts):
            v = snap_boundary(G, v, bverts, iters=3)
    return v


def consistent_winding(v, q):
    """Surface-nets quads are not consistently wound per axis; let bmesh make every patch coherent."""
    me = bpy.data.meshes.new('tmp')
    me.from_pydata([tuple(x) for x in v], [], [tuple(f) for f in q])
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table()
    out = np.array([[vv.index for vv in f.verts] for f in bm.faces], np.int64)
    bm.free(); bpy.data.meshes.remove(me)
    return out


def orient_outward(G, v, q):
    """Make face winding point out of the garment (Solidify then offsets inward)."""
    a, b, c = v[q[:, 0]], v[q[:, 1]], v[q[:, 2]]
    n = np.cross(b - a, c - a)
    cen = v[q].mean(1)
    gd = grad(G['field'].eval, cen)
    if (np.einsum('ij,ij->i', n, gd) < 0).mean() > 0.5:
        q = q[:, ::-1]
    return q


def to_object(name, v, q, coll, parent):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(x) for x in v], [], [tuple(f) for f in q])
    me.validate(clean_customdata=False); me.shade_smooth()
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob); ob.parent = parent
    return ob


# ------------------------------------------------------------------------------------------- materials
def clay(name, col, rough=0.7):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = 0.35
    m.diffuse_color = (*col, 1)
    return m


# ------------------------------------------------------------------------------------------- main
def main():
    root = bpy.data.objects['RF01_Character_ROOT']
    croot = bpy.data.collections['RF01_Character']
    cloth = bpy.data.collections['CLOTHING']
    for ob in list(cloth.objects):
        bpy.data.objects.remove(ob)
    if STAGE >= 3:
        for ob in list(bpy.data.collections['ACCESSORIES'].objects):
            bpy.data.objects.remove(ob)
    log(f'build garment fields (quick={QUICK}, stage={STAGE})')
    body, J, garments = build_all(stage=STAGE)
    mats = {
        'RF01_Jacket': [clay('MAT_Review_Jacket', (0.52, 0.515, 0.49), 0.75), clay('MAT_Review_GarmentInside', (0.16, 0.16, 0.165), 0.9)],
        'RF01_Trousers': [clay('MAT_Review_Trousers', (0.050, 0.056, 0.070), 0.8), clay('MAT_Review_GarmentInside', (0.16, 0.16, 0.165), 0.9)],
        'RF01_Shoes': [clay('MAT_Review_ShoeUpper', (0.030, 0.031, 0.034), 0.55), clay('MAT_Review_ShoeSole', (0.075, 0.075, 0.078), 0.85)],
    }
    report = {}
    for name in ('RF01_Shoes', 'RF01_Trousers', 'RF01_Jacket'):
        G = garments[name]
        h = H_SHOE if name == 'RF01_Shoes' else H_GARMENT
        log(f'{name}: meshing at {h*1000:.1f} mm')
        v, q = mesh_sparse(G['mesh'], *G['bbox'], h, log=log, reach=3.0)   # displaced fields are not exact SDFs
        if G['thickness'] > 0:
            v, q, be, bv = open_shell(G, v, q, h)
            v = snap_boundary(G, v, bv)
        else:
            be, bv = np.zeros((0, 2), np.int64), np.zeros(0, np.int64)
        v = relax(G, v, q, be, bv, iters=2 if QUICK else 3)
        q = consistent_winding(v, q)
        q = orient_outward(G, v, q)
        if G['mirror']:
            vm = v * np.array([-1.0, 1.0, 1.0]); qm = q[:, ::-1] + len(v)
            v = np.concatenate([v, vm]); q = np.concatenate([q, qm])
        ob = to_object(name, v, q, cloth, root)
        # safety net: close any tiny stray hole (a dropped surface-nets quad); real openings are long loops
        bm = bmesh.new(); bm.from_mesh(ob.data)
        nb = sum(1 for e in bm.edges if e.is_boundary)
        res = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=12)
        bm.to_mesh(ob.data); bm.free(); ob.data.update()
        report.setdefault('holes_filled', {})[name] = len(res['faces'])
        if STAGE >= 3:
            paint_attributes(ob, G)
            for m in cp3_materials()[name]:
                ob.data.materials.append(m)
        else:
            for m in mats[name]:
                ob.data.materials.append(m)
        if name == 'RF01_Shoes':
            # sole faces: below the sole top line (28 mm heel -> 19 mm forefoot), material slot 1
            c = np.empty(len(ob.data.polygons) * 3); ob.data.polygons.foreach_get('center', c); c = c.reshape(-1, 3)
            idx = (c[:, 2] < 0.0283).astype(np.int32)
            ob.data.polygons.foreach_set('material_index', idx); ob.data.update()
        if G['thickness'] > 0:
            so = ob.modifiers.new('Thickness', 'SOLIDIFY')
            so.thickness = G['thickness']; so.offset = -1.0; so.use_even_offset = False; so.use_rim = True
            so.use_rim_only = False; so.material_offset = 1; so.material_offset_rim = 0
            so.use_quality_normals = True
        ob['rf_stage'] = ('CP3 hero design' if STAGE >= 3 else 'CP2 clothing blockout') + ' (pre-retopology)'
        ob['rf_thickness_m'] = G['thickness']
        report[name] = dict(base_quads=len(q))
        log(f'  {name}: {len(v)} verts, {len(q)} quads (before Solidify)')
    # ---- intersection audit
    report['audit'] = audit(body, garments)
    if STAGE >= 3:
        report['identity'] = build_identity(garments, J, root, cloth)
        report['silhouette_vs_cp2'] = silhouette_check(garments)
    report['evaluated_triangles'] = tri_counts()
    log('report', json.dumps(report))
    root['rf_cp3_report' if STAGE >= 3 else 'rf_cp2_report'] = json.dumps(report)
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    log('saved', OUT)


def tri_counts():
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    names = ['RF01_Body', 'RF01_Eyes', 'RF01_Jacket', 'RF01_Trousers', 'RF01_Shoes']
    names += [o.name for o in bpy.data.collections['ACCESSORIES'].objects]
    names += [n for n in ('RF01_Hardware', 'RF01_JacketPiping') if n in bpy.data.objects]
    for name in names:
        ob = bpy.data.objects[name].evaluated_get(dg)
        me = ob.to_mesh(); me.calc_loop_triangles(); out[name] = len(me.loop_triangles); ob.to_mesh_clear()
    return out


def hands_mask(p):
    root = bpy.data.objects['RF01_Character_ROOT']
    W = np.array(root['joint_wrist.L']); E = np.array(root['joint_elbow.L'])
    df = (W - E) / np.linalg.norm(W - E)
    m = np.zeros(len(p), bool)
    for s in (1, -1):
        mv = np.array([s, 1, 1])
        m |= ((p - W * mv) @ (df * mv) > 0.0) & (np.linalg.norm(p - W * mv, axis=1) < 0.24)
    return m


def audit(body, garments):
    """Counts of vertices where layers interpenetrate (A-pose)."""
    def verts(name):
        me = bpy.data.objects[name].data
        a = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', a); return a.reshape(-1, 3)
    res = {}
    bv = verts('RF01_Body')
    for name in ('RF01_Jacket', 'RF01_Trousers'):
        G = garments[name]; t = G['thickness']
        v = verts(name)
        n = grad(G['field'].eval, v); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-9)[:, None]
        inner = v - t * n
        db = body.eval(inner)
        res[name + ' inner surface inside body (verts)'] = int((db < 0).sum())
        res[name + ' inner surface within 2 mm of body (verts)'] = int((db < 0.002).sum())
        # body poking out through this garment where the garment covers it
        cov = (G['clip'](bv) < -0.004)
        if name == 'RF01_Trousers':
            cov &= np.abs(bv[:, 0]) < 0.24                 # legs/pelvis only, not the hanging hands
        else:
            cov &= ~hands_mask(bv)
        dg = G['field'].eval(bv[cov])
        res[name + ' body verts outside garment shell'] = int((dg > -t).sum())
    J = garments['RF01_Jacket']; T = garments['RF01_Trousers']
    v = verts('RF01_Jacket')
    n = grad(J['field'].eval, v); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-9)[:, None]
    inner = v - J['thickness'] * n
    m = T['clip'](inner) < 0
    res['jacket inner surface inside trousers (verts)'] = int((T['field'].eval(inner[m]) < 0).sum())
    S = garments['RF01_Shoes']
    tv = verts('RF01_Trousers')
    n = grad(T['field'].eval, tv); n /= np.maximum(np.linalg.norm(n, axis=1), 1e-9)[:, None]
    inner = tv - T['thickness'] * n
    near = inner[:, 2] < 0.20
    sl = S['mesh'].eval(inner[near]); sr = S['mesh'].eval(inner[near] * np.array([-1, 1, 1]))
    res['trouser inner surface inside shoes (verts)'] = int((np.minimum(sl, sr) < 0).sum())
    feet = bv[bv[:, 2] < 0.075]                    # below the collar opening
    fl = S['mesh'].eval(feet); fr = S['mesh'].eval(feet * np.array([-1, 1, 1]))
    res['foot verts outside the shoes (below 7.5 cm)'] = int((np.minimum(fl, fr) > 0).sum())
    return res



# ------------------------------------------------------------------------------------------- Checkpoint 3
def paint_attributes(ob, G):
    """Signed distance to the colour-block regions, per vertex; the shader thresholds it (crisp panel edges that
    do not follow the mesh faces)."""
    me = ob.data
    v = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', v); v = v.reshape(-1, 3)
    for key in ('dark', 'orange', 'tone'):
        prims = G['paint'][key]
        d = np.full(len(v), 1.0)
        for p in prims:
            d = np.minimum(d, p.d(v))
        a = me.attributes.get('rf_' + key) or me.attributes.new('rf_' + key, 'FLOAT', 'POINT')
        a.data.foreach_set('value', d.astype(np.float32))


_CP3_MATS = {}


def blocked_material(name, base, dark, tone, orange, rough=0.8, sheen=0.25, width=0.0006):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    for n in list(N):
        if n.type not in ('BSDF_PRINCIPLED', 'OUTPUT_MATERIAL'):
            N.remove(n)
    b = N['Principled BSDF']
    b.inputs['Roughness'].default_value = rough
    b.inputs['Sheen Weight'].default_value = sheen
    col = None
    for key, c in (('tone', tone), ('dark', dark), ('orange', orange)):
        at = N.new('ShaderNodeAttribute'); at.attribute_name = 'rf_' + key
        mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY_ADD'; mul.use_clamp = True
        mul.inputs[1].default_value = -1.0 / width; mul.inputs[2].default_value = 0.5
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


def sole_material():
    m = bpy.data.materials.get('MAT_RF_ShoeSole') or bpy.data.materials.new('MAT_RF_ShoeSole')
    m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N['Principled BSDF']; b.inputs['Roughness'].default_value = 0.85
    geo = N.new('ShaderNodeNewGeometry'); sep = N.new('ShaderNodeSeparateXYZ')
    L.new(geo.outputs['Position'], sep.inputs[0])
    st = N.new('ShaderNodeMath'); st.operation = 'LESS_THAN'; st.inputs[1].default_value = 0.0075
    L.new(sep.outputs['Z'], st.inputs[0])
    mix = N.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = (0.095, 0.098, 0.104, 1)          # midsole: mid grey
    mix.inputs['B'].default_value = (0.012, 0.012, 0.013, 1)          # outsole: black rubber
    L.new(st.outputs[0], mix.inputs['Factor']); L.new(mix.outputs['Result'], b.inputs['Base Color'])
    m.diffuse_color = (0.095, 0.098, 0.104, 1)
    return m


# Red Frontier palette (linear). Light jacket = warm off-white fabric, navy = facility-dark structure,
# orange = facility #C2501C, used only as small accents.
OFFWHITE = (0.600, 0.585, 0.545)
LIGHTGREY = (0.410, 0.405, 0.390)
NAVY = (0.019, 0.027, 0.048)
ORANGE = (0.539, 0.080, 0.011)
TROUSER = (0.021, 0.025, 0.038)
TROUSER_TONE = (0.013, 0.016, 0.025)
SHOE = (0.027, 0.029, 0.033)
RUBBER = (0.010, 0.010, 0.011)
SHOE_TONE = (0.048, 0.050, 0.055)


def cp3_materials():
    if not _CP3_MATS:
        lining = flat('MAT_RF_Lining', (0.015, 0.020, 0.032), 0.85)
        _CP3_MATS['RF01_Jacket'] = [blocked_material('MAT_RF_Jacket', OFFWHITE, NAVY, LIGHTGREY, ORANGE, 0.78, 0.3), lining]
        _CP3_MATS['RF01_Trousers'] = [blocked_material('MAT_RF_Trousers', TROUSER, (0.008, 0.009, 0.012), TROUSER_TONE, ORANGE, 0.82, 0.25), lining]
        _CP3_MATS['RF01_Shoes'] = [blocked_material('MAT_RF_ShoeUpper', SHOE, RUBBER, SHOE_TONE, ORANGE, 0.55, 0.0), sole_material()]
    return _CP3_MATS


def flat(name, col, rough=0.6, metallic=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metallic
    m.diffuse_color = (*col, 1)
    return m


def build_identity(garments, J, root, cloth):
    import rf01_identity as ID
    importlib.reload(ID)
    acc = bpy.data.collections['ACCESSORIES']
    jf, tf = garments['RF01_Jacket']['field'], garments['RF01_Trousers']['field']
    mats = {'holder': flat('MAT_RF_BadgeHolder', NAVY, 0.45), 'metal': flat('MAT_RF_Metal', (0.62, 0.62, 0.64), 0.3, 1.0),
            'gunmetal': flat('MAT_RF_Gunmetal', (0.20, 0.21, 0.22), 0.35, 1.0),
            'orange_rubber': flat('MAT_RF_OrangeRubber', ORANGE, 0.55),
            'strap': flat('MAT_RF_Strap', NAVY, 0.8), 'housing': flat('MAT_RF_DeviceHousing', (0.030, 0.032, 0.036), 0.4)}
    out = {}
    ob, fr = ID.decal('RF01_ChestMark', jf, P(0.085, -0.12, 1.420), (0, -1, 0), (0, 0, 1), 0.080, 0.080 * 578 / 2189,
                      'T_RF01_ChestMark.png', acc, root)
    out['RF01_ChestMark'] = [round(float(x), 4) for x in fr[0]]
    ob, fr = ID.decal('RF01_BackMark', jf, P(0.0, 0.16, 1.430), (0, 1, 0), (0, 0, 1), 0.062, 0.0775,
                      'T_RF01_BackMark.png', acc, root, res=(24, 30))
    out['RF01_BackMark'] = [round(float(x), 4) for x in fr[0]]
    ob, fr = ID.mission_patch(jf, J, acc, root)
    out['RF01_MissionPatch'] = [round(float(x), 4) for x in fr[0]]
    ID.badge(jf, J, acc, root, mats)
    ID.wrist_interface(jf, J, acc, root, mats, log=log)
    ID.hardware(jf, tf, J, cloth, root, mats, log=log)
    ID.yoke_piping(jf, J, cloth, root, flat('MAT_RF_Piping', ORANGE, 0.6), log=log)
    for o in list(acc.objects) + [bpy.data.objects['RF01_Hardware'], bpy.data.objects['RF01_JacketPiping']]:
        o['rf_stage'] = 'CP3 hero design'
    log('identity objects:', [o.name for o in acc.objects])
    return out


def silhouette_check(garments):
    """How far the CP3 garment surfaces sit from the approved CP2 surfaces (same code at stage 2)."""
    _, _, g2 = build_all(stage=2)
    out = {}
    for name in ('RF01_Jacket', 'RF01_Trousers', 'RF01_Shoes'):
        me = bpy.data.objects[name].data
        v = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', v); v = v.reshape(-1, 3)
        d = np.abs(g2[name]['mesh'].eval(v))
        if g2[name]['mirror']:                       # shoes: the object holds both feet, the field the left
            d = np.minimum(d, np.abs(g2[name]['mesh'].eval(v * np.array([-1.0, 1.0, 1.0]))))
        out[name] = dict(median_mm=round(float(np.median(d)) * 1000, 3), p99_mm=round(float(np.percentile(d, 99)) * 1000, 3),
                         max_mm=round(float(d.max()) * 1000, 3), over_2mm_pct=round(float((d > 0.002).mean()) * 100, 3))
    return out


main()
