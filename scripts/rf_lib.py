"""
rf_lib.py - shared helpers for the Mission: Red Frontier Blender pipeline.

Conventions
  * 1 Blender unit = 1 m. +Y = north (facility flow direction), +Z = up.
  * Box helpers build real geometry at true size (object scale stays 1.0) with the
    origin at the bottom-centre, so pieces drop onto the floor and export cleanly.
  * Every object gets a meaningful name; nothing is left as Cube.001.
  * Walls are built OUTSIDE a room's footprint so interior dimensions are exact.
"""
import bpy, bmesh, math
from mathutils import Vector

ROOT = r"D:\RedFrontier"
WALL_T = 0.25          # wall thickness
SLAB_T = 0.30          # floor / ceiling slab thickness

# --------------------------------------------------------------------------- scene

def reset_scene():
    """Start from an empty file so every build script is safe to rerun."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 1.0
    return sc


def collection(path):
    """collection('RF_FACILITY/01_ARCH/Hangar') -> nested collection, created on demand."""
    parent = bpy.context.scene.collection
    col = None
    for name in path.split('/'):
        col = bpy.data.collections.get(name)
        if col is None:
            col = bpy.data.collections.new(name)
        if col.name not in parent.children:
            parent.children.link(col)
        parent = col
    return col


def link(obj, col):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj

# ------------------------------------------------------------------------ materials

def hex_rgb(h):
    h = h.lstrip('#')
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, 1.0)


def create_material(name, color='#cccccc', rough=0.6, metal=0.0, emit=None, emit_strength=0.0, alpha=1.0):
    """Principled material; reruns update the existing one instead of duplicating."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    rgba = hex_rgb(color)
    b.inputs['Base Color'].default_value = rgba
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = hex_rgb(emit)
        b.inputs['Emission Strength'].default_value = emit_strength
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        if hasattr(m, 'surface_render_method'):
            m.surface_render_method = 'BLENDED'
    # Workbench (greybox renders) reads the viewport colour
    m.diffuse_color = hex_rgb(emit) if emit else rgba
    if alpha < 1.0:
        m.diffuse_color = (*m.diffuse_color[:3], alpha)
    m.roughness = rough
    m.metallic = metal
    return m


def assign_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj

# ------------------------------------------------------------------------ geometry

def _box_mesh(name, sx, sy, sz):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx; v.co.y *= sy; v.co.z = (v.co.z + 0.5) * sz   # origin at bottom-centre
    bm.to_mesh(me); bm.free()
    return me


def create_box(name, size, loc, col, mat=None, rot_z=0.0, bevel=0.0):
    """size=(x,y,z) metres, loc = bottom-centre position."""
    obj = bpy.data.objects.new(name, _box_mesh(name, *size))
    obj.location = loc
    obj.rotation_euler.z = math.radians(rot_z)
    col.objects.link(obj)
    if mat: assign_material(obj, mat)
    if bevel > 0: create_bevel_modifier(obj, bevel)
    return obj


def create_cylinder(name, radius, height, loc, col, mat=None, verts=48, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=radius, radius2=radius, depth=height)
    for v in bm.verts: v.co.z += height / 2
    bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(name, me); obj.location = loc
    col.objects.link(obj)
    for p in me.polygons: p.use_smooth = len(p.vertices) == 4
    if mat: assign_material(obj, mat)
    if bevel > 0: create_bevel_modifier(obj, bevel)
    return obj


def create_panel(name, w, h, loc, facing, col, mat=None, depth=0.02):
    """Thin vertical panel (screens, signs, glass). facing = 'N','S','E','W' = direction its face points."""
    rot = {'S': 0, 'N': 180, 'E': 90, 'W': -90}[facing]
    obj = create_box(name, (w, depth, h), loc, col, mat, rot_z=rot)
    return obj


def create_bevel_modifier(obj, width=0.01, segments=2):
    """Clean edge treatment + weighted normals (game-friendly, no subdivision)."""
    if 'Bevel' not in obj.modifiers:
        b = obj.modifiers.new('Bevel', 'BEVEL')
        b.width = width; b.segments = segments; b.limit_method = 'ANGLE'
        b.harden_normals = True
    if 'WeightedNormal' not in obj.modifiers:
        w = obj.modifiers.new('WeightedNormal', 'WEIGHTED_NORMAL'); w.keep_sharp = True
    for p in obj.data.polygons: p.use_smooth = True
    return obj


