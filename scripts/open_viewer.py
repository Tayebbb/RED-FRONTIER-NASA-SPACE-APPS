"""
open_viewer.py - opens the facility in Blender ready to look at (no editing needed).

Starts in the Hangar entrance camera with Material Preview shading, overlays (empties,
light gizmos, grid) hidden. Number keys 1-4 in the 3D view switch between the four
approved Hangar cameras; 0 returns to free navigation.

Used by Open_Hangar_In_Blender.bat:
  blender RF_Facility.blend --python scripts/open_viewer.py
"""
import bpy

CAMS = ['CAM_Hangar_Entrance', 'CAM_Hangar_Wide', 'CAM_Hangar_Rover', 'CAM_Hangar_Station']

def view3d_areas():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                yield win, area

def look_through(name):
    cam = bpy.data.objects.get(name)
    if not cam: return
    bpy.context.scene.camera = cam
    for win, area in view3d_areas():
        area.spaces.active.region_3d.view_perspective = 'CAMERA'

class RF_OT_camera(bpy.types.Operator):
    """Look through one of the approved Hangar cameras"""
    bl_idname = 'rf.camera'
    bl_label = 'RF camera'
    index: bpy.props.IntProperty()
    def execute(self, ctx):
        if self.index == 0:
            for win, area in view3d_areas():
                area.spaces.active.region_3d.view_perspective = 'PERSP'
        else:
            look_through(CAMS[self.index - 1])
        return {'FINISHED'}

def setup():
    for win, area in view3d_areas():
        sp = area.spaces.active
        sp.shading.type = 'MATERIAL'
        sp.overlay.show_extras = False          # hide empties, cameras, light gizmos
        sp.overlay.show_floor = False
        sp.overlay.show_axis_x = sp.overlay.show_axis_y = False
        sp.clip_start, sp.clip_end = 0.05, 300
        sp.lens = 30
    look_through(CAMS[0])
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    for i, key in enumerate(('ZERO', 'ONE', 'TWO', 'THREE', 'FOUR')):
        km.keymap_items.new('rf.camera', key, 'PRESS').properties.index = i
    print('RF_VIEWER_READY')
    return None

bpy.utils.register_class(RF_OT_camera)
bpy.app.timers.register(setup, first_interval=1.0)
