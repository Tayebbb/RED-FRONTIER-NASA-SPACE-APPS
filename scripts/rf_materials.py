"""
rf_materials.py - the Red Frontier material library (Blender side).

Principled BSDF + image textures only, so everything exports through glTF to Godot.
UVs are authored in metres by rf_lib.uv_box(), so tiling textures need no mapping nodes.
Palette: 70% neutral light / 20% dark structure / <=10% orange + functional accents.
"""
import bpy, os
from rf_lib import hex_rgb

TEX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "textures")

def _img(path, non_color=False):
    name = os.path.basename(path)
    im = bpy.data.images.get(name) or bpy.data.images.load(path)
    if non_color: im.colorspace_settings.name = 'Non-Color'
    return im

def pbr(name, color='#cccccc', rough=0.5, metal=0.0, base=None, rough_tex=None, normal=None, normal_strength=1.0,
        emit=None, emit_strength=0.0, emit_tex=None, alpha_tex=False, transmission=0.0, coat=0.0, alpha=1.0):
    """Create or refresh a material. Texture args are file names under textures/."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (500, 0)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); b.location = (200, 0)
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    b.inputs['Base Color'].default_value = hex_rgb(color)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    y = 300
    def tex(fn, non_color=False):
        nonlocal y
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = _img(os.path.join(TEX, fn), non_color); t.location = (-400, y); y -= 300
        return t
    if base:
        t = tex(base); nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
        if alpha_tex:
            nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
    if rough_tex:
        t = tex(rough_tex, True); nt.links.new(t.outputs['Color'], b.inputs['Roughness'])
    if normal:
        t = tex(normal, True); nm = nt.nodes.new('ShaderNodeNormalMap'); nm.location = (-100, -400)
        nm.inputs['Strength'].default_value = normal_strength
        nt.links.new(t.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    if emit:
        b.inputs['Emission Color'].default_value = hex_rgb(emit)
        b.inputs['Emission Strength'].default_value = emit_strength
    if emit_tex:
        t = tex(emit_tex); nt.links.new(t.outputs['Color'], b.inputs['Emission Color'])
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
        b.inputs['Emission Strength'].default_value = emit_strength
    if transmission:
        b.inputs['Transmission Weight'].default_value = transmission
    if coat:
        b.inputs['Coat Weight'].default_value = coat
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        if hasattr(m, 'surface_render_method'): m.surface_render_method = 'BLENDED'
    if alpha_tex and hasattr(m, 'surface_render_method'):
        m.surface_render_method = 'BLENDED'
    m.diffuse_color = hex_rgb(emit or color)          # viewport / Workbench colour
    return m

def build():
    """Create every library material once; returns a dict keyed by short name."""
    L = {}
    def add(key, *a, **k): L[key] = pbr(*a, **k)
    # architecture
    add('wall_white',  'MAT_Wall_White', '#E4E1DA', 0.55)
    add('wall_white_b','MAT_Wall_White_B', '#E1DED6', 0.60)       # panel-to-panel finish variation
    add('wall_white_c','MAT_Wall_White_C', '#E6E3DC', 0.50)
    add('wall_lower',  'MAT_Wall_Lower', '#C9C5BD', 0.62)         # protective lower row: slightly darker, matte
    add('wall_grey',   'MAT_Wall_Grey', '#8C9197', 0.66)        # upper zones recede
    add('wall_grey_b', 'MAT_Wall_Grey_B', '#898E94', 0.72)
    add('wall_grey_c', 'MAT_Wall_Grey_C', '#8F949A', 0.60)
    add('backer',      'MAT_Wall_Backer', '#16181B', 0.8)
    add('graphite',    'MAT_Structural_Graphite', '#2C2F34', 0.42)
    add('navy',        'MAT_Structural_Navy', '#1C2636', 0.5)
    add('ceiling_dark','MAT_Ceiling_Dark', '#24272C', 0.85, normal='surfaces/T_RoofDeck_Normal.png', normal_strength=0.8)
    add('ceiling_white','MAT_Ceiling_White', '#ECEBE7', 0.9)
    # floors
    add('floor_epoxy', 'MAT_Floor_Epoxy', base='surfaces/T_Floor_Epoxy_BaseColor.png', rough_tex='surfaces/T_Floor_Epoxy_Roughness.png',
        normal='surfaces/T_Floor_Epoxy_Normal.png', normal_strength=0.6)
    add('floor_rubber','MAT_Floor_Rubber', '#2F3236', 0.85)
    add('floor_metal', 'MAT_Floor_Metal', '#7E8288', 0.45, 1.0, base='surfaces/T_Grate_BaseColor.png', normal='surfaces/T_Grate_Normal.png')
    # metals and paints
    add('brushed',     'MAT_Brushed_Metal', '#A9ADB2', 0.32, 1.0, rough_tex='surfaces/T_Brushed_Roughness.png')
    add('painted',     'MAT_Painted_Metal', '#D3D6D9', 0.42)
    add('deck',        'MAT_Painted_Deck', '#7C8288', 0.6)        # turntable deck: matte so it never mirrors the dark roof
    add('painted_dark','MAT_Painted_Metal_Dark', '#565B62', 0.48)
    add('rubber',      'MAT_Black_Rubber', '#141516', 0.8)
    add('orange',      'MAT_Orange_Accent', '#C2501C', 0.45)
    add('yellow',      'MAT_Warning_Yellow', '#E3A928', 0.5)
    add('glass',       'MAT_Glass', '#B9CCD4', 0.03, transmission=1.0, alpha=0.3)   # transmission for Cycles, alpha for Godot
    # emissive
    add('screen_dark', 'MAT_Screen_Dark', '#0A0D11', 0.12)
    add('screen',      'MAT_Screen_Emissive', '#000000', 0.2, emit='#74B6FF', emit_strength=2.5)
    add('orange_led',  'MAT_Orange_Emissive', '#C2501C', 0.4, emit='#FF6A2B', emit_strength=6.0)
    add('diffuser',    'MAT_Light_Diffuser', '#FFFFFF', 0.4, emit='#FFF3E4', emit_strength=9.0)
    add('led_cool',    'MAT_LED_Cool', '#FFFFFF', 0.4, emit='#DCEBFF', emit_strength=5.0)
    add('status_cyan', 'MAT_Status_Cyan', '#000000', 0.3, emit='#74B6FF', emit_strength=6.0)
    add('status_amber','MAT_Status_Amber', '#000000', 0.3, emit='#FFB43A', emit_strength=6.0)
    # Phase 5 - Mission Control (appended; nothing above changes, so the locked Hangar is unaffected)
    add('floor_access','MAT_Floor_Access', base='surfaces/T_Floor_Access_BaseColor.png', rough_tex='surfaces/T_Floor_Access_Roughness.png',
        normal='surfaces/T_Floor_Access_Normal.png', normal_strength=0.5)
    add('ceiling_acoustic', 'MAT_Ceiling_Acoustic', '#4A4D52', 0.95)
    add('media_a',     'MAT_Wall_Media', '#2B2E33', 0.70)         # media wall: the Hangar panel module in graphite
    add('media_b',     'MAT_Wall_Media_B', '#282B30', 0.78)
    add('media_c',     'MAT_Wall_Media_C', '#2E3136', 0.64)
    add('diffuser_dim','MAT_Light_Diffuser_Dim', '#FFFFFF', 0.4, emit='#FFE9D2', emit_strength=1.6)
    add('beacon',      'MAT_Beacon_Amber', '#E3A928', 0.25, emit='#FFB43A', emit_strength=0.05)   # ~off; non-zero so glTF keeps the emissive
    # Phase 5 - Mars Intelligence
    add('mars_terrain','MAT_MarsTable_Terrain', '#000000', 0.85, base='surfaces/T_MarsTable_BaseColor.png',
        emit_tex='surfaces/T_MarsTable_BaseColor.png', emit_strength=0.25)      # relief model, faintly projection-lit
    return L

def screen(name, image, strength=2.2):
    """Emissive screen material with generated content. Matte anti-glare finish: no light hotspots."""
    m = pbr(f'MAT_Screen_{name}', '#000000', 0.45, emit_tex=f'screens/{image}', emit_strength=strength)
    m.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.12
    return m

def atlas_decal():
    """Single shared material for every small service label (cells mapped by UV)."""
    return pbr('MAT_Decal_ServiceAtlas', '#ffffff', 0.5, base='decals/T_Decal_ServiceAtlas.png', alpha_tex=True)

def decal(name, image, rough=0.5):
    """Alpha decal material (painted floor graphics, labels)."""
    return pbr(f'MAT_Decal_{name}', '#ffffff', rough, base=f'decals/{image}', alpha_tex=True)
