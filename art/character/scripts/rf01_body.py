"""
rf01_body.py - anatomical body definition for the RF-01 Mission Systems Engineer (Checkpoint 1).

Units: metres. Blender convention: Z up, the character faces -Y, his left side is +X. Origin on the floor between
the feet. Target stature 1.80 m (about 7.75 heads).

The body is a skeleton (A-pose joint positions, also the future rig) dressed with anatomical forms (bone masses,
muscle groups, fat pads) blended as signed-distance primitives. Left side is built once and mirrored, except
where a small asymmetry is deliberate (face).
"""
import numpy as np
from rf01_sdf import Field, Ellipsoid, Cone, Box, Plane, Intersect, norm, frame, rot

STATURE = 1.80
FWD = np.array([0.0, -1.0, 0.0])
UP = np.array([0.0, 0.0, 1.0])
A_POSE_ARM_DEG = 45.0          # upper arm below horizontal
ELBOW_BEND_DEG = 12.0


def P(*v):
    return np.array(v, dtype=float)


def axes(M):
    """Ellipsoid/box axis rows for a shape rotated by world rotation M (local axes = columns of M)."""
    return np.asarray(M).T


# ============================================================================================== skeleton
def skeleton():
    """Joint positions in the A-pose (left side; right mirrors X). Also returned for the rig later."""
    J = {}
    J['root'] = P(0, 0, 0)
    J['pelvis'] = P(0, 0.010, 0.960)
    J['spine_01'] = P(0, 0.020, 1.065)
    J['spine_02'] = P(0, 0.018, 1.180)
    J['spine_03'] = P(0, 0.012, 1.320)
    J['neck'] = P(0, 0.018, 1.470)
    J['head'] = P(0, 0.006, 1.622)
    J['head_top'] = P(0, 0.0, STATURE)
    J['clavicle.L'] = P(0.022, -0.035, 1.455)
    J['shoulder.L'] = P(0.176, 0.012, 1.440)
    du = norm(P(np.cos(np.radians(A_POSE_ARM_DEG)), -0.06, -np.sin(np.radians(A_POSE_ARM_DEG))))
    J['elbow.L'] = J['shoulder.L'] + 0.318 * du
    ax = norm(np.cross(du, FWD))
    df = rot(ax, ELBOW_BEND_DEG) @ du
    J['wrist.L'] = J['elbow.L'] + 0.258 * df
    J['hip.L'] = P(0.088, 0.004, 0.925)
    J['knee.L'] = P(0.098, -0.006, 0.505)
    J['ankle.L'] = P(0.108, 0.024, 0.084)
    J['_du'] = du; J['_df'] = df
    return J


# ============================================================================================== builders
def torso(f, J):
    # --- core masses (midline)
    f.add(Ellipsoid(P(0, 0.014, 1.290), (0.132, 0.098, 0.165)), tag='ribcage')
    f.add(Ellipsoid(P(0, 0.024, 1.395), (0.155, 0.082, 0.078)), k=0.03, tag='upper chest')
    f.add(Ellipsoid(P(0, 0.006, 1.425), (0.120, 0.066, 0.060)), k=0.035, tag='upper thorax')
    f.add(Ellipsoid(P(0, -0.006, 1.120), (0.124, 0.082, 0.150)), k=0.04, tag='abdomen')
    f.add(Ellipsoid(P(0, -0.012, 1.010), (0.116, 0.072, 0.085)), k=0.03, tag='lower belly')
    f.add(Ellipsoid(P(0, 0.016, 0.945), (0.150, 0.100, 0.098)), k=0.04, tag='pelvis')
    # rectus abdominis: very soft relief (fit, not a bodybuilder)
    f.add(Ellipsoid(P(0, -0.073, 1.150), (0.060, 0.018, 0.120)), k=0.03, tag='rectus')
    f.sub(Cone(P(0, -0.097, 1.08), P(0, -0.100, 1.235), 0.0025, 0.0025), k=0.010, tag='linea alba')
    f.sub(Ellipsoid(P(0, -0.103, 1.075), (0.006, 0.010, 0.008)), k=0.006, tag='navel')
    f.add(Ellipsoid(P(0, -0.062, 0.868), (0.034, 0.030, 0.040)), k=0.025, tag='groin (modesty form)')
    # back
    f.sub(Cone(P(0, 0.118, 0.985), P(0, 0.121, 1.400), 0.0045, 0.0045), k=0.016, tag='spine groove')


