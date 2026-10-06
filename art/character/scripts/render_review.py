"""
render_review.py - neutral character review renders (turntable, proportion sheet, head views).

Run:
  blender -b art/character/source/RF01_Engineer_MASTER.blend --python art/character/scripts/render_review.py --
      <out_dir> [--quick] [--size 1500] [--samples 96] [--views FRONT,BACK,...] [--sheet] [--head]

The review studio (REVIEW_Studio collection) is built in memory and is NOT saved into the character file.
Turntable: the camera and lights stay fixed; the character root turns. A 1.80 m ruler stands beside him.
--quick uses Workbench (fast form check); default is Cycles with AgX, like the facility renders.
"""
import bpy, sys, os, math, time
from mathutils import Vector, Euler

argv = sys.argv[sys.argv.index('--') + 1:]
OUT = os.path.abspath(argv[0])
QUICK = '--quick' in argv
SIZE = int(argv[argv.index('--size') + 1]) if '--size' in argv else 1500
SAMPLES = int(argv[argv.index('--samples') + 1]) if '--samples' in argv else 96
VIEWS = argv[argv.index('--views') + 1].split(',') if '--views' in argv else \
    ['FRONT', 'BACK', 'LEFT', 'RIGHT', 'FRONT_34', 'BACK_34']
os.makedirs(OUT, exist_ok=True)

TURN = {'FRONT': 0, 'BACK': 180, 'LEFT': -90, 'RIGHT': 90, 'FRONT_34': -40, 'BACK_34': 140,
        'FRONT_34R': 40}
sc = bpy.context.scene
root = bpy.data.objects['RF01_Character_ROOT']
stature = 1.80
studio = bpy.data.collections.new('REVIEW_Studio'); sc.collection.children.link(studio)


def link(ob):
    studio.objects.link(ob); return ob


def mat(name, col, rough=0.6, emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = 1.0
    m.diffuse_color = (*col, 1)
    return m


# ------------------------------------------------------------------------------------------- studio
def cyclorama():
    import bmesh
    bm = bmesh.new()
    W, D, Hh, R = 12.0, 7.0, 6.0, 1.6         # width, floor depth (toward back), wall height, cove radius
    prof = [(y, 0.0) for y in [-6, -4, -2, -1, 0, 1, 2, 3, 3.5, D - R]]
    for i in range(1, 13):
        a = i / 12 * math.pi / 2
        prof.append((D - R + R * math.sin(a), R - R * math.cos(a)))
    prof.append((D, Hh))
    rows = []
    for x in (-W / 2, W / 2):
        rows.append([bm.verts.new((x, y, z)) for y, z in prof])
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    me = bpy.data.meshes.new('REV_Cyc'); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = link(bpy.data.objects.new('REV_Cyclorama', me))
    me.materials.append(mat('MAT_Rev_Backdrop', (0.20, 0.20, 0.205), 0.85))
    return ob


def ruler():
    """1.80 m height ruler 0.95 m to screen-right of the character, ticks every 0.1 m."""
    import bmesh
    m_r = mat('MAT_Rev_Ruler', (0.04, 0.04, 0.045), 0.5)
    m_o = mat('MAT_Rev_RulerMark', (0.60, 0.20, 0.06), 0.5)
    x0, y0 = 0.95, 0.0
    bm = bmesh.new()
    def box(cx, cz, sx, sz, sy=0.012):
        r = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=r['verts'])
        bmesh.ops.translate(bm, vec=(cx, y0, cz), verts=r['verts'])
    box(x0, stature / 2, 0.012, stature)
    for i in range(19):
        z = i * 0.1
        L = 0.09 if i % 5 == 0 else 0.045
        box(x0 - L / 2, z, L, 0.004)
    me = bpy.data.meshes.new('REV_Ruler'); bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new('REV_Ruler', me)); me.materials.append(m_r)
    # top mark at stature
    bm = bmesh.new(); r = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(0.16, 0.014, 0.005), verts=r['verts'])
    bmesh.ops.translate(bm, vec=(x0 - 0.06, y0, stature), verts=r['verts'])
    me = bpy.data.meshes.new('REV_RulerTop'); bm.to_mesh(me); bm.free()
    link(bpy.data.objects.new('REV_RulerTop', me)).data.materials.append(m_o)
    for z, txt in [(0.5, '0.5'), (1.0, '1.0'), (1.5, '1.5'), (stature, '1.80 m')]:
        cu = bpy.data.curves.new('REV_Lbl', 'FONT'); cu.body = txt; cu.size = 0.055
        cu.align_y = 'CENTER'
        t = link(bpy.data.objects.new('REV_Lbl_' + txt, cu))
        t.location = (x0 + 0.03, y0, z); t.rotation_euler = (math.radians(90), 0, 0)
        cu.materials.append(m_o if txt.endswith('m') else m_r)


