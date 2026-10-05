"""check_hangar_fit.py - measure rover vs turntable and wheel marks (no visual judgement)."""
import bpy, math
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get()
xs, ys, contact = [], [], []
for inst in dg.object_instances:
    if inst.is_instance and inst.parent and inst.parent.name == 'REF_RF01_Rover' and inst.object.type == 'MESH':
        m = inst.matrix_world
        for c in inst.object.bound_box:
            w = m @ Vector(c); xs.append(w.x); ys.append(w.y)
        if inst.object.name.startswith('Wheels_objs'):
            contact = [m @ v.co for v in inst.object.data.vertices if (m @ v.co).z < 0.12 + 0.03]
plat = bpy.data.objects['HERO_RoverPlatform'].location
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
print(f"FIT rover bbox centre=({cx:.3f},{cy:.3f}) platform centre=({plat.x:.3f},{plat.y:.3f})")
rmax = max(math.hypot(x - plat.x, y - plat.y) for x, y in zip(xs, ys))
print(f"FIT farthest rover bbox corner from platform centre = {rmax:.2f} m (turntable radius 3.25)")
if contact:
    print(f"FIT wheel contact verts on turntable: {len(contact)}  min z={min(p.z for p in contact):.3f}")
else:
    print("FIT detailed Perseverance asset uses separate wheel meshes; legacy wheel-contact check skipped")
for o in sorted((o for o in bpy.data.objects if o.name.startswith('DEC_WheelMark')), key=lambda o: o.name):
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    c = sum(vs, Vector()) / len(vs)
    near = sum(1 for p in contact if abs(p.x - c.x) < 0.32 and abs(p.y - c.y) < 0.32)
    print(f"FIT {o.name} centre=({c.x:.2f},{c.y:.2f}) wheel-contact verts within 0.32 m: {near}")
