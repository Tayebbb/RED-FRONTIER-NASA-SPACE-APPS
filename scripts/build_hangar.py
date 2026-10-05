"""
build_hangar.py - PHASE 3/4: the Engineering Hangar at near-final quality, built from the kit.

Layout is NOT redefined here: every position comes from build_blockout (the locked Phase 2
layout). The rest of the facility is rebuilt as greybox around it, so the file stays whole.
The Hangar establishes the visual language later propagated to the other rooms:
  walls   warm-white lower panels / cool-grey upper panels / graphite trim rail with LED wash
  floor   sealed epoxy on the 4.4 m column grid, flush cable-trench grates, rubber work zones
  ceiling dark roof deck, graphite Warren trusses, linear high-bay fixtures
  props   satin painted consoles with recessed kicks, orange-lit = interactable
  screens chamfered graphite bezels, navy UI with restrained cyan, orange = selected
  decals  white Bahnschrift stencils; orange only for the mission path and step badges

Run:  blender -b --factory-startup --python scripts/build_hangar.py
"""
import bpy, sys, os, math, bmesh
sys.path.insert(0, os.path.dirname(__file__))
import rf_lib as rf, rf_kit as kit, rf_materials as rm
import build_blockout as bb
from mathutils import Vector, Matrix

X0, X1, Y0, Y1, H = bb.HANG
# fronts face the room: rot 90 faces +X (west wall), -90 faces -X (east wall)
CABINETS = ((-8.45, 50.4, 90), (-8.45, 51.3, 90), (-8.45, 52.2, 90), (8.45, 35.0, -90), (8.45, 35.9, -90))
COL_Y = (35.2, 39.6, 44.0, 48.4, 52.8)
STATION_SCREENS = {'POWER': 'T_Screen_Power.png', 'SCIENCE': 'T_Screen_Science.png',
                   'MOBILITY': 'T_Screen_Mobility.png', 'COMMS': 'T_Screen_Comms.png'}

def C(k): return bb.C[k]

def sub(path):
    return rf.collection('RF_FACILITY/' + path)

def world_uv(obj, tile, ox=0.0, oy=0.0):
    """World-space box UVs (metres / tile) for shell pieces created by rf_lib boxes."""
    me = obj.data; bm = bmesh.new(); bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify(); mw = obj.matrix_world
    for f in bm.faces:
        n = f.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            w = mw @ l.vert.co
            u, v = {0: (w.y, w.z), 1: (w.x, w.z), 2: (w.x - ox, w.y - oy)}[ax]
            l[uv].uv = (u / tile, v / tile)
    bm.to_mesh(me); bm.free()

def img_size(path):
    im = bpy.data.images.get(os.path.basename(path)) or bpy.data.images.load(os.path.join(rm.TEX, path))
    return im.size

def wall_text(name, image, height, loc, facing_rot, col=None):
    mat = rm.decal(name, image)
    return kit.wall_decal(f'DEC_{name}', mat, img_size(f'decals/{image}'), height, col or C('decals'), loc, facing_rot)

def floor_decal(name, image, w, loc, rot_z=0.0, z=0.006, rough=0.55):
    mat = rm.decal(name, image, rough)
    iw, ih = img_size(f'decals/{image}')
    return kit.decal_plane(f'DEC_{name}', mat, w, w * ih / iw, C('decals'), (loc[0], loc[1], z), (0, 0, math.radians(rot_z)))

def screen_quad(name, image, w, h, loc, rot, strength=2.2):
    return kit.decal_plane(f'UI_{name}', rm.screen(name, image, strength), w, h, C('ui'), loc, rot)

# ===================================================================== SHELL
def build_shell(L):
    col = sub('01_ARCH/Hangar')
    mats = {'floor': L['floor_epoxy'], 'wall': L['graphite'], 'ceiling': L['ceiling_dark'], 'glass': L['glass']}
    rf.create_room('Hangar', X0, X1, Y0, Y1, H, col, mats, {
        'S': [dict(off=9.0, **bb.DOORH)],
        'W': [dict(off=11.0, w=8.0, h=7.0)],
        'E': [dict(off=13.0, w=8.0, h=2.6, sill=1.0, glass=True), dict(off=19.6, **bb.DOOR2)]}, ceil_col=C('ceil'))
    bpy.context.view_layer.update()
    world_uv(bpy.data.objects['Hangar_Floor'], 4.4, ox=-2.2, oy=COL_Y[0])       # joints on the column grid
    world_uv(bpy.data.objects['Hangar_Ceiling'], 1.0)
    bpy.data.objects['Hangar_Ceiling']['rf_overhead'] = True
    # cladding on the four interior faces (local +X along the wall, panels toward the room)
    clad = sub('01_ARCH/Hangar/Cladding')
    # openings in each wall's local x (metres from its origin end), z
    for nm, origin, rot, length, opens in (
        ('S', (X1, Y0), 180, X1 - X0, [(7.7, 10.3, 0, 2.9)]),                    # runs from x=+9 toward -X; door at x 0
        ('N', (X0, Y1), 0, X1 - X0, []),
        ('W', (X0, Y0), 90, Y1 - Y0, [(7.0, 15.0, 0, 7.0)]),                     # hangar door y 40..48
        ('E', (X1, Y1), -90, Y1 - Y0, [(5.0, 13.0, 1.0, 3.6), (1.5, 3.3, 0, 2.4)])):   # glass y 42..50, MC door
        o = kit.cladding(f'MOD_Cladding_{nm}', length, H, L, clad, openings=opens)
        kit.place(o, (*origin, 0), rot)
    for o in col.objects:
        if 'Glass' in o.name: rf.assign_material(o, L['glass'])

