"""
rf01_identity.py - Checkpoint 3 identity objects for the RF-01 engineer (runs inside Blender).

Everything here is separate geometry seated on the approved garments (projected onto their SDF surfaces):
  RF01_ChestMark      left-chest identifier, embroidered on the navy yoke     (decal)
  RF01_BackMark       back-yoke insignia + RF-01, read from the gameplay camera (decal)
  RF01_MissionPatch   round RF-01 mission patch, left upper arm               (raised 1.6 mm, merrowed edge)
  RF01_Badge          facility ID card in a holder, clipped to the right chest pocket flap
  RF01_WristInterface slim mission interface strapped over the left sleeve
  RF01_Hardware       jacket zip slider + orange pull, cuff-tab snaps, thigh pocket zip pull
Artwork: art/character/textures/cp3/ (gen_cp3_textures.py). Fictional programme branding only.
"""
import bpy, bmesh, os
import numpy as np
from rf01_sdf import Field, Box, Cone, Ellipsoid, Intersect, Slab, Plane, FieldPrim, mesh_sparse, project, norm, frame
from rf01_body import hand_frame, P, FWD, UP

TEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'textures', 'cp3')


# ------------------------------------------------------------------------------------------- helpers
def unit_grad(field, p):
    g = field.grad(np.atleast_2d(p))
    return g / np.maximum(np.linalg.norm(g, axis=1), 1e-12)[:, None]


def seat(field, p, iters=8):
    """Closest surface point and outward normal."""
    q = project(field, np.atleast_2d(np.asarray(p, float)), iters=iters, max_step=0.02)
    return q[0], unit_grad(field, q)[0]


def link(ob, coll, parent):
    coll.objects.link(ob); ob.parent = parent
    return ob


