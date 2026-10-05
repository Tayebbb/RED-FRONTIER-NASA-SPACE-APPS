"""
build_mars_intelligence.py - PHASE 5: Mars Intelligence at near-final quality, in the Hangar's visual language.

Two decisions, in the order the brief locks: the LANDING SYSTEM (standard / precision) at the console
by the entrance, then the LANDING SITE at the Mars table, because precision landing decides which
sites are reachable. Footprint, doors, table, console and desk positions come from build_blockout.
  hero     the Mars table: a physical relief model of Jezero (crater, inflow channel, delta, boulder
           field) displaced from T_MarsTable_Height, landing ellipses that follow the terrain, site pins
  walls    Hangar cladding on N / S / E; the W wall carries the terrain map, so it gets the Mission
           Control media treatment (graphite panel module, one dark recess for the display)
  floor    Hangar epoxy, joints on a 4.4 m grid centred on the table
  ceiling  dark acoustic plane; a suspended light halo frames the table, linear lines over the aisles
  orange   only the landing-system console strip and the three site-pick strips on the table edge
Called by build_facility.py.
"""
import bpy, bmesh, sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import rf_lib as rf, rf_kit as kit, rf_materials as rm
import build_blockout as bb
import build_hangar as bh
import rf_room as room

X0, X1, Y0, Y1, H = bb.INTEL
TC = (0.0, 22.0)                       # table centre (greybox)
TZ, RELIEF = 0.84, 0.06                # terrain base height, relief amplitude (m)
SITES = {'A': (-1.2, -0.5), 'B': (0.4, 0.6), 'C': (1.3, -0.5)}       # table-local, same as gen_textures
ELLIPSE = (0.17, 0.145)
CONSOLE = (0.0, 19.0)
DESKS = ((-3.6, 17.4, 180), (-1.4, 17.4, 180), (3.9, 26.6, 0), (-3.7, 26.6, 0))   # rot 180: operator north of desk
C = bh.C

def sub(path): return bh.sub(path)

# ===================================================================== TERRAIN
class Relief:
    """Bilinear sampler over the 16-bit height map (table-local metres -> 0..1)."""
    def __init__(self):
        im = bpy.data.images.load(os.path.join(rm.TEX, 'surfaces', 'T_MarsTable_Height.png'))
        im.colorspace_settings.name = 'Non-Color'
        w, h = im.size; px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
        self.h = px.reshape(h, w, 4)[..., 0]; self.w, self.hh = w, h              # row 0 = south (Blender)
        bpy.data.images.remove(im)
    def __call__(self, x, y):
        fx = min(max((x + 2) / 4, 0), 1) * (self.w - 1); fy = min(max((y + 1.2) / 2.4, 0), 1) * (self.hh - 1)
        i, j = int(fx), int(fy); i1, j1 = min(i + 1, self.w - 1), min(j + 1, self.hh - 1); a, b = fx - i, fy - j
        return float((self.h[j, i] * (1 - a) + self.h[j, i1] * a) * (1 - b) + (self.h[j1, i] * (1 - a) + self.h[j1, i1] * a) * b)

def terrain_mesh(rel, L, col, nx=160, ny=96):
    me = bpy.data.meshes.new('HERO_MarsTable_Terrain'); bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    vs = [[bm.verts.new((-2 + 4 * i / nx, -1.2 + 2.4 * j / ny, rel(-2 + 4 * i / nx, -1.2 + 2.4 * j / ny) * RELIEF))
           for i in range(nx + 1)] for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i])); f.smooth = True
            for l, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))): l[uv].uv = (a / nx, b / ny)
    bm.to_mesh(me); bm.free(); me.materials.append(L['mars_terrain'])
    o = bpy.data.objects.new('HERO_MarsTable_Terrain', me); col.objects.link(o); o.location = (*TC, TZ)
    return o

def ellipse_ring(name, rel, cx, cy, rx, ry, mat, col, w=0.012, segs=72):     # 24 mm: reads from across the room
    """Landing ellipse that hugs the relief, 4 mm above it."""
    me = bpy.data.meshes.new(name); bm = bmesh.new(); ring = []
    for k in range(segs):
        a = 2 * math.pi * k / segs; c, s = math.cos(a), math.sin(a)
        pts = [(cx + c * (rx + d), cy + s * (ry + d)) for d in (-w, w)]
        ring.append([bm.verts.new((x, y, rel(x, y) * RELIEF + 0.004)) for x, y in pts])
    for k in range(segs):
        a, b = ring[k], ring[(k + 1) % segs]; bm.faces.new((a[0], b[0], b[1], a[1]))
    bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = (*TC, TZ)
    return o