# ================================================================= STRUCTURE
def build_structure(L):
    col = sub('01_ARCH/Hangar/Structure')
    src = kit.column('MOD_Column', H, L, col); src.location = (X0 + 0.3, COL_Y[0], 0)
    n = 0
    for i, y in enumerate(COL_Y):
        for side, x in (('W', X0 + 0.32), ('E', X1 - 0.32)):
            if side == 'W' and 40.0 < y < 48.0: continue          # hangar door span: carried by the header beam
            if side == 'E' and 51.5 < y < 53.6: continue          # Mission Control door (y 51.7..53.5): framed by its portal
            o = src if n == 0 else kit.instance(src, f'MOD_Column_{side}{i}', col, (x, y, 0))
            if n == 0: o.name = f'MOD_Column_{side}{i}'; o.location = (x, y, 0)
            n += 1
            face = 90 if side == 'W' else -90
            wall_text(f'ColumnID_{side}{i}', f'T_Decal_ColumnH{i + 1}.png', 0.22, (x + (0.29 if side == 'W' else -0.29), y, 2.6), face)
    tsrc = kit.truss('MOD_Beam_Truss', X1 - X0, L, col)
    for i, y in enumerate(COL_Y):
        o = tsrc if i == 0 else kit.instance(tsrc, f'MOD_Beam_Truss{i}', col, (0, y, H - 0.75))
        if i == 0: o.name = 'MOD_Beam_Truss0'; o.location = (0, y, H - 0.75)
        o['rf_overhead'] = True
    # hangar-door header beam and crane runway rails on brackets
    hdr = kit.MB().box((0.5, 8.6, 0.8), (X0 + 0.25, 44.0, 7.4), L['graphite']).build('MOD_HangarDoor_Header', col, bevel=0.01)
    for side, x in (('W', X0 + 0.55), ('E', X1 - 0.55)):
        mb = kit.MB().box((0.35, Y1 - Y0, 0.45), (x, (Y0 + Y1) / 2, 7.55), L['graphite'])
        for y in COL_Y: mb.box((0.5, 0.35, 0.5), (x - (0.1 if side == 'E' else -0.1), y, 7.1), L['graphite'])
        mb.build(f'MOD_CraneRail_{side}', col, bevel=0.008)['rf_overhead'] = True

def build_crane(L):
    col = sub('02_PROPS/Hangar')
    y = 47.0; span = X1 - X0 - 1.1
    mb = kit.MB()
    mb.box((span, 0.75, 0.95), (0, y, 8.25), L['graphite'])                       # box girder
    for sx in (-1, 1):
        mb.box((0.7, 2.6, 0.6), (sx * (span / 2), y, 7.95), L['graphite'])      # end trucks
        mb.box((0.04, 2.6, 0.5), (sx * (span / 2 + 0.36), y, 7.95), L['yellow'])
    tx = -5.6                                                                      # trolley parked over MOBILITY, clear of the DT axis
    mb.box((1.3, 1.5, 0.6), (tx, y, 7.5), L['painted_dark'])                      # trolley
    mb.cyl(0.02, 1.5, (tx, y, 6.45), L['graphite'], segs=8)                       # wire rope
    mb.box((0.42, 0.32, 0.5), (tx, y, 5.5), L['yellow'])                          # hook block
    mb.cyl(0.06, 0.2, (tx, y, 5.18), L['graphite'], segs=12)
    o = mb.build('PROP_Gantry_Crane', col, bevel=0.01); o['rf_overhead'] = True
    for sx in (-1, 1):                                                              # hazard bands near the girder ends
        for sy in (-1, 1):
            d = kit.decal_plane(f'DEC_Crane_Hazard{sx}{sy}', rm.decal('Hazard', 'T_Decal_Hazard.png'), 1.6, 0.2, C('decals'),
                                (sx * (span / 2 - 1.2), y + sy * 0.378, 8.25), (math.radians(90), 0, math.radians(0 if sy < 0 else 180)))
            d['rf_overhead'] = True

def build_lights_fixtures(L):
    col = sub('02_PROPS/Hangar/Lighting')
    src = kit.high_bay_light('PROP_HighBayLight', L, col, drop=0.7)
    n = 0
    for i, y in enumerate((37.4, 41.8, 46.2, 50.6)):
        for j, x in enumerate((-4.6, 0.0, 4.6)):
            o = src if n == 0 else kit.instance(src, f'PROP_HighBayLight_{i}{j}', col, (x, y, 8.35))
            if n == 0: o.name = 'PROP_HighBayLight_00'; o.location = (x, y, 8.35)
            o['rf_overhead'] = True; n += 1

# ============================================================== TURNTABLE / ROVER
def hazard_ring(name, r_in, r_out, mat, col, segs=192, tile=0.96):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    ring = [(bm.verts.new((math.cos(a) * r_in, math.sin(a) * r_in, 0)), bm.verts.new((math.cos(a) * r_out, math.sin(a) * r_out, 0)))
            for a in (2 * math.pi * i / segs for i in range(segs + 1))]
    circ = 2 * math.pi * (r_in + r_out) / 2
    for i in range(segs):
        (a0, a1), (b0, b1) = ring[i], ring[i + 1]
        f = bm.faces.new((a0, b0, b1, a1))
        u0, u1 = circ * i / segs / tile, circ * (i + 1) / segs / tile
        for l, c in zip(f.loops, ((u0, 0), (u1, 0), (u1, 1), (u0, 1))): l[uv].uv = c
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new(name, me); col.objects.link(o); return o

