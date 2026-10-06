"""
rf01_sdf.py - signed-distance sculpting kernel for the RF-01 engineer (numpy only, no Blender dependency).

A body is an ordered list of operations [(op, primitive, k), ...] applied to a running distance d:
  'add'  smooth union        d = smin(d, prim, k)
  'sub'  smooth subtraction  d = smax(d, -prim, k)
Each primitive carries a bounding sphere so evaluation can skip primitives that cannot affect a region.

Also: block-sparse grid sampling, Naive Surface Nets meshing (quads), and Newton projection of mesh vertices onto
the zero level set (so a coarse remesh can be re-sharpened against the exact field).
"""
import numpy as np

F = np.float32


# ---------------------------------------------------------------------------------------------- frames / maths
def norm(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def frame(axis, side):
    """Orthonormal frame (x=side, y=axis x side, z=axis) for a segment pointing along `axis`."""
    z = norm(axis)
    x = np.asarray(side, float) - z * np.dot(side, z)
    x = norm(x)
    y = np.cross(z, x)
    return np.stack([x, y, z])          # rows = local axes in world


def rot(axis, deg):
    """Rotation matrix about `axis` by `deg` degrees (Rodrigues)."""
    a = norm(axis); t = np.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K


def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


# ---------------------------------------------------------------------------------------------- primitives
MX = np.diag([-1.0, 1.0, 1.0])


class Prim:
    """Base: subclasses implement d(points in world) and set self.c (bound centre), self.r (bound radius).
    mirror() returns the primitive reflected through the X=0 plane (all shapes are symmetric about their own
    local axes, so reflecting centres and axis rows is exact)."""
    def bound_dist(self, lo, hi):
        q = np.clip(self.c, lo, hi)
        return np.linalg.norm(self.c - q) - self.r

    def mirror(self):
        import copy
        m = copy.copy(self)
        for k, v in list(vars(self).items()):
            if k in ('c', 'a', 'b') and isinstance(v, np.ndarray):
                setattr(m, k, v @ MX)
            elif k == 'R':
                setattr(m, k, v @ MX)
            elif k == 'n':
                setattr(m, k, v @ MX)
            elif isinstance(v, Prim):
                setattr(m, k, v.mirror())
        return m


class Ellipsoid(Prim):
    """Ellipsoid centre c, radii r3 along the rows of rotation R (R rows = local axes in world)."""
    def __init__(self, c, r3, R=None):
        self.c = np.asarray(c, float); self.r3 = np.asarray(r3, float)
        self.R = np.eye(3) if R is None else np.asarray(R, float)
        self.r = float(self.r3.max())

    def d(self, p):
        q = (p - self.c) @ self.R.T                      # world -> local
        k0 = np.linalg.norm(q / self.r3, axis=1)
        k1 = np.linalg.norm(q / (self.r3 * self.r3), axis=1)
        return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


class Cone(Prim):
    """Round cone from a (radius ra) to b (radius rb). Cross-section scaled by (sx, sy) in the frame built from
    `side` (sx along side, sy along axis x side): gives elliptical limbs. Distance is approximate when sx,sy != 1."""
    def __init__(self, a, b, ra, rb, side=(1, 0, 0), sx=1.0, sy=1.0):
        self.a = np.asarray(a, float); self.b = np.asarray(b, float)
        self.ra, self.rb, self.sx, self.sy = ra, rb, sx, sy
        self.R = frame(self.b - self.a, side)
        self.L = np.linalg.norm(self.b - self.a)
        self.c = 0.5 * (self.a + self.b)
        self.r = 0.5 * self.L + max(ra, rb) * max(sx, sy, 1.0)

    def d(self, p):
        q = (p - self.a) @ self.R.T
        s = min(self.sx, self.sy)
        x = q[:, 0] / self.sx; y = q[:, 1] / self.sy
        rq = np.sqrt(x * x + y * y)                       # radial (2D: rq, z)
        z = q[:, 2]
        # iq round cone (2D form)
        L, r1, r2 = self.L, self.ra, self.rb
        b = (r1 - r2) / L; a = np.sqrt(max(1.0 - b * b, 1e-9))
        k = rq * (-b) + z * a                             # dot(q, vec2(-b, a))
        d_side = (rq * a + z * b) - r1                    # dot(q, vec2(a, b)) - r1
        d_a = np.sqrt(rq * rq + z * z) - r1
        d_b = np.sqrt(rq * rq + (z - L) ** 2) - r2
        out = np.where(k < 0.0, d_a, np.where(k > a * L, d_b, d_side))
        return out * s


class Box(Prim):
    """Rounded box: centre c, half extents h3 (before rounding rr), oriented by rows of R."""
    def __init__(self, c, h3, rr, R=None):
        self.c = np.asarray(c, float); self.h3 = np.asarray(h3, float); self.rr = rr
        self.R = np.eye(3) if R is None else np.asarray(R, float)
        self.r = float(np.linalg.norm(self.h3)) + rr

    def d(self, p):
        q = np.abs((p - self.c) @ self.R.T) - self.h3
        return np.linalg.norm(np.maximum(q, 0.0), axis=1) + np.minimum(q.max(axis=1), 0.0) - self.rr


class Plane(Prim):
    """Half-space (inside = below the plane through c with normal n), limited by a bound radius for culling.
    Only meaningful inside an intersection ('cut') operation."""
    def __init__(self, c, n, bound=None):
        # a half-space is unbounded: never culled (Intersect takes the tighter bound of its operands)
        self.c = np.asarray(c, float); self.n = norm(n); self.r = 1e3

    def d(self, p):
        return (p - self.c) @ self.n


class Slab(Prim):
    """|distance to a plane| - half width: a band through space (seams, fold lines). Bounded only for culling."""
    def __init__(self, c, n, hw, bound=None):
        self.c = np.asarray(c, float); self.n = norm(n); self.hw = hw; self.r = 1e3

    def d(self, p):
        return np.abs((p - self.c) @ self.n) - self.hw


class Segment(Prim):
    """Distance to a polyline (fold paths)."""
    def __init__(self, pts):
        self.pts = np.asarray(pts, float)
        self.c = self.pts.mean(0); self.r = float(np.linalg.norm(self.pts - self.c, axis=1).max())

    def d(self, p):
        best = np.full(len(p), 1e9)
        for a, b in zip(self.pts[:-1], self.pts[1:]):
            ab = b - a; t = np.clip(((p - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
            best = np.minimum(best, np.linalg.norm(p - (a + t[:, None] * ab), axis=1))
        return best

    def mirror(self):
        import copy
        m = copy.copy(self); m.pts = self.pts @ MX; m.c = self.c @ MX; return m


class FieldPrim(Prim):
    """Another Field used as a primitive (e.g. the body offset by a clearance)."""
    def __init__(self, field, offset=0.0, c=(0, 0, 0.9), r=1.3):
        self.field, self.offset = field, offset
        self.c = np.asarray(c, float); self.r = r

    def d(self, p):
        return self.field._eval_chunk(p, p.min(0), p.max(0), 1.0) - self.offset

    def mirror(self):
        return self


class Disp(Prim):
    """Displacement layer: pushes the running surface out by h where the region is.
    profile 'step': full height inside region (smoothstep edge of +-soft); 'bump': gaussian ridge of width soft
    around the region (for folds)."""
    def __init__(self, region, h, soft, profile='step'):
        self.region, self.h, self.soft, self.profile = region, h, soft, profile
        self.c, self.r = region.c, region.r + (6 * soft if profile == 'bump' else soft)

    def weight(self, p):
        s = self.region.d(p)
        if self.profile == 'bump':
            return np.exp(-(np.maximum(s, 0.0) / self.soft) ** 2)
        t = np.clip((s + self.soft) / (2 * self.soft), 0, 1)
        return 1.0 - t * t * (3 - 2 * t)


class Intersect(Prim):
    """Smooth intersection of two primitives (used to trim a shape)."""
    def __init__(self, A, B, k=0.0):
        self.A, self.B, self.k = A, B, k
        tight = A if A.r <= B.r else B                    # the intersection lies inside both bounds
        self.c, self.r = tight.c, tight.r

    def d(self, p):
        return smax(self.A.d(p), self.B.d(p), self.k)


# ---------------------------------------------------------------------------------------------- the field
class Field:
    def __init__(self):
        self.ops = []          # (op, prim, k, tag, phase)
        self.warps = []        # smooth coordinate warps: (centre, radius, surface displacement), e.g. facial asymmetry

    # phase orders the operations: masses (0) -> carving (1) -> features laid over carving (2) -> fine carving (3)
    # -> trims (9). Within a phase, insertion order is kept.
    def add(self, prim, k=0.0, tag='', phase=0):
        self.ops.append(('add', prim, k, tag, phase)); return prim

    def sub(self, prim, k=0.0, tag='', phase=1):
        self.ops.append(('sub', prim, k, tag, phase)); return prim

    def cut(self, prim, k=0.0, tag='', phase=9):
        """Keep only what is inside prim (smooth intersection). Never culled."""
        self.ops.append(('cut', prim, k, tag, phase)); return prim

    def disp(self, region, h, soft, profile='step', tag='', phase=5):
        """Surface displacement layer (panels, seams, folds). Applied after all shape operations."""
        self.ops.append(('disp', Disp(region, h, soft, profile), 0.0, tag, phase)); return region

    def finalize(self):
        self.ops.sort(key=lambda o: o[4])
        return self

    def _eval_chunk(self, p, lo, hi, far):
        if self.warps:
            p = p.copy()
            for c, r, v in self.warps:
                w = np.exp(-np.sum((p - c) ** 2, axis=1) / (r * r))
                p -= w[:, None] * np.asarray(v)[None, :]
        d = np.full(len(p), far, dtype=float)
        for op, prim, k, _, _ in self.ops:
            if op == 'cut':
                d = smax(d, prim.d(p), k)
                continue
            if op == 'disp':
                if prim.bound_dist(lo, hi) <= 0.0:
                    d = d - prim.h * prim.weight(p)
                continue
            # conservative: scaled cones / approximate ellipsoids can under-report distance, and a skipped
            # primitive must have no effect anywhere in the chunk, or blocks disagree at shared lattice points
            if prim.bound_dist(lo, hi) > 2.0 * k + 0.05:
                continue
            v = prim.d(p)
            if op == 'add':
                d = smin(d, v, k)
            else:
                d = smax(d, -v, k)
        return d

    def eval(self, p, cell=0.06, far=1.0):
        """Distance at points p (N,3). Points are bucketed into `cell`-sized boxes; each box only evaluates the
        primitives whose bounds reach it."""
        p = np.asarray(p, float)
        out = np.empty(len(p))
        key = np.floor(p / cell).astype(np.int64)
        key = (key[:, 0] * 73856093) ^ (key[:, 1] * 19349663) ^ (key[:, 2] * 83492791)
        order = np.argsort(key, kind='stable')
        ks = key[order]
        splits = np.flatnonzero(np.diff(ks)) + 1
        for idx in np.split(order, splits):
            pts = p[idx]
            lo, hi = pts.min(axis=0), pts.max(axis=0)
            out[idx] = self._eval_chunk(pts, lo, hi, far)
        return out

    def grad(self, p, e=2.5e-4):
        k = np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], float)
        g = np.zeros_like(p)
        for kk in k:
            g += kk[None, :] * self.eval(p + e * kk)[:, None]
        return g / (4.0 * e)


# ---------------------------------------------------------------------------------------------- sampling + meshing
def mesh_sparse(field, lo, hi, h, block=8, log=print, reach=1.7):
    """Block-sparse Naive Surface Nets. Only blocks whose centre is within reach of the surface are sampled
    (on a (block+1)^3 lattice each). Returns verts (V,3) and quads (Q,4); winding is fixed later in Blender."""
    lo = np.asarray(lo, float); hi = np.asarray(hi, float)
    B = block
    nb = np.ceil((hi - lo) / (h * B)).astype(int)
    N = nb * B + 1                                         # global lattice points per axis
    bi = np.stack(np.meshgrid(*[np.arange(m) for m in nb], indexing='ij'), -1).reshape(-1, 3)
    bc = lo + (bi + 0.5) * B * h
    dc = field.eval(bc)
    reach = 0.5 * np.sqrt(3) * B * h * reach + 0.004
    act = bi[np.abs(dc) < reach]
    log(f'  lattice {N.tolist()} h={h*1000:.2f}mm  blocks {len(bc)}  active {len(act)}')
    off = np.stack(np.meshgrid(*[np.arange(B + 1)] * 3, indexing='ij'), -1).reshape(-1, 3)
    corners = np.array([[x, y, z] for x in (0, 1) for y in (0, 1) for z in (0, 1)])
    edges = [(a, b) for a in range(8) for b in range(a + 1, 8) if np.abs(corners[a] - corners[b]).sum() == 1]
    gid = lambda g: (g[:, 0] * N[1] + g[:, 1]) * N[2] + g[:, 2]
    V_ids, V_pos, Q, QP = [], [], [], []
    step = max(1, 60000 // len(off))
    for s in range(0, len(act), step):
        blk = act[s:s + step]; nbk = len(blk)
        pts = (blk[:, None, :] * B + off[None]).reshape(-1, 3)
        vals = field.eval(lo + pts * h).reshape(nbk, B + 1, B + 1, B + 1)
        ins = vals < 0
        # ---- cells
        cnt = np.zeros((nbk, B, B, B), np.uint8)
        for o in corners:
            cnt += ins[:, o[0]:o[0] + B, o[1]:o[1] + B, o[2]:o[2] + B]
        cb, ci, cj, ck = np.nonzero((cnt > 0) & (cnt < 8))
        if len(cb):
            cv = np.stack([vals[cb, ci + o[0], cj + o[1], ck + o[2]] for o in corners], 1)
            acc = np.zeros((len(cb), 3)); n_ = np.zeros(len(cb))
            for a, b in edges:
                va, vb = cv[:, a], cv[:, b]
                m = (va < 0) != (vb < 0)
                t = va[m] / (va[m] - vb[m])
                acc[m] += corners[a] + t[:, None] * (corners[b] - corners[a]); n_[m] += 1
            g = blk[cb] * B + np.stack([ci, cj, ck], 1)
            V_ids.append(gid(g)); V_pos.append(lo + (g + acc / n_[:, None]) * h)
        # ---- quads across sign-changing lattice edges starting inside this block
        for ax in range(3):
            o1, o2 = [i for i in range(3) if i != ax]
            sl0 = [slice(None), slice(0, B), slice(0, B), slice(0, B)]
            sl1 = list(sl0); sl1[ax + 1] = slice(1, B + 1)
            s0 = ins[tuple(sl0)]; s1 = ins[tuple(sl1)]
            eb, ei, ej, ek = np.nonzero(s0 != s1)
            if not len(eb):
                continue
            P = blk[eb] * B + np.stack([ei, ej, ek], 1)
            flip = s0[eb, ei, ej, ek]
            def cell(d1, d2):
                q = P.copy(); q[:, o1] -= d1; q[:, o2] -= d2
                return gid(q)
            quad = np.stack([cell(0, 0), cell(1, 0), cell(1, 1), cell(0, 1)], 1)
            quad[flip] = quad[flip][:, ::-1]
            Q.append(quad); QP.append(lo + P * h)
    ids = np.concatenate(V_ids); pos = np.concatenate(V_pos)
    ids, first = np.unique(ids, return_index=True); pos = pos[first]
    Q = np.concatenate(Q)
    qi = np.searchsorted(ids, Q); qi = np.minimum(qi, len(ids) - 1)
    ok = (ids[qi] == Q).all(1)
    global LAST_DROPPED
    LAST_DROPPED = np.concatenate(QP)[~ok]
    log(f'  surface nets: {len(ids)} verts, {int(ok.sum())} quads ({int((~ok).sum())} dropped)')
    return pos, qi[ok]


def project(field, v, iters=4, max_step=0.004):
    """Newton-project vertices onto the zero level set, with the step clamped so vertices cannot jump gaps."""
    v = v.copy()
    for _ in range(iters):
        d = field.eval(v)
        g = field.grad(v)
        g2 = np.maximum((g * g).sum(1), 1e-6)
        step = (d / g2)[:, None] * g
        ln = np.linalg.norm(step, axis=1)
        sc = np.minimum(1.0, max_step / np.maximum(ln, 1e-12))
        v -= step * sc[:, None]
    return v