def torso_side(f, J):
    S = J['shoulder.L']; du = J['_du']
    # pectoral: fan from sternum to the upper arm
    Rp = axes(rot(FWD, 14))
    f.add(Ellipsoid(P(0.072, -0.040, 1.420), (0.075, 0.028, 0.045)), k=0.035, tag='upper pec (clavicular)')
    f.add(Ellipsoid(P(0.068, -0.052, 1.352), (0.080, 0.032, 0.064), Rp), k=0.045, tag='pec')
    f.add(Cone(P(0.115, -0.050, 1.370), S + 0.060 * du + P(0, -0.028, 0.0), 0.022, 0.016, side=UP), k=0.035,
          tag='pec to arm')
    # latissimus / serratus / obliques
    f.add(Ellipsoid(P(0.100, 0.040, 1.250), (0.044, 0.056, 0.125), axes(rot(FWD, -18))), k=0.04, tag='lat')
    f.add(Ellipsoid(P(0.092, -0.012, 1.065), (0.040, 0.068, 0.070)), k=0.04, tag='oblique')
    # scapula + rear shoulder
    f.add(Ellipsoid(P(0.082, 0.094, 1.360), (0.058, 0.024, 0.074)), k=0.03, tag='scapula')
    f.add(Cone(P(0.028, 0.076, 1.030), P(0.030, 0.082, 1.300), 0.028, 0.022), k=0.035, tag='erector')
    # glute + hip
    f.add(Ellipsoid(P(0.070, 0.064, 0.888), (0.078, 0.060, 0.092), axes(rot(UP, 8))), k=0.035, tag='glute')
    f.add(Ellipsoid(P(0.128, 0.012, 0.915), (0.050, 0.065, 0.085)), k=0.04, tag='glute med / TFL')
    # trapezius slope neck -> acromion
    f.add(Cone(P(0.030, 0.040, 1.555), P(0.150, 0.020, 1.474), 0.040, 0.026, side=FWD, sx=1.0, sy=0.80), k=0.045,
          tag='trapezius')
    f.add(Ellipsoid(P(0.050, 0.070, 1.430), (0.055, 0.028, 0.080)), k=0.035, tag='mid trap')
    # clavicle (S-curve) -> acromion
    a = P(0.020, -0.052, 1.460); m = P(0.085, -0.052, 1.468); e = P(0.165, -0.004, 1.478)
    f.add(Cone(a + P(0.008, 0.004, 0), m, 0.0070, 0.0070), k=0.018, tag='clavicle')
    f.add(Cone(m, e, 0.0075, 0.0090), k=0.016, tag='clavicle')
    # deltoid
    Rd = frame(du, FWD)
    f.add(Ellipsoid(S + 0.040 * du + P(0.010, 0.0, 0.016), (0.057, 0.054, 0.094), Rd), k=0.03, tag='deltoid')


def neck(f, J):
    f.add(Cone(P(0, 0.012, 1.420), P(0, 0.008, 1.630), 0.061, 0.052, side=P(1, 0, 0), sx=1.0, sy=0.93), k=0.03,
          tag='neck')
    f.add(Ellipsoid(P(0, -0.040, 1.530), (0.008, 0.008, 0.011)), k=0.012, tag='larynx')
    f.sub(Ellipsoid(P(0, -0.072, 1.468), (0.015, 0.010, 0.010)), k=0.012, tag='jugular notch')


def neck_side(f, J):
    f.add(Cone(P(0.052, 0.012, 1.632), P(0.016, -0.050, 1.468), 0.0100, 0.0085), k=0.018, tag='SCM')


