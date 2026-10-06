"""
rf01_clothing.py - Checkpoint 2 clothing blockout for the RF-01 Mission Systems Engineer.

Each garment is a signed-distance field built on the approved CP1 skeleton:
  base shape   = garment forms (drape, ease)  UNION  (inner layer offset by a clearance)
                 so the garment can never sink into the body (or into the garment under it)
  construction = displacement layers that follow the surface: panels (steps), seams (grooves), folds (ridges)
  openings     = a separate clip field (hem, cuffs, collar, waist...). The mesher caps the clipped volume and
                 the caps are deleted afterwards, leaving an open shell that Solidify gives real thickness.

Layering, inside -> out: body | shoes | trousers | jacket.
Units metres, Z up, character faces -Y, his left is +X (same as rf01_body).
"""
import numpy as np
from rf01_sdf import (Field, Ellipsoid, Cone, Box, Plane, Slab, Segment, Intersect, FieldPrim, norm, frame, rot,
                      smax, project)
from rf01_sdf import Prim, MX
from rf01_body import build as build_body, skeleton, hand_frame, FWD, UP, P, axes

STAGE = 2                     # 3 = append the Checkpoint 3 hero/identity layers (CP2 layers are never changed)

# garment shell thickness (Solidify, inward) and clearances to the layer underneath
T_JACKET, T_TROUSERS = 0.0035, 0.0028
CLEAR_TROUSERS, CLEAR_JACKET, CLEAR_SHOE = 0.010, 0.012, 0.006


def both(f, fn, *args):
    """Run a left-side builder, then mirror what it added to the right."""
    n0 = len(f.ops)
    fn(f, *args)
    for op, prim, k, tag, ph in list(f.ops[n0:]):
        f.ops.append((op, prim.mirror(), k, tag + ' R', ph))


class ClipPrim(Prim):
    """A clipped garment used as a primitive by the layer above it."""
    def __init__(self, field, clip, c, r):
        self.field, self.clip = field, clip
        self.c = np.asarray(c, float); self.r = r

    def d(self, p):
        return np.maximum(self.field._eval_chunk(p, p.min(0), p.max(0), 1.0), self.clip(p))

    def mirror(self):
        return self


class Clip:
    """Garment field clipped by an openings field: what gets meshed. eval/grad like a Field."""
    def __init__(self, g, r):
        self.g, self.r = g, r

    def eval(self, p):
        return np.maximum(self.g.eval(p), self.r(p))

    def grad(self, p, e=2.5e-4):
        k = np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], float)
        g = np.zeros_like(p)
        for kk in k:
            g += kk[None, :] * self.eval(p + e * kk)[:, None]
        return g / (4.0 * e)


def zone(d_fn, centre, radius):
    """Restrict a clip constraint to a ball around `centre` (elsewhere it never clips)."""
    c = np.asarray(centre, float)
    def r(p):
        out = d_fn(p)
        far = np.linalg.norm(p - c, axis=1) > radius
        out[far] = -1.0
        return out
    return r


def plane_d(c, n):
    c = np.asarray(c, float); n = norm(n)
    return lambda p: (p - c) @ n


def front_only(prim, y0=-0.02):
    """Restrict a region to the front of the body (y < y0)."""
    return Intersect(prim, Box(P(0, y0 - 0.3, 0.9), (0.6, 0.3, 1.0), 0.0))


def back_only(prim, y0=0.02):
    return Intersect(prim, Box(P(0, y0 + 0.3, 0.9), (0.6, 0.3, 1.0), 0.0))


def surface_path(field, pts, n=8):
    """Resample a polyline and project it onto a garment surface (fold paths that lie on the fabric)."""
    pts = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); t = np.concatenate([[0], np.cumsum(seg)]) / seg.sum()
    s = np.linspace(0, 1, n)
    q = np.stack([np.interp(s, t, pts[:, i]) for i in range(3)], 1)
    return project(field, q, iters=6, max_step=0.02)


def ring_path(field, centre, axis, ref, r, a0, a1, n=9):
    """Arc of angle a0..a1 (deg, 0 = ref direction) around an axis, projected onto the garment (limb folds)."""
    ax = norm(axis); u = norm(np.asarray(ref, float) - ax * np.dot(ref, ax)); v = np.cross(ax, u)
    ang = np.radians(np.linspace(a0, a1, n))
    pts = np.asarray(centre)[None] + r * (np.cos(ang)[:, None] * u + np.sin(ang)[:, None] * v)
    return project(field, pts, iters=8, max_step=0.03)


