"""
game_3_rig.py - game production stage 3: humanoid armature, skin weights, Idle / Walk / Run.

Run:  blender -b art/character/source/RF01_Engineer_GAME.blend --python art/character/scripts/game_3_rig.py

Bones use Godot's SkeletonProfileHumanoid names (Root, Hips, Spine, Chest, UpperChest, Neck, Head, Left/Right
Shoulder, UpperArm, LowerArm, Hand, finger chains, UpperLeg, LowerLeg, Foot, Toes), built from the approved
A-pose skeleton. Weights: bone heat on a full-body proxy, transferred to the game meshes; rigid parts (hair, eyes,
badge, marks, patch, wrist unit) are bound to one bone. Animations are in place (no root motion) and keyed
procedurally; their authored speeds are stored on the armature for the Godot visual script.
"""
import bpy, sys, os, math, time
import numpy as np
from mathutils import Matrix, Vector, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import importlib, rf01_body, rf01_head_v4
importlib.reload(rf01_body); importlib.reload(rf01_head_v4)
from rf01_body import skeleton
from rf01_head_v4 import hand_joints

FPS = 24
T0 = time.time()
def log(*a):
    print(f'[{time.time() - T0:7.1f}s]', *a, flush=True)


def V(p):
    return Vector((float(p[0]), float(p[1]), float(p[2])))


# ------------------------------------------------------------------------------------------- armature
def bone_specs():
    """(name, head, tail, parent, roll_ref) in the A-pose. roll_ref: the bone Z axis is aligned to this vector."""
    J = skeleton()
    hj = hand_joints(J)
    S = []
    back, fwd, up = (0, 1, 0), (0, -1, 0), (0, 0, 1)
    S.append(('Root', (0, 0, 0), (0, 0.0, 0.12), None, fwd))
    S.append(('Hips', J['pelvis'], J['spine_01'], 'Root', fwd))
    S.append(('Spine', J['spine_01'], J['spine_02'], 'Hips', fwd))
    S.append(('Chest', J['spine_02'], J['spine_03'], 'Spine', fwd))
    S.append(('UpperChest', J['spine_03'], J['neck'], 'Chest', fwd))
    S.append(('Neck', J['neck'], J['head'], 'UpperChest', fwd))
    S.append(('Head', J['head'], J['head_top'], 'Neck', fwd))
    ankle = np.array(J['ankle.L']); fdir = np.array([np.sin(np.radians(7)), -np.cos(np.radians(7)), 0])
    ball = ankle * np.array([1, 1, 0]) + 0.130 * fdir + np.array([0, 0, 0.018])
    toe = ankle * np.array([1, 1, 0]) + 0.205 * fdir + np.array([0, 0, 0.012])
    for side, s in (('Left', 1), ('Right', -1)):
        m = lambda p: np.array(p, float) * np.array([s, 1, 1])
        S.append((f'{side}Shoulder', m((0.030, 0.008, 1.452)), m(J['shoulder.L']), 'UpperChest', fwd))
        S.append((f'{side}UpperArm', m(J['shoulder.L']), m(J['elbow.L']), f'{side}Shoulder', fwd))
        S.append((f'{side}LowerArm', m(J['elbow.L']), m(J['wrist.L']), f'{side}UpperArm', fwd))
        S.append((f'{side}Hand', m(J['wrist.L']), m(hj['Middle'][0]), f'{side}LowerArm', tuple(-np.array(m(hj['palm_normal'])))))
        for f, parts in (('Thumb', ('Metacarpal', 'Proximal', 'Distal')), ('Index', ('Proximal', 'Intermediate', 'Distal')),
                         ('Middle', ('Proximal', 'Intermediate', 'Distal')), ('Ring', ('Proximal', 'Intermediate', 'Distal')),
                         ('Little', ('Proximal', 'Intermediate', 'Distal'))):
            pts = hj[f]; parent = f'{side}Hand'
            for i, part in enumerate(parts):
                nm = f'{side}{f}{part}'
                S.append((nm, m(pts[i]), m(pts[i + 1]), parent, tuple(-np.array(m(hj['palm_normal'])))))
                parent = nm
        S.append((f'{side}UpperLeg', m(J['hip.L']), m(J['knee.L']), 'Hips', back))
        S.append((f'{side}LowerLeg', m(J['knee.L']), m(J['ankle.L']), f'{side}UpperLeg', back))
        S.append((f'{side}Foot', m(J['ankle.L']), m(ball), f'{side}LowerLeg', up))
        S.append((f'{side}Toes', m(ball), m(toe), f'{side}Foot', up))
    return S