def build_table(L):
    hero = C('hero'); rel = Relief()
    mb = kit.MB()
    mb.box((4.2, 2.6, 0.1), (0, 0, 0.05), L['backer'])                                         # recessed kick
    mb.box((4.4, 2.8, 0.7), (0, 0, 0.45), L['painted'])                                        # satin body
    for sy in (-1, 1): mb.box((4.4, 0.2, 0.14), (0, sy * 1.3, 0.87), L['graphite'])           # rim: terrain sits in a tray
    for sx in (-1, 1): mb.box((0.2, 2.4, 0.14), (sx * 2.1, 0, 0.87), L['graphite'])
    mb.box((4.0, 2.4, 0.02), (0, 0, TZ - 0.01), L['backer'])
    for x in (SITES[k][0] for k in 'ABC'):                                                   # site-pick strips: orange-lit = interactable
        mb.box((0.36, 0.012, 0.025), (x, -1.406, 0.86), L['orange_led'])
    mb.box((4.4, 0.012, 0.012), (0, -1.406, 0.79), L['brushed'])
    kit.place(mb.build('HERO_MarsTable', hero, bevel=0.006), (*TC, 0))
    terrain_mesh(rel, L, hero)
    mats = {k: rm.pbr(f'MAT_Site_{k}', '#000000', 0.4, emit=e, emit_strength=2.8)              # B selected, C needs precision;
            for k, e in (('A', '#74B6FF'), ('B', '#FF6A2B'), ('C', '#FFB43A'))}                 # dimmer than status LEDs: lines, not dots
    for k, (x, y) in SITES.items():
        ellipse_ring(f'HERO_MarsTable_Ellipse{k}', rel, x, y, *ELLIPSE, mats[k], hero)
        z = TZ + rel(x, y) * RELIEF; wx, wy = TC[0] + x, TC[1] + y                         # survey pin + letter flag
        pin = kit.MB().cyl(0.004, 0.17, (0, 0, 0.085), L['brushed'], segs=8).cyl(0.016, 0.012, (0, 0, 0.176), mats[k], segs=16) \
                      .box((0.09, 0.004, 0.09), (0, 0.004, 0.25), L['graphite'])
        kit.place(pin.build(f'HERO_MarsTable_Pin{k}', hero, bevel=0.0), (wx, wy, z))
        kit.decal_plane(f'DEC_MarsTable_Site{k}', rm.decal(f'Site{k}', f'T_Decal_Site{k}.png'), 0.06, 0.06, C('decals'),
                        (wx, wy - 0.0025, z + 0.25), (math.radians(90), 0, 0))
    sc = bh.img_size('decals/T_Decal_MarsTableScale.png')
    kit.decal_plane('DEC_MarsTable_Scale', rm.decal('MarsTableScale', 'T_Decal_MarsTableScale.png'), 0.045 * sc[0] / sc[1], 0.045,
                    C('decals'), (TC[0] - 0.9, TC[1] - 1.3, 0.9405))
    # suspended halo: frames the table from above and carries its light
    mb = kit.MB(); ox, oy, wd = 2.3, 1.5, 0.12
    for sy in (-1, 1):
        mb.box((2 * ox, wd, 0.1), (0, sy * (oy - wd / 2), 0.05), L['graphite'])
        mb.box((2 * ox - 0.3, 0.04, 0.008), (0, sy * (oy - wd - 0.01), -0.003), L['diffuser_dim'])
    for sx in (-1, 1):
        mb.box((wd, 2 * oy - 2 * wd, 0.1), (sx * (ox - wd / 2), 0, 0.05), L['graphite'])
        mb.box((0.04, 2 * oy - 0.3, 0.008), (sx * (ox - wd - 0.01), 0, -0.003), L['diffuser_dim'])
    for sx in (-1, 1):
        for sy in (-1, 1): mb.cyl(0.008, H - 3.4, (sx * (ox - 0.3), sy * (oy - 0.06), 0.1 + (H - 3.4) / 2), L['graphite'], segs=8)
    kit.place(mb.build('HERO_MarsTable_Halo', hero, bevel=0.003), (*TC, 3.3))['rf_overhead'] = True