# ============================================================================================== shoes
def foot_frame(J):
    A = J['ankle.L']
    fd = rot(UP, 7) @ FWD
    lat = np.cross(fd, UP) * -1.0
    if lat[0] < 0:
        lat = -lat
    F = lambda a, b, c: P(A[0], A[1], 0) + a * fd + b * lat + c * UP
    return A, fd, lat, F


class SolePrim(Prim):
    """Outsole + midsole: a plan-view outline (heel disc -> ball -> toe) extruded between a floor line with toe
    spring and a top line that drops from heel to forefoot. Left foot; mirrors like any primitive."""
    def __init__(self, J):
        A, fd, lat, F = foot_frame(J)
        self.o = P(A[0], A[1], 0.0); self.fd, self.lat = fd, lat
        self.c = F(0.06, 0.0, 0.015); self.r = 0.20
        self.R = np.stack([lat, fd, UP])

    def d(self, p):
        q = (p - self.o) @ self.R.T            # (b lateral, a forward, z)
        b, a, z = q[:, 0], q[:, 1], q[:, 2]
        # plan outline: union of round cones heel(-0.052, r .041) -> ball(0.128, r .056) -> toe(0.162, r .054)
        def seg2(a0, b0, r0, a1, b1, r1):
            pa = np.stack([a - a0, b - b0], 1); ba = np.array([a1 - a0, b1 - b0])
            h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
            return np.linalg.norm(pa - h[:, None] * ba, axis=1) - (r0 + (r1 - r0) * h)
        plan = np.minimum(seg2(-0.052, 0.001, 0.041, 0.128, -0.004, 0.056), seg2(0.128, -0.004, 0.056, 0.164, -0.007, 0.054))
        floor = 0.010 * np.clip((a - 0.135) / 0.085, 0, 1) ** 2              # toe spring
        top = 0.028 - 0.009 * np.clip((a + 0.02) / 0.15, 0, 1) + floor        # 28 mm heel, 19 mm forefoot
        vert = np.maximum(floor - z, z - top)
        return smax(plan, vert, 0.0025)

    def mirror(self):
        import copy
        from rf01_sdf import MX
        m = copy.copy(self); m.o = self.o @ MX; m.c = self.c @ MX; m.R = self.R @ MX; return m


def shoe(body, J):
    """Left shoe: a mid-height engineering shoe. Returns (field, clip, sole prim)."""
    A, fd, lat, F = foot_frame(J)
    Rf = np.stack([lat, fd, UP])
    f = Field()
    f.add(Intersect(FieldPrim(body, CLEAR_SHOE), Box(F(0.06, 0.0, 0.10), (0.10, 0.19, 0.11), 0.0, Rf)),
          tag='last (foot + clearance)')
    f.add(Ellipsoid(F(0.150, -0.006, 0.034), (0.052, 0.074, 0.030), Rf), k=0.012, tag='toe box')
    f.add(Ellipsoid(F(0.040, -0.002, 0.056), (0.050, 0.100, 0.044), Rf), k=0.02, tag='vamp')
    f.add(Ellipsoid(F(-0.050, 0.000, 0.060), (0.043, 0.046, 0.058), Rf), k=0.015, tag='heel counter')
    f.add(Cone(A + P(0, 0.006, -0.03), A + P(0, 0.010, 0.07), 0.049, 0.046, side=lat, sx=1.0, sy=1.08), k=0.015,
          tag='ankle collar')
    sole = SolePrim(J)
    f.add(sole, k=0.003, tag='sole')
    # opening for the leg
    f.sub(Cone(A + P(0, 0.010, 0.036), A + P(0, 0.016, 0.25), 0.041, 0.043), k=0.006, tag='collar opening', phase=1)
    # construction: lacing panel, tongue edges, mudguard line, heel counter panel, padded collar roll
    f.disp(Intersect(Box(F(0.075, -0.002, 0.10), (0.017, 0.060, 0.05), 0.002, Rf), Plane(P(0, 0, 0.045), -UP, 0.3)),
           0.0016, 0.0008, tag='lacing panel')
    for s in (-1, 1):
        f.disp(Intersect(Slab(F(0.0, s * 0.018, 0.0), lat, 0.0006), Box(F(0.075, 0.0, 0.10), (0.04, 0.060, 0.05), 0, Rf)),
               -0.0010, 0.0007, tag='tongue edge')
    f.disp(Slab(P(0, 0, 0.041), UP, 0.0005), -0.0009, 0.0007, tag='mudguard line')
    f.disp(Intersect(Box(F(-0.075, 0.0, 0.065), (0.06, 0.045, 0.040), 0.004, Rf), Plane(P(0, 0, 0.03), -UP, 0.3)),
           0.0012, 0.0008, tag='heel counter panel')
    f.disp(Slab(P(0, 0, 0.0285), UP, 0.0004), -0.0008, 0.0006, tag='sole / upper line')
    if STAGE >= 3:
        shoe_cp3(f, J)
    f.finalize()
    # clip: collar top, lower at the tongue than at the heel
    collar = plane_d(F(0.0, 0.0, 0.125), norm(UP + 0.10 * fd))
    clip = zone(collar, A, 0.35)
    return f, clip, sole


