"""
rf_kit.py - modular kit generators for the Red Frontier facility.

Every piece is built from oriented boxes / cylinders in one bmesh (MeshBuilder), gets
metre-scaled box UVs, a light bevel + weighted normals, and named material slots from
rf_materials. Origins sit at the bottom-centre (props) or the wall line (cladding).
Pieces are reused as linked duplicates, which export as glTF mesh instances for Godot.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Euler
import rf_lib as rf

# ------------------------------------------------------------------ mesh builder
class MB:
    """Accumulates primitives into one bmesh with per-face material slots."""
    def __init__(self):
        self.bm = bmesh.new(); self.mats = []
    def _slot(self, mat):
        if mat not in self.mats: self.mats.append(mat)
        return self.mats.index(mat)
    def _tag(self, n0, mat):
        self.bm.faces.ensure_lookup_table()
        i = self._slot(mat)
        for f in self.bm.faces[n0:]: f.material_index = i
    def box(self, size, center, mat, rot=(0, 0, 0)):
        n0 = len(self.bm.faces)
        m = Matrix.Translation(center) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((*size, 1))
        bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        self._tag(n0, mat); return self
    def beam(self, p0, p1, w, h, mat):
        p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length
        x = d.normalized(); up = Vector((0, 0, 1)) if abs(x.z) < 0.95 else Vector((0, 1, 0))
        y = up.cross(x).normalized(); z = x.cross(y)
        R = Matrix((x, y, z)).transposed().to_4x4()
        n0 = len(self.bm.faces)
        bmesh.ops.create_cube(self.bm, size=1.0, matrix=Matrix.Translation((p0 + p1) / 2) @ R @ Matrix.Diagonal((L, w, h, 1)))
        self._tag(n0, mat); return self
    def cyl(self, r, h, center, mat, segs=32, axis='Z', r2=None):
        n0 = len(self.bm.faces)
        rot = {'Z': Matrix(), 'X': Matrix.Rotation(math.pi / 2, 4, 'Y'), 'Y': Matrix.Rotation(math.pi / 2, 4, 'X')}[axis]
        bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h,
                              matrix=Matrix.Translation(center) @ rot)
        self._tag(n0, mat)
        for f in self.bm.faces[n0:]: f.smooth = len(f.verts) == 4
        return self
    def ring(self, r_in, r_out, h, z0, mat, segs=96):
        """Flat annulus solid (turntable bands, grooves)."""
        n0 = len(self.bm.faces); vs = []
        for i in range(segs):
            a = 2 * math.pi * i / segs; c, s = math.cos(a), math.sin(a)
            vs.append([self.bm.verts.new((c * r, s * r, z)) for r, z in ((r_in, z0), (r_out, z0), (r_out, z0 + h), (r_in, z0 + h))])
        for i in range(segs):
            a, b = vs[i], vs[(i + 1) % segs]
            for k in range(4):
                self.bm.faces.new((a[k], b[k], b[(k + 1) % 4], a[(k + 1) % 4]))
        self._tag(n0, mat); return self
    def build(self, name, col, bevel=0.006, uv_tile=1.0, smooth=False):
        me = bpy.data.meshes.new(name)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        uv_box(self.bm, uv_tile)
        self.bm.to_mesh(me); self.bm.free()
        for m in self.mats: me.materials.append(m)
        obj = bpy.data.objects.new(name, me); col.objects.link(obj)
        if bevel > 0:
            b = obj.modifiers.new('Bevel', 'BEVEL'); b.width = bevel; b.segments = 2
            b.limit_method = 'ANGLE'; b.angle_limit = math.radians(35); b.harden_normals = True
            obj.modifiers.new('WeightedNormal', 'WEIGHTED_NORMAL').keep_sharp = True
            for p in me.polygons: p.use_smooth = True
        return obj

def uv_box(bm, tile=1.0):
    """Box-projected UVs in metres / tile, chosen per face by dominant normal."""
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            co = l.vert.co
            u, v = {0: (co.y, co.z), 1: (co.x, co.z), 2: (co.x, co.y)}[ax]
            l[uv].uv = (u / tile, v / tile)

def place(obj, loc=(0, 0, 0), rot_z=0.0):
    obj.location = loc; obj.rotation_euler.z = math.radians(rot_z); return obj

def instance(src, name, col, loc, rot_z=0.0):
    """Linked duplicate (shared mesh) - becomes a glTF mesh instance."""
    o = bpy.data.objects.new(name, src.data); col.objects.link(o)
    for m in src.modifiers:
        n = o.modifiers.new(m.name, m.type)
        for k in ('width', 'segments', 'limit_method', 'angle_limit', 'harden_normals', 'keep_sharp'):
            if hasattr(m, k): setattr(n, k, getattr(m, k))
    return place(o, loc, rot_z)

def decal_plane(name, mat, w, h, col, loc, rot=(0, 0, 0)):
    """Flat alpha decal quad, UV 0..1. Default lies on the floor facing +Z."""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0))]
    f = bm.faces.new(vs); uv = bm.loops.layers.uv.verify()
    for l, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): l[uv].uv = c
    bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new(name, me); col.objects.link(o); o.location = loc; o.rotation_euler = rot
    return o

def wall_decal(name, mat, img_size, height, col, loc, facing_rot_z):
    """Vertical decal sized from its image aspect; faces direction given by rot_z (0 = faces -Y)."""
    w = height * img_size[0] / img_size[1]
    return decal_plane(name, mat, w, height, col, loc, (math.radians(90), 0, math.radians(facing_rot_z)))

# ===================================================================== ARCHITECTURE
def cladding(name, length, height, L, col, lower=3.0, openings=(), tile_low=1.1, tile_up=2.2):
    """
    Wall cladding along +X from 0..length, wall face at y=0, panels proud toward -Y (room side).
    Lower band: warm-white panels 2 rows (kick plate + trim rail with LED wash under it).
    Upper band: cool-grey large panels. openings: (x0, x1, z0, z1) rects left uncovered.
    """
    mb = MB(); gap = 0.014; d = 0.035
    def blocked(x0, x1, z0, z1):
        return any(x0 < ox1 and x1 > ox0 and z0 < oz1 and z1 > oz0 for ox0, ox1, oz0, oz1 in openings)
    xs = sorted({0.0, length, *[min(max(v, 0.0), length) for o in openings for v in (o[0], o[1])]})
    for a, b in zip(xs, xs[1:]):                                   # backer sheet, open where the wall is open
        cuts = [(o[2], o[3]) for o in openings if o[0] < (a + b) / 2 < o[1]]
        for z0, z1 in _spans(0, height, cuts):
            mb.box((b - a, 0.012, z1 - z0), ((a + b) / 2, -0.006, (z0 + z1) / 2), L['backer'])
    # kick plate
    for x0, x1 in _spans(0, length, [(o[0], o[1]) for o in openings if o[2] < 0.2]):
        mb.box((x1 - x0, 0.06, 0.2), ((x0 + x1) / 2, -0.03, 0.1), L['graphite'])
    def panels(z0, z1, rows, tile, variants, bottom=None):
        # variants: panel-to-panel finish variation (deterministic hash, so rebuilds are stable)
        nx = max(1, round(length / tile)); pw = length / nx; ph = (z1 - z0) / rows
        for i in range(nx):
            for j in range(rows):
                x0, x1 = i * pw + gap / 2, (i + 1) * pw - gap / 2; zz0, zz1 = z0 + j * ph + gap / 2, z0 + (j + 1) * ph - gap / 2
                if not blocked(x0, x1, zz0, zz1):
                    mat = bottom if (bottom is not None and j == 0) else variants[(i * 7 + j * 13 + int(length * 10)) % len(variants)]
                    mb.box((x1 - x0, d, zz1 - zz0), ((x0 + x1) / 2, -0.012 - d / 2, (zz0 + zz1) / 2), mat)
    whites = [L[k] for k in ('wall_white', 'wall_white_b', 'wall_white_c') if k in L]
    greys = [L[k] for k in ('wall_grey', 'wall_grey_b', 'wall_grey_c') if k in L]
    panels(0.2, lower, 2, tile_low, whites, bottom=L.get('wall_lower'))
    # trim rail with downward LED wash
    for x0, x1 in _spans(0, length, [(o[0], o[1]) for o in openings if o[2] < lower + 0.15 and o[3] > lower]):
        mb.box((x1 - x0, 0.1, 0.13), ((x0 + x1) / 2, -0.05, lower + 0.065), L['graphite'])
        mb.box((x1 - x0 - 0.04, 0.012, 0.012), ((x0 + x1) / 2, -0.085, lower - 0.004), L['diffuser'])
    panels(lower + 0.13, height, max(1, round((height - lower) / 2.3)), tile_up, greys)
    return mb.build(name, col, bevel=0.004)

def _spans(a, b, cuts):
    """Sub-intervals of [a,b] not covered by cuts."""
    out, cur = [], a
    for c0, c1 in sorted(cuts):
        if c0 > cur: out.append((cur, min(c0, b)))
        cur = max(cur, c1)
    if cur < b: out.append((cur, b))
    return [(x0, x1) for x0, x1 in out if x1 - x0 > 0.05]

def column(name, h, L, col):
    mb = MB()
    mb.box((0.8, 0.8, 0.03), (0, 0, 0.015), L['graphite'])                  # base plate
    mb.box((0.56, 0.56, h - 0.03), (0, 0, 0.03 + (h - 0.03) / 2), L['graphite'])
    for sx in (-1, 1):                                                         # flange reveals
        mb.box((0.02, 0.6, h - 0.4), (sx * 0.29, 0, h / 2), L['backer'])
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.cyl(0.018, 0.03, (sx * 0.33, sy * 0.33, 0.045), L['brushed'], segs=12)   # anchor bolts
    return mb.build(name, col, bevel=0.01)

def truss(name, span, L, col, depth=1.0):
    """Warren roof truss across X, centred; chords 0.22 m, webs every ~1.5 m."""
    mb = MB(); hs = span / 2; n = max(4, round(span / 1.5)); step = span / n
    mb.box((span, 0.22, 0.22), (0, 0, depth / 2), L['graphite'])
    mb.box((span, 0.22, 0.22), (0, 0, -depth / 2), L['graphite'])
    for i in range(n):
        x0, x1 = -hs + i * step, -hs + (i + 1) * step
        a, b = ((x0, 0, -depth / 2 + 0.1), (x1, 0, depth / 2 - 0.1)) if i % 2 == 0 else ((x0, 0, depth / 2 - 0.1), (x1, 0, -depth / 2 + 0.1))
        mb.beam(a, b, 0.12, 0.12, L['graphite'])
        mb.box((0.1, 0.16, depth - 0.2), (x0, 0, 0), L['graphite'])
    return mb.build(name, col, bevel=0.008)

def high_bay_light(name, L, col, drop=1.0):
    """Linear high-bay fixture: graphite housing, warm-white diffuser underneath, two hanger rods."""
    mb = MB()
    mb.box((2.4, 0.36, 0.09), (0, 0, 0.045), L['graphite'])
    mb.box((2.3, 0.28, 0.01), (0, 0, -0.004), L['diffuser'])
    for sx in (-0.9, 0.9): mb.cyl(0.008, drop, (sx, 0, 0.09 + drop / 2), L['graphite'], segs=8)
    return mb.build(name, col, bevel=0.004)

def display_frame(name, w, h, screen_mat, L, col, border=0.12, depth=0.14):
    """Screen with a chamfered graphite bezel and a ledge. Origin bottom-centre, faces -Y."""
    mb = MB()
    mb.box((w + 2 * border, depth, h + 2 * border), (0, depth / 2, h / 2 + border), L['graphite'])
    mb.box((w, 0.01, h), (0, -0.004, h / 2 + border), screen_mat)
    mb.box((w + 2 * border, depth + 0.08, 0.05), (0, depth / 2 - 0.04, 0.025), L['graphite'])     # ledge
    return mb.build(name, col, bevel=0.012)

# ============================================================================ PROPS
def console(name, L, col, w=1.7, dpt=0.75, h=0.95, screen_mat=None, tilt=18):
    """Station console: recessed kick, satin body, angled deck with inset screen, orange interact strip."""
    mb = MB()
    mb.box((w - 0.12, dpt - 0.14, 0.09), (0, 0.03, 0.045), L['backer'])                       # recessed kick
    mb.box((w, dpt, h - 0.09 - 0.05), (0, 0, 0.09 + (h - 0.14) / 2), L['painted'])            # body
    t = math.radians(tilt)
    mb.box((w + 0.02, dpt + 0.04, 0.05), (0, 0, h - 0.025), L['graphite'], rot=(t, 0, 0))     # deck: low front, high back
    mb.box((w - 0.24, dpt - 0.22, 0.012), (0, -0.01, h + 0.002), screen_mat or L['screen_dark'], rot=(t, 0, 0))   # black glass; UI quad sits on top
    mb.box((w - 0.2, 0.012, 0.025), (0, -dpt / 2 - 0.003, h - 0.16), L['orange_led'])          # interactable
    for i, x in enumerate((-w / 2 + 0.12, -w / 2 + 0.2)):
        mb.cyl(0.008, 0.01, (x, -dpt / 2 - 0.004, h - 0.26), L['status_cyan'] if i == 0 else L['status_amber'], segs=10, axis='Y')
    return mb.build(name, col, bevel=0.008)

def bay_frame(name, L, col, title_mat=None, title_size=None):
    """Two square posts + header plate with downlight; title decal added by caller."""
    mb = MB()
    for sx in (-1.0, 1.0):
        mb.box((0.1, 0.1, 2.75), (sx, 0, 1.375), L['graphite'])
        mb.box((0.22, 0.22, 0.012), (sx, 0, 0.006), L['graphite'])
    mb.box((2.1, 0.14, 0.55), (0, 0, 2.475), L['graphite'])
    mb.box((0.06, 0.01, 0.3), (-0.92, -0.075, 2.475), L['orange'])                            # identity tab
    mb.box((1.8, 0.04, 0.012), (0, -0.03, 2.195), L['diffuser'])                              # downlight onto hardware
    return mb.build(name, col, bevel=0.006)

def cabinet(name, L, col, w=0.8, d=0.6, h=2.0):
    mb = MB()
    mb.box((w, d, h - 0.08), (0, 0, 0.08 + (h - 0.08) / 2), L['painted_dark'])
    mb.box((w - 0.08, d - 0.08, 0.08), (0, 0, 0.04), L['backer'])
    for sx in (-1, 1):
        mb.box((w / 2 - 0.03, 0.012, h - 0.3), (sx * (w / 4), -d / 2 - 0.004, h / 2 + 0.05), L['painted_dark'])
        mb.box((0.02, 0.03, 0.22), (sx * 0.05, -d / 2 - 0.02, h * 0.55), L['brushed'])
    mb.box((w - 0.2, 0.01, 0.25), (0, -d / 2 - 0.012, 0.35), L['floor_metal'])                 # vent grille
    mb.cyl(0.01, 0.01, (w / 2 - 0.08, -d / 2 - 0.012, h - 0.12), L['status_cyan'], segs=10, axis='Y')
    return mb.build(name, col, bevel=0.006)

def tool_cart(name, L, col):
    mb = MB()
    for z in (0.18, 0.58, 0.9): mb.box((1.0, 0.55, 0.035), (0, 0, z), L['painted'])
    for sx in (-0.47, 0.47):
        for sy in (-0.24, 0.24): mb.box((0.035, 0.035, 0.9), (sx, sy, 0.47), L['graphite'])
    for sx in (-0.4, 0.4):
        for sy in (-0.2, 0.2): mb.cyl(0.05, 0.04, (sx, sy, 0.05), L['rubber'], segs=12, axis='X')
    mb.beam((-0.55, -0.2, 0.95), (-0.55, 0.2, 0.95), 0.03, 0.03, L['brushed'])
    mb.box((0.35, 0.25, 0.12), (0.2, 0, 0.98), L['orange'])                                     # tool case
    return mb.build(name, col, bevel=0.005)

def cable_reel(name, L, col):
    mb = MB()
    for sy in (-0.24, 0.24): mb.cyl(0.42, 0.04, (0, sy, 0.45), L['graphite'], segs=40, axis='Y')
    mb.cyl(0.32, 0.44, (0, 0, 0.45), L['rubber'], segs=40, axis='Y')
    mb.box((0.7, 0.6, 0.06), (0, 0, 0.03), L['graphite'])
    return mb.build(name, col, bevel=0.004)

def stanchion(name, L, col):
    mb = MB()
    mb.cyl(0.17, 0.03, (0, 0, 0.015), L['graphite'], segs=24)
    mb.cyl(0.03, 0.95, (0, 0, 0.5), L['brushed'], segs=16)
    mb.cyl(0.045, 0.08, (0, 0, 0.98), L['yellow'], segs=16)
    return mb.build(name, col, bevel=0.003)

# ============================================================ HANGAR HERO PIECES
def turntable(name, R, H, L, col):
    """Floor-level work-bay turntable: flush steel bed, graphite lip band, recessed light groove."""
    mb = MB()
    mb.ring(R - 0.02, R + 0.32, 0.012, 0.0, L['brushed'])                                      # flush bed ring
    mb.ring(R - 0.1, R, H, 0.0, L['graphite'])                                                 # lip band
    mb.cyl(R - 0.1 - 0.30, H, (0, 0, H / 2), L['deck'], segs=128)                               # deck
    mb.ring(R - 0.40, R - 0.34, H - 0.016, 0.0, L['backer'])                                   # groove floor
    mb.ring(R - 0.385, R - 0.355, 0.006, H - 0.016, L['orange_led'])                           # light line in groove
    mb.ring(R - 0.34, R - 0.1, H, 0.0, L['deck'])                                               # deck outer band
    return mb.build(name, col, bevel=0.004, smooth=True)

def service_port(name, L, col):
    mb = MB()
    mb.box((0.46, 0.26, 0.14), (0, 0, 0.07), L['graphite'])
    mb.box((0.3, 0.012, 0.07), (0, -0.134, 0.075), L['brushed'])
    for x in (-0.08, 0.0, 0.08): mb.cyl(0.018, 0.02, (x, -0.142, 0.075), L['backer'], segs=12, axis='Y')
    mb.cyl(0.009, 0.01, (0.18, -0.134, 0.11), L['status_cyan'], segs=10, axis='Y')
    return mb.build(name, col, bevel=0.006)

def hatch(name, L, col, w=0.9, d=0.55):
    mb = MB()
    mb.box((w, d, 0.006), (0, 0, 0.003), L['backer'])
    mb.box((w - 0.03, d - 0.03, 0.006), (0, 0, 0.006), L['painted_dark'])
    for sx in (-1, 1):
        for sy in (-1, 1): mb.cyl(0.012, 0.004, (sx * (w / 2 - 0.05), sy * (d / 2 - 0.05), 0.011), L['brushed'], segs=10)
    return mb.build(name, col, bevel=0.0)

# ============================================================ PHASE 5: MISSION CONTROL
def desk_monitors(length=3.4, dpt=0.85, h=0.74, positions=(-0.85, 0.85)):
    """Monitor layout shared by operator_desk and the screen quads placed on it:
    (lx, ly, z, rz_deg) of each screen centre, already 2 cm in front of its bezel."""
    out = []
    for px in positions:
        for side, rz in ((-1, 10.0), (1, -10.0)):                 # pair turned in toward the operator
            r = math.radians(rz); bx, by = px + side * 0.33, dpt / 2 - 0.2
            out.append((bx + math.sin(r) * 0.02, by - math.cos(r) * 0.02, h + 0.36, rz))
    return out

def operator_desk(name, L, col, length=3.4, dpt=0.85, h=0.74, positions=(-0.85, 0.85)):
    """Mission Control desk run, front faces -Y. Not interactable, so no orange: graphite top,
    satin pedestals, rear monitor spine, two 16:9 monitors and a keyboard per position."""
    mb = MB(); knee = 0.9
    edges = sorted({-length / 2, length / 2, *[p + s * knee / 2 for p in positions for s in (-1, 1)]})
    for a, b in zip(edges, edges[1:]):                             # pedestals between the knee spaces
        if any(abs((a + b) / 2 - p) < 1e-6 for p in positions) or b - a < 0.1: continue
        mb.box((b - a - 0.04, dpt - 0.15, 0.08), ((a + b) / 2, 0.06, 0.04), L['backer'])
        mb.box((b - a, dpt - 0.05, h - 0.12), ((a + b) / 2, 0.025, 0.08 + (h - 0.12) / 2), L['painted'])
    mb.box((length - 0.04, 0.03, h - 0.3), (0, dpt / 2 - 0.05, 0.25 + (h - 0.3) / 2), L['painted'])   # modesty panel
    mb.box((length + 0.02, dpt, 0.04), (0, 0, h - 0.02), L['graphite'])                                # worktop
    mb.box((length + 0.02, 0.012, 0.02), (0, -dpt / 2 - 0.004, h - 0.03), L['brushed'])                # front edge
    mb.box((length - 0.1, 0.1, 0.12), (0, dpt / 2 - 0.1, h + 0.06), L['graphite'])                     # monitor spine
    for (lx, ly, z, rz) in desk_monitors(length, dpt, h, positions):
        r = math.radians(rz); bx, by = lx - math.sin(r) * 0.02, ly + math.cos(r) * 0.02
        mb.box((0.64, 0.035, 0.4), (bx, by, z), L['graphite'], rot=(0, 0, r))                         # bezel
        mb.box((0.06, 0.05, 0.2), (bx - math.sin(r) * 0.04, by + math.cos(r) * 0.04, h + 0.12), L['graphite'], rot=(0, 0, r))
    for px in positions:
        mb.box((0.44, 0.14, 0.018), (px, -dpt / 2 + 0.2, h + 0.009), L['rubber'])                     # keyboard
        mb.cyl(0.008, 0.01, (px + 0.5, dpt / 2 - 0.152, h + 0.09), L['status_cyan'], segs=10, axis='Y')
    return mb.build(name, col, bevel=0.005)

def task_chair(name, L, col):
    """Operator chair, occupant faces -Y. Five-star base on casters, graphite frame, black upholstery."""
    mb = MB()
    for k in range(5):
        a = 2 * math.pi * k / 5 + math.pi / 2
        tip = (math.cos(a) * 0.32, math.sin(a) * 0.32)
        mb.beam((0, 0, 0.09), (tip[0], tip[1], 0.07), 0.05, 0.03, L['graphite'])
        mb.cyl(0.028, 0.03, (tip[0], tip[1], 0.03), L['rubber'], segs=10, axis='X')
    mb.cyl(0.03, 0.34, (0, 0, 0.26), L['brushed'], segs=14)                                  # gas column
    mb.box((0.5, 0.48, 0.08), (0, 0, 0.47), L['rubber'])                                     # seat
    mb.box((0.42, 0.4, 0.03), (0, 0, 0.42), L['graphite'])
    mb.beam((0, 0.2, 0.44), (0, 0.27, 0.72), 0.06, 0.03, L['graphite'])                      # back spine
    mb.box((0.46, 0.06, 0.55), (0, 0.29, 0.84), L['rubber'], rot=(math.radians(-8), 0, 0))   # backrest
    for sx in (-1, 1):
        mb.box((0.03, 0.04, 0.2), (sx * 0.24, 0.02, 0.58), L['graphite'])
        mb.box((0.06, 0.28, 0.03), (sx * 0.24, -0.01, 0.69), L['graphite'])                  # armrests
    return mb.build(name, col, bevel=0.004)

def warning_beacon(name, L, col):
    """Wall-bracket amber beacon (yellow = hazard). Lens is dark by day, lit in LIGHTSET_Launch_Mode.
    Origin on the wall line, faces -Y."""
    mb = MB()
    mb.box((0.14, 0.2, 0.03), (0, -0.1, 0.015), L['graphite'])                                # bracket shelf
    mb.box((0.1, 0.02, 0.12), (0, -0.01, -0.04), L['graphite'])                               # wall plate
    mb.cyl(0.08, 0.05, (0, -0.12, 0.055), L['graphite'], segs=24)                             # base
    mb.cyl(0.065, 0.15, (0, -0.12, 0.155), L['beacon'], segs=24)                              # lens
    mb.cyl(0.04, 0.02, (0, -0.12, 0.24), L['graphite'], segs=16)
    return mb.build(name, col, bevel=0.003)

def linear_light(name, length, L, col, drop=0.5, mat=None):
    """Suspended linear fixture along X: slim graphite housing, diffuser underneath, two rods."""
    mb = MB()
    mb.box((length, 0.12, 0.07), (0, 0, 0.035), L['graphite'])
    mb.box((length - 0.04, 0.09, 0.008), (0, 0, -0.003), mat or L['diffuser_dim'])
    for sx in (-1, 1): mb.cyl(0.006, drop, (sx * (length / 2 - 0.4), 0, 0.07 + drop / 2), L['graphite'], segs=8)
    return mb.build(name, col, bevel=0.003)
