"""
export_material_library.py - every facility material, once, with its textures, in one GLB.

Room exports (export_gltf.py) carry no images. This library is the single source of every material and
texture for Godot: godot_sync.py imports it, extracts its materials to res://shared/materials/*.tres, and
every room resolves its materials there by name. One texture file per image, however many rooms use it.

Each material gets a 1 x 1 m quad (UV 0..1) so the exporter writes it; the quads themselves are never used.
Also writes RF_Route.json: the mission route in Godot coordinates (traversal test).
Run:  blender -b blender/RF_Facility.blend --python scripts/export_material_library.py
"""
import bpy, os, json
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "export", "godot")
SKIP = ('GB_', 'REF_', 'KIT_', 'Material', 'Dots Stroke')       # greybox, scale figures, Blender defaults

mats = sorted({m for o in bpy.data.objects if o.type == 'MESH' and not o.library
               for m in o.data.materials if m and not m.library and not m.name.startswith(SKIP)}, key=lambda m: m.name)
for o in bpy.data.objects: o.select_set(False)
lib = bpy.data.collections.new('RF_MaterialLibrary'); bpy.context.scene.collection.children.link(lib)
for i, m in enumerate(mats):
    me = bpy.data.meshes.new(f'LIB_{m.name}')
    me.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(); [setattr(uv.data[k], 'uv', c) for k, c in enumerate(((0, 0), (1, 0), (1, 1), (0, 1)))]
    me.materials.append(m)
    o = bpy.data.objects.new(f'LIB_{m.name}', me); lib.objects.link(o); o.location = (i * 1.2, -100, 0); o.select_set(True)
path = os.path.join(OUT, 'RF_MaterialLibrary.glb')
bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_materials='EXPORT',
                          export_texcoords=True, export_normals=True, export_tangents=True, export_yup=True, export_image_format='AUTO')
images = sorted({n.image.name for m in mats if m.node_tree for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image})
json.dump({'materials': [m.name for m in mats], 'images': images}, open(os.path.join(OUT, 'RF_MaterialLibrary.json'), 'w'), indent=1)
print(f'LIBRARY_OK {path} materials={len(mats)} images={len(images)} size_mb={os.path.getsize(path) / 1e6:.1f}')
# the mission route (same points as the orange floor line), in Godot coordinates, for the traversal test
import sys; sys.path.insert(0, os.path.dirname(__file__)); import build_blockout as bb
json.dump({'route': [[round(x, 3), round(-y, 3)] for x, y in bb.mission_path()],
           'order': ['Briefing', 'Corridor01', 'MarsIntel', 'Corridor02', 'Hangar', 'MissionControl']},
          open(os.path.join(OUT, 'RF_Route.json'), 'w'), indent=1)
print('ROUTE_OK points=', len(bb.mission_path()))