# ============================================================================================== trousers
def trousers(body, shoes, J):
    f = Field()
    f.add(Intersect(FieldPrim(body, CLEAR_TROUSERS), Box(P(0, 0, 0.50), (0.26, 0.30, 0.56), 0.0)), tag='body + ease')
    f.add(shoes, tag='over the shoes')
    # waist ring and seat
    f.add(Cone(P(0, 0.010, 0.900), P(0, 0.008, 1.010), 0.183, 0.163, side=P(1, 0, 0), sx=1.0, sy=0.68), k=0.03,
          tag='waist / hip')
    f.add(Ellipsoid(P(0, 0.040, 0.880), (0.170, 0.088, 0.085)), k=0.035, tag='seat')
    both(f, trouser_leg, J)
    f.finalize()
    base = f
    # --- construction (displacements), defined on the base surface
    g = Field(); g.ops = list(base.ops)
    top = lambda y: 1.002 + 0.06 * y
    # waistband
    g.disp(Box(P(0, 0.0, top(0.0) - 0.021), (0.30, 0.25, 0.021), 0.0), 0.0018, 0.0008, tag='waistband')
    for x, y in ((0.0, 0.13), (0.085, -0.10), (-0.085, -0.10), (0.158, 0.02), (-0.158, 0.02), (0.075, 0.115),
                 (-0.075, 0.115)):
        g.disp(Box(P(x, y, top(y) - 0.022), (0.006, 0.10, 0.024), 0.0), 0.0022, 0.0006, tag='belt loop')
    # fly: placket overlap + J-stitch
    g.disp(front_only(Box(P(0.006, 0, 0.905), (0.016, 0.3, 0.055), 0.0)), 0.0010, 0.0006, tag='fly placket')
    g.disp(front_only(Segment([(0.022, -0.10, 0.958), (0.022, -0.10, 0.872), (0.004, -0.10, 0.845)])), -0.0010,
           0.0012, profile='bump', tag='fly stitch')
    both(g, trouser_details, J, base)
    if STAGE >= 3:
        both(g, trouser_cp3, J, base)
        trouser_cp3_left(g, J)
    g.finalize()
    # --- openings: waist top, two hems
    waist = plane_d(P(0, 0, top(0.0)), norm(P(0, -0.06, 1)))
    hem_n = norm(P(0, 0.237, 1.0))                     # front hem higher than the back (break over the shoe)
    def hem(p):
        return -((p - P(0, -0.045, 0.080)) @ hem_n)
    def clip(p):
        return np.maximum(waist(p), hem(p))
    return g, clip, base


def trouser_leg(f, J):
    H, K, A = J['hip.L'], J['knee.L'], J['ankle.L']
    X = P(1, 0, 0)
    top = P(0.096, 0.004, 0.865); knee = K + P(0.002, -0.004, 0.0); hem = A + P(0.002, -0.004, -0.024)
    f.add(Cone(top, knee, 0.110, 0.073, side=X, sx=1.0, sy=1.0), k=0.03, tag='thigh')
    f.add(Cone(knee, hem, 0.073, 0.064, side=X, sx=1.0, sy=1.04), k=0.02, tag='lower leg')
    f.add(Ellipsoid(K + P(0.002, -0.030, 0.006), (0.056, 0.040, 0.060)), k=0.02, tag='knee volume')