def area(name, loc, target, size, power, color=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA'); l.shape = 'DISK'; l.size = size; l.energy = power; l.color = color
    o = link(bpy.data.objects.new(name, l)); o.location = loc
    d = Vector(target) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o


def lights():
    # soft key (camera-left, high), soft fill (camera-right, lower), two rims behind
    area('REV_Key', (-2.6, -3.2, 3.0), (0, 0, 1.1), 2.2, 330, (1.0, 0.97, 0.93))
    area('REV_Fill', (3.0, -2.6, 1.4), (0, 0, 1.0), 2.6, 95, (0.95, 0.97, 1.0))
    area('REV_Rim_L', (-2.0, 2.8, 2.6), (0, 0, 1.2), 1.4, 170)
    area('REV_Rim_R', (2.2, 2.6, 2.4), (0, 0, 1.2), 1.4, 130)
    w = bpy.data.worlds.new('REV_World'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.25, 0.25, 0.26, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35


def camera(name, loc, target, lens=85, ortho=None):
    c = bpy.data.cameras.new(name); c.lens = lens; c.sensor_fit = 'VERTICAL'; c.sensor_height = 24
    c.clip_start = 0.05; c.clip_end = 50
    if ortho:
        c.type = 'ORTHO'; c.ortho_scale = ortho
    o = link(bpy.data.objects.new(name, c)); o.location = loc
    d = Vector(target) - Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o


# ------------------------------------------------------------------------------------------- render settings
def setup_render():
    sc.render.resolution_x = SIZE; sc.render.resolution_y = SIZE; sc.render.resolution_percentage = 100
    sc.render.use_persistent_data = True          # turntable only moves the root: keep the BVH between frames
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = -0.6
    try:
        sc.view_settings.look = 'AgX - Base Contrast'
    except Exception:
        pass
    if '--wb' in argv:
        sc.render.engine = 'BLENDER_WORKBENCH'
        sh = sc.display.shading
        sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_cavity = True; sh.cavity_type = 'BOTH'
        sh.show_shadows = True; sh.shadow_intensity = 0.4
        sc.view_settings.view_transform = 'Standard'
    else:
        sc.render.engine = 'CYCLES'
        cy = sc.cycles; cy.device = 'CPU'; cy.samples = 20 if QUICK else SAMPLES
        cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.015
        cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
        cy.max_bounces = 8; cy.diffuse_bounces = 3; cy.glossy_bounces = 3
        sc.render.film_transparent = False


def shot(cam, name, turn):
    sc.camera = cam
    root.rotation_euler = Euler((0, 0, math.radians(turn)))
    sc.render.filepath = os.path.join(OUT, name + '.png')
    t = time.time(); bpy.ops.render.render(write_still=True)
    print(f'RENDERED {name} {time.time() - t:.0f}s', flush=True)


# ------------------------------------------------------------------------------------------- proportion sheet
def proportion_lines(head_h):
    """Head-unit lines from the crown down, for the orthographic proportion sheet."""
    import bmesh
    m = mat('MAT_Rev_Line', (0.0, 0.0, 0.0), 1.0, emit=(0.02, 0.35, 0.65))
    bm = bmesh.new()
    n = int(stature / head_h) + 1
    for i in range(n + 1):
        z = stature - i * head_h
        if z < -0.001:
            break
        r = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(2.2, 0.002, 0.0025), verts=r['verts'])
        bmesh.ops.translate(bm, vec=(0, -0.9, z), verts=r['verts'])
    me = bpy.data.meshes.new('REV_HeadLines'); bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new('REV_HeadLines', me)); me.materials.append(m)
    return ob


