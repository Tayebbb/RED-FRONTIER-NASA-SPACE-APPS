import bpy, sys
sc = bpy.context.scene
cam = bpy.data.objects.new('CAM_DBG', bpy.data.cameras.new('CAM_DBG')); sc.collection.objects.link(cam)
cam.location = (0, 42.6, 9); cam.rotation_euler = (0, 0, 0); cam.data.type = 'ORTHO'; cam.data.ortho_scale = 8
sc.camera = cam; sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.device = 'CPU'
sc.render.resolution_x = sc.render.resolution_y = 400
for o in bpy.data.objects:
    if o.get('rf_overhead'): o.hide_render = True
for hide in (False, True):
    bpy.data.objects['DEC_TurntableRing'].hide_render = hide
    bpy.data.objects['REF_RF01_Rover'].hide_render = True
    sc.render.filepath = rf'D:\RedFrontier\tmp\dbg_tt_decal{"off" if hide else "on"}.png'
    bpy.ops.render.render(write_still=True)
print('DBG done')