def trouser_details(g, J, base):
    H, K, A = J['hip.L'], J['knee.L'], J['ankle.L']
    X = P(1, 0, 0)
    # slant front pocket opening and side seam
    g.disp(Segment(surface_path(base, [(0.098, -0.11, 0.995), (0.150, -0.08, 0.905), (0.170, -0.03, 0.880)])),
           -0.0012, 0.0012, profile='bump', tag='front pocket')
    g.disp(Intersect(Slab(P(0, 0.014, 0), P(0, 1, 0), 0.0006), Box(P(0.20, 0.014, 0.45), (0.10, 0.1, 0.45), 0)),
           -0.0009, 0.0007, tag='side seam')
    g.disp(Intersect(Slab(P(0, 0.014, 0), P(0, 1, 0), 0.0006), Box(P(0.06, 0.014, 0.40), (0.05, 0.1, 0.40), 0)),
           -0.0008, 0.0007, tag='inseam')
    # back yoke (V toward centre back) + flat back pockets
    g.disp(back_only(Segment(surface_path(base, [(0.0, 0.13, 0.925), (0.09, 0.13, 0.940), (0.175, 0.06, 0.950)]))),
           -0.0010, 0.0012, profile='bump', tag='back yoke')
    g.disp(back_only(Box(P(0.085, 0.2, 0.872), (0.045, 0.2, 0.043), 0.004), 0.06), 0.0013, 0.0008, tag='back pocket')
    # articulated knee: darts above and below the kneecap, front half only
    for dz in (0.055, -0.045):
        g.disp(Intersect(Slab(K + P(0, 0, dz), norm(P(0, 0.25, 1)), 0.0006),
                         Box(K + P(0.0, -0.06, dz), (0.06, 0.035, 0.03), 0)), -0.0010, 0.0007, tag='knee dart')
    # folds: crotch whiskers, back of knee, hem break
    for (a, b) in [((0.030, -0.08, 0.815), (0.120, -0.09, 0.770)), ((0.035, -0.07, 0.790), (0.110, -0.085, 0.720))]:
        g.disp(Segment(surface_path(base, [a, b])), 0.0026, 0.0045, profile='bump', tag='crotch fold')
    for dz in (0.035, -0.005):
        g.disp(back_only(Intersect(Slab(K + P(0, 0, dz), norm(P(0, -0.2, 1)), 0.0), Box(K + P(0, 0.05, dz), (0.07, 0.05, 0.03), 0)),
                         0.02), 0.0028, 0.0045, profile='bump', tag='knee back fold')
    g.disp(front_only(Intersect(Slab(A + P(0, 0, 0.040), norm(P(0, 0.3, 1)), 0.0), Box(A + P(0, -0.05, 0.04), (0.07, 0.05, 0.03), 0)),
                      0.0), 0.0035, 0.0055, profile='bump', tag='hem break')


# ============================================================================================== jacket
def jacket(body, trousers_g, J):
    S = J['shoulder.L']; du = J['_du']
    f = Field()
    f.add(FieldPrim(body, CLEAR_JACKET), tag='body + ease')
    f.add(trousers_g, tag='over the trousers')
    # torso drape: hip-length, slightly fitted at the waist, straight to the hem
    f.add(Cone(P(0, 0.018, 0.835), P(0, 0.016, 1.085), 0.196, 0.172, side=P(1, 0, 0), sx=1.0, sy=0.70), k=0.0,
          tag='lower torso')
    f.add(Cone(P(0, 0.016, 1.085), P(0, 0.018, 1.330), 0.172, 0.170, side=P(1, 0, 0), sx=1.0, sy=0.72), k=0.04,
          tag='upper torso')
    f.add(Ellipsoid(P(0, 0.020, 1.385), (0.160, 0.098, 0.080)), k=0.04, tag='chest / shoulder girdle')
    # stand collar
    f.add(Cone(P(0, 0.010, 1.430), P(0, 0.010, 1.575), 0.080, 0.072, side=P(1, 0, 0), sx=1.0, sy=0.96), k=0.025,
          tag='collar')
    both(f, jacket_arm, J)
    f.finalize()
    base = f
    g = Field(); g.ops = list(base.ops)
    # --- front placket and zip
    g.disp(front_only(Box(P(0, 0, 1.18), (0.017, 0.4, 0.40), 0.0), -0.03), 0.0026, 0.0010, tag='front placket')
    g.disp(front_only(Box(P(0, 0, 1.18), (0.0011, 0.4, 0.40), 0.0), -0.03), -0.0016, 0.0006, tag='zip line')
    # hem band (follows the tilted hem)
    hem_n = norm(P(0, 0.08, 1.0))
    g.disp(Slab(P(0, 0.0, 0.850 + 0.022), hem_n, 0.022), 0.0016, 0.0008, tag='hem band')
    # collar base seam
    cb_n = norm(P(0, -0.30, 1.0))
    g.disp(Intersect(Slab(P(0, -0.07, 1.458), cb_n, 0.0007), Cone(P(0, 0.01, 1.40), P(0, 0.01, 1.56), 0.12, 0.12)),
           -0.0012, 0.0008, tag='collar seam')
    both(g, jacket_details, J, base)
    if STAGE >= 3:
        both(g, jacket_cp3, J, base)
        jacket_cp3_centre(g, J)
    g.finalize()
    # --- openings: collar top, hem, cuffs
    ct_n = norm(P(0, -0.26, 1.0))
    collar_top = plane_d(P(0, -0.075, 1.522), ct_n)
    hem = lambda p: -((p - P(0, 0.0, 0.850)) @ hem_n)
    W = J['wrist.L']; df = J['_df']
    cuffs = []
    for s in (1, -1):
        Ws = W * np.array([s, 1, 1]); dfs = df * np.array([s, 1, 1])
        cuffs.append(zone(plane_d(Ws + 0.004 * dfs, dfs), Ws, 0.22))
    def clip(p):
        out = np.maximum(collar_top(p), hem(p))
        for c in cuffs:
            out = np.maximum(out, c(p))
        return out
    return g, clip, base