def arm(f, J):
    S, E, W = J['shoulder.L'], J['elbow.L'], J['wrist.L']
    du, df = J['_du'], J['_df']
    Ru = frame(du, FWD)            # rows: x ~ front, y ~ (lateral/up), z along arm
    front_u, side_u = Ru[0], Ru[1]
    f.add(Cone(S, E, 0.050, 0.038, side=FWD, sx=1.0, sy=0.93), k=0.02, tag='upper arm')
    f.add(Ellipsoid(S + 0.185 * du + 0.016 * front_u, (0.031, 0.034, 0.085), Ru), k=0.02, tag='biceps')
    f.add(Ellipsoid(S + 0.140 * du - 0.019 * front_u, (0.033, 0.038, 0.108), Ru), k=0.02, tag='triceps')
    Rf = frame(df, FWD)
    front_f, side_f = Rf[0], Rf[1]
    f.add(Ellipsoid(E - 0.020 * front_f + 0.004 * df, (0.020, 0.024, 0.024), Rf), k=0.015, tag='olecranon')
    f.add(Cone(E, W, 0.039, 0.026, side=front_f, sx=1.10, sy=0.90), k=0.02, tag='forearm')
    f.add(Ellipsoid(E + 0.075 * df + 0.006 * front_f + 0.008 * side_f, (0.036, 0.040, 0.085), Rf), k=0.025,
          tag='forearm muscles')
    u, t, n = hand_frame(J)
    f.add(Ellipsoid(W - 0.004 * u, (0.028, 0.019, 0.020), np.stack([t, n, u])), k=0.012, tag='wrist')


def hand_frame(J):
    """Rows: u (wrist -> fingers), t (thumb side), n (palm normal)."""
    u = J['_df']
    t = FWD - u * np.dot(FWD, u); t = norm(t)
    n = np.cross(u, t)
    return np.stack([u, t, n])


