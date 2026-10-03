import bpy
from mathutils import Vector


GROUPS = {
    'mobility': ['ASSEMBLY', 'SM_Chassis', 'SM_Arm_Bogie_L', 'SM_Arm_Bogie_R',
                 'Wheel_Standard', 'Wheel_Reinforced'],
    'science': ['SM_Mast', 'Inst_Camera', 'Inst_Radar', 'Inst_Radiation',
                'Inst_Soil', 'Inst_Spectrometer', 'Inst_Weather'],
    'systems': ['Solar_Light', 'Solar_Large', 'Battery_Standard',
                'Battery_Extended', 'Shield_Minimal', 'Shield_Standard',
                'Shield_Heavy', 'Antenna_Std', 'Antenna_HighGain', 'Power_Nuclear'],
}


def capture_reviews(suffix='before'):
    production = bpy.context.scene
    direction = Vector((6, -9, 6)).normalized()
    rotation = (-direction).to_track_quat('-Z', 'Y')
    right = rotation @ Vector((1, 0, 0))
    up = rotation @ Vector((0, 1, 0))
    for group_name, names in GROUPS.items():
        scene = bpy.data.scenes.new('QA_TEMP')
        scene.render.engine = 'BLENDER_WORKBENCH'
        scene.display.shading.light = 'STUDIO'
        scene.display.shading.color_type = 'MATERIAL'
        scene.display.shading.show_shadows = True
        scene.display.shading.show_cavity = True
        scene.display.shading.background_type = 'WORLD'
        scene.world = bpy.data.worlds.new('QA_TEMP_WORLD')
        scene.world.color = (0.12, 0.12, 0.12)
        scene.render.resolution_x = 1800
        rows = (len(names) + 2) // 3
        scene.render.resolution_y = rows * 540
        scene.render.resolution_percentage = 100
        camera_data = bpy.data.cameras.new('QA_TEMP_CAMERA')
        camera_data.type = 'ORTHO'
        camera_data.ortho_scale = max(7.5, rows * 2.7)
        camera = bpy.data.objects.new('QA_TEMP_CAMERA', camera_data)
        scene.collection.objects.link(camera)
        camera.location = direction * 25
        camera.rotation_mode = 'QUATERNION'
        camera.rotation_quaternion = rotation
        scene.camera = camera
        for index, name in enumerate(names):
            anchor = right * ((index % 3 - 1) * 2.5) + up * (((rows - 1) / 2 - index // 3) * 2.25)
            sources = [obj for obj in bpy.data.collections['ROVER_BASE'].objects if obj.type == 'MESH'] if name == 'ASSEMBLY' else [bpy.data.objects[name]]
            points = [obj.matrix_world @ Vector(corner) for obj in sources for corner in obj.bound_box]
            lower = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
            upper = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
            center = (lower + upper) / 2
            factor = 1.6 / max(upper - lower)
            for source in sources:
                duplicate = source.copy()
                duplicate.data = source.data.copy()
                duplicate.parent = None
                duplicate.matrix_world = source.matrix_world.copy()
                duplicate.location = (duplicate.location - center) * factor + anchor
                duplicate.scale *= factor
                duplicate.hide_viewport = False
                duplicate.hide_render = False
                scene.collection.objects.link(duplicate)
                duplicate.hide_set(False, view_layer=scene.view_layers[0])
            text_data = bpy.data.curves.new('QA_TEMP_LABEL', 'FONT')
            text_data.body = name
            text_data.align_x = 'CENTER'
            text_data.size = 0.12
            text = bpy.data.objects.new('QA_TEMP_LABEL', text_data)
            scene.collection.objects.link(text)
            text.location = anchor - up * 1.0 + direction * 1.2
            text.rotation_mode = 'QUATERNION'
            text.rotation_quaternion = rotation
            text.color = (0.95, 0.95, 0.95, 1)
        scene.render.filepath = 'E:/Nasa Space APps/art/qa/' + group_name + '_' + suffix + '.png'
        bpy.ops.render.render(write_still=True, scene=scene.name)
        print('CAPTURE', scene.render.filepath)
        temporary_objects = list(scene.objects)
        temporary_world = scene.world
        bpy.data.scenes.remove(scene)
        for obj in temporary_objects:
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Curve):
                    bpy.data.curves.remove(data)
                elif isinstance(data, bpy.types.Camera):
                    bpy.data.cameras.remove(data)
        bpy.data.worlds.remove(temporary_world)
    print('PRODUCTION_UNCHANGED', production.name, len(production.objects))


capture_reviews()