def jacket_arm(f, J):
    S, E, W = J['shoulder.L'], J['elbow.L'], J['wrist.L']
    du, df = J['_du'], J['_df']
    Rd = frame(du, FWD)
    f.add(Ellipsoid(S + 0.030 * du + P(0.004, 0.0, 0.018), (0.062, 0.060, 0.090), Rd), k=0.016, tag='shoulder cap')
    f.add(Cone(S + 0.02 * du, E, 0.059, 0.051, side=FWD), k=0.016, tag='upper sleeve')
    cs = W - 0.068 * df
    f.add(Cone(E, cs, 0.051, 0.046, side=FWD), k=0.02, tag='lower sleeve')
    f.add(Cone(cs, W + 0.006 * df, 0.041, 0.040, side=FWD, sx=1.06, sy=0.94), k=0.010, tag='cuff')


def jacket_details(g, J, base):
    S, E, W = J['shoulder.L'], J['elbow.L'], J['wrist.L']
    du, df = J['_du'], J['_df']
    Ru = frame(du, FWD); front_u, side_u = Ru[0], Ru[1]
    Rf = frame(df, FWD); front_f, side_f = Rf[0], Rf[1]
    arm_out = Plane(S + 0.034 * du, -du, 0.6)               # inside = torso side of the armhole
    # yoke (front higher than back), stops at the armhole seam
    yoke = Intersect(Plane(P(0, 0, 1.375), norm(P(0, 0.15, -1.0)), 0.6), arm_out)
    g.disp(Intersect(yoke, Box(P(0.15, 0, 1.45), (0.15, 0.3, 0.15), 0)), 0.0028, 0.0009, tag='yoke')
    g.disp(Intersect(Slab(P(0, 0, 1.375), norm(P(0, 0.15, -1.0)), 0.0007), Intersect(arm_out, Box(P(0.15, 0, 1.38), (0.15, 0.3, 0.06), 0))),
           -0.0012, 0.0007, tag='yoke seam')
    g.disp(Intersect(Slab(S + 0.034 * du, du, 0.0007), Cone(S, S + 0.05 * du, 0.10, 0.10)), -0.0012, 0.0008,
           tag='armhole seam')
    # side panel under the arm, hem to armpit
    g.disp(Intersect(Box(P(0.215, 0.015, 1.03), (0.085, 0.075, 0.22), 0.0), arm_out), 0.0016, 0.0008, tag='side panel')
    # back princess seam
    g.disp(back_only(Intersect(Slab(P(0.078, 0, 0), P(1, 0, 0), 0.0007), Box(P(0.078, 0.1, 1.10), (0.02, 0.2, 0.25), 0)),
                     0.05), -0.0014, 0.0008, tag='princess seam')
    # chest pocket with flap
    g.disp(front_only(Box(P(0.088, 0, 1.290), (0.043, 0.3, 0.055), 0.003), -0.03), 0.0022, 0.0009, tag='chest pocket')
    g.disp(front_only(Box(P(0.088, 0, 1.333), (0.045, 0.3, 0.016), 0.003), -0.03), 0.0014, 0.0008, tag='pocket flap')
    # hand-warmer welt pocket (zip slot)
    g.disp(front_only(Segment(surface_path(base, [(0.098, -0.13, 0.925), (0.120, -0.12, 1.055)]))), -0.0012, 0.0010,
           profile='bump', tag='welt pocket')
    g.disp(front_only(Segment(surface_path(base, [(0.104, -0.13, 0.925), (0.126, -0.12, 1.055)]))), 0.0010, 0.0016,
           profile='bump', tag='welt lip')
    # cuff band
    g.disp(Intersect(Plane(W - 0.066 * df, -df, 0.3), Cone(W - 0.1 * df, W + 0.02 * df, 0.07, 0.07)), 0.0016, 0.0008,
           tag='cuff band')
    # ---- folds (medium only)
    for i, t in enumerate((-0.020, 0.004, 0.026)):           # inner elbow (front of the arm)
        c = E + t * du * (1 if t < 0 else 0) + t * df * (1 if t > 0 else 0)
        g.disp(Segment(ring_path(base, c, df if t > 0 else du, front_f, 0.06, -55 + 8 * i, 45 - 6 * i)), 0.0030,
               0.0045, profile='bump', tag='elbow fold')
    for t, a0, a1 in ((0.095, -120, 40), (0.125, -40, 110)):  # blousing above the cuff
        g.disp(Segment(ring_path(base, W - t * df, df, front_f, 0.06, a0, a1)), 0.0024, 0.0040, profile='bump',
               tag='forearm fold')
    for t, a0, a1 in ((0.13, 150, 230), (0.18, 160, 240)):    # under-arm compression in the A-pose
        g.disp(Segment(ring_path(base, S + t * du, du, front_u, 0.07, a0, a1)), 0.0026, 0.0045, profile='bump',
               tag='underarm fold')
    for pts in ([(0.150, -0.050, 1.290), (0.185, -0.080, 1.150), (0.195, -0.090, 1.020)],    # armpit drape, front
                [(0.150, 0.080, 1.290), (0.188, 0.100, 1.150), (0.198, 0.108, 1.020)]):      # and back
        g.disp(Segment(surface_path(base, pts)), 0.0030, 0.0055, profile='bump', tag='armpit drape')
    g.disp(Segment(surface_path(base, [(0.060, -0.07, 1.455), (0.140, -0.04, 1.465)])), 0.0018, 0.0040,
           profile='bump', tag='shoulder fold')