def build_armature(coll):
    arm_data = bpy.data.armatures.new('RF01_Armature')
    arm = bpy.data.objects.new('RF01_Armature', arm_data); coll.objects.link(arm)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = arm; arm.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones
    for name, h, t, parent, ref in bone_specs():
        b = eb.new(name); b.head = V(h); b.tail = V(t)
        b.align_roll(V(ref))
        if parent:
            b.parent = eb[parent]
            b.use_connect = False
        b.use_deform = name != 'Root'
    bpy.ops.object.mode_set(mode='OBJECT')
    arm.show_in_front = True
    return arm


# ------------------------------------------------------------------------------------------- weights
def ctx(ob, sel=None):
    sel = sel or [ob]
    return dict(active_object=ob, object=ob, selected_objects=sel, selected_editable_objects=sel)


SPINE = ['Hips', 'Spine', 'Chest', 'UpperChest', 'Neck', 'Head']
FINGERS = [f + p for f, ps in (('Thumb', ('Metacarpal', 'Proximal', 'Distal')),) for p in ps] +     [f + p for f in ('Index', 'Middle', 'Ring', 'Little') for p in ('Proximal', 'Intermediate', 'Distal')]


def allowed_bones(kind):
    arm_ = ['Shoulder', 'UpperArm', 'LowerArm']
    hand_ = ['Hand'] + FINGERS
    leg_ = ['UpperLeg', 'LowerLeg', 'Foot', 'Toes']
    side = lambda parts: [s + p for s in ('Left', 'Right') for p in parts]
    return {'skin': ['UpperChest', 'Neck', 'Head'] + side(['LowerArm'] + hand_),
            'jacket': SPINE[:5] + side(arm_ + ['Hand']),
            'trousers': ['Hips', 'Spine'] + side(['UpperLeg', 'LowerLeg', 'Foot']),
            'shoes': side(['LowerLeg', 'Foot', 'Toes'])}[kind]