def build_turntable(L):
    hero = C('hero'); R, Hp = bb.PLAT_R, bb.PLAT_H
    tt = kit.turntable('HERO_RoverPlatform', R, Hp, L, hero); tt.location = (*bb.ROVER, 0)
    ring = floor_decal('TurntableRing', 'T_Decal_TurntableRing.png', 2 * (R - 0.42), (*bb.ROVER,), z=Hp + 0.002, rough=0.42)
    hz = hazard_ring('DEC_RoverPlatform_HazardRing', R + 0.42, R + 0.56, rm.decal('HazardRing', 'T_Decal_Hazard.png', 0.55), C('decals'))
    hz.location = (*bb.ROVER, 0.005)
    hsrc = kit.hatch('HERO_RoverPlatform_Hatch', L, hero)
    for i, a in enumerate((150, 270, 30)):
        r = math.radians(a)
        o = hsrc if i == 0 else kit.instance(hsrc, f'HERO_RoverPlatform_Hatch{i}', hero, (0, 0, 0))
        o.location = (bb.ROVER[0] + math.cos(r) * 2.35, bb.ROVER[1] + math.sin(r) * 2.35, Hp); o.rotation_euler.z = r + math.pi / 2
    psrc = kit.service_port('HERO_RoverPlatform_Port', L, hero)
    for i in range(6):
        r = math.radians(30 + 60 * i)
        o = psrc if i == 0 else kit.instance(psrc, f'HERO_RoverPlatform_Port{i}', hero, (0, 0, 0))
        o.location = (bb.ROVER[0] + math.cos(r) * (R + 0.2), bb.ROVER[1] + math.sin(r) * (R + 0.2), 0.012)
        o.rotation_euler.z = r + math.pi / 2
    inst = bb.link_rover(rot_z=-28)
    wheel_brackets(inst, L)
    floor_decal('WorkBay', 'T_Decal_WorkBay.png', 2.6, (0.0, 37.95))

def wheel_brackets(inst, L):
    """Graphite painted L-corners around each real wheel contact patch (from the linked rover)."""
    paint = rm.pbr('MAT_Paint_Graphite', '#24272B', 0.55)            # dark brackets read on the lit deck
    wheels = next(o for o in inst.instance_collection.objects if o.name == 'Wheels_objs')
    mw = bb.trs_world(wheels)
    pts = [mw @ v.co for v in wheels.data.vertices]; pts = [p for p in pts if p.z < 0.03]
    m = Matrix.Translation(inst.location) @ inst.rotation_euler.to_matrix().to_4x4()
    rz = inst.rotation_euler.z; hx, hy, arm = 0.3, 0.34, 0.14
    for side in (-1, 1):
        sp = sorted((p for p in pts if p.x * side > 0), key=lambda p: p.y)
        gaps = sorted(range(1, len(sp)), key=lambda i: sp[i].y - sp[i - 1].y)[-2:]
        cuts = [0] + sorted(gaps) + [len(sp)]
        for k in range(3):
            grp = sp[cuts[k]:cuts[k + 1]]; c = sum(grp, Vector()) / len(grp); w = m @ Vector((c.x, c.y, 0))
            P = lambda u, v: (w.x + u * math.cos(rz) - v * math.sin(rz), w.y + u * math.sin(rz) + v * math.cos(rz))
            for cx in (-1, 1):
                for cy in (-1, 1):
                    rf.create_floor_marking(f"DEC_WheelBracket_{'L' if side < 0 else 'R'}{k}_{cx}{cy}",
                                            [P(cx * (hx - arm), cy * hy), P(cx * hx, cy * hy), P(cx * hx, cy * (hy - arm))],
                                            0.03, C('decals'), paint, z=bb.PLAT_H + 0.003)

# ====================================================================== STATIONS
def build_stations(L):
    p = sub('02_PROPS/Hangar/Stations')
    con_src, frame_src = None, None
    for idx, (name, (x, y, dec)) in enumerate(bb.STATIONS.items()):
        rot = math.degrees(math.atan2(bb.ROVER[1] - y, bb.ROVER[0] - x)) + 90
        f = bb.Frame(x, y, rot)
        con = kit.console(f'PROP_Station_{name}_Console', L, p); kit.place(con, (x, y, 0), rot)
        r = math.radians(rot); t = math.radians(18)
        screen_quad(f'Station_{name}', STATION_SCREENS[name], 1.42, 0.52, f.at(0, -0.01, 0.966), (t, 0, r))
        fr = kit.bay_frame(f'PROP_Station_{name}_BayFrame', L, p); kit.place(fr, f.at(0, 1.05), rot)
        wall_text(f'Station_{name}', f'T_Decal_{name}.png', 0.2, f.at(0.06, 1.05 - 0.071, 2.56), rot, col=C('decals'))
        wall_text(f'Station_{name}_Sub', f'T_Decal_Dec_{name}.png', 0.07, f.at(0.06, 1.05 - 0.071, 2.33), rot, col=C('decals'))
        identity(f, name, L, p)
        # rubber work zone + orange corner ticks + trench grate to the nearest turntable port
        zone = kit.MB().box((3.0, 2.8, 0.004), (0, 0.35, 0.002), L['floor_rubber']).build(f'PROP_Station_{name}_WorkZone', p, bevel=0)
        kit.place(zone, (x, y, 0), rot)
        trench(name, x, y, f, L, p)
        bb.rf.create_marker(f'INT_Station_{name}', (*bb.station_int(x, y), 0), C('game'), 'SINGLE_ARROW', 0.6)
        lx, ly = bb.station_int(x, y)
        floor_decal(f'Step{idx + 2:02d}', f'T_Decal_Step{idx + 2:02d}.png', 0.5, (lx + 0.55, ly - 0.25), 0)

