"""
build_cp1_body.py - Checkpoint 1: build the RF-01 engineer body from the anatomical SDF into a new .blend.

Run:
  blender -b --factory-startup --python art/character/scripts/build_cp1_body.py -- [--quick] [--h 0.002] [--out PATH]

--quick   4 mm look-dev mesh
default   2 mm sculpt-stage mesh (surface nets, relaxed and projected onto the anatomy field). QuadriFlow is not
          usable here (Blender 5.2 rejects voxel-remeshed input as non-manifold), so designed retopology is a
          separate step before rigging.

Never touches facility, rover or Godot files: writes only under art/character/.
"""
import bpy, bmesh, sys, os, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                         # art/character
sys.path.insert(0, HERE)
import importlib, rf01_sdf, rf01_body
importlib.reload(rf01_sdf); importlib.reload(rf01_body)
from rf01_sdf import mesh_sparse, project
from rf01_body import build, eye_centres, skeleton

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
QUICK = '--quick' in argv
H = float(argv[argv.index('--h') + 1]) if '--h' in argv else (0.004 if QUICK else 0.002)
OUT = argv[argv.index('--out') + 1] if '--out' in argv else os.path.join(ROOT, 'source', 'RF01_Engineer_MASTER.blend')
REGION = argv[argv.index('--region') + 1] if '--region' in argv else 'all'
CP = int(argv[argv.index('--cp') + 1]) if '--cp' in argv else 1
BOXES = {'all': ((-0.75, -0.26, -0.01), (0.75, 0.26, 1.83)), 'head': ((-0.11, -0.16, 1.50), (0.11, 0.13, 1.83)),
         'hand': ((0.45, -0.20, 0.80), (0.75, 0.05, 1.10))}

T0 = time.time()
def log(*a):
    print(f'[{time.time() - T0:7.1f}s]', *a, flush=True)


# ------------------------------------------------------------------------------------------- scene skeleton
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 1.0; sc.unit_settings.length_unit = 'METERS'
    return sc


def coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def mesh_obj(name, verts, faces, collection, parent=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(clean_customdata=False)
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    if parent:
        ob.parent = parent
    return ob


def fix_normals(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    ob.data.shade_smooth()


def verts_np(me):
    a = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', a); return a.reshape(-1, 3)


def set_verts(me, v):
    me.vertices.foreach_set('co', v.ravel()); me.update()


def relax(me, v, field, iters=2, lam=0.5):
    """Laplacian relax along the surface, then project back onto the field."""
    e = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get('vertices', e); e = e.reshape(-1, 2)
    for _ in range(iters):
        acc = np.zeros_like(v); cnt = np.zeros(len(v))
        np.add.at(acc, e[:, 0], v[e[:, 1]]); np.add.at(acc, e[:, 1], v[e[:, 0]])
        np.add.at(cnt, e[:, 0], 1); np.add.at(cnt, e[:, 1], 1)
        v = v + lam * (acc / np.maximum(cnt, 1)[:, None] - v)
        v = project(field, v, iters=3)
    return v


# ------------------------------------------------------------------------------------------- materials
def mat_clay():
    m = bpy.data.materials.new('MAT_Review_Clay'); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.40, 0.355, 0.325, 1)   # warm neutral clay (skin-adjacent value)
    b.inputs['Roughness'].default_value = 0.58
    b.inputs['Specular IOR Level'].default_value = 0.35
    m.diffuse_color = (0.40, 0.355, 0.325, 1)
    return m


def mat_base_garment():
    m = bpy.data.materials.new('MAT_Review_BaseGarment'); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.055, 0.060, 0.070, 1)
    b.inputs['Roughness'].default_value = 0.8
    m.diffuse_color = (0.055, 0.06, 0.07, 1)
    return m