# ===================================================================== SHELL
def build_shell(L):
    col = sub('01_ARCH/MarsIntelligence')
    mats = {'floor': L['floor_epoxy'], 'wall': L['graphite'], 'ceiling': L['ceiling_acoustic'], 'glass': L['glass']}
    rf.create_room('MarsIntel', X0, X1, Y0, Y1, H, col, mats, {'S': [dict(off=7.75, **bb.DOOR1)], 'N': [dict(off=5.0, **bb.DOOR2)]},
                   ceil_col=C('ceil'))
    bpy.context.view_layer.update()
    bh.world_uv(bpy.data.objects['MarsIntel_Floor'], 4.4, ox=TC[0] - 2.2, oy=TC[1] - 2.2)    # joints line up with the table edges
    bh.world_uv(bpy.data.objects['MarsIntel_Ceiling'], 1.0)
    bpy.data.objects['MarsIntel_Ceiling']['rf_overhead'] = True
    clad = sub('01_ARCH/MarsIntelligence/Cladding')
    media = dict(L, wall_white=L['media_a'], wall_white_b=L['media_b'], wall_white_c=L['media_c'], wall_lower=L['media_b'],
                 wall_grey=L['media_a'], wall_grey_b=L['media_b'], wall_grey_c=L['media_c'])
    for nm, origin, rot, length, opens, LL in (
            ('N', (X0, Y1), 0, X1 - X0, [(4.1, 5.9, 0, 2.4)], L),                    # exit to Corridor 02, x 0
            ('S', (X1, Y0), 180, X1 - X0, [(1.65, 2.85, 0, 2.3)], L),               # from Corridor 01, x 2.75
            ('E', (X1, Y1), -90, Y1 - Y0, [], L),
            ('W', (X0, Y0), 90, Y1 - Y0, [(1.5, 10.5, 0.85, 4.05)], media)):        # terrain map recess
        kit.place(kit.cladding(f'MOD_Intel_Cladding_{nm}', length, H, LL, clad, openings=opens), (*origin, 0), rot)
    op = sub('01_ARCH/MarsIntelligence/Openings')
    room.door_portal('MOD_Intel_DoorPortal_N', 0.0, Y1, 1.8, 2.4, 'x', -1, L, op)
    room.door_portal('MOD_Intel_DoorPortal_S', 2.75, Y0, 1.2, 2.3, 'x', 1, L, op)
    bh.wall_text('Intel_HangarSign', 'T_Decal_EngineeringHangar.png', 0.16, (0.0, Y1 - 0.06, 2.72), 0)

# ================================================================= WALLS: MAP, SITES, ENV
def build_walls(L):
    hero = C('hero'); x = X0 + 0.16
    mw = kit.display_frame('HERO_TerrainMapWall', 8.6, 2.8, L['screen_dark'], L, hero, border=0.12, depth=0.14)
    kit.place(mw, (x, TC[1], 0.88), 90)
    bh.screen_quad('Intel_Map', 'T_Screen_Intel_Map.png', 8.6, 2.8, (x + 0.01, TC[1], 0.88 + 0.12 + 1.4), (math.radians(90), 0, math.radians(90)), 1.6)
    bh.wall_text('Intel_Title', 'T_Decal_MarsIntel.png', 0.2, (X0 + 0.06, TC[1] + 0.35, 4.22), 90)
    kit.decal_plane('DEC_Intel_Insignia', rm.decal('Insignia', 'T_Decal_Insignia.png'), 0.38, 0.38, C('decals'),
                    (X0 + 0.06, TC[1] - 0.75, 4.22), (math.radians(90), 0, math.radians(90)))
    p = sub('02_PROPS/MarsIntelligence')
    for k, y in (('A', 18.8), ('B', 22.0), ('C', 25.2)):                                   # along the walking path, A -> C
        room.wall_screen(L, 'Intel', f'Site{k}', f'T_Screen_Intel_Site{k}.png', 2.4, 1.5, (X1 - 0.17, y, 1.2), -90, 1.4, hero, border=0.08)
    env = rm.screen('Intel_EnvAtlas', 'T_Screen_Intel_EnvAtlas.png', 1.3); cells = room.atlas_cells(2, 1)
    for i, sx in enumerate((-3.0, 3.0)):
        fr = kit.display_frame(f'PROP_Intel_EnvScreen{i}', 2.2, 1.2, L['screen_dark'], L, p, border=0.08, depth=0.12)
        kit.place(fr, (sx, Y1 - 0.18, 1.45), 0)
        room.uv_quad(f'UI_Intel_EnvScreen{i}', env, 2.2, 1.2, cells[i], C('ui'), (sx, Y1 - 0.19, 1.45 + 0.08 + 0.6), (math.radians(90), 0, 0))