def trench(name, x, y, f, L, col):
    a = math.atan2(y - bb.ROVER[1], x - bb.ROVER[0])
    port = min((math.radians(30 + 60 * i) for i in range(6)), key=lambda q: abs(math.atan2(math.sin(q - a), math.cos(q - a))))
    end = Vector((bb.ROVER[0] + math.cos(port) * (bb.PLAT_R + 0.45), bb.ROVER[1] + math.sin(port) * (bb.PLAT_R + 0.45), 0))
    start = Vector(f.at(0.55, -0.42))
    d = end - start; L_ = d.length; ang = math.atan2(d.y, d.x)
    mb = kit.MB()
    mb.box((L_, 0.3, 0.004), (L_ / 2, 0, 0.002), L['floor_metal'])
    for s in (-1, 1): mb.box((L_, 0.035, 0.006), (L_ / 2, s * 0.168, 0.003), L['graphite'])
    o = mb.build(f'PROP_Station_{name}_CableTrench', col, bevel=0); o.location = start; o.rotation_euler.z = ang
    me = o.data; uvl = me.uv_layers.active                       # re-tile grate along the run (0.3 m tiles)
    for poly in me.polygons:
        if me.materials[poly.material_index] == L['floor_metal']:
            for li in poly.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                uvl.data[li].uv = (v.x / 0.3, (v.y + 0.15) / 0.3)

def identity(f, name, L, col):
    """Each station shows the hardware it configures, inside its bay frame."""
    mb = kit.MB(); ly = 1.3
    if name == 'POWER':
        for i, lx in enumerate((-0.82, -0.27, 0.28)):
            mb.box((0.48, 0.5, 1.4), (lx, ly, 0.72), L['painted_dark'])
            mb.box((0.36, 0.38, 0.05), (lx, ly, 1.445), L['yellow'])
            mb.box((0.3, 0.012, 0.08), (lx, ly - 0.256, 1.2), L['status_cyan'])
            mb.box((0.02, 0.012, 0.9), (lx - 0.14, ly - 0.256, 0.7), L['backer'])
        for i in range(7):
            mb.box((0.03, 0.46, 1.6), (0.62 + i * 0.055, ly, 0.85), L['brushed'])
        mb.box((0.42, 0.5, 0.06), (0.785, ly, 1.68), L['graphite'])
        mb.box((0.42, 0.5, 0.06), (0.785, ly, 0.03), L['graphite'])
    elif name == 'SCIENCE':
        for lx in (-0.85, 0.85):
            for dy in (-0.25, 0.25): mb.box((0.05, 0.05, 2.0), (lx, ly + dy, 1.0), L['graphite'])
        for i, z in enumerate((0.45, 1.05, 1.65)):
            mb.box((1.76, 0.56, 0.035), (0, ly, z), L['graphite'])
            mb.box((1.6, 0.012, 0.014), (0, ly - 0.285, z + 0.03), L['status_cyan'])
        mb.cyl(0.16, 0.4, (-0.45, ly, 0.47 + 0.2), L['painted'], segs=28, axis='Y')            # slot 1: camera head
        mb.cyl(0.11, 0.06, (-0.45, ly - 0.22, 0.67), L['screen_dark'], segs=24, axis='Y')
        mb.box((0.5, 0.4, 0.38), (0.15, ly, 1.07 + 0.19), L['painted'])                           # slot 2: laser unit
        mb.cyl(0.06, 0.08, (0.15, ly - 0.24, 1.3), L['brushed'], segs=16, axis='Y')
        mb.box((0.62, 0.4, 0.22), (0.4, ly, 1.67 + 0.11), L['painted'])                           # slot 3: organics
        for k in range(6): mb.cyl(0.018, 0.16, (-0.6 + k * 0.08, ly, 1.67 + 0.08), L['brushed'], segs=8)
    elif name == 'MOBILITY':
        mb.box((0.62, 0.5, 0.06), (-0.35, ly, 0.03), L['graphite'])                                 # display stand: wheel at eye level
        mb.box((0.12, 0.12, 0.95), (-0.35, ly + 0.1, 0.5), L['graphite'])
        mb.box((0.5, 0.16, 0.08), (-0.35, ly + 0.1, 0.97), L['graphite'])
        mb.box((0.8, 0.06, 0.9), (0.55, ly + 0.05, 1.35), L['graphite'])
        # spare wheel (real 52.5 cm dia) as its own object, turned 55 deg so face + spokes read from gameplay distance
        R, wb = 0.262, kit.MB()
        wb.cyl(R, 0.4, (0, 0, 0), L['brushed'], segs=48, axis='X')
        for k in range(24):                                                                         # grousers
            a = 2 * math.pi * k / 24
            wb.box((0.4, 0.02, 0.03), (0, math.cos(a) * (R + 0.008), math.sin(a) * (R + 0.008)), L['brushed'], rot=(a, 0, 0))
        wb.cyl(R - 0.02, 0.01, (0.201, 0, 0), L['graphite'], segs=48, axis='X')                     # dark face disc
        wb.cyl(0.08, 0.06, (0.22, 0, 0), L['brushed'], segs=24, axis='X')                            # hub
        for k in range(6):                                                                          # curved flexure spokes
            a = 2 * math.pi * k / 6
            mid = (0.214, math.cos(a + 0.35) * 0.16, math.sin(a + 0.35) * 0.16)
            wb.beam((0.214, math.cos(a) * 0.08, math.sin(a) * 0.08), mid, 0.018, 0.02, L['brushed'])
            wb.beam(mid, (0.214, math.cos(a + 0.2) * 0.235, math.sin(a + 0.2) * 0.235), 0.018, 0.02, L['brushed'])
        kit.place(wb.build(f'PROP_Station_{name}_SpareWheel', col, bevel=0.004), f.at(-0.35, ly, 1.28), f.rot - 55)
    elif name == 'COMMS':
        for k in range(3):
            a = 2 * math.pi * k / 3 + 0.5
            mb.beam((0.45, ly, 1.2), (0.45 + math.cos(a) * 0.45, ly + math.sin(a) * 0.45, 0.0), 0.03, 0.03, L['graphite'])
        mb.cyl(0.04, 2.0, (0.45, ly, 1.0), L['graphite'], segs=12)
        mb.cyl(0.55, 0.05, (0.45, ly, 2.0), L['painted'], segs=40, r2=0.5)
        mb.cyl(0.03, 0.42, (0.45, ly, 2.25), L['graphite'], segs=10)
        mb.box((0.14, 0.14, 0.5), (-0.7, ly, 1.25), L['painted_dark'])
        mb.box((0.8, 0.06, 0.55), (-0.25, ly + 0.05, 1.3), L['graphite'])
    o = mb.build(f'PROP_Station_{name}_Hardware', col, bevel=0.006)
    kit.place(o, f.at(0, 0), f.rot)
    scr ={'MOBILITY': ('T_Screen_Mobility.png', 0.72, 0.45, (0.55, ly + 0.015, 1.35)),
           'COMMS': ('T_Screen_Comms.png', 0.72, 0.45, (-0.25, ly + 0.015, 1.3))}.get(name)
    if scr:
        img, w, h, (lx, ly2, z) = scr
        screen_quad(f'Station_{name}_Aux', img, w, h, f.at(lx, ly2 - 0.035, z), (math.radians(90), 0, math.radians(f.rot)), 1.6)