def hand(f, J):
    """Relaxed hand, palm toward the thigh. Hand-local axes: u wrist -> fingers, t thumb side, n palm normal."""
    W = J['wrist.L']
    u, t, n = hand_frame(J)
    L = lambda a, b, c: W + a * u + b * t + c * n
    Rh = np.stack([t, n, u])                                  # ellipsoid axes: x=t, y=n, z=u
    # palm: tapered slab, wrist-wide at the heel, knuckle-wide at the metacarpal heads
    f.add(Cone(L(0.016, -0.002, 0.001), L(0.074, -0.003, 0.0), 0.029, 0.037, side=t, sx=1.0, sy=0.40), k=0.012,
          tag='palm')
    f.add(Ellipsoid(L(0.050, -0.003, -0.003), (0.036, 0.011, 0.044), Rh), k=0.012, tag='back of hand')
    # metacarpal-head arch (knuckle line), index -> pinky
    f.add(Cone(L(0.092, 0.024, -0.002), L(0.094, 0.005, -0.003), 0.0105, 0.0108), k=0.010, tag='knuckle row')
    f.add(Cone(L(0.094, 0.005, -0.003), L(0.084, -0.030, -0.001), 0.0108, 0.0092), k=0.010, tag='knuckle row')
    # pads
    f.add(Ellipsoid(L(0.034, 0.020, 0.010), (0.017, 0.013, 0.030), Rh @ rot(n, 25).T), k=0.012, tag='thenar')
    f.add(Ellipsoid(L(0.046, -0.029, 0.008), (0.011, 0.010, 0.034), Rh), k=0.012, tag='hypothenar')
    f.add(Ellipsoid(L(0.090, -0.004, 0.009), (0.036, 0.008, 0.010), Rh), k=0.010, tag='distal palm pad')
    # fingers: (name, mcp(u,t), spread deg, lengths, radii at MCP, PIP, DIP, tip)
    fingers = [
        ('index',  (0.096, 0.025),  5.0, (0.042, 0.024, 0.019), (0.0094, 0.0086, 0.0076, 0.0068)),
        ('middle', (0.101, 0.006),  1.0, (0.046, 0.028, 0.020), (0.0097, 0.0089, 0.0079, 0.0070)),
        ('ring',   (0.097, -0.013), -4.0, (0.044, 0.027, 0.020), (0.0091, 0.0084, 0.0074, 0.0066)),
        ('pinky',  (0.087, -0.030), -9.0, (0.034, 0.019, 0.017), (0.0081, 0.0075, 0.0067, 0.0060)),
    ]
    curl = (12.0, 18.0, 10.0)
    for name, (mu, mt), spread, lens, rads in fingers:
        p = L(mu, mt, -0.001)
        d = rot(n, spread) @ u
        side = np.cross(n, d)
        for i in range(3):
            d = rot(side, -curl[i]) @ d              # flex toward the palm (+n)
            q = p + lens[i] * d
            ra, rb = rads[i], rads[i + 1]
            # phalanx shaft slightly waisted between the joints
            f.add(Cone(p, q, ra, rb, side=side, sx=1.05, sy=0.92), k=0.004 if i else 0.008, tag=f'{name} {i}')
            if i == 2:
                pn = norm(n - d * np.dot(n, d))
                Rn = np.stack([side, pn, d])
                f.add(Ellipsoid(p + 0.55 * lens[i] * d + 0.0022 * pn, (rb * 0.98, rb * 0.75, lens[i] * 0.42), Rn),
                      k=0.003, tag=name + ' pad')
                f.add(Ellipsoid(p + 0.62 * lens[i] * d - (rb * 0.80) * pn, (rb * 0.82, rb * 0.24, lens[i] * 0.36),
                                Rn), k=0.0012, tag=name + ' nail', phase=2)
            p = q
    # thumb: metacarpal from the trapezium, close to the index side, nail facing sideways
    c = L(0.014, 0.022, 0.006)
    d = norm(rot(n, 24) @ u + 0.22 * n)
    side = norm(np.cross(n, d))
    tl = (0.046, 0.031, 0.026); tr = (0.0130, 0.0108, 0.0096, 0.0084)
    mcp = c + tl[0] * d
    f.add(Cone(L(0.045, 0.012, 0.004), mcp, 0.012, 0.009, side=n, sx=0.55), k=0.012, tag='thumb web')
    for i in range(3):
        if i:
            d = rot(side, -(8 if i == 1 else 12)) @ d
        q = c + tl[i] * d
        f.add(Cone(c, q, tr[i], tr[i + 1], side=side, sx=1.05, sy=0.92), k=0.012 if i == 0 else 0.004,
              tag=f'thumb {i}')
        if i == 2:
            nb = norm(np.cross(side, d))
            nb = nb * np.sign(np.dot(nb, n))
            f.add(Ellipsoid(c + 0.60 * tl[i] * d + 0.0024 * nb, (tr[3] * 0.95, tr[3] * 0.78, tl[i] * 0.42),
                            np.stack([side, nb, d])), k=0.003, tag='thumb pad')
            f.add(Ellipsoid(c + 0.62 * tl[i] * d - (tr[3] * 0.82) * nb, (tr[3] * 0.85, tr[3] * 0.24, tl[i] * 0.36),
                            np.stack([side, nb, d])), k=0.0012, tag='thumb nail', phase=2)
        c = q


