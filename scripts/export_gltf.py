"""
export_gltf.py - export one room of the facility to GLB for Godot, plus a light/rover manifest.

Selection = objects tagged rf_room=<room> by their builder, plus untagged objects whose world bounds
centre lies in the room footprint (walls included; the Hangar keeps its 0.3 m pad, later rooms use the
exact footprint so a shared wall is never exported twice), minus objects owned by another room, the
linked rover (separate asset), scale figures, debug labels and other rooms' triggers.
Each light records its light set; materials with rf_emit_day / rf_emit_launch are listed so Godot can
switch LIGHTSET_Launch_Mode (screens up, fixtures down, beacons on).
Area lights cannot travel through glTF, so they are written to <room>_lights.json in Godot
coordinates (x, z, -y) for the Godot scene to rebuild. Modifiers (bevel, weighted normals)
are applied on export; linked duplicates export as shared meshes.

Images are NOT embedded: rooms carry geometry + material names only. Every material and texture lives once
in RF_MaterialLibrary.glb (export_material_library.py); Godot resolves room materials to that shared library
by name (scripts/godot_sync.py). The manifest also carries the room footprint for room streaming.

Run:  blender -b blender/RF_Facility.blend --python scripts/export_gltf.py -- Hangar
"""
import bpy, sys, os, json, math
from mathutils import Vector
room = (sys.argv[sys.argv.index('--') + 1:] or ['Hangar'])[0]
sys.path.insert(0, os.path.dirname(__file__))
import build_blockout as bb, rf_lightsets
x0, x1, y0, y1, h = {'Hangar': bb.HANG, 'MissionControl': bb.MC, 'MarsIntel': bb.INTEL, 'Briefing': bb.BRIEF, 'Corridor01': bb.C1, 'Corridor02': bb.C2}[room]
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "export", "godot"); os.makedirs(OUT, exist_ok=True)

def centre(o):
    if o.type == 'EMPTY' or o.type == 'CAMERA' or o.type == 'LIGHT': return o.matrix_world.translation
    cs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return sum(cs, Vector()) / 8

PAD = 0.3 if room == 'Hangar' else 0.0          # Hangar export stays exactly as approved

def inside(p, pad=PAD):
    return x0 - pad <= p.x <= x1 + pad and y0 - pad <= p.y <= y1 + pad

bpy.ops.object.select_all(action='DESELECT')
picked, lights = [], []
for o in bpy.data.objects:
    if o.library or o.name.startswith(('REF_', 'DBG_')): continue
    if o.name.startswith('TRIG_Room_') and o.name != f'TRIG_Room_{room}': continue
    if o.type == 'FONT': continue
    owner = o.get('rf_room')
    if owner is not None and owner != room: continue
    if owner is None and not inside(centre(o)): continue
    if o.type == 'LIGHT':
        lights.append(o); continue
    if o.type == 'CAMERA' and not o.name.startswith(f'CAM_{room}'): continue
    o.hide_set(False); o.select_set(True); picked.append(o)

path = os.path.join(OUT, f'RF_{room}.glb')
bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                          export_cameras=True, export_lights=False, export_extras=True, export_yup=True,
                          export_texcoords=True, export_normals=True, export_tangents=True, export_materials='EXPORT',
                          export_image_format='NONE')                    # textures come from the shared library

def gd(v): return [round(v.x, 4), round(v.z, 4), round(-v.y, 4)]            # Blender Z-up -> Godot Y-up
manifest = {'room': room, 'lights': [], 'rover': None,
            'footprint': {'x': [x0, x1], 'z': [-y1, -y0], 'h': h}}            # Godot coords (x, -y): room streaming
for l in lights:
    fwd = l.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    lset = 'Launch_Mode' if any(c.name == 'LIGHTSET_Launch_Mode' for c in l.users_collection) else 'Day_Operational'
    manifest['lights'].append({'name': l.name, 'type': l.data.type, 'pos': gd(l.matrix_world.translation), 'dir': gd(fwd),
                               'watts': l.data.energy, 'color': list(l.data.color), 'set': lset,
                               'switch': any(c.name == rf_lightsets.SWITCHED_DAY for c in l.users_collection),   # replaced in Launch Mode
                               'spread_deg': round(math.degrees(getattr(l.data, 'spread', math.pi)), 1),
                               'size': [getattr(l.data, 'size', 0.1), getattr(l.data, 'size_y', getattr(l.data, 'size', 0.1))]})
used = {m for o in picked if o.type == 'MESH' for m in o.data.materials if m}
manifest['materials'] = sorted(m.name for m in used)
manifest['emission_sets'] = {m.name: {'Day_Operational': m['rf_emit_day'], 'Launch_Mode': m['rf_emit_launch']}
                             for m in used if 'rf_emit_day' in m}
rv = bpy.data.objects.get('REF_RF01_Rover')
if rv and inside(rv.location):
    manifest['rover'] = {'pos': gd(rv.location), 'rot_y_deg': math.degrees(rv.rotation_euler.z), 'asset': 'RF01_Rover.glb'}   # unquantized: Godot lacks KHR_mesh_quantization
json.dump(manifest, open(os.path.join(OUT, f'RF_{room}_lights.json'), 'w'), indent=1)
tris = sum(sum(len(p.vertices) - 2 for p in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh().polygons) for o in picked if o.type == 'MESH')
print(f'EXPORT_OK {path} objects={len(picked)} lights={len(lights)} tris={tris} size_mb={os.path.getsize(path) / 1e6:.1f}')