def create_wall(name, a, b, height, col, mat, openings=(), t=WALL_T, z0=0.0, glass_mat=None):
    """
    Axis-aligned wall from point a to point b (inner face on the a-b line, thickness pushed
    to the side given by the sign of t). openings: dicts with
        off  - distance from a to the opening centre
        w, h - opening size
        sill - bottom of opening (0 for doors)
        glass - fill opening with a glass pane
    Built from solid segments (no booleans) so topology stays clean.
    """
    ax, ay = a; bx, by = b
    along_x = abs(by - ay) < 1e-6
    length = abs(bx - ax) if along_x else abs(by - ay)
    sgn = 1 if (bx - ax if along_x else by - ay) > 0 else -1
    ops = sorted(openings, key=lambda o: o['off'])
    pieces = []          # (start, end, z_bottom, z_top)
    cur = 0.0
    for o in ops:
        s, e = o['off'] - o['w'] / 2, o['off'] + o['w'] / 2
        if s > cur: pieces.append((cur, s, 0.0, height))
        sill = o.get('sill', 0.0)
        if sill > 0: pieces.append((s, e, 0.0, sill))
        if sill + o['h'] < height: pieces.append((s, e, sill + o['h'], height))
        if o.get('glass') and glass_mat:
            pieces.append(('glass', s, e, sill, sill + o['h']))
        cur = e
    if cur < length: pieces.append((cur, length, 0.0, height))
    objs = []
    for i, p in enumerate(pieces):
        glass = p[0] == 'glass'
        s, e, zb, zt = p[1:] if glass else p
        seg_len = e - s
        mid = (s + e) / 2 * sgn
        thick = 0.03 if glass else abs(t)
        off_t = (t / 2) if not glass else (t / 2)
        if along_x:
            size = (seg_len, thick, zt - zb); loc = (ax + mid, ay + off_t, z0 + zb)
        else:
            size = (thick, seg_len, zt - zb); loc = (ax + off_t, ay + mid, z0 + zb)
        nm = f"{name}_Glass{i:02d}" if glass else f"{name}_{i:02d}"
        objs.append(create_box(nm, size, loc, col, glass_mat if glass else mat))
    return objs


def create_room(name, x0, x1, y0, y1, h, col, mats, openings=None, skip=(), ceiling=True, ceil_col=None):
    """
    Rectangular room: floor slab, ceiling slab, four walls outside the footprint.
    openings: {'N': [...], 'S': [...], 'E': [...], 'W': [...]} offsets measured from the
    west end (N/S walls) or south end (E/W walls).
    """
    openings = openings or {}
    t = WALL_T
    create_box(f"{name}_Floor", (x1 - x0 + 2 * t, y1 - y0 + 2 * t, SLAB_T), ((x0 + x1) / 2, (y0 + y1) / 2, -SLAB_T), col, mats['floor'])
    if ceiling:
        create_box(f"{name}_Ceiling", (x1 - x0 + 2 * t, y1 - y0 + 2 * t, SLAB_T), ((x0 + x1) / 2, (y0 + y1) / 2, h), ceil_col or col, mats['ceiling'])
    g = mats.get('glass')
    if 'S' not in skip: create_wall(f"{name}_WallS", (x0 - t, y0), (x1 + t, y0), h, col, mats['wall'], [dict(o, off=o['off'] + t) for o in openings.get('S', [])], t=-t, glass_mat=g)
    if 'N' not in skip: create_wall(f"{name}_WallN", (x0 - t, y1), (x1 + t, y1), h, col, mats['wall'], [dict(o, off=o['off'] + t) for o in openings.get('N', [])], t=t, glass_mat=g)
    if 'W' not in skip: create_wall(f"{name}_WallW", (x0, y0), (x0, y1), h, col, mats['wall'], openings.get('W', []), t=-t, glass_mat=g)
    if 'E' not in skip: create_wall(f"{name}_WallE", (x1, y0), (x1, y1), h, col, mats['wall'], openings.get('E', []), t=t, glass_mat=g)

# ----------------------------------------------------------------- text / markings

def create_text_placeholder(name, body, loc, facing, size, col, mat, align='CENTER', flat=False):
    """Text label. facing as in create_panel; flat=True lays it on the floor reading northward."""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body; cu.size = size; cu.align_x = align; cu.align_y = 'CENTER'
    obj = bpy.data.objects.new(name, cu)
    obj.location = loc
    if flat:
        obj.rotation_euler = (0, 0, math.radians({'N': 0, 'S': 180, 'E': -90, 'W': 90}[facing]))
    else:
        obj.rotation_euler = (math.radians(90), 0, math.radians({'S': 0, 'N': 180, 'E': 90, 'W': -90}[facing]))
    col.objects.link(obj)
    cu.materials.append(mat)
    return obj