def leg(f, J):
    H, K, A = J['hip.L'], J['knee.L'], J['ankle.L']
    X = P(1, 0, 0)
    f.add(Cone(P(0.094, -0.002, 0.870), K + P(0, 0, 0.035), 0.086, 0.050, side=X, sx=0.96, sy=1.0), k=0.03,
          tag='thigh')
    f.add(Ellipsoid(P(0.136, -0.010, 0.715), (0.038, 0.050, 0.140)), k=0.03, tag='vastus lateralis')
    f.add(Ellipsoid(P(0.100, -0.050, 0.730), (0.044, 0.034, 0.150)), k=0.03, tag='rectus femoris')
    f.add(Ellipsoid(P(0.070, -0.036, 0.588), (0.034, 0.034, 0.058), axes(rot(FWD, 12))), k=0.025, tag='vastus medialis')
    f.add(Ellipsoid(P(0.100, 0.044, 0.720), (0.050, 0.040, 0.140)), k=0.03, tag='hamstrings')
    f.add(Ellipsoid(P(0.058, 0.002, 0.800), (0.040, 0.052, 0.085), axes(rot(FWD, 10))), k=0.03, tag='adductors')
    # knee
    f.add(Ellipsoid(K + P(0, 0.002, 0.010), (0.050, 0.046, 0.042)), k=0.02, tag='knee')
    f.add(Ellipsoid(K + P(0.002, -0.044, 0.014), (0.022, 0.012, 0.026)), k=0.012, tag='patella')
    f.add(Cone(K + P(0.0, -0.036, -0.012), K + P(0.003, -0.034, -0.060), 0.010, 0.009), k=0.012,
          tag='patellar tendon')
    # shin + calf
    f.add(Cone(K, A + P(0, 0, 0.02), 0.046, 0.029, side=X, sx=1.0, sy=0.95), k=0.02, tag='shin')
    f.add(Ellipsoid(P(0.083, 0.044, 0.395), (0.031, 0.034, 0.088)), k=0.025, tag='gastroc med')
    f.add(Ellipsoid(P(0.118, 0.040, 0.405), (0.028, 0.031, 0.078)), k=0.025, tag='gastroc lat')
    f.add(Ellipsoid(P(0.100, 0.030, 0.290), (0.040, 0.030, 0.090)), k=0.03, tag='soleus')
    f.add(Ellipsoid(P(0.114, -0.024, 0.380), (0.019, 0.020, 0.095)), k=0.02, tag='tibialis')
    f.add(Cone(P(0.104, 0.046, 0.250), A + P(0, 0.040, -0.015), 0.014, 0.011, side=X, sx=1.25), k=0.02,
          tag='achilles')
    f.add(Ellipsoid(A + P(-0.021, -0.004, 0.006), (0.011, 0.013, 0.014)), k=0.008, tag='malleolus med')
    f.add(Ellipsoid(A + P(0.024, 0.008, -0.010), (0.010, 0.012, 0.014)), k=0.008, tag='malleolus lat')


def foot(f, J):
    A = J['ankle.L']
    fd = rot(UP, 7) @ FWD                       # toe-out 7 deg
    lat = np.cross(fd, UP) * -1.0               # lateral (+X for the left foot)
    if lat[0] < 0:
        lat = -lat
    F = lambda a, b, c: P(A[0], A[1], 0) + a * fd + b * lat + c * UP     # a fwd from ankle, b lateral, c height
    Rf = np.stack([lat, fd, UP])
    f.add(Ellipsoid(F(-0.048, 0.002, 0.034), (0.031, 0.036, 0.034), Rf), k=0.02, tag='heel')
    f.add(Cone(A, F(-0.040, 0.0, 0.040), 0.030, 0.028), k=0.02, tag='ankle to heel')
    f.add(Ellipsoid(F(0.040, 0.002, 0.040), (0.040, 0.075, 0.034), Rf), k=0.025, tag='midfoot')
    f.add(Ellipsoid(F(0.010, -0.002, 0.060), (0.034, 0.045, 0.030), Rf), k=0.02, tag='instep')
    f.add(Ellipsoid(F(0.130, 0.002, 0.022), (0.049, 0.036, 0.022), Rf), k=0.02, tag='ball')
    f.sub(Ellipsoid(F(0.050, -0.040, -0.004), (0.020, 0.050, 0.020), Rf), k=0.015, tag='arch')
    toes = [(-0.024, 0.180, 0.0120, 0.0115, 0.0125), (-0.001, 0.172, 0.0082, 0.0076, 0.0092),
            (0.015, 0.165, 0.0078, 0.0072, 0.0088), (0.029, 0.156, 0.0074, 0.0068, 0.0084),
            (0.041, 0.146, 0.0070, 0.0064, 0.0080)]
    for i, (b, a, ra, rb, h) in enumerate(toes):
        f.add(Cone(F(a - 0.040, b, h + 0.004), F(a + (0.004 if i else 0.002), b - (0.002 if i else 0.0), h),
                   ra, rb, side=UP, sx=0.85, sy=1.0), k=0.006, tag=f'toe {i}')
        nr = rb * 0.85
        f.add(Ellipsoid(F(a - 0.004, b, h + rb * 0.70), (nr, nr * 0.9, rb * 0.22), Rf), k=0.0012, tag=f'toenail {i}', phase=2)