# ============================================================== MISSION CONFIG / DT
def build_mission_config(L):
    p = sub('02_PROPS/Hangar/Stations')
    f = bb.Frame(*bb.CONFIG_POS, bb.CONFIG_ROT)
    con = kit.console('PROP_MissionConfig_Console', L, p, w=1.4, dpt=0.65); kit.place(con, f.at(0, 0), f.rot)
    pan = kit.display_frame('PROP_MissionConfig_Panel', 1.3, 0.62, L['screen_dark'], L, p, border=0.07, depth=0.1)
    kit.place(pan, f.at(0, 0.27, 0.95), f.rot)
    screen_quad('MissionConfig', 'T_Screen_MissionConfig.png', 1.3, 0.62, f.at(0, 0.215, 0.95 + 0.07 + 0.31),
                (math.radians(90), 0, math.radians(f.rot)), 1.35)                     # dimmer: never competes with the rover
    hdr = kit.MB().box((1.44, 0.1, 0.16), (0, 0, 0.08), L['graphite']).build('PROP_MissionConfig_Header', p, bevel=0.006)
    kit.place(hdr, f.at(0, 0.27, 1.72), f.rot)
    wall_text('MissionConfigTitle', 'T_Decal_MissionConfig.png', 0.075, f.at(0, 0.215, 1.8), f.rot)
    bb.rf.create_marker('INT_MissionConfig', f.at(0, -0.75), C('game'), 'SINGLE_ARROW', 0.6)
    lx, ly = f.at(0, -0.75)[:2]
    floor_decal('Step01', 'T_Decal_Step01.png', 0.5, (lx - 0.55, ly - 0.3))

def build_digital_twin(L):
    hero = C('hero'); y = Y1 - 0.02
    dt = kit.display_frame('HERO_DigitalTwinDisplay', 8.0, 4.0, L['screen_dark'], L, hero, border=0.15, depth=0.18)
    dt.location = (0, y - 0.18, 2.05)
    screen_quad('DigitalTwin', 'T_Screen_DigitalTwin.png', 8.0, 4.0, (0, y - 0.19, 2.2 + 2.0), (math.radians(90), 0, 0), 1.8)
    mb = kit.MB()
    for sx in (-1, 1):
        mb.box((0.55, 0.32, 7.3), (sx * 4.75, y - 0.16, 3.65), L['graphite'])
        mb.box((0.035, 0.02, 6.6), (sx * (4.75 - 0.2), y - 0.33, 3.65), L['led_cool'])
    mb.box((10.05, 0.3, 0.95), (0, y - 0.15, 7.0), L['graphite'])                               # header
    mb.box((9.6, 1.1, 0.45), (0, y - 0.55, 0.225), L['graphite'])                               # plinth
    mb.box((9.6, 0.03, 0.02), (0, y - 1.11, 0.43), L['brushed'])
    mb.build('HERO_DigitalTwin_Surround', hero, bevel=0.01)
    wall_text('DigitalTwinTitle', 'T_Decal_DigitalTwin.png', 0.42, (0.45, y - 0.31, 7.0), 0)
    kit.decal_plane('DEC_DigitalTwin_Insignia', rm.decal('Insignia', 'T_Decal_Insignia.png'), 0.7, 0.7, C('decals'),
                    (-2.9, y - 0.31, 7.0), (math.radians(90), 0, 0))
    con = kit.console('PROP_DigitalTwin_Console', L, sub('02_PROPS/Hangar/Stations'), w=3.2, dpt=0.9)
    kit.place(con, (0, Y1 - 3.4, 0), 0)
    screen_quad('DigitalTwinConsole', 'T_Screen_DigitalTwin.png', 2.9, 0.62, (0, Y1 - 3.4 - 0.01, 0.966), (math.radians(18), 0, 0), 1.6)
    bb.rf.create_marker('INT_DigitalTwin', (0, Y1 - 4.3, 0), C('game'), 'SINGLE_ARROW', 0.6)
    floor_decal('Step06', 'T_Decal_Step06.png', 0.5, (0.55, Y1 - 4.55))

