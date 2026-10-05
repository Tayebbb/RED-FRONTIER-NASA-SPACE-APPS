"""
build_corridors.py - PHASE 5: the two corridors. Connective spaces, not hero rooms: clean, fast to
traverse, built only from existing kit pieces, decals and one small cropped texture.

Corridor 01  Briefing -> Mars Intelligence: mission context into planetary analysis.
             Standard cladding, one Mars map strip mounted on the W panels, one directional sign over the far door.
Corridor 02  Mars Intelligence -> Engineering Hangar: anticipation before the rover reveal.
             Graphite (media) cladding for darker framing, so the lit Hangar opens up ahead; one
             recessed RF-01 line-art graphic (W), restrained ENGINEERING HANGAR signage on the E wall.
             Nothing on the centre line and nothing near the Hangar threshold: the rover is in view
             from the Mars Intelligence door onward.
Both         orange route line (split_mission_path), trim rail + LED wash at 3.0 m like every room,
             one suspended linear light, graphite portals on the corridor side of each door.
Called by build_facility.py.
"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import rf_lib as rf, rf_kit as kit, rf_materials as rm
import build_blockout as bb
import build_hangar as bh
import rf_room as room

C = bh.C
def sub(path): return bh.sub(path)

def shell(name, fp, L, wall_set, recess=None):
    """Floor, ceiling, E/W walls (open ends), cladding (optionally one recess on the W wall)."""
    x0, x1, y0, y1, h = fp
    col = sub(f'01_ARCH/Corridor/{name}')
    mats = {'floor': L['floor_epoxy'], 'wall': L['graphite'], 'ceiling': L['ceiling_acoustic'], 'glass': L['glass']}
    rf.create_room(name, x0, x1, y0, y1, h, col, mats, {}, skip=('N', 'S'), ceil_col=C('ceil'))
    bpy.context.view_layer.update()
    bh.world_uv(bpy.data.objects[f'{name}_Floor'], 4.4, ox=-2.2, oy=0.0)          # same joint grid as the rooms
    bh.world_uv(bpy.data.objects[f'{name}_Ceiling'], 1.0)
    bpy.data.objects[f'{name}_Ceiling']['rf_overhead'] = True
    clad = sub(f'01_ARCH/Corridor/{name}/Cladding')
    kit.place(kit.cladding(f'MOD_{name}_Cladding_W', y1 - y0, h, wall_set, clad, openings=[recess] if recess else []), (x0, y0, 0), 90)
    kit.place(kit.cladding(f'MOD_{name}_Cladding_E', y1 - y0, h, wall_set, clad), (x1, y1, 0), -90)

def ceiling_light(name, fp, L, watts):
    x0, x1, y0, y1, h = fp
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    fx = kit.linear_light(f'PROP_{name}_LinearLight', y1 - y0 - 1.0, L, sub(f'02_PROPS/{name}'), drop=0.1)
    kit.place(fx, (cx, cy, h - 0.17), 90)['rf_overhead'] = True
    rf.create_area_light(f'LGT_{name}_Line', (cx, cy, h - 0.22), 0.2, watts, sub(f'04_LIGHTS/LIGHTSET_Day_Operational/LIGHTS_{name}'),
                         '#FFE6CC', size_y=y1 - y0 - 1.2)

def recessed_graphic(name, image, w, hgt, x, y, z0, strength, L, col):
    """Slim display on the W wall: set into a recess in Corridor 02, surface-mounted on the panels in Corridor 01."""
    fr = kit.display_frame(f'PROP_{name}', w, hgt, L['screen_dark'], L, col, border=0.06, depth=0.1)
    kit.place(fr, (x + 0.15, y, z0), 90)
    bh.screen_quad(name, image, w, hgt, (x + 0.16, y, z0 + 0.06 + hgt / 2), (math.radians(90), 0, math.radians(90)), strength)

def build_corridor01(L):
    fp = bb.C1; x0, x1, y0, y1, h = fp; cy = (y0 + y1) / 2
    shell('Corridor01', fp, L, L)               # no recess: cladding drops whole 1.4 m panels, which would darken the wall
    p = sub('02_PROPS/Corridor01')
    recessed_graphic('Corridor01_Strip', 'T_Screen_Corridor01_Strip.png', 2.4, 0.5, x0, cy, 1.35, 1.2, L, p)
    op = sub('01_ARCH/Corridor/Corridor01/Openings')
    room.door_portal('MOD_Corridor01_Portal_S', 2.75, y0, 1.2, 2.3, 'x', 1, L, op)       # Briefing exit (corridor side)
    room.door_portal('MOD_Corridor01_Portal_N', 2.75, y1, 1.2, 2.3, 'x', -1, L, op)      # Mars Intelligence entry
    bh.wall_text('Corridor01_Sign', 'T_Decal_MarsIntel.png', 0.13, (2.75, y1 - 0.01, 2.62), 0)   # one directional sign
    ceiling_light('Corridor01', fp, L, 80)
    rf.create_camera('CAM_Corridor01', (2.75, y0 + 0.35, 1.65), (2.55, y1 + 1.0, 1.5), C('cams'), lens=20)

def build_corridor02(L):
    fp = bb.C2; x0, x1, y0, y1, h = fp; cy = (y0 + y1) / 2
    media = dict(L, wall_white=L['media_a'], wall_white_b=L['media_b'], wall_white_c=L['media_c'], wall_lower=L['media_b'],
                 wall_grey=L['media_a'], wall_grey_b=L['media_b'], wall_grey_c=L['media_c'])
    shell('Corridor02', fp, L, media, (cy - y0 - 1.3, cy - y0 + 0.7, 1.15, 2.3))         # recess around the graphic at cy - 0.3
    p = sub('02_PROPS/Corridor02')
    recessed_graphic('Corridor02_RF01', 'T_Screen_DigitalTwin.png', 1.8, 0.9, x0, cy - 0.3, 1.2, 1.1, L, p)   # reused texture
    op = sub('01_ARCH/Corridor/Corridor02/Openings')
    room.door_portal('MOD_Corridor02_Portal_S', 0.0, y0, 1.8, 2.4, 'x', 1, L, op)        # from Mars Intelligence
    room.door_portal('MOD_Corridor02_Portal_N', 0.0, y1, 2.6, 2.9, 'x', -1, L, op)       # Hangar threshold: frame only
    bh.wall_text('Corridor02_HangarSign', 'T_Decal_EngineeringHangar.png', 0.14, (x1 - 0.06, cy + 0.6, 2.3), -90)
    bh.wall_text('Corridor02_WorkBay', 'T_Decal_WorkBay.png', 0.07, (x1 - 0.06, cy + 0.6, 2.08), -90)
    ceiling_light('Corridor02', fp, L, 55)                                                 # darker than the rooms either side
    rf.create_camera('CAM_Corridor02', (0.0, y0 + 0.35, 1.65), (0.0, 42.0, 1.35), C('cams'), lens=20)

def build(L):
    before = set(bpy.data.objects.keys())
    build_corridor01(L); n1 = room.tag_room(before, 'Corridor01')
    before = set(bpy.data.objects.keys())
    build_corridor02(L); n2 = room.tag_room(before, 'Corridor02')
    print('CORRIDORS_OK objects=', n1, n2)
