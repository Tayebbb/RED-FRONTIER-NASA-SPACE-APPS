"""
export_gltf.py - export one room of the facility to GLB for Godot, plus a light/rover manifest.

Selection = everything whose world bounds centre lies in the room footprint (walls included),
minus the linked rover (separate asset), scale figures, debug labels and other rooms' triggers.
Area lights cannot travel through glTF, so they are written to <room>_lights.json in Godot
coordinates (x, z, -y) for the Godot scene to rebuild. Modifiers (bevel, weighted normals)
are applied on export; linked duplicates export as shared meshes.

Run:  blender -b blender/RF_Facility.blend --python scripts/export_gltf.py -- Hangar
"""
import bpy, sys, os, json, math
from mathutils import Vector
room = (sys.argv[sys.argv.index('--') + 1:] or ['Hangar'])[0]
sys.path.insert(0, os.path.dirname(__file__))
import build_blockout as bb
x0, x1, y0, y1, h = {'Hangar': bb.HANG, 'MissionControl': bb.MC}[room]
OUT = os.path.join(r"D:\RedFrontier\export\godot"); os.makedirs(OUT, exist_ok=True)

def centre(o):
    if o.type == 'EMPTY' or o.type == 'CAMERA' or o.type == 'LIGHT': return o.matrix_world.translation
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return sum(cs, Vector()) / 8

def inside(p, pad=0.3):
    return x0 - pad <= p.x <= x1 + pad and y0 - pad <= p.y <= y1 + pad

bpy.ops.object.select_all(action='DESELECT')
picked, lights = [], []
for o in bpy.data.objects:
    if o.library or o.name.startswith(('REF_', 'DBG_')): continue
    if o.name.startswith('TRIG_Room_') and o.name != f'TRIG_Room_{room}': continue
    if o.type == 'FONT': continue
    if not inside(centre(o)): continue
    if o.type == 'LIGHT':
        lights.append(o); continue
    if o.type == 'CAMERA' and not o.name.startswith(f'CAM_{room}'): continue
    o.hide_set(False); o.select_set(True); picked.append(o)

path = os.path.join(OUT, f'RF_{room}.glb')
bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                          export_cameras=True, export_lights=False, export_extras=True, export_yup=True,
                          export_texcoords=True, export_normals=True, export_tangents=True, export_materials='EXPORT')

def gd(v): return [round(v.x, 4), round(v.z, 4), round(-v.y, 4)]            # Blender Z-up -> Godot Y-up
manifest = {'room': room, 'lights': [], 'rover': None}
for l in lights:
    fwd = l.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    manifest['lights'].append({'name': l.name, 'type': l.data.type, 'pos': gd(l.matrix_world.translation), 'dir': gd(fwd),
                               'watts': l.data.energy, 'color': list(l.data.color),
                               'size': [l.data.size, getattr(l.data, 'size_y', l.data.size)]})
rv = bpy.data.objects.get('REF_RF01_Rover')
if rv and inside(rv.location):
    manifest['rover'] = {'pos': gd(rv.location), 'rot_y_deg': math.degrees(rv.rotation_euler.z), 'asset': 'RF01_Rover.glb'}   # unquantized: Godot lacks KHR_mesh_quantization
json.dump(manifest, open(os.path.join(OUT, f'RF_{room}_lights.json'), 'w'), indent=1)
tris = sum(sum(len(p.vertices) - 2 for p in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh().polygons) for o in picked if o.type == 'MESH')
print(f'EXPORT_OK {path} objects={len(picked)} lights={len(lights)} tris={tris} size_mb={os.path.getsize(path) / 1e6:.1f}')
