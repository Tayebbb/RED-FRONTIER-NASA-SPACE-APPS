"""
rf_room.py - helpers shared by the Phase 5 room builders (Mission Control, Mars Intelligence, ...).

Keeps every room on the Hangar's screen and label language without copying code between builders.
"""
import bpy, bmesh, math
import rf_kit as kit
import build_blockout as bb
import build_hangar as bh

def emit_states(mat, day, launch):
    """Emission strengths per light set; rf_lightsets.apply() switches them, export carries them to Godot."""
    mat['rf_emit_day'], mat['rf_emit_launch'] = day, launch
    return mat

def uv_quad(name, mat, w, h, uv, col, loc, rot):
    """Flat quad showing one cell (u0, v0, u1, v1) of an atlas texture."""
    u0, v0, u1, v1 = uv
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    f = bm.faces.new([bm.verts.new(p) for p in ((-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0))])
    uvl = bm.loops.layers.uv.verify()
    for l, c in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))): l[uvl].uv = c
    bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = loc; o.rotation_euler = rot
    return o

def atlas_cells(cols, rows):
    """UV rects of a cols x rows atlas, row-major from the top-left cell (as the PNG is drawn)."""
    return [(c / cols, 1 - (r + 1) / rows, (c + 1) / cols, 1 - r / rows) for r in range(rows) for c in range(cols)]

def wall_screen(L, prefix, name, image, w, h, loc, facing, strength, col, border=0.1):
    """Bezel + content quad. loc = bottom-centre of the bezel front; facing = kit rot_z (0 faces -Y).
    Objects PROP_<prefix>_<name> / UI_<prefix>_<name>; returns the screen material."""
    fr = kit.display_frame(f'PROP_{prefix}_{name}', w, h, L['screen_dark'], L, col, border=border, depth=0.12)
    kit.place(fr, loc, facing)
    f = bb.Frame(loc[0], loc[1], facing)
    bh.screen_quad(f'{prefix}_{name}', image, w, h, f.at(0, -0.01, loc[2] + border + h / 2), (math.radians(90), 0, math.radians(facing)), strength)
    return bpy.data.materials[f'MAT_Screen_{prefix}_{name}']

def door_portal(name, x, y, w, h, axis, sign, L, col):
    """Graphite portal around a door on the room side of a wall. axis 'x' = wall along X (N/S walls),
    'y' = wall along Y (E/W walls); sign = +1/-1 direction from the wall line into the room."""
    mb = kit.MB(); d = 0.04 * sign
    for s in (-1, 1):
        if axis == 'x': mb.box((0.12, 0.16, h + 0.12), (x + s * (w / 2 + 0.06), y + d, (h + 0.12) / 2), L['graphite'])
        else: mb.box((0.16, 0.12, h + 0.12), (x + d, y + s * (w / 2 + 0.06), (h + 0.12) / 2), L['graphite'])
    if axis == 'x': mb.box((w + 0.24, 0.16, 0.12), (x, y + d, h + 0.06), L['graphite'])
    else: mb.box((0.16, w + 0.24, 0.12), (x + d, y, h + 0.06), L['graphite'])
    return mb.build(name, col, bevel=0.006)

def tag_room(before, room):
    """Room ownership for export: everything created since `before` (a set of object names)."""
    new = set(bpy.data.objects.keys()) - before
    for n in new: bpy.data.objects[n]['rf_room'] = room
    return len(new)
