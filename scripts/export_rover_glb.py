"""export_rover_glb.py - unquantized GLB of the LOCKED rover for Godot (which lacks KHR_mesh_quantization).
Same geometry, names and hierarchy as the source; only the vertex encoding changes (floats).
Run: blender -b assets/rover/RF01_Rover.blend --python scripts/export_rover_glb.py"""
import bpy, os
p = r"D:\RedFrontier\assets\rover\RF01_Rover.glb"
bpy.ops.export_scene.gltf(filepath=p, export_format='GLB', export_apply=True, export_extras=True, export_yup=True)
print('ROVER_EXPORT', round(os.path.getsize(p) / 1e6, 1), 'MB')