def seg_dist(v, a, b):
    ab = b - a
    t = np.clip(((v - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(v - (a + t[:, None] * ab), axis=1)


def solve_weights(ob, arm, kind, power=5.0, keep=4):
    """Inverse-distance-to-bone weights with anatomical gating. Deterministic and robust on decimated meshes."""
    me = ob.data
    v = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', v); v = v.reshape(-1, 3)
    v = v @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)
    J = skeleton()
    names = allowed_bones(kind)
    W = np.zeros((len(v), len(names)))
    for k, n in enumerate(names):
        b = arm.data.bones[n]
        a, t = np.array(b.head_local), np.array(b.tail_local)
        d = seg_dist(v, a, t)
        ok = np.ones(len(v), bool)
        if n.startswith('Left'):
            ok &= v[:, 0] > -0.005
        if n.startswith('Right'):
            ok &= v[:, 0] < 0.005
        s = 1.0 if n.startswith('Left') else -1.0
        mv = np.array([s, 1, 1])
        if any(p in n for p in ('UpperArm', 'LowerArm')):
            S, du = np.array(J['shoulder.L']) * mv, np.array(J['_du']) * mv
            ok &= (v - S) @ du > -0.025
        if 'LowerArm' in n or n.endswith('Hand') or any(f in n for f in FINGERS):
            E, df = np.array(J['elbow.L']) * mv, np.array(J['_df']) * mv
            ok &= (v - E) @ df > -0.03
        if n.endswith('Hand') or any(f in n for f in FINGERS):
            Wr, df = np.array(J['wrist.L']) * mv, np.array(J['_df']) * mv
            ok &= (v - Wr) @ df > (-0.012 if any(f in n for f in FINGERS) else -0.03)
        if any(p in n for p in ('UpperArm', 'LowerArm')) or n.endswith('Hand'):
            ok &= d < 0.10                       # sleeves only: the jacket hem must not follow the arm swing
        if any(f in n for f in FINGERS):
            ok &= d < 0.04
        if any(p in n for p in ('UpperLeg', 'LowerLeg', 'Foot', 'Toes')):
            ok &= v[:, 2] < 1.0
        if n in ('Neck', 'Head'):
            ok &= v[:, 2] > 1.40
        W[:, k] = np.where(ok, 1.0 / (d + 0.004) ** power, 0.0)
    # keep the strongest influences, normalise
    order = np.argsort(-W, axis=1)[:, :keep]
    top = np.take_along_axis(W, order, 1)
    top = top / np.maximum(top.sum(1, keepdims=True), 1e-12)
    for g in list(ob.vertex_groups):
        ob.vertex_groups.remove(g)
    groups = {n: ob.vertex_groups.new(name=n) for n in names}
    for k in range(keep):
        for n_idx, n in enumerate(names):
            sel = np.flatnonzero((order[:, k] == n_idx) & (top[:, k] > 0.01))
            if len(sel):
                for vi, w in zip(sel.tolist(), top[sel, k].tolist()):
                    groups[n].add([vi], w, 'REPLACE')
    bind(ob, arm)
    log(f'weights -> {ob.name} ({kind}): {len(v)} verts, {sum(1 for g in groups.values())} bones')


def rigid(ob, arm, bone):
    for g in list(ob.vertex_groups):
        ob.vertex_groups.remove(g)
    g = ob.vertex_groups.new(name=bone)
    g.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
    bind(ob, arm)


def bind(ob, arm):
    mw = ob.matrix_world.copy()
    ob.parent = arm; ob.matrix_world = mw
    m = ob.modifiers.get('Armature') or ob.modifiers.new('Armature', 'ARMATURE')
    m.object = arm


# ------------------------------------------------------------------------------------------- posing
def Q(axis, deg):
    return Quaternion(Vector(axis), math.radians(deg))


QI = Quaternion()
X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)


def pose_frame(arm, rots, hips_offset, frame):
    """rots: bone -> world rotation applied to the bone's rest orientation (absolute, chains composed by caller).
    Bones without an entry inherit their parent's rotation. Writes basis rotations and keys them."""
    pm = {}
    qw = {}
    for pb in arm.pose.bones:                                   # parents come first (creation order)
        b = pb.bone
        rest = b.matrix_local
        q = rots.get(b.name, qw.get(b.parent.name) if b.parent else QI)
        qw[b.name] = q
        desired = q.to_matrix() @ rest.to_3x3()
        if b.parent:
            nob = pm[b.parent.name] @ (b.parent.matrix_local.inverted() @ rest)
        else:
            nob = rest.copy()
        basis_rot = nob.to_3x3().inverted() @ desired
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = basis_rot.to_quaternion()
        loc = Vector((0, 0, 0))
        if b.name == 'Hips':
            loc = nob.to_3x3().inverted() @ Vector(hips_offset)
        pb.location = loc
        basis = Matrix.Translation(loc) @ basis_rot.to_4x4()
        pm[b.name] = nob @ basis
        pb.keyframe_insert('rotation_quaternion', frame=frame)
        if b.name == 'Hips':
            pb.keyframe_insert('location', frame=frame)


L1, L2, ANKLE_H, HIP_DROP = 0.420, 0.421, 0.084, 0.035


def pelvis_for(t, k):
    """pelvis height at which a leg with thigh flexion t and knee flexion k (deg) puts its ankle at rest height."""
    return ANKLE_H + L1 * math.cos(math.radians(t)) + L2 * math.cos(math.radians(t - k)) + HIP_DROP


def bump(p, c, w):
    d = ((p - c + 0.5) % 1.0) - 0.5
    return math.exp(-(d / w) ** 2)


def body_pose(p, gait):
    """Return (rots, hips_offset) for phase p in [0,1) of 'idle' | 'walk' | 'run'."""
    r = {}
    tw = 2 * math.pi * p
    if gait == 'idle':
        breathe = math.sin(tw)
        sway = math.sin(tw * 0.5 + 0.3)
        hips = Q(Y, 1.2 * sway)
        r['Hips'] = hips
        r['Spine'] = hips @ Q(X, 1.0 + 0.4 * breathe)
        r['Chest'] = r['Spine'] @ Q(X, 0.6 * breathe)
        r['UpperChest'] = r['Chest'] @ Q(X, 0.5 * breathe)
        r['Neck'] = r['UpperChest'] @ Q(X, -1.5)
        r['Head'] = r['Neck'] @ Q(Z, 2.0 * math.sin(tw * 0.5)) @ Q(X, -1.0)
        legs = {'Left': (2.0 - 1.2 * sway, 4.0), 'Right': (2.0 + 1.2 * sway, 4.0)}
        arms = {'Left': (3.0, 14.0), 'Right': (3.0, 14.0)}
        lean = 0.0
        pz = max(pelvis_for(*legs['Left']), pelvis_for(*legs['Right'])) - 0.004
        for side, s in (('Left', 1), ('Right', -1)):
            t, k = legs[side]
            r[f'{side}UpperLeg'] = hips @ Q(Y, -s * 1.5) @ Q(X, -t)
            r[f'{side}LowerLeg'] = r[f'{side}UpperLeg'] @ Q(X, k)
            r[f'{side}Foot'] = hips                                   # flat on the floor
        offset = (0.012 * sway, 0.0, pz - 0.960)
        arm_pose(r, arms, swing=None, curl=8.0)
        return r, offset
    run = gait == 'run'
    A = dict(thigh=(30.0, 10.0) if run else (19.0, 5.0), knee_sw=95.0 if run else 54.0, knee_st=28.0 if run else 12.0,
             arm=34.0 if run else 22.0, elbow=88.0 if run else 18.0, yaw=8.0 if run else 6.0, lean=9.0 if run else 2.5,
             roll=3.0 if run else 2.5)
    legs = {}
    for side, ph in (('Left', p), ('Right', (p + 0.5) % 1.0)):
        t = A['thigh'][0] * math.cos(2 * math.pi * (ph + 0.10)) + A['thigh'][1]      # hip flexion peaks in late swing
        k = 5.0 + A['knee_st'] * bump(ph, 0.14, 0.08) + A['knee_sw'] * bump(ph, 0.70 if not run else 0.66, 0.12)
        ankle = 6.0 * bump(ph, 0.0, 0.05) - (22.0 if run else 14.0) * bump(ph, 0.55, 0.07) + 4.0 * bump(ph, 0.8, 0.1)
        legs[side] = (t, k, ankle, ph)
    yaw = -A['yaw'] * math.cos(tw)
    hips = Q(Z, yaw) @ Q(Y, A['roll'] * math.sin(tw * 2 + 0.6)) @ Q(X, A['lean'] * 0.4)
    r['Hips'] = hips
    r['Spine'] = hips @ Q(Z, -yaw * 0.5) @ Q(X, A['lean'] * 0.4)
    r['Chest'] = r['Spine'] @ Q(Z, -yaw * 0.6)
    r['UpperChest'] = r['Chest'] @ Q(Z, -yaw * 0.6) @ Q(X, A['lean'] * 0.2)
    r['Neck'] = r['UpperChest'] @ Q(Z, yaw * 0.4) @ Q(X, -A['lean'] * 0.5)
    r['Head'] = r['Neck'] @ Q(Z, yaw * 0.3) @ Q(X, -A['lean'] * 0.4)
    pz = max(pelvis_for(t, k) for t, k, a, ph in legs.values())
    if run:
        flight = max(bump(p, 0.40, 0.07), bump(p, 0.90, 0.07))
        pz = pz + 0.035 * flight - 0.035
    else:
        pz -= 0.012
    for side, s in (('Left', 1), ('Right', -1)):
        t, k, ankle, ph = legs[side]
        r[f'{side}UpperLeg'] = hips @ Q(X, -t)
        r[f'{side}LowerLeg'] = r[f'{side}UpperLeg'] @ Q(X, k)
        r[f'{side}Foot'] = Q(Z, yaw) @ Q(X, -ankle)                  # world pitch: + toes up (heel strike), - push-off
        r[f'{side}Toes'] = Q(Z, yaw) @ Q(X, -min(ankle, 0.0) * 0.8)   # toes stay near the floor while the heel lifts
    # arms swing opposite to the legs
    arms = {'Left': (-A['arm'] * math.cos(tw) + 4.0, A['elbow'] + (8 if run else 6) * math.sin(tw)),
            'Right': (A['arm'] * math.cos(tw) + 4.0, A['elbow'] - (8 if run else 6) * math.sin(tw))}
    arm_pose(r, arms, swing=True, run=run, curl=38.0 if run else 12.0)
    return r, (0.0, -0.02 if run else -0.005, pz - 0.960)


LOWER = 33.0          # A-pose (45 deg) -> arms hanging at the sides, clear of the jacket's side panels


HJ = None


def arm_pose(r, arms, swing=None, run=False, curl=10.0):
    global HJ
    if HJ is None:
        HJ = hand_joints(skeleton())
    for side, s in (('Left', 1), ('Right', -1)):
        sw, flex = arms[side]
        base = r['UpperChest']
        lower = Q(Y, s * (LOWER - (6.0 if run else 0.0)))
        r[f'{side}UpperArm'] = base @ Q(X, -sw) @ lower
        r[f'{side}LowerArm'] = base @ Q(X, -sw - flex) @ lower
        r[f'{side}Hand'] = r[f'{side}LowerArm'] @ Q(Y, -s * 4.0)
        # finger curl about each finger's rest flexion axis (mirrored as an axial vector for the right hand)
        for f, parts, scale in (('Index', ('Proximal', 'Intermediate', 'Distal'), 1.0),
                                ('Middle', ('Proximal', 'Intermediate', 'Distal'), 1.05),
                                ('Ring', ('Proximal', 'Intermediate', 'Distal'), 1.1),
                                ('Little', ('Proximal', 'Intermediate', 'Distal'), 1.15),
                                ('Thumb', ('Metacarpal', 'Proximal', 'Distal'), 0.35)):
            a = np.array(HJ[f + '_axis']); a = a if s > 0 else np.array([a[0], -a[1], -a[2]])
            parent = r[f'{side}Hand']
            for i, part in enumerate(parts):
                c = curl * scale * (1.0, 1.25, 0.8)[i]
                parent = parent @ Q(tuple(a), -c)
                r[f'{side}{f}{part}'] = parent


def make_action(arm, name, gait, frames, speed):
    act = bpy.data.actions.new(name)
    arm.animation_data_create(); arm.animation_data.action = act
    for f in range(frames + 1):
        p = (f % frames) / frames
        rots, off = body_pose(p, gait)
        pose_frame(arm, rots, off, f)
    act.use_frame_range = True; act.frame_start = 0; act.frame_end = frames
    act['rf_speed_mps'] = speed
    act['rf_loop'] = True
    track = arm.animation_data.nla_tracks.new(); track.name = name
    strip = track.strips.new(name, 0, act); strip.name = name
    track.mute = True
    arm.animation_data.action = None
    log(f'action {name}: {frames} frames, authored speed {speed:.2f} m/s')
    return act


# ------------------------------------------------------------------------------------------- main
def cleanup():
    """Idempotent: remove a previous rig, its actions and bindings so the stage can be re-run."""
    for o in bpy.data.collections['GAME'].objects:
        if o.type == 'MESH':
            mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
            for m in list(o.modifiers):
                if m.type == 'ARMATURE':
                    o.modifiers.remove(m)
            for g in list(o.vertex_groups):
                o.vertex_groups.remove(g)
    if 'RF01_Armature' in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects['RF01_Armature'])
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    for a in list(bpy.data.armatures):
        if a.users == 0:
            bpy.data.armatures.remove(a)


