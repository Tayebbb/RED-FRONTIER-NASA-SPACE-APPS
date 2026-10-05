"""
render_previews.py - render every CAM_* in a facility file to renders/<tag>/.

Greybox mode uses Workbench (fast, readable clay). Plan / cutaway cameras hide
ceilings and overhead structure (objects tagged rf_overhead); DBG_ labels only
show in the plan view.

Run:  blender -b <file.blend> --python scripts/render_previews.py -- <tag> [CAM_name ...]
"""
import bpy, sys, os
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
tag = argv[0] if argv else 'blockout'
only = set(argv[1:])
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out_dir = os.path.join(ROOT, 'renders', tag); os.makedirs(out_dir, exist_ok=True)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1600, 900, 100
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'
sh.show_cavity = True; sh.cavity_type = 'BOTH'
sh.cavity_ridge_factor = 0.6; sh.cavity_valley_factor = 1.0
sh.show_specular_highlight = True
sc.display.shading.show_object_outline = False
sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'

overhead = [o for o in bpy.data.objects if o.get('rf_overhead')]
plan_only = [o for o in bpy.data.objects if o.get('rf_plan_only')]
cutaway = [o for o in bpy.data.objects if o.get('rf_cutaway_hide')]
cams = sorted((o for o in bpy.data.objects if o.type == 'CAMERA' and o.name.startswith('CAM_')), key=lambda o: o.name)
for cam in cams:
    if only and cam.name not in only: continue
    cut = cam.name in ('CAM_Plan_Top', 'CAM_Axo_Cutaway')
    for o in overhead: o.hide_render = cut
    for o in cutaway: o.hide_render = cam.name == 'CAM_Axo_Cutaway'
    for o in plan_only: o.hide_render = cam.name != 'CAM_Plan_Top'
    sh.show_shadows = cut                       # interiors: ceilings would shadow everything
    sc.display.shadow_shift = 0.1
    sc.display.light_direction = (0.45, -0.35, 0.82)
    if cam.name == 'CAM_Plan_Top':
        sc.render.resolution_x, sc.render.resolution_y = 1400, 1600
    else:
        sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.camera = cam
    sc.render.filepath = os.path.join(out_dir, cam.name + '.png')
    bpy.ops.render.render(write_still=True)
    print('RENDERED', cam.name)