def measure():
    """Anthropometric read-out from the body mesh (A-pose, metres); written next to the renders."""
    import numpy as np, json
    me = bpy.data.objects['RF01_Body'].data
    v = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', v); v = v.reshape(-1, 3)
    x, y, z = v[:, 0], v[:, 1], v[:, 2]
    top = z.max()
    chin = z[(np.abs(x) < 0.012) & (y < -0.066) & (z > 1.52) & (z < 1.65)].min()
    head_h = top - chin
    def width(z0, z1, xmax=0.30):
        m = (z > z0) & (z < z1) & (np.abs(x) < xmax)
        return float(x[m].max() - x[m].min())
    def depth(z0, z1, xmax=0.15):
        m = (z > z0) & (z < z1) & (np.abs(x) < xmax)
        return float(y[m].max() - y[m].min())
    J = {k[6:]: root[k][:] for k in root.keys() if k.startswith('joint_')}
    crotch = z[(np.abs(x) < 0.006) & (np.abs(y) < 0.05) & (z < 1.0)].min()
    m = {
        'stature_m': round(float(top), 4),
        'head_height_m': round(float(head_h), 4),
        'heads_tall': round(float(top / head_h), 2),
        'head_breadth_m': round(width(1.72, 1.74, 0.10), 3),
        'eye_height_m': 1.683,
        'chin_height_m': round(float(chin), 3),
        'shoulder_breadth_at_acromion_level_m': round(width(1.45, 1.47, 0.30), 3),
        'chest_breadth_m': round(width(1.25, 1.30, 0.17), 3),
        'chest_depth_m': round(depth(1.29, 1.33, 0.12), 3),
        'waist_breadth_m': round(width(1.06, 1.09, 0.20), 3),
        'hip_breadth_m': round(width(0.86, 0.94, 0.22), 3),
        'crotch_height_m': round(float(crotch), 3),
        'hip_joint_height_m': J['hip.L'][2], 'knee_height_m': J['knee.L'][2], 'ankle_height_m': J['ankle.L'][2],
        'shoulder_joint_height_m': J['shoulder.L'][2],
        'upper_arm_len_m': round(float(np.linalg.norm(np.subtract(J['elbow.L'], J['shoulder.L']))), 3),
        'forearm_len_m': round(float(np.linalg.norm(np.subtract(J['wrist.L'], J['elbow.L']))), 3),
        'foot_length_m': round(float(y[(z < 0.03) & (x > 0)].max() - y[(z < 0.03) & (x > 0)].min()), 3),
        'body_vertices': len(me.vertices), 'body_quads': len(me.polygons),
        'eyes_vertices': len(bpy.data.objects['RF01_Eyes'].data.vertices),
    }
    root['rf_head_height'] = m['head_height_m']
    with open(os.path.join(OUT, 'measurements.json'), 'w') as fh:
        json.dump(m, fh, indent=1)
    print('MEASURE', json.dumps(m))
    return m


