import bpy
from mathutils import Vector
w = bpy.data.objects['Wheels_objs']
print("DBG matrix_world", [list(map(lambda v: round(v,3), r)) for r in w.matrix_world])
print("DBG loc/rot/scale", tuple(w.location), tuple(w.rotation_euler), tuple(w.scale), "parent", w.parent)
pts = [w.matrix_world @ v.co for v in w.data.vertices]
print("DBG z range", min(p.z for p in pts), max(p.z for p in pts))
low = [p for p in pts if p.z < 0.03]
print("DBG low count", len(low))
import collections
h = collections.Counter((round(p.x*2)/2, round(p.y*2)/2) for p in low)
print("DBG bins", sorted(h.items()))