# ============================================================ DOORS / GLASS / SIGNS
def build_openings(L):
    col = sub('01_ARCH/Hangar/Openings')
    # sectional hangar door (rover exit, west)
    mb = kit.MB()
    for i in range(14):
        mb.box((0.12, 7.9, 0.48), (X0 - 0.05, 44.0, 0.25 + i * 0.5), L['painted_dark'])
    for sy in (-1, 1): mb.box((0.18, 0.2, 7.0), (X0 + 0.02, 44.0 + sy * 4.05, 3.5), L['graphite'])
    mb.cyl(0.11, 0.22, (X0 + 0.35, 44.0, 7.95), L['status_amber'], segs=20)
    mb.build('MOD_HangarDoor', col, bevel=0.006)
    for sy in (-1, 1):
        kit.decal_plane(f'DEC_HangarDoor_Jamb{sy}', rm.decal('Hazard', 'T_Decal_Hazard.png'), 7.0, 0.22, C('decals'),
                        (X0 + 0.125, 44.0 + sy * 4.05, 3.5), (math.radians(90), math.radians(90), math.radians(90)))
    floor_decal('HangarDoorFloor', 'T_Decal_Hazard.png', 8.0, (X0 + 0.55, 44.0), 90)
    wall_text('FlightOps', 'T_Decal_FlightOps.png', 0.38, (X0 + 0.52, 44.0, 7.4), 90)
    # mullions on the Mission Control glass wall
    mb = kit.MB()
    for y in (42.0, 44.0, 46.0, 48.0, 50.0): mb.box((0.16, 0.08, 2.7), (X1 - 0.02, y, 1.0 + 1.3), L['graphite'])
    for z in (1.0, 3.6): mb.box((0.2, 8.1, 0.1), (X1 - 0.02, 46.0, z), L['graphite'])
    mb.build('MOD_GlassWall_Mullions', col, bevel=0.004)
    # door portals
    for nm, (cx, cy, w, h, axis) in {'Entry': (0.0, Y0, 2.6, 2.9, 'x'), 'MC': (X1, 52.6, 1.8, 2.4, 'y')}.items():
        mb = kit.MB()
        for s in (-1, 1):
            if axis == 'x': mb.box((0.12, 0.16, h + 0.12), (cx + s * (w / 2 + 0.06), cy + 0.04, (h + 0.12) / 2), L['graphite'])
            else: mb.box((0.16, 0.12, h + 0.12), (cx - 0.04, cy + s * (w / 2 + 0.06), (h + 0.12) / 2), L['graphite'])
        if axis == 'x': mb.box((w + 0.24, 0.16, 0.12), (cx, cy + 0.04, h + 0.06), L['graphite'])
        else: mb.box((0.16, w + 0.24, 0.12), (cx - 0.04, cy, h + 0.06), L['graphite'])
        mb.build(f'MOD_DoorPortal_{nm}', col, bevel=0.006)
    wall_text('MCSign', 'T_Decal_MissionControl.png', 0.2, (X1 - 0.06, 52.6, 2.85), -90)

def build_props(L):
    p = sub('02_PROPS/Hangar')
    cab = kit.cabinet('PROP_EquipmentCabinet', L, p)
    for i, (x, y, r) in enumerate(CABINETS):
        o = cab if i == 0 else kit.instance(cab, f'PROP_EquipmentCabinet_{i}', p, (0, 0, 0))
        if i == 0: o.name = 'PROP_EquipmentCabinet_0'
        kit.place(o, (x, y, 0), r)
    tc = kit.tool_cart('PROP_ToolCart_0', L, p); kit.place(tc, (-3.4, 38.9, 0), 20)
    kit.place(kit.instance(tc, 'PROP_ToolCart_1', p, (0, 0, 0)), (7.7, 40.4, 0), 90)
    kit.place(kit.cable_reel('PROP_CableReel_0', L, p), (4.45, 40.9, 0), 30)
    st = kit.stanchion('PROP_Stanchion', L, p)
    ys = (40.4, 42.4, 44.4, 46.4, 48.4)
    for i, y in enumerate(ys):
        o = st if i == 0 else kit.instance(st, f'PROP_Stanchion_{i}', p, (0, 0, 0))
        if i == 0: o.name = 'PROP_Stanchion_0'
        kit.place(o, (X0 + 1.6, y, 0))
    belt = kit.MB()
    for a, b in zip(ys, ys[1:]): belt.box((0.012, b - a - 0.09, 0.05), (X0 + 1.6, (a + b) / 2, 0.92), L['yellow'])
    belt.build('PROP_Stanchion_Belts', p, bevel=0)