# ===================================================================== CONSOLE + DESKS
def build_console(L):
    p = sub('02_PROPS/MarsIntelligence')
    con = kit.console('HERO_LandingSystemConsole', L, C('hero'), w=1.8, dpt=0.75); kit.place(con, (*CONSOLE, 0), 0)
    bh.screen_quad('Intel_LandingSystem', 'T_Screen_Intel_LandingSystem.png', 1.5, 0.52, (CONSOLE[0], CONSOLE[1] - 0.01, 0.966),
                   (math.radians(18), 0, 0), 1.4)

def build_desks(L):
    p = sub('02_PROPS/MarsIntelligence/Desks')
    ops = rm.screen('Intel_OpsAtlas', 'T_Screen_Intel_OpsAtlas.png', 1.2); cells = room.atlas_cells(2, 2)
    desk = kit.operator_desk('PROP_Intel_AnalystDesk_0', L, p, 1.6, positions=(0.0,))
    chair = kit.task_chair('PROP_Intel_Chair_0', L, p)
    for i, (x, y, r) in enumerate(DESKS):
        o = desk if i == 0 else kit.instance(desk, f'PROP_Intel_AnalystDesk_{i}', p, (0, 0, 0)); kit.place(o, (x, y, 0), r)
        c = chair if i == 0 else kit.instance(chair, f'PROP_Intel_Chair_{i}', p, (0, 0, 0))
        f = bb.Frame(x, y, r); kit.place(c, f.at(0, -0.78), r + 180 + (5, -6, 4, -3)[i])
        for m, (lx, ly, z, rz) in enumerate(kit.desk_monitors(1.6, positions=(0.0,))):
            room.uv_quad(f'UI_Intel_Monitor_{i}{m}', ops, 0.6, 0.34, cells[(i * 2 + m) % 4], C('ui'), f.at(lx, ly, z),
                         (math.radians(90), 0, math.radians(r + rz)))

# ====================================================================== LIGHTING
def build_lighting(L):
    fx = sub('02_PROPS/MarsIntelligence/Lighting')
    src = kit.linear_light('PROP_Intel_LinearLight_E', 9.2, L, fx, drop=0.4)
    kit.place(src, (3.4, TC[1], H - 0.47), 90)['rf_overhead'] = True
    o = kit.instance(src, 'PROP_Intel_LinearLight_W', fx, (0, 0, 0)); kit.place(o, (-3.0, TC[1], H - 0.47), 90); o['rf_overhead'] = True
    col = sub('04_LIGHTS/LIGHTSET_Day_Operational/LIGHTS_MarsIntel')
    rf.create_area_light('LGT_Intel_Table', (*TC, 3.24), 3.8, 190, col, '#FFF1E2', size_y=2.2)
    rf.create_area_light('LGT_Intel_Line_E', (3.4, TC[1], H - 0.54), 0.2, 170, col, '#FFE6CC', size_y=9.0)
    rf.create_area_light('LGT_Intel_Line_W', (-3.0, TC[1], H - 0.54), 0.2, 110, col, '#FFE6CC', size_y=9.0)
    l = rf.create_area_light('LGT_Intel_Console', (1.2, 17.6, 3.9), 0.8, 90, col, '#FFF1E2', target=(*CONSOLE, 0.95))
    l.data.spread = math.radians(50)

def build_cameras():
    c = C('cams')
    rf.create_camera('CAM_MarsIntel_Entry', (2.75, 16.35, 1.7), (-1.2, 24.6, 1.2), c, lens=18)
    rf.create_camera('CAM_MarsIntel_Table', (0.55, 20.05, 1.62), (0.45, 22.6, 0.82), c, lens=22)
    rf.create_camera('CAM_MarsIntel_Sites', (1.4, 17.4, 1.7), (4.9, 23.6, 1.85), c, lens=20)

def build(L):
    before = set(bpy.data.objects.keys())
    build_shell(L); build_table(L); build_walls(L); build_console(L); build_desks(L); build_lighting(L); build_cameras()
    print('MARS_INTEL_OK objects=', room.tag_room(before, 'MarsIntel'))
