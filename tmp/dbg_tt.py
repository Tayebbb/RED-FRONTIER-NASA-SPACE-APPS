import bpy
from collections import Counter
o = bpy.data.objects['HERO_RoverPlatform']
print('DBG slots', [m.name for m in o.data.materials])
cnt = Counter()
for p in o.data.polygons:
    cnt[(o.data.materials[p.material_index].name, round(p.center.z, 3), round(p.normal.z, 2))] += 1
for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])[:12]: print('DBG', k, v)
d = bpy.data.objects['DEC_TurntableRing']
print('DBG decal', d.location[:], d.dimensions[:], [m.name for m in d.data.materials])
m = bpy.data.materials['MAT_Painted_Deck']; b = m.node_tree.nodes['Principled BSDF']
print('DBG deck color', tuple(round(c,3) for c in b.inputs['Base Color'].default_value), b.inputs['Roughness'].default_value)
