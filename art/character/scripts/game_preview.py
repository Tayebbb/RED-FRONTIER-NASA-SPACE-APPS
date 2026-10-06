"""
game_preview.py - fast Eevee previews of the game character (rig + animations), for review without Cycles.

Run:  blender -b art/character/source/RF01_Engineer_GAME.blend --python art/character/scripts/game_preview.py --
      <out_dir> [--shots idle_front,walk_side,...] [--size 720]
Each shot: <action>_<view>[_<frame>]. Views: front, back, side, q34 (3/4 front), b34 (3/4 back), game (gameplay camera).
"""
import bpy, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
OUT = os.path.abspath(argv[0]); os.makedirs(OUT, exist_ok=True)
SIZE = int(argv[argv.index('--size') + 1]) if '--size' in argv else 720
SHOTS = argv[argv.index('--shots') + 1].split(',') if '--shots' in argv else \
    ['Idle_front_0', 'Idle_back_0', 'Idle_q34_0', 'Walk_side_0', 'Walk_side_4', 'Walk_side_9', 'Run_side_0', 'Run_side_4',
     'Walk_game_4', 'Run_q34_6']
sc = bpy.context.scene
for c in ('RF01_Character', 'BAKE_HIGH'):
    if c in bpy.data.collections:
        bpy.data.collections[c].hide_render = True
if 'GAME_Proxy' in bpy.data.objects:
    bpy.data.objects['GAME_Proxy'].hide_render = True
arm = bpy.data.objects['RF01_Armature']
arm.hide_render = True
try:
    sc.render.engine = 'BLENDER_EEVEE'
except Exception:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x = SIZE; sc.render.resolution_y = SIZE
sc.view_settings.view_transform = 'AgX'
w = bpy.data.worlds.new('PV'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.32, 0.33, 0.35, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
for nm, loc, e in (('Key', (-2.5, -3.0, 3.2), 600), ('Fill', (3.0, -2.0, 1.6), 220), ('Rim', (0.5, 3.5, 3.0), 380)):
    l = bpy.data.lights.new(nm, 'AREA'); l.size = 2.5; l.energy = e
    o = bpy.data.objects.new(nm, l); sc.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector((0, 0, 1.0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
floor = bpy.data.meshes.new('PVFloor'); floor.from_pydata([(-6, -6, 0), (6, -6, 0), (6, 6, 0), (-6, 6, 0)], [], [(0, 1, 2, 3)])
fo = bpy.data.objects.new('PVFloor', floor); sc.collection.objects.link(fo)
fm = bpy.data.materials.new('PVFloor'); fm.use_nodes = True
fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.25, 0.25, 0.26, 1); floor.materials.append(fm)
cam = bpy.data.cameras.new('PVCam'); co = bpy.data.objects.new('PVCam', cam); sc.collection.objects.link(co); sc.camera = co
VIEWS = {'front': ((0, -4.6, 1.0), (0, 0, 0.93), 2.15), 'back': ((0, 4.6, 1.0), (0, 0, 0.93), 2.15),
         'side': ((4.6, 0, 1.0), (0, 0, 0.93), 2.15), 'q34': ((2.9, -3.6, 1.15), (0, 0, 0.93), 2.15),
         'b34': ((-2.9, 3.6, 1.2), (0, 0, 0.93), 2.15),
         # gameplay: CAMERA_DISTANCE 3.2 m behind a 1.55 m pivot, 12 deg down, 0.35 m shoulder offset, fov 65
         'game': ((0.35, 3.2 * math.cos(math.radians(12)), 1.55 + 3.2 * math.sin(math.radians(12))), (0.35, 0, 1.55), None),
         'head': ((0.35, -1.0, 1.66), (0.0, 0, 1.62), 0.55),
         'hf': ((0.0, -1.3, 1.70), (0.0, 0, 1.67), 0.42), 'hq': ((0.85, -1.0, 1.74), (0.0, 0, 1.67), 0.42),
         'hs': ((1.3, 0.0, 1.70), (0.0, 0, 1.67), 0.42), 'hb': ((-0.45, 1.25, 1.78), (0.0, 0, 1.67), 0.42),
         'hc': ((0.25, -0.45, 1.80), (0.02, -0.06, 1.76), 0.12)}
for shot in SHOTS:
    parts = shot.split('_'); act, view = parts[0], parts[1]; frame = int(parts[2]) if len(parts) > 2 else 0
    arm.animation_data.action = bpy.data.actions[act]
    sc.frame_set(frame)
    loc, tgt, span = VIEWS[view]
    co.location = loc; co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if span is None:
        cam.sensor_fit = 'VERTICAL'; cam.angle_y = math.radians(65)
    else:
        cam.sensor_fit = 'VERTICAL'; cam.sensor_height = 24; cam.lens = 24 / (span / (Vector(tgt) - Vector(loc)).length)
    sc.render.filepath = os.path.join(OUT, shot + '.png')
    bpy.ops.render.render(write_still=True)
    print('SHOT', shot, flush=True)