# ============================================================================================== assembly
class Offset(Prim):
    def __init__(self, prim, off):
        self.prim, self.off, self.c, self.r = prim, off, prim.c, prim.r + off

    def d(self, p):
        return self.prim.d(p) - self.off

    def mirror(self):
        return self


def build_all(log=print, stage=2):
    """Returns body field, skeleton and the three garments:
    {name: dict(field=garment field, clip=openings fn, mesh=Clip to mesh, bbox=(lo, hi), thickness)}"""
    global STAGE
    STAGE = stage
    body, J = build_body()
    shoeL, clipL, _ = shoe(body, J)
    clipR = lambda p: clipL(p * np.array([-1.0, 1.0, 1.0]))
    shoes = Field()
    shoes.ops = list(shoeL.ops) + [(op, prim.mirror(), k, tag + ' R', ph) for op, prim, k, tag, ph in shoeL.ops]
    shoes.finalize()
    clip_shoes = lambda p: np.maximum(clipL(p), clipR(p))
    shoes_prim = Offset(ClipPrim(shoes, clip_shoes, P(0, -0.03, 0.08), 0.40), 0.004)
    tro, clipT, tro_base = trousers(body, shoes_prim, J)
    # the jacket drapes over the trouser *base* shape: pocket/loop details must not print through it
    tro_prim = Offset(ClipPrim(tro_base, clipT, P(0, 0, 0.55), 0.62), 0.008)
    jac, clipJ, _ = jacket(body, tro_prim, J)
    A = J['ankle.L']
    g = {
        'RF01_Shoes': dict(field=shoeL, clip=clipL, mesh=Clip(shoeL, clipL), thickness=0.0, mirror=True,
                           bbox=((A[0] - 0.09, A[1] - 0.26, -0.01), (A[0] + 0.12, A[1] + 0.13, 0.20))),
        'RF01_Trousers': dict(field=tro, clip=clipT, mesh=Clip(tro, clipT), thickness=T_TROUSERS, mirror=False,
                              bbox=((-0.30, -0.22, 0.02), (0.30, 0.24, 1.05))),
        'RF01_Jacket': dict(field=jac, clip=clipJ, mesh=Clip(jac, clipJ), thickness=T_JACKET, mirror=False,
                            bbox=((-0.70, -0.22, 0.80), (0.70, 0.25, 1.62))),
    }
    if stage >= 3:
        g['RF01_Jacket']['paint'] = paint_jacket(J)
        g['RF01_Trousers']['paint'] = paint_trousers(J)
        g['RF01_Shoes']['paint'] = paint_shoes(J)
    return body, J, g


