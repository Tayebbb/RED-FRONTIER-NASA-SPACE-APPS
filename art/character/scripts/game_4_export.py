"""
game_4_export.py - game production stage 4: export the game character to GLB for Godot 4.7.

Run:  blender -b art/character/source/RF01_Engineer_GAME.blend --python art/character/scripts/game_4_export.py

Exports RF01_Armature and the GAME_* meshes (not the weight proxy, not the bake sources, not the master character)
with skins, textures and the Idle / Walk / Run actions to
  art/character/export/RF01_Engineer.glb   and   godot/assets/characters/rf01/RF01_Engineer.glb
glTF converts Blender Z-up / -Y-forward to Godot Y-up: the model arrives facing +Z; the Godot visual scene turns
it 180 degrees so it faces the controller's -Z.
"""
import bpy, os, shutil, json

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(ROOT))
OUT = os.path.join(ROOT, 'export', 'RF01_Engineer.glb')
GODOT = os.path.join(REPO, 'godot', 'assets', 'characters', 'rf01', 'RF01_Engineer.glb')


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True); os.makedirs(os.path.dirname(GODOT), exist_ok=True)
    arm = bpy.data.objects['RF01_Armature']
    for n in ('T_GAME_Hair_BaseColor', 'T_GAME_Hair_Normal'):    # baked at 2K, shipped at 1K (supersampled strands)
        im = bpy.data.images.get(n)
        if im and im.size[0] > 1024:
            im.scale(1024, 1024)
    hair = bpy.data.materials.get('MAT_GAME_Hair')
    if hair:                                             # matte enough not to read grey under rim lights
        hair.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.65
    sel = [arm] + [o for o in bpy.data.collections['GAME'].objects if o.type == 'MESH' and o.name != 'GAME_Proxy']
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in sel:
        o.hide_set(False); o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    arm.animation_data.action = None
    for t in arm.animation_data.nla_tracks:
        t.mute = False
    kw = dict(filepath=OUT, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
              export_texcoords=True, export_normals=True, export_tangents=True, export_materials='EXPORT',
              export_skins=True, export_animations=True, export_animation_mode='ACTIONS',
              export_force_sampling=True, export_def_bones=True, export_image_format='AUTO')
    try:
        bpy.ops.export_scene.gltf(**kw)
    except TypeError as e:                       # option names differ between Blender versions
        print('retry without optional args:', e)
        for k in ('export_def_bones', 'export_force_sampling', 'export_image_format'):
            kw.pop(k, None)
        bpy.ops.export_scene.gltf(**kw)
    shutil.copyfile(OUT, GODOT)
    tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sel if o.type == 'MESH')
    info = dict(file=OUT, godot=GODOT, triangles=tri, meshes=[o.name for o in sel if o.type == 'MESH'],
                bones=len(arm.data.bones), actions=[a.name for a in bpy.data.actions if a.get('rf_loop')],
                size_mb=round(os.path.getsize(OUT) / 1e6, 2))
    print('EXPORT', json.dumps(info))


main()
