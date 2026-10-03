"""
render_cycles.py - beauty renders of facility cameras (Cycles, CPU).

Run:  blender -b blender/RF_Facility.blend --python scripts/render_cycles.py -- <tag> <width> <samples> CAM_a [CAM_b ...]
"""
import bpy, sys, os, time
argv = sys.argv[sys.argv.index('--') + 1:]
tag, width, samples, cams = argv[0], int(argv[1]), int(argv[2]), argv[3:]
out_dir = os.path.join(r"D:\RedFrontier\renders", tag); os.makedirs(out_dir, exist_ok=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
cy = sc.cycles
cy.device = 'CPU'; cy.samples = samples; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.02
cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6; cy.diffuse_bounces = 3; cy.glossy_bounces = 3; cy.transmission_bounces = 4; cy.transparent_max_bounces = 8
cy.sample_clamp_indirect = 6.0; cy.blur_glossy = 1.0
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = width, round(width * 9 / 16), 100
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
sc.view_settings.exposure = float(os.environ.get('RF_EXPOSURE', '0'))
for o in bpy.data.objects:
    if o.get('rf_plan_only'): o.hide_render = True
for name in cams:
    cam = bpy.data.objects[name]; sc.camera = cam
    sc.render.filepath = os.path.join(out_dir, name + '.png')
    t = time.time(); bpy.ops.render.render(write_still=True)
    print(f'CYCLES_RENDERED {name} {time.time() - t:.0f}s')