# ============================================================================================== Checkpoint 3
# Hero/identity layers, appended on top of the approved CP2 garments. No CP2 shape or layer is altered.
YOKE_C, YOKE_N = P(0, 0, 1.375), norm(P(0, 0.15, -1.0))        # yoke seam plane (normal points down)
COLLAR_SEAM_C, COLLAR_SEAM_N = P(0, -0.07, 1.458), norm(P(0, -0.30, 1.0))
COLLAR_TOP_C, COLLAR_TOP_N = P(0, -0.075, 1.522), norm(P(0, -0.26, 1.0))
NECK = Cone(P(0, 0.01, 1.40), P(0, 0.01, 1.58), 0.12, 0.12)


def arm_frames(J):
    S, E, W = J['shoulder.L'], J['elbow.L'], J['wrist.L']
    du, df = J['_du'], J['_df']
    Rf = frame(df, FWD)
    return S, E, W, du, df, Rf[0], Rf[1], Rf


def elbow_region(J):
    S, E, W, du, df, front_f, side_f, Rf = arm_frames(J)
    ax = norm(du + df)
    return Intersect(Intersect(Slab(E, ax, 0.052), Plane(E - 0.006 * front_f, front_f)),
                     Cone(E - 0.1 * ax, E + 0.1 * ax, 0.09, 0.09))


def cuff_tab_region(J):
    S, E, W, du, df, front_f, side_f, Rf = arm_frames(J)
    return Box(W - 0.036 * df - 0.042 * front_f, (0.012, 0.0095, 0.022), 0.002, np.stack([front_f, side_f, df]))


def torso_side(J):
    """Half-space on the body side of the armhole seam (the CP2 'arm_out' plane faces the other way: its inside
    is the sleeve cap, which is why the CP2 yoke step sits on the shoulder cap; that approved geometry is kept)."""
    S = J['shoulder.L']; du = J['_du']
    return Plane(S + 0.034 * du, du)


def yoke_seam_region(J):
    return Intersect(Slab(YOKE_C, YOKE_N, 0.0007), Intersect(torso_side(J), Box(P(0.15, 0, 1.38), (0.15, 0.3, 0.06), 0)))


def yoke_piping_region(J):
    return Intersect(Slab(YOKE_C + 0.0019 * YOKE_N, YOKE_N, 0.0013),
                     Intersect(torso_side(J), Box(P(0.15, 0, 1.38), (0.15, 0.3, 0.06), 0)))


def yoke_dark_region(J):
    yoke = Intersect(Plane(YOKE_C, YOKE_N), torso_side(J))
    below_collar = Plane(COLLAR_SEAM_C, COLLAR_SEAM_N)
    return Intersect(Intersect(yoke, below_collar), Box(P(0.15, 0, 1.45), (0.15, 0.3, 0.15), 0))


def side_panel_region(J):
    S = J['shoulder.L']; du = J['_du']
    return Intersect(Box(P(0.215, 0.015, 1.03), (0.085, 0.075, 0.22), 0.0), Plane(S + 0.034 * du, -du))


def cuff_band_region(J):
    W, df = J['wrist.L'], J['_df']
    return Intersect(Plane(W - 0.066 * df, -df), Cone(W - 0.1 * df, W + 0.02 * df, 0.07, 0.07))


def chest_tab_region():
    return front_only(Box(P(0.088, -0.2, 1.3085), (0.0075, 0.2, 0.0125), 0.002), -0.03)


def jacket_cp3(g, J, base):
    S, E, W, du, df, front_f, side_f, Rf = arm_frames(J)
    ax = norm(du + df)
    g.disp(elbow_region(J), 0.0012, 0.0008, tag='CP3 elbow reinforcement')
    g.disp(Intersect(Intersect(Slab(E + 0.052 * ax, ax, 0.0005), Plane(E - 0.006 * front_f, front_f)),
                     Cone(E - 0.1 * ax, E + 0.1 * ax, 0.09, 0.09)), -0.0008, 0.0006, tag='CP3 elbow stitch')
    g.disp(cuff_tab_region(J), 0.0016, 0.0007, tag='CP3 cuff tab')
    g.disp(yoke_seam_region(J), -0.0012, 0.0007, tag='CP3 yoke seam (body side)')
    g.disp(yoke_piping_region(J), 0.0008, 0.0005, tag='CP3 yoke piping')


