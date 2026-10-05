"""
build_blockout.py - PHASE 2 greybox of the Red Frontier facility.

Flow (south -> north, then east):
  Briefing (8x10x4) -> C1 -> Mars Intelligence (10x12x4.5) -> C2 -> Engineering Hangar
  (18x22x10) -> Mission Control (15x12x5, east of the Hangar behind a glass wall).

Everything is plain boxes/cylinders on purpose: this file answers layout, scale, sight
lines and player flow. Detail comes in later phases. Safe to rerun (rebuilds from empty).

Run:  blender -b --factory-startup --python scripts/build_blockout.py
"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import rf_lib as rf
from rf_lib import create_box as box, create_panel as panel, create_text_placeholder as text
from mathutils import Vector, Matrix

def setup():
    """Fresh scene, collection tree and greybox materials (globals C, M)."""
    global sc, C, M
    sc = rf.reset_scene()

    # ------------------------------------------------------------------ collections
    C = {k: rf.collection(p) for k, p in {
        'ref':      'RF_FACILITY/00_REFERENCE',
        'brief':    'RF_FACILITY/01_ARCH/Briefing',
        'intel':    'RF_FACILITY/01_ARCH/MarsIntelligence',
        'hangar':   'RF_FACILITY/01_ARCH/Hangar',
        'mc':       'RF_FACILITY/01_ARCH/MissionControl',
        'corr':     'RF_FACILITY/01_ARCH/Corridor',
        'ceil':     'RF_FACILITY/01_ARCH/Ceilings',
        'props':    'RF_FACILITY/02_PROPS',
        'hero':     'RF_FACILITY/03_HERO',
        'lights':   'RF_FACILITY/04_LIGHTS',
        'cams':     'RF_FACILITY/05_CAMERAS',
        'decals':   'RF_FACILITY/06_DECALS',
        'ui':       'RF_FACILITY/07_UI_PLACEHOLDERS',
        'game':     'RF_FACILITY/08_GAMEPLAY_MARKERS',
        'debug':    'RF_FACILITY/99_DEBUG',
    }.items()}

    # ------------------------------------------------------------- greybox materials
    M = {
        'floor':     rf.create_material('GB_Floor', '#7d8085', rough=0.85),
        'wall':      rf.create_material('GB_Wall', '#d6d4ce', rough=0.8),          # warm off-white
        'wall_cool': rf.create_material('GB_Wall_Cool', '#c3c6c9', rough=0.8),     # cool light grey (hangar)
        'ceiling':   rf.create_material('GB_Ceiling', '#e2e1dc', rough=0.9),
        'struct':    rf.create_material('GB_Structure', '#3a3d42', rough=0.6),     # graphite
        'navy':      rf.create_material('GB_Navy', '#243044', rough=0.7),
        'prop':      rf.create_material('GB_Prop', '#9ea1a6', rough=0.7),
        'prop_dark': rf.create_material('GB_Prop_Dark', '#4a4e55', rough=0.7),
        'hero':      rf.create_material('GB_Hero', '#b6b9bd', rough=0.6),
        'orange':    rf.create_material('GB_Orange', '#c2501c', rough=0.5, emit='#c2501c', emit_strength=0.0),
        'orange_lit':rf.create_material('GB_Orange_Lit', '#e0662a', emit='#f07a45', emit_strength=3.0),
        'amber':     rf.create_material('GB_Amber', '#e3a928', rough=0.6),
        'screen':    rf.create_material('GB_Screen_Info', '#2a6fa8', emit='#74b6ff', emit_strength=2.0),
        'screen_w':  rf.create_material('GB_Screen_White', '#dfe6ee', emit='#e7ecf5', emit_strength=2.0),
        'screen_off':rf.create_material('GB_Screen_Dark', '#121418', rough=0.2),
        'mars':      rf.create_material('GB_Mars_Terrain', '#9a4b2e', rough=0.9),
        'glass':     rf.create_material('GB_Glass', '#a9c3cf', rough=0.05, alpha=0.25),
        'human':     rf.create_material('REF_Human', '#3d8f5a', rough=0.7),
        'label':     rf.create_material('GB_Label_Dark', '#2b2e33', rough=0.6),
        'label_w':   rf.create_material('GB_Label_White', '#f2f2ee', rough=0.6),
    }
ROOM_M = lambda wall: {'floor': M['floor'], 'wall': wall, 'ceiling': M['ceiling'], 'glass': M['glass']}
DOOR1 = dict(w=1.2, h=2.3)      # single door  (1.1 m clear + frame)
DOOR2 = dict(w=1.8, h=2.4)      # double door
DOORH = dict(w=2.6, h=2.9)      # hangar personnel entry (wide, on the rover axis)

def overhead(obj):
    """Tag objects hidden in plan / cutaway renders."""
    obj['rf_overhead'] = True
    return obj

# ======================================================================= LAYOUT
# Interior footprints (x0, x1, y0, y1, height)
BRIEF = (-4.0, 4.0, 0.0, 10.0, 4.0)
C1    = (1.25, 4.25, 10.25, 15.75, 3.2)
INTEL = (-5.0, 5.0, 16.0, 28.0, 4.5)
C2    = (-1.5, 1.5, 28.25, 32.75, 3.2)
HANG  = (-9.0, 9.0, 33.0, 55.0, 10.0)
MC    = (9.25, 24.25, 41.75, 53.75, 5.0)
ROVER = (0.0, 42.6)            # platform centre (pulled toward the entry so the rover dominates)
PLAT_R, PLAT_H = 3.25, 0.12     # Ø6.5 m turntable with a 12 cm lip: a work bay, not a pedestal

def room(name, fp, col, wall_mat, openings, skip=()):
    x0, x1, y0, y1, h = fp
    rf.create_room(name, x0, x1, y0, y1, h, col, ROOM_M(wall_mat), openings, skip, ceil_col=C['ceil'])
    for o in bpy.data.objects:
        if o.name.endswith('_Ceiling'): overhead(o)

# ------------------------------------------------------------------ architecture
def build_shells(hangar=True, skip=()):
    """Room shells. hangar=False / skip=(room, ...) leave those rooms to their near-final builders."""
    if 'Briefing' not in skip:
        room('Briefing', BRIEF, C['brief'], M['wall'], {
            'S': [dict(off=4.0, **DOOR2)],                   # facility entry
            'N': [dict(off=6.75, **DOOR1)]})                 # exit -> C1 (x = 2.75)
    if 'Corridor01' not in skip: room('Corridor01', C1, C['corr'], M['wall'], {}, skip=('N', 'S'))
    if 'MarsIntel' not in skip:
        room('MarsIntel', INTEL, C['intel'], M['wall'], {
            'S': [dict(off=7.75, **DOOR1)],                  # from C1 (x = 2.75)
            'N': [dict(off=5.0, **DOOR2)]})                  # exit -> C2 (x = 0)
    if 'Corridor02' not in skip: room('Corridor02', C2, C['corr'], M['wall'], {}, skip=('N', 'S'))
    if hangar:
        room('Hangar', HANG, C['hangar'], M['wall_cool'], {
            'S': [dict(off=9.0, **DOORH)],                                       # entry on rover axis
            'W': [dict(off=11.0, w=8.0, h=7.0)],                                 # MOD_HangarDoor (rover exit)
            'E': [dict(off=13.0, w=8.0, h=2.6, sill=1.0, glass=True),            # Mission Control glass wall
                  dict(off=19.6, **DOOR2)]})                                     # -> Mission Control
    if 'MissionControl' not in skip:
        room('MissionControl', MC, C['mc'], M['navy'], {}, skip=('W',))

# ============================================================== 01 BRIEFING ROOM
def build_briefing():
    col, ui = C['brief'], C['ui']
    disp_x = -0.6
    rf.create_emissive_screen('HERO_BriefingDisplay', 5.6, 2.6, (disp_x, 9.93, 1.1), 'S', C['hero'], M['screen_w'], M['struct'])
    text('UI_Briefing_Title', 'MISSION: RED FRONTIER', (disp_x, 9.85, 2.75), 'S', 0.32, ui, M['label'])
    text('UI_Briefing_Sub', 'objective  |  science goal  |  context', (disp_x, 9.85, 2.15), 'S', 0.16, ui, M['label'])
    # mission table under the display: a working briefing, not a lecture
    box('HERO_Briefing_MissionTable', (3.8, 1.3, 0.76), (disp_x, 6.9, 0), C['hero'], M['struct'], bevel=0.03)
    box('HERO_Briefing_MissionTable_Top', (3.5, 1.0, 0.02), (disp_x, 6.9, 0.76), C['hero'], M['screen'])
    # one shallow arc of six seats, split by the path to the table
    for i, (x, y, r) in enumerate(((-3.1, 4.9, -14), (-2.3, 4.7, -8), (-1.5, 4.6, -3), (0.9, 4.6, 3), (1.7, 4.7, 8), (2.5, 4.9, 14))):
        box(f'PROP_Briefing_Chair{i}', (0.55, 0.55, 0.9), (x, y, 0), C['props'], M['prop_dark'], rot_z=r, bevel=0.02)
    for i, y in enumerate((3.5, 6.8)):                              # context screens, west wall
        rf.create_emissive_screen(f'UI_Briefing_Side{i}', 1.8, 1.0, (-3.96, y, 1.5), 'E', ui, M['screen'], M['struct'])
    # exit door framed in orange: the room points you onward
    for nm, sz, loc in (('L', (0.08, 0.06, 2.4), (2.11, 9.97, 0)), ('R', (0.08, 0.06, 2.4), (3.39, 9.97, 0)), ('T', (1.36, 0.06, 0.08), (2.75, 9.97, 2.36))):
        box(f'DEC_Briefing_ExitFrame_{nm}', sz, loc, C['decals'], M['orange_lit'])
    text('DEC_Briefing_ExitSign', 'MARS INTELLIGENCE', (2.75, 9.95, 2.75), 'S', 0.14, C['decals'], M['label'])

# ========================================================== 02 MARS INTELLIGENCE
def build_intel():
    ui = C['ui']
    # planning table: recessed terrain inside a raised data rim (walk-around, waist height)
    box('HERO_MarsTable_Base', (4.4, 2.8, 0.8), (0, 22.0, 0), C['hero'], M['struct'], bevel=0.03)
    box('HERO_MarsTable_Terrain', (4.0, 2.4, 0.04), (0, 22.0, 0.8), C['hero'], M['mars'])
    for nm, sz, loc in (('S', (4.4, 0.2, 0.14), (0, 20.7, 0.8)), ('N', (4.4, 0.2, 0.14), (0, 23.3, 0.8)),
                        ('W', (0.2, 2.4, 0.14), (-2.1, 22.0, 0.8)), ('E', (0.2, 2.4, 0.14), (2.1, 22.0, 0.8))):
        box(f'HERO_MarsTable_Rim{nm}', sz, loc, C['hero'], M['struct'])
    box('HERO_MarsTable_DataEdge', (4.0, 0.02, 0.05), (0, 20.79, 0.88), C['hero'], M['screen'])        # data strip facing the player
    # three illuminated landing-site markers; C is the risky site (precision landing only)
    for s, (x, y, c) in {'A': (-1.2, 21.5, M['screen']), 'B': (0.4, 22.6, M['screen']), 'C': (1.3, 21.5, M['amber'])}.items():
        rf.create_floor_ring(f'HERO_MarsTable_Site{s}', 0.17, 0.035, (x, y, 0.84), C['hero'], c, segs=32)
        rf.create_cylinder(f'HERO_MarsTable_Site{s}_Core', 0.05, 0.015, (x, y, 0.84), C['hero'], c, verts=16)
        text(f'UI_MarsTable_Site{s}', s, (x, y + 0.32, 0.9), 'N', 0.2, ui, M['label_w'], flat=True)
    # landing-system selector: decide the technology first, then the reachable sites
    con = box('HERO_LandingSystemConsole', (1.6, 0.6, 0.95), (0, 19.0, 0), C['hero'], M['prop'], bevel=0.02)
    lip = box('HERO_LandingSystemConsole_Interact', (1.4, 0.02, 0.03), (0, 0, 0), C['hero'], M['orange_lit']); lip.parent = con; lip.location = (0, -0.31, 0.88)
    text('UI_LandingSystem', 'LANDING SYSTEM:  STANDARD  |  PRECISION', (0, 18.68, 1.12), 'S', 0.075, ui, M['label'])
    rf.create_emissive_screen('HERO_TerrainMapWall', 8.6, 2.8, (-4.96, 22.0, 1.0), 'E', C['hero'], M['mars'], M['struct'])
    text('UI_TerrainMap_Title', 'JEZERO REGION  |  ELEVATION / SLOPE / GEOLOGY', (-4.9, 22.0, 4.05), 'E', 0.17, ui, M['label'])
    for i, (s, y, note) in enumerate((('A', 18.8, 'standard landing'), ('B', 22.0, 'standard landing'), ('C', 25.2, 'REQUIRES PRECISION LANDING'))):
        rf.create_emissive_screen(f'HERO_LandingSite{s}', 2.4, 1.5, (4.96, y, 1.3), 'W', C['hero'], M['amber'] if s == 'C' else M['screen'], M['struct'])
        text(f'UI_LandingSite{s}', f'SITE {s}', (4.9, y, 3.2), 'W', 0.32, ui, M['label'])
        text(f'UI_LandingSite{s}_Req', note, (4.9, y, 2.95), 'W', 0.09, ui, M['label'])
    for i, x in enumerate((-3.0, 3.0)):                                             # env data screens, north wall
        rf.create_emissive_screen(f'UI_Intel_EnvData{i}', 2.2, 1.2, (x, 27.93, 1.6), 'S', ui, M['screen'], M['struct'])
    for i, (x, y, r) in enumerate(((-3.6, 17.4, 0), (-1.4, 17.4, 0), (3.9, 26.6, 180), (-3.9, 26.6, 180))):   # analyst stations
        box(f'PROP_Intel_Desk{i}', (1.6, 0.75, 0.75), (x, y, 0), C['props'], M['prop'], rot_z=r, bevel=0.02)
        box(f'PROP_Intel_Chair{i}', (0.52, 0.52, 0.85), (x, y + (0.7 if r == 0 else -0.7), 0), C['props'], M['prop_dark'], bevel=0.02)
    text('DEC_Intel_ExitSign', 'ENGINEERING', (0, 27.95, 2.75), 'S', 0.16, C['decals'], M['label'])

# ============================================================ 03 ENGINEERING HANGAR
# Guided first pass follows the artifact's design order ("every rover is designed backwards
# from its science question"): Mission Config -> Science -> Power -> Mobility -> Comms -> Digital Twin.
# Corners chosen so that order is one clean loop: SE -> SW -> NW -> NE -> north wall.
STATIONS = {   # name: (x, y, decisions)
    'SCIENCE':  (5.9, 36.8, '3 instrument slots  |  mission style'),
    'POWER':    (-5.9, 36.8, 'power  |  battery  |  thermal'),
    'MOBILITY': (-5.9, 48.6, 'wheels  |  computer / AutoNav'),
    'COMMS':    (5.9, 48.6, 'communications'),
}

CONFIG_POS, CONFIG_ROT = (2.35, 38.6), -26     # Mission Configuration kiosk (first Hangar interaction)

def station_int(x, y):
    """Interaction point: 0.7 m in front of the console, toward the rover."""
    d = math.hypot(ROVER[0] - x, ROVER[1] - y)
    return (x + (ROVER[0] - x) / d * 0.7, y + (ROVER[1] - y) / d * 0.7)

class Frame:
    """Local frame of a station: +X lateral, +Y away from the rover, origin on the floor."""
    def __init__(self, x, y, rot):
        self.x, self.y, self.rot = x, y, rot
        r = math.radians(rot)
        self.t = (math.cos(r), math.sin(r)); self.u = (-math.sin(r), math.cos(r))
    def at(self, lx, ly, z=0.0):
        return (self.x + self.t[0] * lx + self.u[0] * ly, self.y + self.t[1] * lx + self.u[1] * ly, z)
    def box(self, name, size, lx, ly, z, mat, col=None, bevel=0.0):
        return box(name, size, self.at(lx, ly, z), col or C['props'], mat, rot_z=self.rot, bevel=bevel)
    def text(self, name, body, lx, ly, z, size, mat, col=None):
        o = text(name, body, self.at(lx, ly, z), 'S', size, col or C['decals'], mat)
        o.rotation_euler.z = math.radians(self.rot)
        return o

def bay_frame(f, name, title, sub):
    """Shared station language: two slim posts + header plate carrying the station name."""
    for s in (-1, 1):
        f.box(f'PROP_{name}_BayPost{"L" if s < 0 else "R"}', (0.1, 0.1, 2.75), s * 1.0, 1.05, 0, M['struct'])
    f.box(f'PROP_{name}_BayHeader', (2.1, 0.1, 0.55), 0, 1.05, 2.25, M['struct'])
    f.text(f'DEC_{name}_Sign', title, 0, 0.99, 2.58, 0.26 if len(title) < 12 else 0.16, M['label_w'])
    f.text(f'DEC_{name}_Decisions', sub, 0, 0.99, 2.34, 0.075, M['label_w'])

def identity_props(f, name):
    """Recognisable before reading: each station shows the hardware it configures."""
    n = f'PROP_Station_{name}'
    if name == 'POWER':          # battery bank + thermal radiator
        for i, lx in enumerate((-0.62, 0.0, 0.62)):
            f.box(f'{n}_BatteryCell{i}', (0.5, 0.5, 1.45), lx - 0.2, 1.3, 0, M['prop_dark'], bevel=0.03)
            f.box(f'{n}_BatteryCap{i}', (0.36, 0.36, 0.05), lx - 0.2, 1.3, 1.45, M['amber'])
        for i in range(6):
            f.box(f'{n}_RadiatorFin{i}', (0.035, 0.5, 1.7), 0.62 + i * 0.07, 1.3, 0.1, M['struct'])
    elif name == 'SCIENCE':      # instrument rack with three visible payload slots
        for i, (lx, ly) in enumerate(((-0.85, 1.05), (0.85, 1.05), (-0.85, 1.55), (0.85, 1.55))):
            f.box(f'{n}_RackPost{i}', (0.06, 0.06, 2.0), lx, ly, 0, M['struct'])
        for i, z in enumerate((0.45, 1.05, 1.65)):
            f.box(f'{n}_RackShelf{i}', (1.76, 0.56, 0.04), 0, 1.3, z, M['struct'])
            f.box(f'{n}_Instrument{i}', ((0.6, 0.38, 0.5)[i], 0.4, (0.32, 0.42, 0.26)[i]), (-0.4, 0.1, 0.35)[i], 1.3, z + 0.04, M['hero'], bevel=0.02)
            f.box(f'{n}_SlotLight{i}', (1.5, 0.02, 0.02), 0, 1.02, z + 0.02, M['screen'])
    elif name == 'MOBILITY':     # spare wheel on a cradle + AutoNav display
        f.box(f'{n}_WheelCradle', (0.75, 0.55, 0.42), -0.35, 1.3, 0, M['struct'], bevel=0.02)
        wl = rf.create_cylinder(f'{n}_SpareWheel', 0.26, 0.4, f.at(-0.35 - 0.2, 1.3, 0.42 + 0.26), C['props'], M['prop_dark'], verts=32)
        wl.rotation_euler = (0, math.radians(90), math.radians(f.rot))
        f.box(f'{n}_AutoNavScreen', (0.75, 0.05, 0.9), 0.5, 1.35, 1.0, M['screen'])
    elif name == 'COMMS':        # antenna mast with dish + signal display
        f.box(f'{n}_MastPole', (0.09, 0.09, 2.15), 0.45, 1.35, 0, M['struct'])
        dish = rf.create_cylinder(f'{n}_Dish', 0.5, 0.06, f.at(0.45, 1.3, 2.05), C['props'], M['hero'], verts=32)
        dish.rotation_euler = (math.radians(-55), 0, math.radians(f.rot))
        f.box(f'{n}_LowGainAntenna', (0.12, 0.12, 0.45), -0.75, 1.35, 1.3, M['prop_dark'])
        f.box(f'{n}_SignalScreen', (0.8, 0.05, 0.55), -0.35, 1.35, 1.05, M['screen'])

def station(name, x, y, decisions):
    """Console facing the rover inside a bay frame, station hardware behind it, cable to the turntable."""
    dx, dy = ROVER[0] - x, ROVER[1] - y
    rot = math.degrees(math.atan2(dy, dx)) + 90           # console front (-Y local) faces the rover
    f = Frame(x, y, rot)
    p = C['props']
    con = box(f'PROP_Station_{name}_Console', (1.7, 0.75, 0.92), (x, y, 0), p, M['prop'], rot_z=rot, bevel=0.02)
    top = box(f'PROP_Station_{name}_ConsoleTop', (1.6, 0.6, 0.04), (x, y, 0.92), p, M['screen'], rot_z=rot)
    top.rotation_euler.x = math.radians(-18)
    lip = box(f'PROP_Station_{name}_InteractStrip', (1.5, 0.02, 0.03), (0, 0, 0), p, M['orange_lit'])
    lip.parent = con; lip.location = (0, -0.39, 0.84)                               # orange-lit = interactable
    ux, uy = f.u
    bay_frame(f, f'Station_{name}', name, decisions)
    identity_props(f, name)
    # floor cable run from the console to the nearest turntable port
    a = math.atan2(y - ROVER[1], x - ROVER[0])
    port = min((math.radians(30 + 60 * i) for i in range(6)), key=lambda q: abs(math.atan2(math.sin(q - a), math.cos(q - a))))
    px, py = ROVER[0] + math.cos(port) * (PLAT_R + 0.35), ROVER[1] + math.sin(port) * (PLAT_R + 0.35)
    rf.create_floor_marking(f'PROP_Station_{name}_CableRun', [f.at(0.6, -0.3)[:2], (px, py)], 0.09, p, M['struct'], z=0.012)
    s = 1.6                                                                         # floor zone outline
    pts = [(-s, -s), (s, -s), (s, s), (-s, s), (-s, -s)]
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    rf.create_floor_marking(f'DEC_Station_{name}_Zone', [(x + px * cr - py * sr, y + px * sr + py * cr) for px, py in pts], 0.06, C['decals'], M['orange'])
    rf.create_marker(f'INT_Station_{name}', (x - ux * 0.7, y - uy * 0.7, 0), C['game'], 'SINGLE_ARROW', 0.6)

def build_hangar():
    x0, x1, y0, y1, h = HANG
    col, p = C['hangar'], C['props']
    # --- rover work bay: floor-level turntable, not a show pedestal
    hp = C['hero']
    rf.create_cylinder('HERO_RoverPlatform_Bed', PLAT_R + 0.3, 0.02, (*ROVER, 0), hp, M['struct'], verts=96)       # steel bed flush with floor
    rf.create_cylinder('HERO_RoverPlatform', PLAT_R, PLAT_H, (*ROVER, 0), hp, M['hero'], verts=96, bevel=0.012)   # turntable, 12 cm lip
    rf.create_floor_ring('HERO_RoverPlatform_LightRing', PLAT_R - 0.18, 0.05, (*ROVER, PLAT_H), hp, M['orange_lit'])  # recessed ring (groove in Phase 4)
    rf.create_floor_ring('DEC_RoverPlatform_SafetyRing', PLAT_R + 0.55, 0.1, (*ROVER, 0), C['decals'], M['amber'])
    for i, a in enumerate((150, 270, 30)):                                          # flush maintenance hatches
        r = math.radians(a)
        box(f'HERO_RoverPlatform_Hatch{i}', (0.9, 0.55, 0.004), (ROVER[0] + math.cos(r) * 2.55, ROVER[1] + math.sin(r) * 2.55, PLAT_H),
            hp, M['prop_dark'], rot_z=a + 90)
    for i in range(6):                                                               # power / data connection ports
        r = math.radians(30 + 60 * i)
        box(f'HERO_RoverPlatform_Port{i}', (0.42, 0.22, 0.16), (ROVER[0] + math.cos(r) * (PLAT_R + 0.14), ROVER[1] + math.sin(r) * (PLAT_R + 0.14), 0),
            hp, M['struct'], rot_z=math.degrees(r) + 90, bevel=0.015)
    inst = link_rover(rot_z=-28)
    wheel_alignment_marks(inst)
    # --- Mission Configuration: first Hangar interaction, sets the payload limit before any station
    # in the right edge of the entrance view, angled to face the player walking in
    # Low kiosk (tops out below eye height so it never covers the stations beyond it),
    # set in the right edge of the entrance view and turned toward the player walking in.
    f = Frame(*CONFIG_POS, CONFIG_ROT)
    con = f.box('PROP_MissionConfig_Console', (1.4, 0.65, 0.95), 0, 0, 0, M['prop'], bevel=0.02)
    lip = box('PROP_MissionConfig_InteractStrip', (1.25, 0.02, 0.03), (0, 0, 0), p, M['orange_lit']); lip.parent = con; lip.location = (0, -0.335, 0.87)
    f.box('PROP_MissionConfig_PanelFrame', (1.5, 0.1, 0.85), 0, 0.27, 0.95, M['struct'], bevel=0.01)
    f.box('UI_MissionConfig_Screen', (1.36, 0.02, 0.56), 0, 0.21, 1.0, M['screen'], col=C['ui'])
    f.text('DEC_MissionConfig_Sign', 'MISSION CONFIGURATION', 0, 0.2, 1.67, 0.085, M['label_w'])
    for i, (lab, lx) in enumerate((('VEHICLE', -0.45), ('PAYLOAD', 0.0), ('BUDGET', 0.45))):
        f.text(f'UI_MissionConfig_Readout{i}', lab, lx, 0.19, 1.45, 0.06, M['label_w'], col=C['ui'])
    rf.create_marker('INT_MissionConfig', f.at(0, -0.75), C['game'], 'SINGLE_ARROW', 0.6)
    # guided first pass, numbered on the floor beside each interaction point
    steps = [f.at(0, -0.75)[:2]] + [station_int(x, y) for (x, y, _) in STATIONS.values()] + [(0, y1 - 4.3)]
    for i, (sx, sy) in enumerate(steps):
        text(f'DEC_Step_{i + 1:02d}', f'{i + 1:02d}', (sx + 0.55, sy - 0.25, 0.012), 'N', 0.32, C['decals'], M['label_w'], flat=True)
    # --- Digital Twin display (north wall, on axis)
    rf.create_emissive_screen('HERO_DigitalTwinDisplay', 8.0, 4.0, (0, y1 - 0.12, 2.2), 'S', C['hero'], M['screen'], M['struct'], frame=0.15)
    box('HERO_DigitalTwin_Plinth', (9.0, 1.2, 0.5), (0, y1 - 0.6, 0), C['hero'], M['struct'], bevel=0.02)
    con = box('PROP_DigitalTwin_Console', (3.2, 0.9, 0.95), (0, y1 - 3.4, 0), p, M['prop'], bevel=0.02)
    lip = box('PROP_DigitalTwin_InteractStrip', (3.0, 0.02, 0.03), (0, 0, 0), p, M['orange_lit']); lip.parent = con; lip.location = (0, -0.46, 0.86)
    text('DEC_DigitalTwin_Title', 'DIGITAL TWIN', (0, y1 - 0.1, 6.75), 'S', 0.42, C['decals'], M['label'])
    rf.create_marker('INT_DigitalTwin', (0, y1 - 4.3, 0), C['game'], 'SINGLE_ARROW', 0.6)
    for n, (x, y, dec) in STATIONS.items(): station(n, x, y, dec)
    # --- structure: pilasters, roof trusses, crane rails, bridge crane
    for i, y in enumerate((35.2, 39.6, 44.0, 48.4, 52.8)):
        for side, x in (('W', x0 + 0.3), ('E', x1 - 0.3)):
            box(f'MOD_Column_{side}{i}', (0.6, 0.6, h), (x, y, 0), col, M['struct'])
        overhead(box(f'MOD_Beam_Truss{i}', (x1 - x0, 0.45, 0.9), (0, y, h - 1.0), col, M['struct']))
    for side, x in (('W', x0 + 0.55), ('E', x1 - 0.55)):
        overhead(box(f'MOD_Beam_CraneRail{side}', (0.4, y1 - y0, 0.5), (x, (y0 + y1) / 2, 7.6), col, M['struct']))
    overhead(box('PROP_Gantry_Bridge', (x1 - x0 - 0.8, 0.9, 0.8), (0, 47.0, 8.1), p, M['amber']))
    overhead(box('PROP_Gantry_Trolley', (1.2, 1.6, 0.6), (-1.5, 47.0, 7.5), p, M['struct']))
    overhead(box('PROP_Gantry_HookCable', (0.05, 0.05, 2.2), (-1.5, 47.0, 5.3), p, M['struct']))
    overhead(box('PROP_Gantry_HookBlock', (0.4, 0.3, 0.5), (-1.5, 47.0, 4.8), p, M['amber']))
    for i, y in enumerate((37.4, 41.8, 46.2, 50.6)):                                 # overhead light fixtures
        for j, x in enumerate((-4.5, 0.0, 4.5)):
            overhead(box(f'PROP_CeilingLight_{i}{j}', (3.0, 0.8, 0.12), (x, y, h - 1.5), p, M['screen_w']))
    # --- hangar door (rover exit, west) + glass wall to Mission Control (east)
    box('MOD_HangarDoor', (0.3, 8.0, 7.0), (x0 - 0.12, 44.0, 0), col, M['struct'])
    rf.create_floor_marking('DEC_HangarDoor_Hazard', [(x0 + 0.4, 40.0), (x0 + 0.4, 48.0)], 0.4, C['decals'], M['amber'])
    text('DEC_HangarDoor_Label', 'FLIGHT OPERATIONS', (x0 + 0.05, 44.0, 7.6), 'E', 0.35, C['decals'], M['label'])
    text('DEC_MC_DoorSign', 'MISSION CONTROL', (x1 - 0.05, 52.6, 2.8), 'W', 0.18, C['decals'], M['label'])
    # --- secondary props, kept to the walls so the rover stays clear
    for i, (x, y) in enumerate(((-8.3, 50.5), (-8.3, 52.3), (8.3, 35.0), (8.3, 36.8))):
        box(f'PROP_EquipmentCabinet_{i}', (0.7, 1.6, 2.0), (x, y, 0), p, M['prop_dark'], bevel=0.02)
    for i, (x, y, r) in enumerate(((-3.2, 38.6, 20), (7.7, 40.2, 90))):         # kept off the guided loop
        box(f'PROP_ToolCart_{i}', (1.0, 0.6, 0.95), (x, y, 0), p, M['prop'], rot_z=r, bevel=0.02)
    rf.create_cylinder('PROP_CableReel_0', 0.45, 0.5, (4.4, 41.2, 0), p, M['struct'], verts=24)
    for i, x in enumerate((-6.0, -4.5, -3.0)):                                       # barrier line by the hangar door path
        box(f'PROP_SafetyBarrier_{i}', (1.2, 0.08, 0.9), (x, 34.6, 0), p, M['amber'])

def trs_world(o):
    """World matrix composed from TRS + parent chain. Linked library objects have no evaluated
    matrix_world in a background session, so matrix_world cannot be trusted here."""
    m = Matrix.LocRotScale(o.location, o.rotation_euler if o.rotation_mode != 'QUATERNION' else o.rotation_quaternion, o.scale)
    return (trs_world(o.parent) @ o.matrix_parent_inverse @ m) if o.parent else m

def link_rover(rot_z):
    """Link the locked rover collection and instance it (read-only by construction),
    placed so its footprint centre sits on the turntable centre."""
    path = os.path.join(rf.ROOT, 'assets', 'rover', 'RF01_Rover.blend')
    with bpy.data.libraries.load(path, link=True) as (src, dst):
        dst.collections = ['RF01_Rover']
    col = dst.collections[0]
    xs, ys = [], []
    for o in col.objects:
        if o.type == 'MESH':
            mw = trs_world(o)
            for c in o.bound_box:
                w = mw @ Vector(c); xs.append(w.x); ys.append(w.y)
    centre = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, 0))
    rot = Matrix.Rotation(math.radians(rot_z), 4, 'Z')
    inst = bpy.data.objects.new('REF_RF01_Rover', None)
    inst.instance_type = 'COLLECTION'; inst.instance_collection = col
    inst.location = Vector((ROVER[0], ROVER[1], PLAT_H)) - rot @ centre
    inst.rotation_euler.z = math.radians(rot_z)
    C['ref'].objects.link(inst)
    # exact centring: measure the evaluated instance and correct the residual offset
    dg = bpy.context.evaluated_depsgraph_get(); dg.update()
    ex, ey = [], []
    for di in dg.object_instances:
        if di.is_instance and di.parent and di.parent.name == inst.name and di.object.type == 'MESH':
            for c in di.object.bound_box:
                w = di.matrix_world @ Vector(c); ex.append(w.x); ey.append(w.y)
    inst.location.x += ROVER[0] - (min(ex) + max(ex)) / 2
    inst.location.y += ROVER[1] - (min(ey) + max(ey)) / 2
    return inst

def wheel_alignment_marks(inst):
    """White bracket at each of the six real wheel contact patches (read from the linked rover)."""
    wheels = next(o for o in inst.instance_collection.objects if o.name == 'Wheels_objs')
    mw = trs_world(wheels)
    pts = [mw @ v.co for v in wheels.data.vertices]
    pts = [p for p in pts if p.z < 0.03]
    m = Matrix.Translation(inst.location) @ inst.rotation_euler.to_matrix().to_4x4()     # live transform, never the cached one
    for side in (-1, 1):
        sp = sorted((p for p in pts if p.x * side > 0), key=lambda p: p.y)
        gaps = sorted(range(1, len(sp)), key=lambda i: sp[i].y - sp[i - 1].y)[-2:]
        cuts = [0] + sorted(gaps) + [len(sp)]
        for k in range(3):
            grp = sp[cuts[k]:cuts[k + 1]]
            c = sum((p for p in grp), Vector()) / len(grp)
            w = m @ Vector((c.x, c.y, 0))
            hx, hy = 0.32, 0.36                                                    # half-size of bracket
            rz = inst.rotation_euler.z
            corner = lambda u, v: (w.x + u * math.cos(rz) - v * math.sin(rz), w.y + u * math.sin(rz) + v * math.cos(rz))
            nm = f"DEC_WheelMark_{'L' if side < 0 else 'R'}{k}"
            rf.create_floor_marking(nm, [corner(-hx, -hy), corner(hx, -hy), corner(hx, hy), corner(-hx, hy), corner(-hx, -hy)],
                                    0.035, C['decals'], M['label_w'], z=PLAT_H + 0.004)

# ============================================================== 04 MISSION CONTROL
def build_mc():
    x0, x1, y0, y1, h = MC
    ui, p = C['ui'], C['props']
    cy = (y0 + y1) / 2
    # one dominant front wall: identity, status, countdown, confirmed launch vehicle
    rf.create_emissive_screen('HERO_MissionControlWall', 11.0, 3.9, (x1 - 0.12, cy, 0.8), 'W', C['hero'], M['screen'], M['struct'], frame=0.12)
    for nm, body, z, size in (('Title', 'RED FRONTIER', 4.05, 0.42), ('Status', 'MISSION STATUS:  GO', 3.25, 0.3),
                              ('Countdown', 'T - 00:02:18', 2.3, 0.62), ('Vehicle', 'LAUNCH VEHICLE: HEAVY  |  CONFIRMED', 1.35, 0.13)):
        text(f'UI_MC_{nm}', body, (x1 - 0.17, cy, z), 'W', size, ui, M['label_w'])
    for i, (y, lab) in enumerate(((y0 + 0.08, 'GO / NO-GO'), (y1 - 0.08, 'READINESS'))):
        face = 'N' if i == 0 else 'S'
        rf.create_emissive_screen(f'UI_MC_{lab.replace(" / ", "_").replace("-", "")}', 3.0, 1.8, (x1 - 2.6, y, 1.4), face, ui, M['screen'], M['struct'])
    rf.create_emissive_screen('UI_MC_DigitalTwinSummary', 3.2, 1.8, (x0 + 4.5, y1 - 0.08, 1.4), 'S', ui, M['screen'], M['struct'])
    for r, x in enumerate((15.6, 19.0)):                                             # two operator rows facing the wall
        for i, dy in enumerate((-3.3, -1.5, 1.5, 3.3)):        # central aisle on the room axis
            box(f'PROP_MC_Desk_R{r}_{i}', (0.9, 1.6, 0.76), (x, cy + dy, 0), p, M['prop'], bevel=0.02)
            box(f'PROP_MC_Monitor_R{r}_{i}', (0.06, 1.3, 0.5), (x + 0.3, cy + dy, 0.8), p, M['screen'])
            box(f'PROP_MC_Chair_R{r}_{i}', (0.52, 0.52, 0.85), (x - 0.8, cy + dy, 0), p, M['prop_dark'], bevel=0.02)
    # the one special console: on the room axis, in front of the operators, ringed in orange
    lc = (21.2, cy)
    rf.create_cylinder('HERO_LaunchConsole_Base', 0.95, 0.06, (*lc, 0), C['hero'], M['struct'], verts=48)
    rf.create_floor_ring('HERO_LaunchConsole_Ring', 1.25, 0.06, (*lc, 0), C['hero'], M['orange_lit'], segs=64)
    con = box('HERO_LaunchConsole', (0.9, 1.6, 1.0), (*lc, 0.06), C['hero'], M['struct'], bevel=0.03)
    top = box('HERO_LaunchConsole_Top', (0.7, 1.4, 0.03), (lc[0] - 0.05, lc[1], 1.06), C['hero'], M['orange_lit'])
    text('UI_MC_LaunchLabel', 'ACCEPT RISK & LAUNCH', (lc[0] - 0.47, cy, 0.7), 'W', 0.1, ui, M['label_w'])
    rf.create_marker('INT_LaunchConsole', (lc[0] - 1.0, cy, 0), C['game'], 'SINGLE_ARROW', 0.6)

# ================================================================== CORRIDORS
def build_corridors(skip=()):
    for nm, fp, nxt in (('Corridor01', C1, 'MARS INTELLIGENCE'), ('Corridor02', C2, 'ENGINEERING HANGAR')):
        if nm in skip: continue
        x0, x1, y0, y1, h = fp
        cx = (x0 + x1) / 2
        overhead(box(f'PROP_{nm}_CableTray', (0.35, y1 - y0, 0.08), (x1 - 0.35, (y0 + y1) / 2, h - 0.35), C['props'], M['struct']))
        rf.create_emissive_screen(f'UI_{nm}_Screen', 1.2, 0.7, (x0 + 0.04, (y0 + y1) / 2, 1.5), 'E', C['ui'], M['screen'], M['struct'])
        text(f'DEC_{nm}_Sign', nxt, (cx, y1 - 0.03, 2.65), 'S', 0.16, C['decals'], M['label'])

# ============================================================ GAMEPLAY / FLOW
def mission_path():
    """Major mission path: one continuous orange floor line, entry -> launch console."""
    # Briefing: straight to the mission table, then out past the orange-framed exit
    path = [(0, 0.3), (0, 5.6), (2.75, 6.4), (2.75, 16.0),
            # Mars Intel: landing-system console first, then round the table to the exit
            (2.75, 17.2), (0.4, 17.2), (0.4, 18.1), (3.2, 19.6), (3.2, 24.6), (0, 26.8), (0, 34.0)]
    # Hangar first pass: Mission Configuration -> Science -> Power -> Mobility -> Comms -> Digital Twin
    cfg_int = Frame(*CONFIG_POS, CONFIG_ROT).at(0, -0.75)[:2]
    path += [cfg_int] + [station_int(x, y) for (x, y, _) in STATIONS.values()] + [(0, HANG[3] - 4.3)]
    # -> Mission Control, down the operators' aisle to the launch console
    path += [(6.6, 52.6), (17.4, 52.6), (17.4, 47.75), (20.2, 47.75)]
    return path

def build_flow():
    rf.create_floor_marking('DEC_MissionPath', mission_path(), 0.12, C['decals'], M['orange'])
    rf.create_marker('PLAYER_Start', (0, 1.2, 0), C['game'], 'SINGLE_ARROW', 0.8)
    for nm, fp in (('Briefing', BRIEF), ('MarsIntel', INTEL), ('Hangar', HANG), ('MissionControl', MC)):
        x0, x1, y0, y1, h = fp
        t = rf.create_marker(f'TRIG_Room_{nm}', ((x0 + x1) / 2, (y0 + y1) / 2, h / 2), C['game'], 'CUBE', 1.0)
        t.scale = ((x1 - x0) / 2, (y1 - y0) / 2, h / 2)
        text(f'DBG_Label_{nm}', nm.upper(), ((x0 + x1) / 2, y0 + 1.0, 0.02), 'N', 0.6, C['debug'], M['label'], flat=True)['rf_plan_only'] = True
    rf.create_marker('INT_BriefingTable', (0.0, 5.7, 0), C['game'], 'SINGLE_ARROW', 0.6)
    rf.create_marker('INT_LandingSystem', (0.4, 18.2, 0), C['game'], 'SINGLE_ARROW', 0.6)
    for s, (x, y) in {'A': (-1.2, 20.3), 'B': (0.4, 20.3), 'C': (1.3, 20.3)}.items():      # site pick at the table edge
        rf.create_marker(f'INT_LandingSite{s}', (x, y, 0), C['game'], 'SINGLE_ARROW', 0.4)
    # scale references: 1.75 m humans at key thresholds
    for i, (x, y) in enumerate(((-2.2, 2.6), (-2.6, 18.6), (-2.2, 36.4), (-4.6, 41.2), (12.6, 46.0))):
        rf.create_cylinder(f'REF_Human_{i}_Body', 0.22, 1.5, (x, y, 0), C['ref'], M['human'], verts=16)
        rf.create_cylinder(f'REF_Human_{i}_Head', 0.12, 0.25, (x, y, 1.5), C['ref'], M['human'], verts=16)

# ==================================================================== CAMERAS
def build_cameras():
    c = C['cams']
    rf.create_camera('CAM_Briefing_Hero',       (1.3, 0.7, 1.75),   (-0.6, 10.0, 2.2), c, lens=18)
    rf.create_camera('CAM_MarsIntel_Hero',      (3.9, 17.0, 2.3),   (-0.3, 22.4, 0.9), c, lens=18)
    rf.create_camera('CAM_Corridor',            (2.75, 10.5, 1.7),  (2.75, 16.5, 1.55), c, lens=20)
    rf.create_camera('CAM_Hangar_Entrance',     (0.0, 33.5, 1.9),   (0.0, 44.0, 2.3), c, lens=26)
    rf.create_camera('CAM_Hangar_Rover',        (-4.6, 37.6, 2.0),  (0.0, 42.9, 1.2), c, lens=30)
    rf.create_camera('CAM_Hangar_Wide',         (8.2, 33.5, 8.0),   (-1.5, 47.0, 0.8), c, lens=16)
    rf.create_camera('CAM_MissionControl_Hero', (11.2, 47.75, 2.05), (24.0, 47.75, 1.9), c, lens=20)   # down the operators' aisle
    plan = rf.create_camera('CAM_Plan_Top',     (7.5, 27.0, 60.0),  (7.5, 27.0, 0.0), c)
    plan.data.type = 'ORTHO'; plan.data.ortho_scale = 62.0
    rf.create_camera('CAM_Axo_Cutaway',         (-26.0, -6.0, 44.0), (6.0, 30.0, 0.0), c, lens=38)
    bpy.context.scene.camera = bpy.data.objects['CAM_Hangar_Entrance']

def main(save=True, hangar=True, skip=()):
    """skip: rooms built near-final by a Phase 5 script (their greybox is left out)."""
    setup(); build_shells(hangar, skip)
    if 'Briefing' not in skip: build_briefing()
    if 'MarsIntel' not in skip: build_intel()
    if hangar: build_hangar()
    if 'MissionControl' not in skip: build_mc()
    build_corridors(skip); build_flow(); build_cameras()

    for o in bpy.data.objects:      # walls facing the cutaway camera
        if '_WallS_' in o.name or '_WallW_' in o.name or o.name == 'MOD_HangarDoor':
            o['rf_cutaway_hide'] = True

    # world + render defaults for greybox review
    w = bpy.data.worlds.new('RF_World'); sc.world = w; w.color = (0.05, 0.05, 0.055)

    if save:
        out = os.path.join(rf.ROOT, 'blender', 'RF_Facility_Blockout.blend')
        rf.save(out)
        print('BLOCKOUT_OK objects=', len(bpy.data.objects), 'saved', out)

if __name__ == '__main__':
    main()