def create_floor_marking(name, points, width, col, mat, z=0.004):
    """Polyline strip on the floor (paths, zone outlines). points: [(x,y), ...]."""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        d = Vector((bx - ax, by - ay, 0)); n = Vector((-d.y, d.x, 0)).normalized() * width / 2
        a, b = Vector((ax, ay, z)), Vector((bx, by, z))
        ext = d.normalized() * width / 2
        vs = [bm.verts.new(p) for p in (a - ext - n, b + ext - n, b + ext + n, a - ext + n)]
        bm.faces.new(vs)
    bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(name, me); col.objects.link(obj)
    assign_material(obj, mat)
    return obj


def create_path_strip(name, points, width, col, mat, z=0.004):
    """Continuous mitred floor strip: shared vertices at joints, no overlapping faces
    (overlapping coplanar quads render as black blotches in Cycles and flicker in Godot)."""
    pts = []
    for p in points:                                              # drop duplicates and collinear interior points
        p = Vector((p[0], p[1], 0))
        if pts and (p - pts[-1]).length < 1e-4: continue
        if len(pts) >= 2:
            d1 = (pts[-1] - pts[-2]).normalized(); d2 = (p - pts[-1]).normalized()
            if d1.dot(d2) > 0.9999: pts[-1] = p; continue
        pts.append(p)
    me = bpy.data.meshes.new(name); bm = bmesh.new(); hw = width / 2; rows = []
    for i, p in enumerate(pts):
        dirs = []
        if i > 0: dirs.append((p - pts[i - 1]).normalized())
        if i < len(pts) - 1: dirs.append((pts[i + 1] - p).normalized())
        ns = [Vector((-d.y, d.x, 0)) for d in dirs]
        n = (sum(ns, Vector()) / len(ns)).normalized()
        scale = hw / max(0.3, n.dot(ns[0]))                        # miter length, clamped at sharp turns
        zi = z + i * 0.0003                                            # each leg 0.3 mm higher: self-crossings never coplanar
        rows.append((bm.verts.new((p.x - n.x * scale, p.y - n.y * scale, zi)), bm.verts.new((p.x + n.x * scale, p.y + n.y * scale, zi))))
    for (a0, a1), (b0, b1) in zip(rows, rows[1:]):
        bm.faces.new((a0, b0, b1, a1))
    bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(name, me); col.objects.link(obj)
    assign_material(obj, mat)
    return obj


def create_floor_ring(name, radius, width, loc, col, mat, segs=96, z=0.004):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    ring = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        ring.append((bm.verts.new((math.cos(a) * (radius - width / 2), math.sin(a) * (radius - width / 2), z)),
                     bm.verts.new((math.cos(a) * (radius + width / 2), math.sin(a) * (radius + width / 2), z))))
    for i in range(segs):
        (a0, a1), (b0, b1) = ring[i], ring[(i + 1) % segs]
        bm.faces.new((a0, b0, b1, a1))
    bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(name, me); obj.location = loc; col.objects.link(obj)
    assign_material(obj, mat)
    return obj

# --------------------------------------------------------------- lights / cameras

def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def create_camera(name, loc, target, col, lens=24.0):
    cam = bpy.data.cameras.new(name); cam.lens = lens; cam.clip_start = 0.05; cam.clip_end = 200
    cam.sensor_width = 36
    obj = bpy.data.objects.new(name, cam); obj.location = loc
    col.objects.link(obj); look_at(obj, target)
    return obj


def create_area_light(name, loc, size, energy, col, color='#ffffff', target=None, shape='RECTANGLE', size_y=None):
    l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.shape = shape
    l.size = size; l.size_y = size_y or size; l.color = hex_rgb(color)[:3]
    obj = bpy.data.objects.new(name, l); obj.location = loc; col.objects.link(obj)
    if target: look_at(obj, target)
    return obj


def create_emissive_screen(name, w, h, loc, facing, col, mat, frame_mat=None, frame=0.06):
    """Screen = dark bezel box + emissive face slightly proud of it."""
    if frame_mat:
        create_panel(f"{name}_Bezel", w + 2 * frame, h + 2 * frame, (loc[0], loc[1], loc[2] - frame), facing, col, frame_mat, depth=0.06)
    off = {'S': (0, -0.035), 'N': (0, 0.035), 'E': (0.035, 0), 'W': (-0.035, 0)}[facing]
    return create_panel(name, w, h, (loc[0] + off[0], loc[1] + off[1], loc[2]), facing, col, mat, depth=0.01)


def create_marker(name, loc, col, kind='PLAIN_AXES', size=0.5):
    e = bpy.data.objects.new(name, None); e.empty_display_type = kind; e.empty_display_size = size
    e.location = loc; col.objects.link(e)
    return e


def save(path):
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