def jacket_cp3_centre(g, J):
    g.disp(Intersect(Slab(COLLAR_TOP_C - 0.0045 * COLLAR_TOP_N, COLLAR_TOP_N, 0.0045), NECK), 0.0009, 0.0006,
           tag='CP3 collar binding')
    g.disp(chest_tab_region(), 0.0016, 0.0006, tag='CP3 chest tab')


def mirror_all(prims):
    return list(prims) + [p.mirror() for p in prims]


def paint_jacket(J):
    """Colour-blocking regions (signed distance, negative inside), evaluated on the mesh for the shader."""
    dark = mirror_all([yoke_dark_region(J), side_panel_region(J), cuff_band_region(J), cuff_tab_region(J)])
    dark.append(front_only(Box(P(0, 0, 1.18), (0.0055, 0.4, 0.40), 0.0), -0.03))          # zip tape
    orange = [chest_tab_region()]                  # the yoke piping is a real cord (RF01_JacketPiping)
    tone = mirror_all([elbow_region(J)])
    return dict(dark=dark, orange=orange, tone=tone)


# ---- trousers
def knee_panel_region(J):
    K = J['knee.L']
    n = norm(P(0, 0.25, 1))
    return Intersect(Intersect(Plane(K + P(0, 0, 0.055), n), Plane(K + P(0, 0, -0.045), -n)),
                     Box(K + P(0.0, -0.06, 0.0), (0.075, 0.045, 0.06), 0))


THIGH_POCKET = Box(P(0.215, 0.006, 0.668), (0.040, 0.060, 0.064), 0.005)
THIGH_ZIP = Intersect(Slab(P(0, 0, 0.722), UP, 0.0008), Box(P(0.215, 0.006, 0.722), (0.040, 0.048, 0.01), 0))


def trouser_cp3(g, J, base):
    g.disp(knee_panel_region(J), 0.0008, 0.0006, tag='CP3 knee panel')


def trouser_cp3_left(g, J):
    # one flat zipped utility pocket on the left outer thigh (not cargo)
    g.disp(THIGH_POCKET, 0.0018, 0.0008, tag='CP3 thigh pocket')
    g.disp(THIGH_ZIP, -0.0012, 0.0006, tag='CP3 thigh pocket zip')


def paint_trousers(J):
    zip_tape = Intersect(Slab(P(0, 0, 0.722), UP, 0.0024), Box(P(0.215, 0.006, 0.722), (0.040, 0.048, 0.01), 0))
    return dict(dark=[zip_tape], orange=[], tone=mirror_all([knee_panel_region(J)]))


# ---- shoes
def saddle_regions(J):
    A, fd, lat, F = foot_frame(J)
    out = []
    for s in (-1, 1):
        band = Intersect(Slab(F(0.045, 0.0, 0.0), norm(fd + 0.55 * UP), 0.011), Plane(F(0.0, s * 0.015, 0.0), -s * lat))
        out.append(Intersect(band, Plane(P(0, 0, 0.030), -UP)))
    return out


def shoe_cp3(f, J):
    A, fd, lat, F = foot_frame(J)
    f.disp(Intersect(Slab(F(0.150, 0.0, 0.0), fd, 0.0006), Plane(P(0, 0, 0.032), -UP)), -0.0009, 0.0006,
           tag='CP3 toe cap seam')
    f.disp(Intersect(Plane(F(0.150, 0.0, 0.0), -fd), Plane(P(0, 0, 0.030), -UP)), 0.0010, 0.0007, tag='CP3 toe cap')
    for r in saddle_regions(J):
        f.disp(r, 0.0011, 0.0007, tag='CP3 saddle')


def paint_shoes(J):
    A, fd, lat, F = foot_frame(J)
    rubber = Intersect(Plane(P(0, 0, 0.041), UP), Plane(P(0, 0, 0.0), -UP))          # mudguard band above the sole
    toe = Intersect(Plane(F(0.150, 0.0, 0.0), -fd), Plane(P(0, 0, 0.030), -UP))
    return dict(dark=[rubber] + mirror_all([toe]), orange=[], tone=mirror_all(saddle_regions(J)))
