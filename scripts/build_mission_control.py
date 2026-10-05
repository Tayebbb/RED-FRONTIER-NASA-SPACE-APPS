"""
build_mission_control.py - PHASE 5: Mission Control at near-final quality, in the Hangar's visual language.

Footprint, door and glass wall come from build_blockout (the locked Phase 2 layout); desk rows, the
central aisle and the launch console keep their greybox positions. The room adds no new decision:
it confirms what the player chose upstream and holds the one remaining action, ACCEPT RISK & LAUNCH.
  walls    Hangar cladding on N / S / W (glass side). The E media wall reuses the same panel module
           in graphite, with one dark recess carrying the three displays, so the screens own the room
  floor    raised access floor, 0.6 m tiles, darker than the Hangar epoxy (the dim room)
  ceiling  dark acoustic plane, suspended linear fixtures over the desk runs
  props    two rows of operator desks (not interactable: no orange); one launch console with an
           orange strip + orange floor ring, the only interactable here
  lights   LIGHTSET_Day_Operational: dim and warm, the screens are the main light
           LIGHTSET_Launch_Mode: ambient -30 %, screens up, amber beacons on (rf_lightsets.apply)

Called by build_facility.py (needs the Hangar file state for the shared wall and helpers).
"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import rf_lib as rf, rf_kit as kit, rf_materials as rm
import build_blockout as bb
import build_hangar as bh
import rf_room as room
from rf_room import emit_states, uv_quad

X0, X1, Y0, Y1, H = bb.MC
CY = (Y0 + Y1) / 2
ROWS = (15.6, 19.0)                    # desk-row centres (x) from the greybox; operators sit west, face the wall
RUN_DY, RUN_LEN = 2.4, 3.4             # one desk run either side of the 1.4 m central aisle
LC = (21.2, CY)                        # launch console on the room axis
POSITIONS = (('FLIGHT', 'TRAJECTORY'), ('EDL', 'SURFACE'), ('POWER', 'TELECOM'), ('SCIENCE', 'MOBILITY'))
DOOR_Y, GLASS_Y = 52.6, (42.0, 50.0)   # shared-wall openings (built by the Hangar's east wall)
LAUNCH_SCALE = 1.35                    # screens up in Launch Mode
C = bh.C

def sub(path): return bh.sub(path)

def wall_screen(L, name, image, w, h, loc, facing, strength, border=0.1):
    m = room.wall_screen(L, 'MC', name, image, w, h, loc, facing, strength, sub('02_PROPS/MissionControl'), border)
    emit_states(m, strength, round(strength * LAUNCH_SCALE, 3))

# ===================================================================== SHELL
def build_shell(L):
    col = sub('01_ARCH/MissionControl')
    mats = {'floor': L['floor_access'], 'wall': L['graphite'], 'ceiling': L['ceiling_acoustic'], 'glass': L['glass']}
    rf.create_room('MissionControl', X0, X1, Y0, Y1, H, col, mats, {}, skip=('W',), ceil_col=C('ceil'))
    bpy.context.view_layer.update()
    bh.world_uv(bpy.data.objects['MissionControl_Floor'], 2.4, ox=X0, oy=Y0)      # tile joints start at the room corner
    bh.world_uv(bpy.data.objects['MissionControl_Ceiling'], 1.0)
    bpy.data.objects['MissionControl_Ceiling']['rf_overhead'] = True
    clad = sub('01_ARCH/MissionControl/Cladding')
    media = dict(L, wall_white=L['media_a'], wall_white_b=L['media_b'], wall_white_c=L['media_c'], wall_lower=L['media_b'],
                 wall_grey=L['media_a'], wall_grey_b=L['media_b'], wall_grey_c=L['media_c'])
    g0, g1 = GLASS_Y[0] - Y0, GLASS_Y[1] - Y0
    for nm, origin, rot, length, opens, LL in (
            ('N', (X0, Y1), 0, X1 - X0, [], L),
            ('S', (X1, Y0), 180, X1 - X0, [], L),
            ('W', (X0, Y0), 90, Y1 - Y0, [(g0, g1, 1.0, 3.6), (DOOR_Y - Y0 - 0.9, DOOR_Y - Y0 + 0.9, 0, 2.4)], L),   # glass + door
            ('E', (X1, Y1), -90, Y1 - Y0, [(0.5, Y1 - Y0 - 0.5, 1.3, 4.35)], media)):                               # display recess
        kit.place(kit.cladding(f'MOD_MC_Cladding_{nm}', length, H, LL, clad, openings=opens), (*origin, 0), rot)
    # glass wall, MC side: graphite reveal frame + grey panels closing the band above the glass head
    mb = kit.MB(); gx = X0 + 0.03; gm = (GLASS_Y[0] + GLASS_Y[1]) / 2; gl = GLASS_Y[1] - GLASS_Y[0]
    for z in (1.0, 3.6): mb.box((0.06, gl + 0.12, 0.06), (gx, gm, z), L['graphite'])
    for y in GLASS_Y: mb.box((0.06, 0.06, 2.66), (gx, y, 2.3), L['graphite'])
    for i in range(4):
        y0 = GLASS_Y[0] + i * gl / 4
        mb.box((0.035, gl / 4 - 0.014, H - 3.67), (X0 + 0.03, y0 + gl / 8, (3.67 + H) / 2), L[('wall_grey', 'wall_grey_b', 'wall_grey_c', 'wall_grey')[i]])
    mb.build('MOD_MC_GlassReveal', sub('01_ARCH/MissionControl/Openings'), bevel=0.004)
    mb = kit.MB()                                                                  # door portal, MC side
    for s in (-1, 1): mb.box((0.16, 0.12, 2.52), (X0 + 0.04, DOOR_Y + s * 0.96, 1.26), L['graphite'])
    mb.box((0.16, 2.04, 0.12), (X0 + 0.04, DOOR_Y, 2.46), L['graphite'])
    mb.build('MOD_MC_DoorPortal_Hangar', sub('01_ARCH/MissionControl/Openings'), bevel=0.006)
    bh.wall_text('MC_HangarSign', 'T_Decal_EngineeringHangar.png', 0.18, (X0 + 0.06, DOOR_Y, 2.85), 90)

# ================================================================= MEDIA WALL
def build_media_wall(L):
    hero = C('hero'); x = X1 - 0.16; z0 = 1.35; W, Hs = 7.2, 2.7
    dw = kit.display_frame('HERO_MissionControlWall', W, Hs, L['screen_dark'], L, hero, border=0.12, depth=0.14)
    kit.place(dw, (x, CY, z0), -90)
    bh.screen_quad('MissionControlWall', 'T_Screen_MC_Main.png', W, Hs, (x - 0.01, CY, z0 + 0.12 + Hs / 2), (math.radians(90), 0, math.radians(-90)), 1.8)
    emit_states(bpy.data.materials['MAT_Screen_MissionControlWall'], 1.8, round(1.8 * LAUNCH_SCALE, 3))
    for nm, img, dy in (('GoNoGo', 'T_Screen_MC_GoNoGo.png', 4.7), ('Readiness', 'T_Screen_MC_Readiness.png', -4.7)):
        wall_screen(L, nm, img, 1.3, Hs, (x + 0.02, CY + dy, z0 + 0.04), -90, 1.5, border=0.08)
    bh.wall_text('MC_Title', 'T_Decal_MissionControl.png', 0.26, (X1 - 0.06, CY - 0.45, 4.62), -90)
    kit.decal_plane('DEC_MC_Insignia', rm.decal('Insignia', 'T_Decal_Insignia.png'), 0.5, 0.5, C('decals'),
                    (X1 - 0.06, CY + 0.95, 4.62), (math.radians(90), 0, math.radians(-90)))
    src = kit.warning_beacon('PROP_MC_Beacon_S', L, sub('02_PROPS/MissionControl'))
    for i, y in enumerate((Y0 + 0.3, Y1 - 0.3)):
        o = src if i == 0 else kit.instance(src, 'PROP_MC_Beacon_N', sub('02_PROPS/MissionControl'), (0, 0, 0))
        kit.place(o, (X1 - 0.05, y, 4.5), -90)
    emit_states(L['beacon'], 0.05, 9.0)

# ====================================================================== SIDE WALLS
def build_side_screens(L):
    x = 17.3                                                         # between the rows: operators see them by turning
    wall_screen(L, 'RoverBuild', 'T_Screen_MC_Rover.png', 2.0, 1.125, (x, Y1 - 0.18, 1.35), 0, 1.4)
    wall_screen(L, 'Landing', 'T_Screen_MC_Landing.png', 2.0, 1.125, (x, Y0 + 0.18, 1.35), 180, 1.4)

# ========================================================================= DESKS
def build_desks(L):
    p = sub('02_PROPS/MissionControl/Desks')
    ops = emit_states(rm.screen('MC_OpsAtlas', 'T_Screen_MC_OpsAtlas.png', 1.2), 1.2, round(1.2 * LAUNCH_SCALE, 3))
    desk = kit.operator_desk('PROP_MC_OperatorDesk_0', L, p, RUN_LEN)
    chair = kit.task_chair('PROP_MC_Chair_0', L, p)
    cells = [((k % 2) * 0.5, 0.5 - (k // 2) * 0.5, (k % 2) * 0.5 + 0.5, 1.0 - (k // 2) * 0.5) for k in range(4)]
    jitter = (6, -4, 3, -7, 5, -2, 8, -5)
    n = 0
    for r, x in enumerate(ROWS):
        for s, dy in enumerate((-RUN_DY, RUN_DY)):
            i = r * 2 + s; y = CY + dy
            o = desk if i == 0 else kit.instance(desk, f'PROP_MC_OperatorDesk_{i}', p, (0, 0, 0))
            kit.place(o, (x, y, 0), -90)
            f = bb.Frame(x, y, -90)
            for m, (lx, ly, z, rz) in enumerate(kit.desk_monitors(RUN_LEN)):
                uv_quad(f'UI_MC_Monitor_{i}{m}', ops, 0.6, 0.34, cells[(i + m * 3) % 4], C('ui'), f.at(lx, ly, z),
                        (math.radians(90), 0, math.radians(-90 + rz)))
            for k, px in enumerate((-0.85, 0.85)):
                pos = POSITIONS[i][k]
                bh.atlas_plane(f'DEC_MC_Position_{pos}', f'POS_{pos}', 0.1, f.at(px, 0.85 / 2 - 0.152, 0.8), (math.radians(90), 0, math.radians(-90)))
                c = chair if n == 0 else kit.instance(chair, f'PROP_MC_Chair_{n}', p, (0, 0, 0))
                kit.place(c, f.at(px, -0.78), 90 + jitter[n]); n += 1

# =================================================================== LAUNCH CONSOLE
def build_launch_console(L):
    """The room's single interactable: graphite plinth, orange floor ring, console with screen and guarded button."""
    hero = C('hero'); mb = kit.MB(); w, dpt, h, z0 = 2.0, 0.8, 1.0, 0.06; t = math.radians(18)
    mb.cyl(0.95, z0, (0, 0, z0 / 2), L['graphite'], segs=64)                                # plinth
    mb.ring(1.22, 1.28, 0.006, 0.0, L['orange_led'], segs=96)                                # floor ring: stand here
    mb.box((w - 0.12, dpt - 0.14, 0.09), (0, 0.03, z0 + 0.045), L['backer'])                   # recessed kick
    mb.box((w, dpt, h - 0.14), (0, 0, z0 + 0.09 + (h - 0.14) / 2), L['painted'])              # body
    mb.box((w + 0.02, dpt + 0.04, 0.05), (0, 0, z0 + h - 0.025), L['graphite'], rot=(t, 0, 0))  # deck, low front
    mb.box((1.56, dpt - 0.22, 0.012), (-0.18, -0.01, z0 + h + 0.002), L['screen_dark'], rot=(t, 0, 0))
    bx = 0.75; bz = z0 + h + 0.004                                                             # guarded launch button
    for dx, dy, sx, sy in ((0, -0.11, 0.24, 0.025), (0, 0.11, 0.24, 0.025), (-0.11, 0, 0.025, 0.2), (0.11, 0, 0.025, 0.2)):
        mb.box((sx, sy, 0.035), (bx + dx, dy, bz + 0.0175 + dy * math.tan(t)), L['yellow'], rot=(t, 0, 0))   # hazard guard
    mb.box((0.13, 0.13, 0.03), (bx, 0, bz + 0.015), L['orange_led'], rot=(t, 0, 0))
    mb.box((w - 0.2, 0.012, 0.025), (0, -dpt / 2 - 0.003, z0 + h - 0.16), L['orange_led'])     # interact strip
    for i, x in enumerate((-w / 2 + 0.12, -w / 2 + 0.2)):
        mb.cyl(0.008, 0.01, (x, -dpt / 2 - 0.004, z0 + h - 0.26), L['status_cyan'] if i == 0 else L['status_amber'], segs=10, axis='Y')
    mb.box((1.3, 0.01, 0.16), (0, -dpt / 2 - 0.005, z0 + 0.55), L['graphite'])                 # label band
    o = mb.build('HERO_LaunchConsole', hero, bevel=0.006)
    kit.place(o, (*LC, 0), -90)
    f = bb.Frame(*LC, -90)
    bh.screen_quad('LaunchConsole', 'T_Screen_MC_Launch.png', 1.5, 0.556, f.at(-0.18, -0.01, z0 + h + 0.016), (t, 0, math.radians(-90)), 1.5)
    m = emit_states(bpy.data.materials['MAT_Screen_LaunchConsole'], 1.5, round(1.5 * LAUNCH_SCALE, 3))
    bsdf = m.node_tree.nodes['Principled BSDF']                        # emit only: the room's light no longer washes it out
    for link in list(bsdf.inputs['Base Color'].links): m.node_tree.links.remove(link)
    bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
    bh.wall_text('LaunchAuthority', 'T_Decal_LaunchAuthority.png', 0.07, f.at(0, -dpt / 2 - 0.011, z0 + 0.55), -90)
    rf.create_marker('INT_LaunchConsole', (LC[0] - 1.0, CY, 0), C('game'), 'SINGLE_ARROW', 0.6)

