"""
game_2_bake.py - game production stage 2: bake base colour + tangent normals from the master to the game meshes.

Run:  blender -b art/character/source/RF01_Engineer_GAME.blend --python art/character/scripts/game_2_bake.py -- [--fast]

Bakes (Cycles, selected-to-active) into art/character/textures/game/, builds simple game materials (base colour,
normal map, one roughness value), then gives the garments their thickness (Solidify, lining material inside) and
sets glTF-friendly alpha clipping on the decals. Saves the GAME .blend.
"""
import bpy, sys, os, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
TEXG = os.path.join(ROOT, 'textures', 'game')
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
FAST = '--fast' in argv
T0 = time.time()
def log(*a):
    print(f'[{time.time() - T0:7.1f}s]', *a, flush=True)

# (game object, high sources, texture size, roughness, bake colour?)
TARGETS = [
    ('GAME_Skin', ['HIGH_Skin'], 2048, 0.50, True),
    ('GAME_Jacket', ['RF01_Jacket', 'RF01_JacketPiping', 'RF01_Hardware'], 2048, 0.75, True),
    ('GAME_Trousers', ['RF01_Trousers', 'RF01_Hardware'], 2048, 0.80, True),
    ('GAME_Shoes', ['RF01_Shoes'], 1024, 0.60, True),
    ('GAME_Hair', ['HIGH_Hair'], 1024, 0.65, False),
]
LINING = (0.015, 0.020, 0.032)


def image(name, size, data):
    im = bpy.data.images.get(name)
    if im:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(name, size, size, alpha=False, float_buffer=False)
    if data:
        im.colorspace_settings.name = 'Non-Color'
    im.generated_color = (0.5, 0.5, 1.0, 1.0) if data else (0.5, 0.5, 0.5, 1.0)
    return im


def game_material(name, base_img, normal_img, rough, base_col=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; L = nt.links
    b = N['Principled BSDF']; b.inputs['Roughness'].default_value = rough
    nodes = {}
    if base_img is not None:
        t = N.new('ShaderNodeTexImage'); t.image = base_img; t.location = (-500, 250)
        L.new(t.outputs['Color'], b.inputs['Base Color']); nodes['base'] = t
    else:
        b.inputs['Base Color'].default_value = (*base_col, 1)
    tn = N.new('ShaderNodeTexImage'); tn.image = normal_img; tn.location = (-500, -150)
    nm = N.new('ShaderNodeNormalMap'); nm.location = (-200, -150)
    L.new(tn.outputs['Color'], nm.inputs['Color']); L.new(nm.outputs['Normal'], b.inputs['Normal'])
    nodes['normal'] = tn
    return m, nodes


def bake(low, highs, kind, node):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for h in highs:
        h.hide_set(False); h.hide_render = False; h.select_set(True)
    low.select_set(True); bpy.context.view_layer.objects.active = low
    low.active_material.node_tree.nodes.active = node
    sc = bpy.context.scene
    kw = dict(use_selected_to_active=True, cage_extrusion=0.006, max_ray_distance=0.03, margin=8,
              use_clear=True, target='IMAGE_TEXTURES')
    if kind == 'COLOR':
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'}, **kw)
    else:
        bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', **kw)
    for h in highs:
        h.select_set(False)


def main():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    sc.cycles.samples = 1 if FAST else 4
    sc.render.bake.use_selected_to_active = True
    for name, srcs, size, rough, colour in TARGETS:
        low = bpy.data.objects[name]
        highs = [bpy.data.objects[s] for s in srcs]
        size = min(size, 1024) if FAST else size
        short = name.replace('GAME_', '')
        bimg = image(f'T_GAME_{short}_BaseColor', size, False) if colour else None
        nimg = image(f'T_GAME_{short}_Normal', size, True)
        base_col = None if colour else tuple(highs[0].active_material.diffuse_color[:3])
        mat, nodes = game_material(f'MAT_GAME_{short}', bimg, nimg, rough, base_col)
        low.data.materials.clear(); low.data.materials.append(mat)
        t = time.time()
        if colour:
            bake(low, highs, 'COLOR', nodes['base'])
        bake(low, highs, 'NORMAL', nodes['normal'])
        for im in (bimg, nimg):
            if im:
                im.filepath_raw = os.path.join(TEXG, im.name + '.png'); im.file_format = 'PNG'; im.save()
        log(f'baked {name} ({size}px) in {time.time() - t:.0f}s')
    # garment thickness after baking: inner shell gets the lining material (no texture)
    lining = bpy.data.materials.new('MAT_GAME_Lining'); lining.use_nodes = True
    lb = lining.node_tree.nodes['Principled BSDF']; lb.inputs['Base Color'].default_value = (*LINING, 1)
    lb.inputs['Roughness'].default_value = 0.85
    for name in ('GAME_Jacket', 'GAME_Trousers'):
        ob = bpy.data.objects[name]
        ob.data.materials.append(lining)
        so = ob.modifiers.new('Thickness', 'SOLIDIFY'); so.thickness = 0.0025; so.offset = -1.0
        so.use_rim = True; so.material_offset = 1; so.material_offset_rim = 0
        with bpy.context.temp_override(active_object=ob, object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
            bpy.ops.object.modifier_apply(modifier=so.name)
    # decals: alpha clip (glTF MASK) instead of blending
    for name in ('GAME_ChestMark', 'GAME_BackMark'):
        m = bpy.data.objects[name].active_material
        nt = m.node_tree; N = nt.nodes; L = nt.links
        b = N['Principled BSDF']
        link = next((l for l in nt.links if l.to_socket == b.inputs['Alpha']), None)
        if link:
            src = link.from_socket; nt.links.remove(link)
            gt = N.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.5
            L.new(src, gt.inputs[0]); L.new(gt.outputs[0], b.inputs['Alpha'])
    # hide bake sources and the master character from the game file's render
    for o in bpy.data.collections['BAKE_HIGH'].objects:
        o.hide_render = True
    for c in ('RF01_Character',):
        bpy.data.collections[c].hide_render = True
    total = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.collections['GAME'].objects
                if o.type == 'MESH' and o.name != 'GAME_Proxy')
    log(f'game triangles (with garment thickness): {total}')
    bpy.ops.wm.save_mainfile()
    log('saved')


main()
