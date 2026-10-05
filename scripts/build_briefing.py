"""
build_briefing.py - PHASE 5: the Briefing room at near-final quality, in the Hangar's visual language.

The first room: the question, the constraints and the route. No decision is made here; the mission
table is the one interactable ("read, then proceed"). Footprint, doors, display, table and seat
positions come from build_blockout.
  walls    Hangar cladding on S / W / E; the N wall carries the briefing display, so it is a graphite
           media wall (rule from Mission Control / Mars Intelligence). The display is 0.8 m narrower
           than the greybox so it clears the exit portal
  exit     the way on (to Mars Intelligence) gets an orange LED reveal: orange = the mission path
  identity the program board on the E wall: graphite panel, insignia, white type (never white on white)
  floor    Hangar epoxy; ceiling dark acoustic with two linear lines
Called by build_facility.py.
"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import rf_lib as rf, rf_kit as kit, rf_materials as rm
import build_blockout as bb
import build_hangar as bh
import rf_room as room

X0, X1, Y0, Y1, H = bb.BRIEF
DX = -0.6                                  # display + table axis (greybox)
TABLE = (-0.6, 6.9)
EXIT_X, ENTRY_X = 2.75, 0.0
SEATS = ((-3.1, 4.9), (-2.3, 4.7), (-1.5, 4.6), (0.9, 4.6), (1.7, 4.7), (2.5, 4.9))   # split by the aisle at x 0
C = bh.C

def sub(path): return bh.sub(path)

# ===================================================================== SHELL
def build_shell(L):
    col = sub('01_ARCH/Briefing')
    mats = {'floor': L['floor_epoxy'], 'wall': L['graphite'], 'ceiling': L['ceiling_acoustic'], 'glass': L['glass']}
    rf.create_room('Briefing', X0, X1, Y0, Y1, H, col, mats, {'S': [dict(off=4.0, **bb.DOOR2)], 'N': [dict(off=6.75, **bb.DOOR1)]},
                   ceil_col=C('ceil'))
    bpy.context.view_layer.update()
    bh.world_uv(bpy.data.objects['Briefing_Floor'], 4.4, ox=-2.2, oy=Y0)
    bh.world_uv(bpy.data.objects['Briefing_Ceiling'], 1.0)
    bpy.data.objects['Briefing_Ceiling']['rf_overhead'] = True
    clad = sub('01_ARCH/Briefing/Cladding')
    media = dict(L, wall_white=L['media_a'], wall_white_b=L['media_b'], wall_white_c=L['media_c'], wall_lower=L['media_b'],
                 wall_grey=L['media_a'], wall_grey_b=L['media_b'], wall_grey_c=L['media_c'])
    for nm, origin, rot, length, opens, LL in (
            ('N', (X0, Y1), 0, X1 - X0, [(0.8, 6.0, 0.95, 3.55), (EXIT_X - X0 - 0.6, EXIT_X - X0 + 0.6, 0, 2.3)], media),
            ('S', (X1, Y0), 180, X1 - X0, [(X1 - ENTRY_X - 0.9, X1 - ENTRY_X + 0.9, 0, 2.4)], L),   # facility entry
            ('W', (X0, Y0), 90, Y1 - Y0, [], L),
            ('E', (X1, Y1), -90, Y1 - Y0, [], L)):
        kit.place(kit.cladding(f'MOD_Brief_Cladding_{nm}', length, H, LL, clad, openings=opens), (*origin, 0), rot)
    op = sub('01_ARCH/Briefing/Openings')
    room.door_portal('MOD_Brief_DoorPortal_Entry', ENTRY_X, Y0, 1.8, 2.4, 'x', 1, L, op)
    room.door_portal('MOD_Brief_DoorPortal_Exit', EXIT_X, Y1, 1.2, 2.3, 'x', -1, L, op)
    mb = kit.MB(); y = Y1 - 0.126                                                    # orange reveal: the way on
    for s in (-1, 1): mb.box((0.025, 0.012, 2.3), (EXIT_X + s * 0.63, y, 1.15), L['orange_led'])
    mb.box((1.285, 0.012, 0.025), (EXIT_X, y, 2.335), L['orange_led'])
    mb.build('DEC_Brief_ExitReveal', op, bevel=0)
    bh.wall_text('Brief_ExitSign', 'T_Decal_MarsIntel.png', 0.13, (EXIT_X, Y1 - 0.06, 2.62), 0)

# ===================================================================== DISPLAY + TABLE
def build_display(L):
    hero = C('hero'); y = Y1 - 0.16; W, Hs, z0 = 4.8, 2.25, 1.0
    d = kit.display_frame('HERO_BriefingDisplay', W, Hs, L['screen_dark'], L, hero, border=0.12, depth=0.14)
    kit.place(d, (DX, y, z0), 0)
    bh.screen_quad('BriefingDisplay', 'T_Screen_Brief_Main.png', W, Hs, (DX, y - 0.01, z0 + 0.12 + Hs / 2), (math.radians(90), 0, 0), 1.7)
    bh.wall_text('Brief_Title', 'T_Decal_Briefing.png', 0.17, (DX + 0.2, Y1 - 0.06, 3.76), 0)
    kit.decal_plane('DEC_Brief_Insignia', rm.decal('Insignia', 'T_Decal_Insignia.png'), 0.3, 0.3, C('decals'),
                    (DX - 0.75, Y1 - 0.06, 3.76), (math.radians(90), 0, 0))

def build_table(L):
    """Standing mission table: satin body, graphite top with a flat display, orange strip = interactable."""
    mb = kit.MB(); w, dpt, h = 3.8, 1.3, 0.94
    mb.box((w - 0.16, dpt - 0.16, 0.09), (0, 0, 0.045), L['backer'])
    mb.box((w, dpt, h - 0.13), (0, 0, 0.09 + (h - 0.13) / 2), L['painted'])
    mb.box((w + 0.04, dpt + 0.04, 0.04), (0, 0, h - 0.02), L['graphite'])
    mb.box((3.44, 0.94, 0.006), (0, 0, h + 0.003), L['screen_dark'])
    mb.box((w - 0.4, 0.012, 0.025), (0, -dpt / 2 - 0.003, h - 0.14), L['orange_led'])
    for i, x in enumerate((-w / 2 + 0.12, -w / 2 + 0.2)):
        mb.cyl(0.008, 0.01, (x, -dpt / 2 - 0.004, h - 0.24), L['status_cyan'] if i == 0 else L['status_amber'], segs=10, axis='Y')
    kit.place(mb.build('HERO_Briefing_MissionTable', C('hero'), bevel=0.006), (*TABLE, 0))
    bh.screen_quad('BriefingTable', 'T_Screen_Brief_Table.png', 3.4, 0.9, (*TABLE, h + 0.008), (0, 0, 0), 1.3)

# ===================================================================== WALLS + SEATS
def build_walls(L):
    p = sub('02_PROPS/Briefing')
    ctx = rm.screen('Brief_ContextAtlas', 'T_Screen_Brief_ContextAtlas.png', 1.3); cells = room.atlas_cells(2, 1)
    for i, y in enumerate((3.5, 6.8)):
        fr = kit.display_frame(f'PROP_Brief_ContextScreen{i}', 1.8, 1.0, L['screen_dark'], L, p, border=0.08, depth=0.12)
        kit.place(fr, (X0 + 0.17, y, 1.4), 90)
        room.uv_quad(f'UI_Brief_ContextScreen{i}', ctx, 1.8, 1.0, cells[i], C('ui'), (X0 + 0.18, y, 1.4 + 0.08 + 0.5),
                     (math.radians(90), 0, math.radians(90)))
    by, bz = 5.0, 1.8                                                                     # program board, E wall
    board = kit.MB().box((0.05, 3.0, 1.8), (0, 0, 0), L['graphite'])
    kit.place(board.build('PROP_Brief_ProgramBoard', p, bevel=0.006), (X1 - 0.075, by, bz), 0)
    face = X1 - 0.103
    kit.decal_plane('DEC_Brief_ProgramInsignia', rm.decal('Insignia', 'T_Decal_Insignia.png'), 0.75, 0.75, C('decals'),
                    (face, by, bz + 0.35), (math.radians(90), 0, math.radians(-90)))
    bh.wall_text('Brief_Program', 'T_Decal_Program.png', 0.16, (face, by, bz - 0.28), -90)
    bh.wall_text('Brief_ProgramSub', 'T_Decal_ProgramSub.png', 0.085, (face, by, bz - 0.52), -90)

def build_seats(L):
    p = sub('02_PROPS/Briefing/Seats')
    chair = kit.task_chair('PROP_Brief_Chair_0', L, p)
    for i, (x, y) in enumerate(SEATS):
        o = chair if i == 0 else kit.instance(chair, f'PROP_Brief_Chair_{i}', p, (0, 0, 0))
        tx, ty = DX - x, (Y1 - 0.2) - y                                                 # face the display
        kit.place(o, (x, y, 0), math.degrees(math.atan2(tx, -ty)))

# ===================================================================== LIGHTING + CAMERAS
def build_lighting(L):
    fx = sub('02_PROPS/Briefing/Lighting')
    src = kit.linear_light('PROP_Brief_LinearLight_W', 7.4, L, fx, drop=0.33)
    kit.place(src, (-2.4, 5.0, H - 0.4), 90)['rf_overhead'] = True
    o = kit.instance(src, 'PROP_Brief_LinearLight_E', fx, (0, 0, 0)); kit.place(o, (1.6, 5.0, H - 0.4), 90); o['rf_overhead'] = True
    col = sub('04_LIGHTS/LIGHTSET_Day_Operational/LIGHTS_Briefing')
    for nm, x in (('W', -2.4), ('E', 1.6)):
        rf.create_area_light(f'LGT_Brief_Line_{nm}', (x, 5.0, H - 0.47), 0.2, 130, col, '#FFE6CC', size_y=7.0)
    l = rf.create_area_light('LGT_Brief_Table', (0.4, 4.6, 3.7), 1.2, 80, col, '#FFF1E2', target=(TABLE[0], TABLE[1] - 0.66, 0.5))   # onto the front, not the screen
    l.data.spread = math.radians(50)
    l = rf.create_area_light('LGT_Brief_Board', (1.6, 5.0, 3.6), 0.8, 70, col, '#FFF1E2', target=(X1, 5.0, 1.6)); l.data.spread = math.radians(40)

def build_cameras():
    c = C('cams')
    rf.create_camera('CAM_Briefing_Table', (0.3, 5.2, 1.65), (-0.6, 8.6, 1.3), c, lens=22)
    rf.create_camera('CAM_Briefing_Exit', (-3.0, 3.0, 1.7), (2.75, 10.0, 1.6), c, lens=20)
    rf.create_camera('CAM_Briefing_Board', (-1.6, 3.0, 1.7), (4.0, 5.3, 1.65), c, lens=24)

def build(L):
    before = set(bpy.data.objects.keys())
    build_shell(L); build_display(L); build_table(L); build_walls(L); build_seats(L); build_lighting(L); build_cameras()
    print('BRIEFING_OK objects=', room.tag_room(before, 'Briefing'))