# ============================================================================================== head
class HeadSpace:
    """Head-local coordinates: x = his left, y = forward, z = up; origin at ear-canal height on the midline,
    at eye level (the eyes sit at half head height)."""
    def __init__(self, J):
        self.O = P(0.0, 0.0, 1.683)

    def __call__(self, x, y, z):
        return self.O + P(x, -y, z)

    def R(self, *rows):
        """Rows given in head space -> world rows."""
        return np.array([norm([r[0], -r[1], r[2]]) for r in rows], float)

    def v(self, x, y, z):
        return P(x, -y, z)


EYE_C = (0.0318, 0.0720, 0.0)        # eyeball centre (head space, left)
EYE_R = 0.0120


def arc(f, h, op, tag, y0, z, w, ry, rz, curv, k, taper=0.45, n=9, phase=None):
    """A smooth bar along the dental arch y = y0 - curv*x^2 from x = -w to w (head space): a chain of round cones,
    flattened vertically (rz) and tapering toward the corners."""
    xs = np.linspace(-w, w, n)
    pts = [h(x, y0 - curv * x * x, z) for x in xs]
    rad = [ry * (1 - taper * (x / w) ** 2) for x in xs]
    kw = {} if phase is None else {'phase': phase}
    for i in range(n - 1):
        c = Cone(pts[i], pts[i + 1], rad[i], rad[i + 1], side=UP, sx=rz / ry, sy=1.0)
        (f.add if op == 'add' else f.sub)(c, k=k, tag=tag, **kw)


def head_mid(f, J, h):
    f.add(Ellipsoid(h(0, -0.004, 0.034), (0.0765, 0.098, 0.084)), k=0.0, tag='cranium')
    f.add(Ellipsoid(h(0, -0.006, -0.008), (0.0660, 0.088, 0.064)), k=0.02, tag='skull base / temporal')
    f.add(Ellipsoid(h(0, -0.048, -0.016), (0.062, 0.052, 0.055)), k=0.02, tag='occiput')
    f.add(Ellipsoid(h(0, 0.030, 0.046), (0.056, 0.054, 0.056)), k=0.032, tag='forehead')
    f.add(Ellipsoid(h(0, 0.046, -0.036), (0.046, 0.044, 0.050)), k=0.02, tag='maxilla')
    # brow: two soft bars meeting at the glabella
    for s in (1, -1):
        f.add(Cone(h(s * 0.046, 0.077, 0.022), h(0, 0.087, 0.019), 0.0075, 0.0080), k=0.018, tag='brow')
    f.add(Ellipsoid(h(0, 0.082, -0.101), (0.023, 0.015, 0.016)), k=0.012, tag='chin')
    f.add(Ellipsoid(h(0, 0.058, -0.107), (0.022, 0.017, 0.0095)), k=0.016, tag='chin underside')
    f.add(Ellipsoid(h(0, 0.030, -0.088), (0.045, 0.048, 0.026)), k=0.02, tag='under jaw')
    f.add(Ellipsoid(h(0, 0.066, -0.066), (0.034, 0.029, 0.028)), k=0.026, tag='muzzle')
    # nose
    f.add(Cone(h(0, 0.082, 0.004), h(0, 0.111, -0.034), 0.0062, 0.0085, side=P(1, 0, 0), sx=1.25), k=0.010,
          tag='nasal bridge')
    f.add(Ellipsoid(h(0, 0.094, -0.030), (0.0135, 0.012, 0.016)), k=0.010, tag='nose sidewalls')
    f.sub(Ellipsoid(h(0, 0.099, 0.007), (0.012, 0.006, 0.006)), k=0.006, tag='nasion')
    f.add(Ellipsoid(h(0, 0.1150, -0.0395), (0.0092, 0.0092, 0.0086)), k=0.007, tag='nose tip')
    for s in (1, -1):
        f.add(Ellipsoid(h(s * 0.0140, 0.0985, -0.0450), (0.0066, 0.0086, 0.0062)), k=0.0065, tag='ala')
    f.add(Cone(h(0, 0.106, -0.046), h(0, 0.100, -0.051), 0.0034, 0.0032), k=0.005, tag='columella')
    # lips + mouth
    # lips and mouth line follow the dental arch (y = y0 - curv * x^2) instead of running straight across
    arc(f, h, 'add', 'upper lip', y0=0.0985, z=-0.0655, w=0.0205, ry=0.0080, rz=0.0055, curv=18.0, k=0.0040)
    f.add(Ellipsoid(h(0, 0.0850, -0.0575), (0.0130, 0.0100, 0.0085)), k=0.008, tag='philtrum mass')
    arc(f, h, 'add', 'lower lip', y0=0.0920, z=-0.0782, w=0.0175, ry=0.0085, rz=0.0063, curv=20.0, k=0.0040)
    arc(f, h, 'sub', 'mouth line', y0=0.1060, z=-0.0718, w=0.0225, ry=0.0065, rz=0.0010, curv=18.0, k=0.0012,
        taper=0.0, phase=1)
    f.sub(Ellipsoid(h(0, 0.0960, -0.0890), (0.0120, 0.0050, 0.0022)), k=0.0080, tag='labiomental fold')