def image_material(name, path, rough=0.75, alpha=True, emission=0.0, sheen=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N['Principled BSDF']
    tex = N.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    tex.interpolation = 'Cubic'
    L.new(tex.outputs['Color'], b.inputs['Base Color'])
    if alpha:
        L.new(tex.outputs['Alpha'], b.inputs['Alpha'])
    b.inputs['Roughness'].default_value = rough
    if sheen:
        b.inputs['Sheen Weight'].default_value = sheen
    if emission:
        L.new(tex.outputs['Color'], b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = emission
    return m


def flat_material(name, col, rough=0.6, metallic=0.0, sheen=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metallic
    if sheen:
        b.inputs['Sheen Weight'].default_value = sheen
    m.diffuse_color = (*col, 1)
    return m


def mesh_from(name, verts, faces, uvs=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    if uvs is not None:
        uv = me.uv_layers.new(name='UVMap')
        loop_v = np.empty(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', loop_v)
        uv.data.foreach_set('uv', np.asarray(uvs)[loop_v].ravel())
    me.validate()
    if smooth:
        me.shade_smooth()
    return me


# ------------------------------------------------------------------------------------------- decals
def conform_grid(field, centre, normal_hint, up_hint, w, h, nu, nv, lift, shape='rect'):
    """Grid (rect) or polar disc in the tangent plane at the seated centre, projected onto the surface and
    lifted along the local normal. Returns verts, quads, uvs, frame (c, n, right, up)."""
    c, n = seat(field, centre)
    if np.dot(n, normal_hint) < 0:
        n = -n
    up = np.asarray(up_hint, float); up = norm(up - n * np.dot(up, n))
    right = np.cross(-n, up)
    if shape == 'rect':
        us, vs = np.meshgrid(np.linspace(0, 1, nu + 1), np.linspace(0, 1, nv + 1), indexing='ij')
        uv = np.stack([us.ravel(), vs.ravel()], 1)
        quads = []
        for i in range(nu):
            for j in range(nv):
                a = i * (nv + 1) + j
                quads.append((a, a + nv + 1, a + nv + 2, a + 1))
    else:                                                     # disc: rings x segments, centre fan as quads
        rings, segs = nv, nu
        uv = [(0.5, 0.5)]
        for r in range(1, rings + 1):
            rr = r / rings
            for k in range(segs):
                t = 2 * np.pi * k / segs
                uv.append((0.5 + 0.5 * rr * np.cos(t), 0.5 + 0.5 * rr * np.sin(t)))
        uv = np.array(uv)
        quads = []
        for k in range(0, segs, 2):                           # centre: quads (0, k, k+1, k+2)
            quads.append((0, 1 + k, 1 + (k + 1) % segs, 1 + (k + 2) % segs))
        for r in range(1, rings):
            b0, b1 = 1 + (r - 1) * segs, 1 + r * segs
            for k in range(segs):
                quads.append((b0 + k, b1 + k, b1 + (k + 1) % segs, b0 + (k + 1) % segs))
    p = c + (uv[:, 0:1] - 0.5) * w * right + (uv[:, 1:2] - 0.5) * h * up
    p = project(field, p, iters=8, max_step=0.01)
    nn = unit_grad(field, p)
    p = p + nn * lift
    quads = np.array(quads)
    a, b, cc = p[quads[:, 0]], p[quads[:, 1]], p[quads[:, 2]]
    if np.dot(np.cross(b - a, cc - a).sum(0), n) < 0:
        quads = quads[:, ::-1]
    return p, quads, uv, (c, n, right, up)


def decal(name, field, centre, normal_hint, up_hint, w, h, image, coll, parent, lift=0.0006, res=(48, 16)):
    v, q, uv, fr = conform_grid(field, centre, normal_hint, up_hint, w, h, res[0], res[1], lift)
    ob = bpy.data.objects.new(name, mesh_from(name, v, q, uv))
    ob.data.materials.append(image_material('MAT_RF_' + name[5:], os.path.join(TEX, image), rough=0.82, sheen=0.3))
    ob.visible_shadow = False                                 # embroidery/print: no self-shadowing slab
    return link(ob, coll, parent), fr


def mission_patch(field, J, coll, parent):
    S, du = J['shoulder.L'], J['_du']
    lateral = norm(-np.cross(du, FWD))                        # outer face of the upper arm (up/out in A-pose)
    centre = S + 0.100 * du + 0.07 * lateral
    v, q, uv, fr = conform_grid(field, centre, lateral, -du, 0.078, 0.078, 64, 10, 0.0004, shape='disc')
    ob = bpy.data.objects.new('RF01_MissionPatch', mesh_from('RF01_MissionPatch', v, q, uv))
    ob.data.materials.append(image_material('MAT_RF_MissionPatch', os.path.join(TEX, 'T_RF01_MissionPatch.png'),
                                            rough=0.8, alpha=False, sheen=0.35))
    ob.data.materials.append(flat_material('MAT_RF_PatchEdge', (0.70, 0.68, 0.62), 0.85, sheen=0.3))
    so = ob.modifiers.new('Embroidered thickness', 'SOLIDIFY')
    so.thickness = 0.0016; so.offset = 1.0; so.use_rim = True; so.material_offset_rim = 1
    return link(ob, coll, parent), fr


# ------------------------------------------------------------------------------------------- badge
def box_mesh(bm, centre, axes, half, uv_front=None):
    """Axis-aligned box in the given frame; optional UV on the +z (front) face."""
    ax, ay, az = axes
    corners = {}
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                corners[(sx, sy, sz)] = bm.verts.new(tuple(centre + sx * half[0] * ax + sy * half[1] * ay + sz * half[2] * az))
    F = [((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)), ((-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)),
         ((-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)), ((1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1)),
         ((1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)), ((-1, 1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1))]
    faces = [bm.faces.new([corners[k] for k in f]) for f in F]
    return faces


def badge(field, J, coll, parent, mats):
    """CR80 card (54 x 86 mm) in a navy holder, clipped to the right chest pocket flap."""
    anchor, n = seat(field, P(-0.088, -0.12, 1.347))
    up = norm(UP - n * np.dot(UP, n)); right = np.cross(-n, up)
    # hang straight down from the flap edge; push out until the whole holder clears the jacket by 1 mm
    off = 0.003
    for _ in range(20):
        centre = anchor - up * 0.0545 + n * off
        pts = [centre + sx * 0.030 * right + sy * 0.0465 * up - n * 0.0014 for sx in (-1, 1) for sy in (-1, 0, 1)]
        dmin = field.eval(np.array(pts)).min()
        if dmin > 0.001:
            break
        off += 0.001
    bm = bmesh.new()
    holder = box_mesh(bm, centre, (right, up, n), (0.030, 0.0465, 0.0013))
    card_c = centre + n * 0.0019
    card = box_mesh(bm, card_c, (right, up, n), (0.027, 0.043, 0.0004))
    clip_c = anchor + n * (off * 0.6) + up * 0.002
    clip = box_mesh(bm, clip_c - up * 0.006, (right, up, n), (0.0062, 0.010, 0.0006))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.verts.index_update()
    for f in holder:
        f.material_index = 0
    for f in card:
        f.material_index = 1
    for f in clip:
        f.material_index = 2
    uv = bm.loops.layers.uv.new('UVMap')
    front = card[0]
    for loop, (u, v) in zip(front.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        loop[uv].uv = (u, v)
    me = bpy.data.meshes.new('RF01_Badge'); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('RF01_Badge', me)
    me.materials.append(mats['holder']); me.materials.append(image_material('MAT_RF_BadgeCard', os.path.join(TEX, 'T_RF01_Badge.png'), rough=0.35, alpha=False))
    me.materials.append(mats['metal'])
    bev = ob.modifiers.new('Edges', 'BEVEL'); bev.width = 0.0005; bev.segments = 2; bev.limit_method = 'ANGLE'
    return link(ob, coll, parent)


# ------------------------------------------------------------------------------------------- wrist interface
def wrist_interface(jacket, J, coll, parent, mats, log=print):
    W, df = J['wrist.L'], J['_df']
    u, t, nh = hand_frame(J)
    dorsal = norm(-nh - df * np.dot(-nh, df))
    c0, n = seat(jacket, W - 0.105 * df + dorsal * 0.06)
    side = norm(np.cross(n, df))
    along = norm(np.cross(side, n))
    f = Field()
    shell = FieldPrim(jacket, 0.0035)                          # outer strap surface: 3.5 mm over the sleeve
    strap = Intersect(Intersect(shell, Slab(c0, df, 0.012)), Cone(c0 - 0.03 * df, c0 + 0.03 * df, 0.075, 0.075))
    f.add(strap, tag='strap')
    housing = Box(c0 + n * 0.0035, (0.0170, 0.0230, 0.0022), 0.0022, np.stack([along, side, n]))    # top ~7.9 mm
    f.add(housing, k=0.003, tag='housing')
    f.sub(Box(c0 + n * 0.0085, (0.0115, 0.0185, 0.0004), 0.0008, np.stack([along, side, n])), k=0.0005,
          tag='screen recess', phase=1)
    inner = FieldPrim(jacket, 0.0002)                          # hollow: the sleeve passes through the strap
    f.sub(inner, k=0.0, tag='sleeve', phase=2)
    f.finalize()
    lo = c0 - 0.07; hi = c0 + 0.07
    v, q = mesh_sparse(f, lo, hi, 0.0009, log=log, reach=3.0)
    v = project(f, v, iters=3, max_step=0.0006)
    me = bpy.data.meshes.new('RF01_WristInterface')
    me.from_pydata([tuple(x) for x in v], [], [tuple(x) for x in q]); me.validate()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    me.shade_smooth()
    # materials: strap (0), housing (1), screen (2) with planar UV on the screen floor
    cen = np.empty(len(me.polygons) * 3); me.polygons.foreach_get('center', cen); cen = cen.reshape(-1, 3)
    nrm = np.empty(len(me.polygons) * 3); me.polygons.foreach_get('normal', nrm); nrm = nrm.reshape(-1, 3)
    loc = cen - c0
    a_, s_, h_ = loc @ along, loc @ side, loc @ n
    is_house = (np.abs(a_) < 0.0200) & (np.abs(s_) < 0.0260) & (h_ > 0.0035)
    is_screen = is_house & (np.abs(a_) < 0.0118) & (np.abs(s_) < 0.0188) & (nrm @ n > 0.9) & (h_ < 0.0077)
    idx = np.where(is_screen, 2, np.where(is_house, 1, 0)).astype(np.int32)
    me.polygons.foreach_set('material_index', idx)
    uvl = me.uv_layers.new(name='UVMap')
    lv = np.empty(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', lv)
    vl = v[lv] - c0
    uvs = np.stack([0.5 + (vl @ side) / 0.0386, 0.5 + (vl @ along) / 0.0246], 1)
    uvl.data.foreach_set('uv', uvs.ravel())
    for m in (mats['strap'], mats['housing'], image_material('MAT_RF_WristScreen', os.path.join(TEX, 'T_RF01_WristUI.png'),
                                                             rough=0.55, alpha=False, emission=1.6)):    # matte anti-glare, like the facility screens
        me.materials.append(m)
    ob = bpy.data.objects.new('RF01_WristInterface', me)
    return link(ob, coll, parent)


# ------------------------------------------------------------------------------------------- hardware
def hardware(jacket, trousers, J, coll, parent, mats, log=print):
    """Small separate parts: zip slider + orange pull at the collar, snaps on the cuff tabs, thigh zip pull."""
    from rf01_clothing import arm_frames, THIGH_POCKET
    parts = []
    # zip slider + pull, at the top of the front zip
    top, n = seat(jacket, P(0.0, -0.11, 1.512))
    up = norm(UP - n * np.dot(UP, n)); right = np.cross(-n, up)
    R = np.stack([right, up, n])
    f = Field()
    f.add(Box(top + n * 0.0030 - up * 0.004, (0.0045, 0.0065, 0.0018), 0.0010, R), tag='slider')
    f.finalize(); parts.append(('slider', f, top, 1))
    g = Field()
    g.add(Box(top + n * 0.0052 - up * 0.022, (0.0042, 0.0140, 0.0012), 0.0011, R), tag='pull')
    g.finalize(); parts.append(('pull', g, top - up * 0.022, 0))
    # snaps on the cuff tabs (both sleeves)
    S, E, W, du, df, front_f, side_f, Rf = arm_frames(J)
    for s in (1, -1):
        mv = np.array([s, 1, 1])
        c, nn = seat(jacket, (W - 0.024 * df - 0.046 * front_f) * mv)
        h = Field(); h.add(Cone(c + nn * 0.0004, c + nn * 0.0028, 0.0046, 0.0040), tag='snap'); h.finalize()
        parts.append(('snap', h, c, 2))
    # thigh pocket zip pull (left)
    c, nn = seat(trousers, P(0.235, 0.020, 0.720))
    up2 = norm(UP - nn * np.dot(UP, nn)); r2 = np.cross(-nn, up2)
    k = Field(); k.add(Box(c + nn * 0.0028 - up2 * 0.010, (0.0035, 0.0100, 0.0010), 0.0009, np.stack([r2, up2, nn])), tag='thigh pull')
    k.finalize(); parts.append(('thigh pull', k, c, 1))
    allv, allq, allm = [], [], []
    off = 0
    for tag, fld, cen, mat in parts:
        v, q = mesh_sparse(fld, cen - 0.035, cen + 0.035, 0.0006, log=lambda *a: None, reach=3.0)
        v = project(fld, v, iters=3, max_step=0.0004)
        allv.append(v); allq.append(q + off); allm.append(np.full(len(q), mat, np.int32)); off += len(v)
    v = np.concatenate(allv); q = np.concatenate(allq); mi = np.concatenate(allm)
    me = bpy.data.meshes.new('RF01_Hardware')
    me.from_pydata([tuple(x) for x in v], [], [tuple(x) for x in q]); me.validate()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    me.polygons.foreach_set('material_index', mi); me.shade_smooth()
    for m in (mats['orange_rubber'], mats['gunmetal'], mats['metal']):
        me.materials.append(m)
    ob = bpy.data.objects.new('RF01_Hardware', me)
    return link(ob, coll, parent)


# ------------------------------------------------------------------------------------------- yoke piping cord
def yoke_piping(jacket, J, coll, parent, mat, radius=0.0011, log=print):
    """Orange piping cord along the body-side yoke seam, front and back, armhole to armhole. A real cord (curve
    with a round bevel) instead of a painted stripe, so it stays continuous at any mesh density."""
    from rf01_clothing import YOKE_C, YOKE_N, torso_side
    side = torso_side(J)
    def seam_point(x, front):
        # point on the yoke plane at this x, on the front (y<0) or back (y>0) surface of the jacket
        ys = np.linspace(-0.22, 0.0, 221) if front else np.linspace(0.24, 0.0, 241)
        z = YOKE_C[2] + (YOKE_N[1] / -YOKE_N[2]) * ys
        p = np.stack([np.full_like(ys, x), ys, z], 1)
        d = jacket.eval(p)
        k = np.flatnonzero(d < 0)
        if not len(k):
            return None
        i = k[0]
        if i == 0:
            return None
        t = d[i - 1] / (d[i - 1] - d[i])
        return p[i - 1] + t * (p[i] - p[i - 1])
    curves = []
    for front in (True, False):
        pts = []
        for x in np.linspace(-0.30, 0.30, 241):
            q = seam_point(x, front)
            if q is None:
                continue
            sm = side if x >= 0 else side.mirror()
            if sm.d(q[None])[0] > 0:                        # beyond the armhole seam
                continue
            pts.append(q)
        if len(pts) > 4:
            pts = np.array(pts)
            n = jacket.grad(pts); n /= np.linalg.norm(n, axis=1)[:, None]
            curves.append(pts + n * (radius + 0.0003))         # tangent to the fabric, clear of mesh error
    cu = bpy.data.curves.new('RF01_JacketPiping', 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = radius; cu.bevel_resolution = 3; cu.resolution_u = 2; cu.use_fill_caps = True
    for pts in curves:
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for p_, c in zip(sp.points, pts):
            p_.co = (*c, 1.0)
    tmp = bpy.data.objects.new('tmp_piping', cu); coll.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp); bpy.data.curves.remove(cu)
    me.name = 'RF01_JacketPiping'; me.materials.clear(); me.materials.append(mat)
    me.shade_smooth()
    ob = bpy.data.objects.new('RF01_JacketPiping', me)
    log(f'  piping: {len(curves)} runs, {sum(len(c) for c in curves)} points')
    return link(ob, coll, parent)
