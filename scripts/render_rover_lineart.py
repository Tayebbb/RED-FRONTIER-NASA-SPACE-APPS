"""render_rover_lineart.py - clay render of the locked rover for the Digital Twin screen content.
Run: blender -b assets/rover/RF01_Rover.blend --python scripts/render_rover_lineart.py
Then gen_textures.py turns it into cyan line art."""
import bpy, math
from mathutils import Vector
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.render.resolution_x, sc.render.resolution_y = 1400, 960
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.8, 0.8, 0.8)
sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.show_object_outline = True; sh.object_outline_color = (1, 1, 1)
sh.background_type = 'VIEWPORT'; sh.background_color = (0, 0, 0)
sc.world = sc.world or bpy.data.worlds.new('W')
cam = bpy.data.objects.new('CAM_Lineart', bpy.data.cameras.new('CAM_Lineart'))
sc.collection.objects.link(cam)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 5.2
az, el, tgt = math.radians(-35), math.radians(14), Vector((0, -0.3, 1.05))
cam.location = tgt + Vector((math.sin(az) * -10, -math.cos(az) * 10, math.tan(el) * 10))
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
sc.render.filepath = r"D:\RedFrontier\textures\screens\rover_clay.png"
bpy.ops.render.render(write_still=True)
print('LINEART_RENDERED')