# ================================================================ POLISH: SERVICE DETAIL
_ATLAS = None
def atlas_plane(name, cell, height, loc, rot, col=None):
    """Small service label cut from the shared atlas (one material for all of them)."""
    global _ATLAS
    import json
    if _ATLAS is None: _ATLAS = json.load(open(os.path.join(rm.TEX, 'decals', 'T_Decal_ServiceAtlas.json')))
    u0, v0, u1, v1 = _ATLAS['cells'][cell]; w = height * _ATLAS['cell_aspect']
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((-w / 2, -height / 2, 0), (w / 2, -height / 2, 0), (w / 2, height / 2, 0), (-w / 2, height / 2, 0))]
    f = bm.faces.new(vs); uv = bm.loops.layers.uv.verify()
    for l, c in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))): l[uv].uv = c
    bm.to_mesh(me); bm.free(); me.materials.append(rm.atlas_decal())
    o = bpy.data.objects.new(name, me); (col or C('decals')).objects.link(o); o.location = loc; o.rotation_euler = rot
    return o

def connected_ports():
    out = set()
    for (x, y, _) in bb.STATIONS.values():
        a = math.atan2(y - bb.ROVER[1], x - bb.ROVER[0])
        out.add(min(range(6), key=lambda i: abs(math.atan2(math.sin(math.radians(30 + 60 * i) - a), math.cos(math.radians(30 + 60 * i) - a)))))
    return out

def build_service_details():
    R, Hp, (cx, cy) = bb.PLAT_R, bb.PLAT_H, bb.ROVER
    def ring_pt(deg, r, z):
        a = math.radians(deg); return (cx + math.cos(a) * r, cy + math.sin(a) * r, z)
    live = connected_ports()
    for i in range(6):                                   # port IDs, cautions beside the live ones (text reads from outside)
        a = 30 + 60 * i
        atlas_plane(f'DEC_PortLabel_P{i + 1}', f'PORT_P{i + 1}', 0.15, ring_pt(a + 9, R + 0.78, 0.006), (0, 0, math.radians(a + 90)))
        if i in live:
            atlas_plane(f'DEC_PortCaution_P{i + 1}', 'CAUTION_LIVE', 0.15, ring_pt(a - 9, R + 0.78, 0.006), (0, 0, math.radians(a + 90)))
    for i, a in enumerate((150, 270, 30)):              # hatch labels on the hatch lids
        atlas_plane(f'DEC_HatchLabel_H{i + 1}', f'HATCH_H{i + 1}', 0.17, ring_pt(a, 2.35, Hp + 0.0105), (0, 0, math.radians(a + 90)))
    atlas_plane('DEC_TurntableLoad', 'LOAD', 0.15, ring_pt(255, R - 0.22, Hp + 0.003), (0, 0, math.radians(255 + 90)))
    atlas_plane('DEC_GroundPoint', 'GROUND', 0.15, ring_pt(180, R + 0.78, 0.006), (0, 0, math.radians(180 + 90)))
    for side, i in (('E', 0), ('E', 1), ('W', 0), ('W', 3), ('E', 3)):          # QC stickers on columns
        if f'MOD_Column_{side}{i}' not in bpy.data.objects: continue
        o = bpy.data.objects[f'MOD_Column_{side}{i}']; s = 1 if side == 'W' else -1
        atlas_plane(f'DEC_QC_Column_{side}{i}', 'INSPECT', 0.12, (o.location.x + s * 0.29, o.location.y + 0.16, 1.55), (math.radians(90), 0, math.radians(90 * s)))
    atlas_plane('DEC_Torque_ColumnE1', 'TORQUE', 0.09, (X1 - 0.32 - 0.29, COL_Y[1] - 0.12, 0.42), (math.radians(90), 0, math.radians(-90)))
    for i, (x, y, r) in enumerate(CABINETS):           # equipment IDs + QC on cabinet doors
        fx, fy = math.sin(math.radians(r)), -math.cos(math.radians(r))
        atlas_plane(f'DEC_Cabinet_EQ0{i + 1}', f'EQ0{i + 1}', 0.11, (x + fx * 0.316, y + fy * 0.316, 1.72), (math.radians(90), 0, math.radians(r)))
    swl = atlas_plane('DEC_Crane_SWL', 'CRANE_SWL', 0.32, (2.2, 47.0 - 0.378, 8.25), (math.radians(90), 0, 0))
    swl['rf_overhead'] = True

def build_floor_wear():
    """Very light wear where people stand and carts roll. Roughness, not dirt."""
    wear = rm.decal('FloorWear', 'T_Decal_FloorWear.png', 0.62)
    spots = [(*bb.station_int(x, y), 2.2) for (x, y, _) in bb.STATIONS.values()]
    spots += [(*bb.Frame(*bb.CONFIG_POS, bb.CONFIG_ROT).at(0, -0.75)[:2], 1.9), (0, Y1 - 4.2, 2.6), (0, 38.4, 3.2), (X0 + 2.2, 44.0, 3.4)]
    for i, (x, y, s) in enumerate(spots):
        kit.decal_plane(f'DEC_FloorWear_{i:02d}', wear, s, s, C('decals'), (x, y, 0.0025), (0, 0, math.radians(i * 37)))
    sc = rm.decal('Scuffs', 'T_Decal_Scuffs.png', 0.6)
    for i, (x, y, r, l) in enumerate(((-2.4, 39.8, 20, 2.6), (X0 + 2.6, 42.5, 90, 4.0), (6.4, 40.6, 75, 2.2))):
        kit.decal_plane(f'DEC_FloorScuff_{i}', sc, l, l / 4, C('decals'), (x, y, 0.0028), (0, 0, math.radians(r)))