def head_side(f, J, h, s=1.0):
    """One side of the face. s is only used to shift tiny asymmetries (called for left; mirrored for right)."""
    # cheekbone + malar
    f.add(Cone(h(0.047, 0.058, -0.012), h(0.064, 0.016, -0.008), 0.0105, 0.0080), k=0.012, tag='zygomatic')
    f.add(Ellipsoid(h(0.036, 0.058, -0.030), (0.019, 0.016, 0.019)), k=0.012, tag='malar')
    f.add(Ellipsoid(h(0.030, 0.068, -0.020), (0.015, 0.010, 0.010)), k=0.010, tag='infraorbital')
    f.add(Cone(h(0.051, 0.030, -0.020), h(0.046, 0.018, -0.064), 0.0125, 0.0115), k=0.030, tag='masseter')
    f.add(Ellipsoid(h(0.034, 0.046, -0.058), (0.014, 0.018, 0.018)), k=0.022, tag='buccal')
    # jaw
    G = h(0.0500, 0.000, -0.074)
    f.add(Cone(G, h(0.020, 0.082, -0.106), 0.0125, 0.0110), k=0.018, tag='mandible')
    f.add(Cone(G, h(0.0540, -0.008, -0.026), 0.0115, 0.0095), k=0.016, tag='ramus')
    # eye socket, lids
    ex, ey, ez = EYE_C
    f.sub(Ellipsoid(h(ex - 0.002, ey + 0.017, ez + 0.006), (0.017, 0.010, 0.012)), k=0.008, tag='orbit')
    f.add(Ellipsoid(h(ex, ey, ez), (EYE_R + 0.0020,) * 3), k=0.0035, tag='lid shell', phase=2)
    tilt = np.radians(4.0)
    Ra = h.R((np.cos(tilt), 0, np.sin(tilt)), (0, 1, 0), (-np.sin(tilt), 0, np.cos(tilt)))
    f.sub(Ellipsoid(h(ex + 0.0006, ey + 0.0128, ez - 0.0010), (0.0150, 0.0110, 0.0046), Ra), k=0.0012,
          tag='palpebral fissure', phase=3)
    f.sub(Ellipsoid(h(ex - 0.001, ey + 0.0105, ez + 0.0130), (0.0120, 0.0040, 0.0008), Ra), k=0.0045,
          tag='lid crease', phase=3)
    f.sub(Ellipsoid(h(0.0068, 0.1035, -0.0498), (0.0030, 0.0050, 0.0018), h.R((1, 0.4, 0), (-0.4, 1, 0), (0, 0, 1))),
          k=0.0015, tag='nostril')
    # nasolabial + mouth corner
    f.sub(Cone(h(0.0200, 0.097, -0.048), h(0.0300, 0.088, -0.078), 0.0012, 0.0010), k=0.0080, tag='nasolabial')
    f.sub(Ellipsoid(h(0.0240, 0.0880, -0.0720), (0.0020, 0.0030, 0.0020)), k=0.0030, tag='mouth corner')
    # ear
    Ec = h(0.0735, -0.010, -0.012)
    n = norm(h.v(1.0, 0.28, 0.0))
    up = norm(h.v(0.0, -0.26, 1.0)); up = norm(up - n * np.dot(up, n))
    w = np.cross(up, n)
    if np.dot(w, h.v(0, 1, 0)) < 0:
        w = -w                                   # w points forward
    Re = np.stack([n, w, up])
    E = lambda a, b, c: Ec + a * n + b * w + c * up
    f.add(Ellipsoid(E(0.002, 0.004, -0.004), (0.006, 0.011, 0.018), Re), k=0.007, tag='ear root')
    f.add(Ellipsoid(E(0.0085, 0.0, 0.0), (0.0062, 0.0170, 0.0310), Re), k=0.0035, tag='helix')
    f.sub(Ellipsoid(E(0.0160, 0.0015, 0.0025), (0.0075, 0.0128, 0.0250), Re), k=0.0020, tag='scapha')
    f.add(Ellipsoid(E(0.0085, 0.0010, 0.0035), (0.0035, 0.0080, 0.0175), Re), k=0.0020, tag='antihelix', phase=2)
    f.sub(Ellipsoid(E(0.0105, 0.0055, -0.0040), (0.0052, 0.0070, 0.0090), Re), k=0.0020, tag='concha', phase=3)
    f.add(Ellipsoid(E(0.0055, 0.0135, -0.0060), (0.0040, 0.0040, 0.0058), Re), k=0.0020, tag='tragus')
    f.add(Ellipsoid(E(0.0060, 0.0015, -0.0255), (0.0045, 0.0092, 0.0088), Re), k=0.0030, tag='lobule')