def main():
    cleanup()
    game = bpy.data.collections['GAME']
    arm = build_armature(game)
    for name, kind in (('GAME_Skin', 'skin'), ('GAME_Jacket', 'jacket'), ('GAME_Trousers', 'trousers'),
                       ('GAME_Shoes', 'shoes')):
        solve_weights(bpy.data.objects[name], arm, kind)
    for name, bone in (('GAME_Hair', 'Head'), ('GAME_Eyes', 'Head'), ('GAME_Badge', 'UpperChest'),
                       ('GAME_ChestMark', 'UpperChest'), ('GAME_BackMark', 'UpperChest'), ('GAME_Patch', 'LeftUpperArm'),
                       ('GAME_Wrist', 'LeftLowerArm')):
        rigid(bpy.data.objects[name], arm, bone)
    # walk: 0.75 s cycle, two 0.85 m steps -> 2.27 m/s; run: 0.667 s, two 1.6 m steps -> 4.8 m/s
    make_action(arm, 'Idle', 'idle', 72, 0.0)
    make_action(arm, 'Walk', 'walk', 18, 1.70 / 0.75)
    make_action(arm, 'Run', 'run', 16, 3.20 / (16 / FPS))
    arm['rf_walk_speed'] = 1.70 / 0.75; arm['rf_run_speed'] = 3.20 / (16 / FPS)
    bpy.context.scene.render.fps = FPS
    bpy.ops.wm.save_mainfile()
    log('saved')


main()