# ========================================================================= PROPS
def build_props(L):
    p = sub('02_PROPS/MissionControl')
    mb = kit.MB(); ln = GLASS_Y[1] - GLASS_Y[0] - 0.6                                         # observation ledge under the glass
    mb.box((ln - 0.1, 0.3, 0.08), (0, 0.05, 0.04), L['backer'])
    mb.box((ln, 0.36, 0.84), (0, 0.02, 0.08 + 0.42), L['painted'])
    mb.box((ln + 0.04, 0.44, 0.04), (0, -0.01, 0.94), L['graphite'])
    mb.box((ln + 0.04, 0.012, 0.02), (0, -0.234, 0.93), L['brushed'])
    kit.place(mb.build('PROP_MC_ObservationLedge', p, bevel=0.005), (X0 + 0.22, (GLASS_Y[0] + GLASS_Y[1]) / 2, 0), 90)
    cab = kit.cabinet('PROP_MC_Cabinet_0', L, p)
    for i, x in enumerate((11.4, 12.25)):
        o = cab if i == 0 else kit.instance(cab, f'PROP_MC_Cabinet_{i}', p, (0, 0, 0))
        kit.place(o, (x, Y0 + 0.32, 0), 180)
        bh.atlas_plane(f'DEC_MC_Cabinet_EQ1{i + 1}', f'EQ1{i + 1}', 0.11, (x, Y0 + 0.32 + 0.316, 1.72), (math.radians(90), 0, math.radians(180)))
    fx = sub('02_PROPS/MissionControl/Lighting')
    src = kit.linear_light('PROP_MC_LinearLight_S', 7.4, L, fx, drop=0.42)
    for i, dy in enumerate((-RUN_DY, RUN_DY)):
        o = src if i == 0 else kit.instance(src, 'PROP_MC_LinearLight_N', fx, (0, 0, 0))
        kit.place(o, ((ROWS[0] + ROWS[1]) / 2, CY + dy, H - 0.49)); o['rf_overhead'] = True
    o = kit.instance(src, 'PROP_MC_LinearLight_Back', fx, (0, 0, 0)); kit.place(o, (11.4, CY, H - 0.49), 90); o['rf_overhead'] = True
    emit_states(L['diffuser_dim'], 1.6, 1.1)                                                    # ambient -30 % in Launch Mode

