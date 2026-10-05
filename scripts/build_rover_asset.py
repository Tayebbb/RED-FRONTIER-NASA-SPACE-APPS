"""
build_rover_asset.py - wrap the detailed Perseverance model as a linkable asset.

Imports the approved art export untouched into collection 'RF01_Rover' and saves
assets/rover/RF01_Rover.blend. Facility scenes LINK this collection, so the rover
cannot be edited from inside an environment file.

Run:  blender -b --factory-startup --python scripts/build_rover_asset.py
"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import rf_lib as rf

rf.reset_scene()
bpy.ops.import_scene.gltf(filepath=os.path.join(
    rf.ROOT, 'art', 'export', 'rover', 'perseverance', 'perseverance_rover.glb'))
col = bpy.data.collections.new('RF01_Rover')
bpy.context.scene.collection.children.link(col)
for o in list(bpy.context.scene.collection.objects):
    rf.link(o, col)

# report footprint so environments can be sized around it
xs, ys, zs = [], [], []
for o in col.objects:
    if o.type == 'MESH':
        for c in o.bound_box:
            w = o.matrix_world @ rf.Vector(c); xs.append(w.x); ys.append(w.y); zs.append(w.z)
print(f"ROVER_BBOX x[{min(xs):.3f},{max(xs):.3f}] y[{min(ys):.3f},{max(ys):.3f}] z[{min(zs):.3f},{max(zs):.3f}] objects={len(col.objects)}")
rf.save(os.path.join(rf.ROOT, 'assets', 'rover', 'RF01_Rover.blend'))
