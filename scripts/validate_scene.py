"""
validate_scene.py - game-readiness checks before export (Godot via glTF).

Reports, does not modify. Checks: default-style names, unapplied object scale, negative
scale, objects with no material slots, empty material slots, hidden-but-exported objects,
mesh/material counts, triangle budget per collection, and that every rover-dependent
marker exists. Exit summary line: VALIDATE <errors> errors, <warnings> warnings.

Run:  blender -b blender/RF_Facility.blend --python scripts/validate_scene.py
"""
import bpy, re
from collections import Counter, defaultdict
errors, warnings = [], []
DEFAULT = re.compile(r'^(Cube|Plane|Cylinder|Sphere|Circle|Text|Empty|Mesh|Object)(\.\d+)?$')
dg = bpy.context.evaluated_depsgraph_get()
tris = defaultdict(int)
for o in bpy.data.objects:
    if o.library: continue
    if DEFAULT.match(o.name): errors.append(f'default name: {o.name}')
    if o.type == 'MESH':
        if any(abs(s - 1) > 1e-4 for s in o.scale): warnings.append(f'unapplied scale {tuple(round(s, 3) for s in o.scale)}: {o.name}')
        if any(s < 0 for s in o.scale): errors.append(f'negative scale: {o.name}')
        if not o.data.materials: errors.append(f'no material: {o.name}')
        elif any(m is None for m in o.data.materials): errors.append(f'empty material slot: {o.name}')
        ev = o.evaluated_get(dg); me = ev.to_mesh()
        tris[o.users_collection[0].name if o.users_collection else '-'] += sum(len(p.vertices) - 2 for p in me.polygons)
        ev.to_mesh_clear()
    if o.hide_render and not o.name.startswith(('REF_', 'DBG_', 'TRIG_')):
        warnings.append(f'hidden from render but would export: {o.name}')
for need in ('PLAYER_Start', 'INT_MissionConfig', 'INT_DigitalTwin', 'INT_LaunchConsole', 'INT_LandingSystem',
             'INT_Station_SCIENCE', 'INT_Station_POWER', 'INT_Station_MOBILITY', 'INT_Station_COMMS'):
    if need not in bpy.data.objects: errors.append(f'missing gameplay marker: {need}')
print('VALIDATE_TRIS', dict(sorted(tris.items(), key=lambda kv: -kv[1])[:12]))
print('VALIDATE_COUNTS objects', len(bpy.data.objects), 'meshes', len(bpy.data.meshes), 'materials', len(bpy.data.materials),
      'images', len(bpy.data.images))
for e in errors[:40]: print('VALIDATE_ERROR', e)
for w in warnings[:40]: print('VALIDATE_WARN', w)
print(f'VALIDATE {len(errors)} errors, {len(warnings)} warnings')