# ====================================================================== LIGHTING
def build_lighting():
    day = sub('04_LIGHTS/LIGHTSET_Day_Operational/LIGHTS_MissionControl_Day')
    launch = sub('04_LIGHTS/LIGHTSET_Launch_Mode')
    mx = (ROWS[0] + ROWS[1]) / 2; tgt = (LC[0] - 0.45, LC[1], 0.55)     # the console front, not its screen (no washout)
    rig = [('LGT_MC_Linear_S', (mx, CY - RUN_DY, H - 0.56), 7.0, 230, '#FFE6CC', None, 0.2, None),
           ('LGT_MC_Linear_N', (mx, CY + RUN_DY, H - 0.56), 7.0, 230, '#FFE6CC', None, 0.2, None),
           ('LGT_MC_Back',     (11.4, CY, H - 0.56), 0.2, 120, '#FFE6CC', None, 7.0, None),
           ('LGT_MC_Launch_Key', (19.6, CY - 1.4, H - 0.3), 1.0, 85, '#FFF1E2', tgt, None, 45)]
    for col, scale, sfx in ((day, 1.0, ''), (launch, 0.7, '_LM')):
        for nm, loc, size, watts, colr, target, size_y, spread in rig:
            w = watts * (1.25 if (sfx and nm == 'LGT_MC_Launch_Key') else scale)              # the console stays lit
            l = rf.create_area_light(nm + sfx, loc, size, w, col, colr, target=target, size_y=size_y)
            if spread: l.data.spread = math.radians(spread)
    for i, y in enumerate((Y0 + 0.3, Y1 - 0.3)):                                               # beacon glow, launch only
        l = bpy.data.lights.new(f'LGT_MC_Beacon{i}_LM', 'POINT'); l.energy = 25; l.color = rf.hex_rgb('#FFB43A')[:3]; l.shadow_soft_size = 0.08
        o = bpy.data.objects.new(f'LGT_MC_Beacon{i}_LM', l); o.location = (X1 - 0.17, y, 4.66); launch.objects.link(o)
    for o in launch.objects: o.hide_render = True; o.hide_viewport = True

def build_cameras():
    c = C('cams')
    rf.create_camera('CAM_MissionControl_Entry',  (9.9, 53.0, 1.7), (22.0, 46.8, 1.9), c, lens=20)
    rf.create_camera('CAM_MissionControl_Launch', (19.25, 46.5, 1.8), (23.6, 48.3, 1.55), c, lens=22)
    rf.create_camera('CAM_MissionControl_Glass',  (23.3, 43.0, 2.4), (9.0, 48.0, 1.6), c, lens=22)

def build(L):
    before = set(bpy.data.objects.keys())
    build_shell(L); build_media_wall(L); build_side_screens(L); build_desks(L)
    build_launch_console(L); build_props(L); build_lighting(); build_cameras()
    print('MISSION_CONTROL_OK objects=', room.tag_room(before, 'MissionControl'))   # ownership: export never splits by position alone