def main():
    try:
        measure()
    except Exception as e:                      # partial meshes (head/hand patches) have no full body
        print('measure skipped:', e)
    cyclorama(); ruler(); lights(); setup_render()
    sc.render.film_transparent = False
    target = (0, 0, 0.93)
    dist = 5.6
    cam = camera('REV_Cam', (0, -dist, 0.98), target, lens=85)
    # frame: 2.25 m vertical at the subject
    cam.data.lens = 24 / (2.25 / dist)
    for v in VIEWS:
        shot(cam, 'turntable_' + v, TURN[v])
    if '--sheet' in argv:
        hh = float(root.get('rf_head_height', 0.233))
        lines = proportion_lines(hh)
        oc = camera('REV_Ortho', (0, -6, 0.93), (0, 0, 0.93), ortho=2.15)
        for v in ('FRONT', 'LEFT'):
            shot(oc, 'proportions_' + v, TURN[v])
        lines.hide_render = True
    if '--head' in argv:
        hc = camera('REV_HeadCam', (0, -1.25, 1.68), (0, 0, 1.672), lens=85)
        hc.data.lens = 24 / (0.34 / 1.25)
        for v in ('FRONT', 'FRONT_34', 'LEFT', 'BACK_34'):
            shot(hc, 'head_' + v, TURN[v])
        hand = camera('REV_HandCam', (0.95, -1.2, 1.05), (0.60, -0.08, 0.98), lens=85)
        hand.data.lens = 24 / (0.36 / 1.25)
        shot(hand, 'hand_L', 0)
    if '--hands' in argv:
        W = Vector(root['joint_wrist.L']); tgt = W + Vector((0.05, -0.02, -0.05))
        for nm, off in (('hand_L_back', (0.35, 0.0, 0.30)), ('hand_L_palm', (-0.25, -0.30, -0.10))):
            hc2 = camera('REV_' + nm, tgt + Vector(off), tgt, lens=85)
            hc2.data.lens = 24 / (0.24 / Vector(off).length)
            shot(hc2, nm, 0)
    if '--eye' in argv:
        ec = camera('REV_EyeCam', (0.032, -0.6, 1.683), (0.032, 0, 1.683), lens=85)
        ec.data.lens = 24 / (0.06 / 0.6)
        shot(ec, 'eye_L_front', 0)
        ec2 = camera('REV_EyeCam2', (0.30, -0.5, 1.683), (0.032, -0.07, 1.683), lens=85)
        ec2.data.lens = 24 / (0.07 / 0.5)
        shot(ec2, 'eye_L_side', 0)
    if '--cp3' in argv:
        W = Vector(root['joint_wrist.L']); E = Vector(root['joint_elbow.L'])
        df = (W - E).normalized()
        shots = [('cp3_chest', (0.16, -0.95, 1.42), (0.0, -0.08, 1.35), 0.36),
                 ('cp3_patch', (0.80, -0.55, 1.62), (0.30, 0.0, 1.42), 0.20),
                 ('cp3_wrist', tuple(W - 0.11 * df + Vector((0.30, -0.42, 0.28))), tuple(W - 0.11 * df), 0.20),
                 ('cp3_back_yoke', (0.0, 1.05, 1.47), (0.0, 0.10, 1.40), 0.42),
                 ('cp3_shoes', (0.62, -0.75, 0.30), (0.05, -0.04, 0.06), 0.42)]
        for nm, loc, tgt, span in shots:
            cc = camera('REV_' + nm, loc, tgt, lens=85)
            cc.data.lens = 24 / (span / (Vector(loc) - Vector(tgt)).length)
            shot(cc, nm, 0)
    if '--lower' in argv:
        lc = camera('REV_LowerCam', (-1.35, -2.6, 0.62), (0, 0, 0.52), lens=85)
        lc.data.lens = 24 / (1.15 / 2.93)
        shot(lc, 'lower_FRONT_34', 0)
        shot(lc, 'lower_BACK_34', 180)
    if '--torso' in argv:
        tc = camera('REV_TorsoCam', (0, -2.2, 1.30), (0, 0, 1.25), lens=85)
        tc.data.lens = 24 / (0.75 / 2.2)
        for v in ('FRONT', 'FRONT_34', 'BACK', 'LEFT'):
            shot(tc, 'torso_' + v, TURN[v])
    root.rotation_euler = Euler((0, 0, 0))


main()