def mat_eye():
    """Proportion-review eye: off-white sclera, brown iris, dark pupil, glossy (CP4 replaces it)."""
    m = bpy.data.materials.new('MAT_Review_Eye'); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; Ln = nt.links
    b = N['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.08
    geo = N.new('ShaderNodeNewGeometry')
    attr = N.new('ShaderNodeAttribute'); attr.attribute_name = 'eye_t'      # 1 at the cornea apex
    r1 = N.new('ShaderNodeValToRGB'); cr = r1.color_ramp
    cr.interpolation = 'EASE'
    cr.elements[0].position = 0.0; cr.elements[0].color = (0.80, 0.76, 0.72, 1)
    cr.elements[1].position = 0.866; cr.elements[1].color = (0.80, 0.76, 0.72, 1)
    e = cr.elements.new(0.878); e.color = (0.16, 0.085, 0.040, 1)
    e = cr.elements.new(0.978); e.color = (0.22, 0.13, 0.06, 1)
    e = cr.elements.new(0.984); e.color = (0.012, 0.010, 0.010, 1)
    e = cr.elements.new(1.0); e.color = (0.012, 0.010, 0.010, 1)
    Ln.new(attr.outputs['Fac'], r1.inputs['Fac'])
    Ln.new(r1.outputs['Color'], b.inputs['Base Color'])
    m.diffuse_color = (0.8, 0.76, 0.72, 1)
    return m


# ------------------------------------------------------------------------------------------- eyes
def make_eyes(col, parent, mat):
    cs, r = eye_centres()
    obs = []
    for i, c in enumerate(cs):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=32, radius=r)
        # orient the pole forward (-Y)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                         matrix=__import__('mathutils').Matrix.Rotation(np.radians(90), 4, 'X'))
        me = bpy.data.meshes.new('RF01_Eye_' + 'LR'[i]); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(me.name, me); col.objects.link(ob)
        v = verts_np(me)
        # slight corneal bulge in front
        t = np.clip(-v[:, 1] / r, 0, 1)
        bulge = np.clip((t - 0.80) / 0.20, 0, 1) ** 2 * 0.0007
        v[:, 1] -= bulge
        set_verts(me, v + np.asarray(c))
        a = me.attributes.new('eye_t', 'FLOAT', 'POINT'); a.data.foreach_set('value', t)
        me.materials.append(mat); me.shade_smooth()
        obs.append(ob)
    # join both into RF01_Eyes
    ctx = {'active_object': obs[0], 'selected_editable_objects': obs, 'selected_objects': obs}
    with bpy.context.temp_override(**ctx):
        bpy.ops.object.join()
    eyes = obs[0]; eyes.name = 'RF01_Eyes'; eyes.data.name = 'RF01_Eyes'
    eyes.parent = parent
    return eyes


# ------------------------------------------------------------------------------------------- base garment mask
def assign_garment(ob, J):
    """Material slot 1 on the faces of a plain boxer-brief zone (review modesty only; CP2 replaces it)."""
    me = ob.data
    n = len(me.polygons)
    c = np.empty(n * 3); me.polygons.foreach_get('center', c); c = c.reshape(-1, 3)
    z, x = c[:, 2], np.abs(c[:, 0])
    top = 0.992 - 0.012 * np.clip((c[:, 1] - 0.0) / 0.08, 0, 1)        # waistband dips slightly at the back
    leg = 0.775 + 0.030 * np.clip((x - 0.04) / 0.10, 0, 1)                 # leg opening rises to the outer thigh
    inside = (z < top) & (z > leg) & (x < 0.22)
    idx = np.zeros(n, dtype=np.int32); idx[inside] = 1
    me.polygons.foreach_set('material_index', idx); me.update()


# ------------------------------------------------------------------------------------------- main
def main():
    sc = reset()
    log(f'build field  (quick={QUICK}, h={H*1000:.1f} mm)')
    field, J = build(cp=CP)
    v, q = mesh_sparse(field, *BOXES[REGION], H, log=log)

    c_root = coll('RF01_Character')
    c_body = coll('BODY', c_root); coll('CLOTHING', c_root); coll('ACCESSORIES', c_root); coll('RIG', c_root)
    root = bpy.data.objects.new('RF01_Character_ROOT', None); c_root.objects.link(root)
    root.empty_display_type = 'PLAIN_AXES'; root.empty_display_size = 0.3

    clay, garment, eyem = mat_clay(), mat_base_garment(), mat_eye()

    # Sculpt-stage mesh: surface nets, relaxed along the surface and projected back onto the anatomy field.
    # Production retopology (designed edge loops for deformation) is done before rigging (checkpoint 6).
    body = mesh_obj('RF01_Body', v, q, c_body, root)
    fix_normals(body)
    set_verts(body.data, relax(body.data, verts_np(body.data), field, iters=2 if QUICK else 3, lam=0.45))
    body['rf_stage'] = 'sculpt (pre-retopology)'
    body.data.materials.append(clay); body.data.materials.append(garment)
    assign_garment(body, J)
    body['rf_stature_m'] = 1.80
    make_eyes(c_body, root, eyem)

    # store the A-pose skeleton for the rig checkpoint
    for k, p in J.items():
        if not k.startswith('_'):
            root[f'joint_{k}'] = [float(x) for x in p]

    vz = verts_np(body.data)
    log(f'body: {len(body.data.vertices)} verts, {len(body.data.polygons)} faces (base); '
        f'height {vz[:, 2].max():.4f} m; width {np.ptp(vz[:, 0]):.3f} m')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    log('saved', OUT)


main()