# ============================================================================================== assembly
def build(include_head=True, cp=1):
    """cp=1: the approved CP1 body (used by the CP2/CP3 garment builds). cp=4: refined face and hands
    (rf01_head_v4), with the facial asymmetry warp. Everything else is identical."""
    J = skeleton()
    f = Field()
    if cp >= 4:
        import rf01_head_v4 as V4

    def both(fn, *args):
        """Run a left-side builder, then mirror the primitives it added to the right."""
        n0 = len(f.ops)
        fn(f, *args)
        for op, prim, k, tag, ph in list(f.ops[n0:]):
            f.ops.append((op, prim.mirror(), k, tag + ' R', ph))

    torso(f, J)
    both(torso_side, J)
    neck(f, J)
    both(neck_side, J)
    both(arm, J)
    both(V4.hand_v4 if cp >= 4 else hand, J)
    both(leg, J)
    both(foot, J)
    if include_head:
        h = HeadSpace(J)
        if cp >= 4:
            V4.head_mid_v4(f, J, h)
            both(V4.head_side_v4, J, h)
            f.warps = V4.face_warps(h)
        else:
            head_mid(f, J, h)
            both(head_side, J, h)
    # flat soles: everything below the floor is removed
    f.cut(Plane(P(0, 0, 0), P(0, 0, -1), 10.0), k=0.002, tag='floor')
    return f.finalize(), J


def eye_centres():
    h = HeadSpace(None)
    ex, ey, ez = EYE_C
    return [h(ex, ey, ez), h(-ex, ey, ez)], EYE_R