def split_mission_path():
    """One path object per room so each room exports with exactly its own section."""
    old = bpy.data.objects.get('DEC_MissionPath')
    if old: bpy.data.objects.remove(old, do_unlink=True)
    rooms = [('Hangar', bb.HANG), ('MissionControl', bb.MC), ('MarsIntel', bb.INTEL), ('Briefing', bb.BRIEF), ('Corridor01', bb.C1), ('Corridor02', bb.C2)]
    def room_of(p):
        for nm, (x0, x1, y0, y1, _) in rooms:
            if x0 - 0.26 <= p[0] <= x1 + 0.26 and y0 - 0.26 <= p[1] <= y1 + 0.26: return nm
        return 'Outside'
    pts = bb.mission_path(); pieces = []
    for p, q in zip(pts, pts[1:]):
        ts = {0.0, 1.0}
        for _, (x0, x1, y0, y1, _h) in rooms:
            for axis, vals in ((0, (x0, x1)), (1, (y0, y1))):
                for v in vals:
                    d = q[axis] - p[axis]
                    if abs(d) > 1e-9 and 0 < (v - p[axis]) / d < 1: ts.add((v - p[axis]) / d)
        ts = sorted(ts)
        for a, b in zip(ts, ts[1:]):
            A = (p[0] + (q[0] - p[0]) * a, p[1] + (q[1] - p[1]) * a); B = (p[0] + (q[0] - p[0]) * b, p[1] + (q[1] - p[1]) * b)
            pieces.append((room_of(((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)), A, B))
    paint = rm.pbr('MAT_Paint_Orange', '#C2501C', 0.55); runs = []
    for room, A, B in pieces:
        if runs and runs[-1][0] == room and math.dist(runs[-1][1][-1], A) < 1e-6: runs[-1][1].append(B)
        else: runs.append((room, [A, B]))
    for k, (room, line) in enumerate(runs):
        rf.create_path_strip(f'DEC_MissionPath_{room}_{k:02d}', line, 0.12, C('decals'), paint)

# ===================================================================== LIGHTING
def build_lighting():
    col = sub('04_LIGHTS/LIGHTSET_Day_Operational')
    for i, y in enumerate((37.4, 41.8, 46.2, 50.6)):                        # high-bay fixtures
        for j, x in enumerate((-4.6, 0.0, 4.6)):
            l = rf.create_area_light(f'LGT_HighBay_{i}{j}', (x, y, 8.33), 2.3, 400, col, '#FFF1E0', size_y=0.3)
            l.rotation_euler = (0, 0, 0)
    tgt = (bb.ROVER[0], bb.ROVER[1], 1.0)
    rf.create_area_light('LGT_Hero_Key', (-3.6, 38.0, 7.2), 2.6, 740, col, '#FFF4E8', target=tgt)
    rf.create_area_light('LGT_Hero_Fill', (5.2, 39.5, 4.6), 4.0, 300, col, '#E8F0FF', target=tgt, size_y=2.0)
    rf.create_area_light('LGT_Hero_Rim', (0.8, 47.8, 5.6), 3.0, 520, col, '#DDE8FF', target=tgt, size_y=1.0)
    for nm, deg in (('LGT_Hero_Key', 60), ('LGT_Hero_Fill', 70), ('LGT_Hero_Rim', 85)):
        bpy.data.lights[nm].spread = math.radians(deg)                       # beam stays on the rover, not the walls
    for name, (x, y, _) in bb.STATIONS.items():                             # bay downlights onto the hardware
        rot = math.degrees(math.atan2(bb.ROVER[1] - y, bb.ROVER[0] - x)) + 90
        f = bb.Frame(x, y, rot)
        l = rf.create_area_light(f'LGT_Station_{name}', f.at(0, 1.05, 2.18), 1.8, 78, col, '#FFE9D0', size_y=0.2)
        l.rotation_euler.z = math.radians(rot)
    w = bpy.context.scene.world
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.018, 0.02, 0.024, 1); bg.inputs['Strength'].default_value = 1.0

def build_cameras_extra():
    c = C('cams')
    rf.create_camera('CAM_Hangar_Station', (-2.6, 45.8, 1.75), (-6.3, 49.3, 1.3), c, lens=28)

def main(save=True, skip=()):
    """Hangar near-final, the other rooms greybox. build_facility.py calls this with save=False and
    skip=(Phase 5 rooms), then adds those rooms; run on its own it reproduces the locked Hangar file."""
    bb.main(save=False, hangar=False, skip=skip)
    L = rm.build()
    build_shell(L); build_structure(L); build_crane(L); build_lights_fixtures(L)
    build_turntable(L); build_stations(L); build_mission_config(L); build_digital_twin(L)
    build_openings(L); build_props(L); build_lighting(); build_cameras_extra()
    build_service_details(); build_floor_wear(); split_mission_path()          # final polish pass
    for o in bpy.data.objects:                       # scale figures stay in the file, out of beauty renders
        if o.name.startswith('REF_Human'): o.hide_render = True
    if save:
        out = os.path.join(rf.ROOT, 'blender', 'RF_Facility.blend')
        rf.save(out)
        print('HANGAR_OK objects=', len(bpy.data.objects), 'saved', out)
    return L

if __name__ == '__main__':
    main()
