"""
rf01_head_v4.py - Checkpoint 4 refinement of the RF-01 face and hands (form only).

Imported by rf01_body.build(cp=4). The CP1 functions in rf01_body stay untouched, so the approved CP1-CP3 builds
remain reproducible. Same head space as CP1: x = his left, y = forward, z = up, origin at ear-canal depth on the
midline at eye level.

Fixes the CP1 notes: lips heavy/forward, brow and lid transitions, short/stubby thumb, face and hands not final.
Asymmetry is applied afterwards as a smooth coordinate warp (FACE_WARPS), so the mirrored halves are not identical.
"""
import numpy as np
from rf01_sdf import Ellipsoid, Cone, Box, Intersect, Plane, norm, frame, rot
from rf01_body import P, UP, FWD, EYE_C, EYE_R, arc, hand_frame

# --------------------------------------------------------------------------------------------- asymmetry
# (head-space centre, radius, head-space displacement of the surface). Restrained: 0.3-0.9 mm.
FACE_WARPS = [
    ((-0.034, 0.080, 0.024), 0.016, (0.0, 0.0, 0.0008)),     # his right brow sits ~0.8 mm higher
    ((0.032, 0.086, 0.006), 0.007, (0.0, 0.0, -0.0003)),     # his left upper lid a touch heavier
    ((-0.024, 0.089, -0.0715), 0.008, (0.0, 0.0, 0.0005)),   # right mouth corner 0.5 mm higher
    ((0.000, 0.113, -0.040), 0.010, (0.0006, 0.0, 0.0)),     # nose tip 0.6 mm toward his left
    ((0.040, 0.060, -0.036), 0.018, (0.0007, 0.0004, 0.0)),  # left cheek slightly fuller
    ((-0.058, -0.004, -0.050), 0.020, (-0.0004, 0.0, 0.0)),  # right jaw angle a little wider
]


def face_warps(h):
    """World-space warps for the Field: (centre, radius, vector)."""
    out = []
    for c, r, v in FACE_WARPS:
        out.append((h(*c), r, h.v(*v)))
    return out


# --------------------------------------------------------------------------------------------- midline
def head_mid_v4(f, J, h):
    f.add(Ellipsoid(h(0, -0.004, 0.034), (0.0765, 0.098, 0.084)), k=0.0, tag='cranium')
    f.add(Ellipsoid(h(0, -0.006, -0.008), (0.0660, 0.088, 0.064)), k=0.02, tag='skull base / temporal')
    f.add(Ellipsoid(h(0, -0.048, -0.016), (0.062, 0.052, 0.055)), k=0.02, tag='occiput')
    f.add(Ellipsoid(h(0, 0.030, 0.046), (0.056, 0.054, 0.056)), k=0.025, tag='forehead')
    for s in (1, -1):                                                    # frontal eminences, very soft
        f.add(Ellipsoid(h(s * 0.026, 0.054, 0.062), (0.022, 0.016, 0.020)), k=0.02, tag='frontal eminence')
    f.add(Ellipsoid(h(0, 0.046, -0.036), (0.046, 0.044, 0.050)), k=0.02, tag='maxilla')
    # brow: softer bars, smoother glabella (no vertical notch), gentle transition into the forehead
    for s in (1, -1):
        f.add(Cone(h(s * 0.046, 0.075, 0.023), h(s * 0.012, 0.086, 0.021), 0.0064, 0.0072), k=0.022, tag='brow')
    f.add(Ellipsoid(h(0, 0.086, 0.016), (0.012, 0.0065, 0.010)), k=0.012, tag='glabella / procerus')
    f.add(Ellipsoid(h(0, 0.081, -0.101), (0.022, 0.015, 0.016)), k=0.012, tag='chin')
    f.add(Ellipsoid(h(0, 0.058, -0.107), (0.022, 0.017, 0.0095)), k=0.016, tag='chin underside')
    f.add(Ellipsoid(h(0, 0.030, -0.090), (0.041, 0.044, 0.022)), k=0.018, tag='under jaw (tighter)')
    f.add(Ellipsoid(h(0, 0.064, -0.066), (0.033, 0.028, 0.027)), k=0.034, tag='muzzle')
    # nose: same bridge, bilobed tip, longer columella
    f.add(Cone(h(0, 0.082, 0.004), h(0, 0.110, -0.034), 0.0060, 0.0080, side=P(1, 0, 0), sx=1.22), k=0.010,
          tag='nasal bridge')
    f.add(Ellipsoid(h(0, 0.094, -0.030), (0.0130, 0.012, 0.016)), k=0.010, tag='nose sidewalls')
    f.sub(Ellipsoid(h(0, 0.099, 0.007), (0.012, 0.006, 0.006)), k=0.006, tag='nasion')
    f.add(Ellipsoid(h(0, 0.1130, -0.0392), (0.0080, 0.0088, 0.0080)), k=0.007, tag='nose tip')
    for s in (1, -1):
        f.add(Ellipsoid(h(s * 0.0036, 0.1150, -0.0402), (0.0056, 0.0062, 0.0060)), k=0.004, tag='tip lobule')
    f.add(Cone(h(0, 0.1085, -0.0450), h(0, 0.1000, -0.0515), 0.0033, 0.0030), k=0.005, tag='columella')
    # lips: less projection, stronger wrap around the dental arch, thinner vermilion, defined corners
    arc(f, h, 'add', 'upper lip', y0=0.0970, z=-0.0652, w=0.0200, ry=0.0066, rz=0.0049, curv=24.0, k=0.0036,
        taper=0.55)
    f.add(Ellipsoid(h(0, 0.0845, -0.0572), (0.0125, 0.0095, 0.0082)), k=0.008, tag='philtrum mass')
    for s in (1, -1):                                                    # philtral columns
        f.add(Cone(h(s * 0.0042, 0.0998, -0.0520), h(s * 0.0054, 0.0995, -0.0610), 0.0011, 0.0012), k=0.0022,
              tag='philtral column')
    f.add(Ellipsoid(h(0, 0.1010, -0.0662), (0.0042, 0.0024, 0.0024)), k=0.0020, tag='upper lip tubercle')
    f.sub(Ellipsoid(h(0, 0.1004, -0.0610), (0.0028, 0.0030, 0.0011)), k=0.0014, tag="cupid's bow dip", phase=3)
    arc(f, h, 'add', 'lower lip', y0=0.0912, z=-0.0779, w=0.0168, ry=0.0071, rz=0.0060, curv=25.0, k=0.0036,
        taper=0.55)
    arc(f, h, 'sub', 'mouth line', y0=0.1048, z=-0.0716, w=0.0228, ry=0.0060, rz=0.0009, curv=23.0, k=0.0012,
        taper=0.0, phase=1)
    f.sub(Ellipsoid(h(0, 0.0955, -0.0888), (0.0115, 0.0048, 0.0021)), k=0.0080, tag='labiomental fold')


# --------------------------------------------------------------------------------------------- one side
def head_side_v4(f, J, h, s=1.0):
    # cheek: bone, malar fat, a little hollow under the cheekbone (not a mask)
    f.add(Cone(h(0.047, 0.058, -0.012), h(0.064, 0.016, -0.008), 0.0102, 0.0078), k=0.012, tag='zygomatic')
    f.add(Ellipsoid(h(0.036, 0.058, -0.030), (0.019, 0.016, 0.019)), k=0.012, tag='malar')
    f.add(Ellipsoid(h(0.030, 0.068, -0.020), (0.015, 0.010, 0.010)), k=0.010, tag='infraorbital')
    f.add(Cone(h(0.051, 0.030, -0.020), h(0.046, 0.018, -0.064), 0.0125, 0.0115), k=0.030, tag='masseter')
    f.add(Ellipsoid(h(0.034, 0.046, -0.058), (0.014, 0.018, 0.018)), k=0.030, tag='buccal')
    # jaw: slightly crisper line, same width
    G = h(0.0500, 0.000, -0.074)
    f.add(Cone(G, h(0.020, 0.082, -0.106), 0.0122, 0.0108), k=0.015, tag='mandible')
    f.add(Cone(G, h(0.0540, -0.008, -0.026), 0.0115, 0.0095), k=0.016, tag='ramus')
    # ---- eye: same eyeball and lid shell; refined lids
    ex, ey, ez = EYE_C
    f.sub(Ellipsoid(h(ex - 0.002, ey + 0.017, ez + 0.006), (0.017, 0.0085, 0.012)), k=0.011, tag='orbit')
    f.add(Ellipsoid(h(ex, ey, ez), (EYE_R + 0.0020,) * 3), k=0.0035, tag='lid shell', phase=2)
    f.add(Ellipsoid(h(ex + 0.0005, ey + 0.0098, ez - 0.0066), (0.0100, 0.0030, 0.0018)), k=0.0035,
          tag='lower lid (pretarsal)', phase=2)
    tilt = np.radians(4.0)
    Ra = h.R((np.cos(tilt), 0, np.sin(tilt)), (0, 1, 0), (-np.sin(tilt), 0, np.cos(tilt)))
    f.sub(Ellipsoid(h(ex + 0.0006, ey + 0.0128, ez - 0.0010), (0.0150, 0.0110, 0.0046), Ra), k=0.0012,
          tag='palpebral fissure', phase=3)
    f.sub(Ellipsoid(h(ex - 0.001, ey + 0.0102, ez + 0.0128), (0.0115, 0.0030, 0.0006), Ra), k=0.0060,
          tag='lid crease (softer)', phase=3)
    # ---- nose: teardrop nostril, alar crease
    Rn = h.R((1, 0.4, 0), (-0.4, 1, 0), (0, 0, 1))
    f.sub(Ellipsoid(h(0.0070, 0.0986, -0.0512), (0.0029, 0.0038, 0.0016), Rn), k=0.0014, tag='nostril')
    f.sub(Cone(h(0.0205, 0.0945, -0.0395), h(0.0195, 0.0985, -0.0500), 0.0008, 0.0008), k=0.0030, tag='alar crease')
    # nasolabial + mouth corner (modiolus)
    f.sub(Cone(h(0.0205, 0.097, -0.049), h(0.0298, 0.088, -0.078), 0.0011, 0.0009), k=0.0085, tag='nasolabial')
    f.add(Ellipsoid(h(0.0285, 0.0815, -0.0710), (0.0038, 0.0034, 0.0045)), k=0.0060, tag='modiolus')
    f.sub(Ellipsoid(h(0.0236, 0.0885, -0.0718), (0.0012, 0.0020, 0.0012)), k=0.0035, tag='mouth corner')
    # ---- ear: plate, rolled helix rim, antihelix with crura, concha, tragus, antitragus, lobule
    Ec = h(0.0735, -0.010, -0.012)
    n = norm(h.v(1.0, 0.28, 0.0))
    up = norm(h.v(0.0, -0.26, 1.0)); up = norm(up - n * np.dot(up, n))
    w = np.cross(up, n)
    if np.dot(w, h.v(0, 1, 0)) < 0:
        w = -w                                    # w points forward
    Re = np.stack([n, w, up])
    E = lambda a, b, c: Ec + a * n + b * w + c * up
    f.add(Ellipsoid(E(0.002, 0.004, -0.004), (0.006, 0.011, 0.018), Re), k=0.007, tag='ear root')
    f.add(Ellipsoid(E(0.0080, 0.0, 0.0), (0.0052, 0.0162, 0.0298), Re), k=0.0030, tag='ear plate')
    f.sub(Ellipsoid(E(0.0150, 0.0012, 0.0022), (0.0072, 0.0124, 0.0242), Re), k=0.0018, tag='scapha')
    th = np.radians(np.linspace(62, 262, 21))                            # helix rim: front-top, over, down the back
    rim = [E(0.0070 + 0.0035 * (t - th[0]) / (th[-1] - th[0]), 0.0150 * np.cos(t), 0.0285 * np.sin(t)) for t in th]
    for a_, b_ in zip(rim[:-1], rim[1:]):
        f.add(Cone(a_, b_, 0.0026, 0.0026), k=0.0012, tag='helix rim', phase=2)
    f.add(Cone(E(0.0055, 0.0080, 0.0150), E(0.0060, 0.0115, 0.0035), 0.0020, 0.0018), k=0.0015,
          tag='helix crus', phase=2)
    ah = [E(0.0084, -0.0085, -0.0130), E(0.0088, -0.0080, -0.0030), E(0.0088, -0.0045, 0.0080), E(0.0085, 0.0000, 0.0150)]
    for a_, b_ in zip(ah[:-1], ah[1:]):
        f.add(Cone(a_, b_, 0.0020, 0.0018), k=0.0016, tag='antihelix', phase=3)
    f.add(Cone(ah[2], E(0.0082, 0.0060, 0.0215), 0.0015, 0.0013), k=0.0014, tag='crus superior', phase=3)
    f.add(Cone(ah[2], E(0.0080, 0.0085, 0.0090), 0.0015, 0.0013), k=0.0014, tag='crus inferior', phase=3)
    f.sub(Ellipsoid(E(0.0100, 0.0050, -0.0045), (0.0050, 0.0068, 0.0088), Re), k=0.0018, tag='concha', phase=4)
    f.add(Ellipsoid(E(0.0055, 0.0130, -0.0060), (0.0038, 0.0040, 0.0055), Re), k=0.0018, tag='tragus', phase=4)
    f.add(Ellipsoid(E(0.0075, -0.0035, -0.0150), (0.0032, 0.0040, 0.0036), Re), k=0.0016, tag='antitragus', phase=4)
    f.add(Ellipsoid(E(0.0058, 0.0010, -0.0255), (0.0042, 0.0090, 0.0085), Re), k=0.0028, tag='lobule')


# --------------------------------------------------------------------------------------------- hand
def hand_v4(f, J):
    """Relaxed hand, palm toward the thigh. u wrist -> fingers, t thumb side, n palm normal.
    Longer, slimmer thumb; waisted phalanges with joint knuckles; nail folds; webbing; dorsal tendons."""
    W = J['wrist.L']
    u, t, n = hand_frame(J)
    L = lambda a, b, c: W + a * u + b * t + c * n
    Rh = np.stack([t, n, u])
    f.add(Cone(L(0.016, -0.002, 0.001), L(0.074, -0.003, 0.0), 0.029, 0.037, side=t, sx=1.0, sy=0.40), k=0.012,
          tag='palm')
    f.add(Ellipsoid(L(0.050, -0.003, -0.003), (0.036, 0.011, 0.044), Rh), k=0.012, tag='back of hand')
    f.add(Cone(L(0.092, 0.024, -0.002), L(0.094, 0.005, -0.003), 0.0102, 0.0105), k=0.010, tag='knuckle row')
    f.add(Cone(L(0.094, 0.005, -0.003), L(0.084, -0.030, -0.001), 0.0105, 0.0090), k=0.010, tag='knuckle row')
    f.add(Ellipsoid(L(0.040, 0.021, 0.010), (0.016, 0.013, 0.034), Rh @ rot(n, 24).T), k=0.012, tag='thenar')
    f.add(Ellipsoid(L(0.046, -0.029, 0.008), (0.011, 0.010, 0.034), Rh), k=0.012, tag='hypothenar')
    f.add(Ellipsoid(L(0.090, -0.004, 0.009), (0.036, 0.008, 0.010), Rh), k=0.010, tag='distal palm pad')
    # dorsal extensor tendons (very soft) and palm creases (very shallow)
    for mt in (0.024, 0.006, -0.012, -0.029):
        f.add(Cone(L(0.022, mt * 0.45, -0.0118), L(0.086, mt, -0.0128), 0.0015, 0.0018), k=0.007, tag='tendon')
    f.sub(Cone(L(0.060, 0.030, 0.016), L(0.030, 0.008, 0.017), 0.0007, 0.0007), k=0.0022, tag='thenar crease')
    f.sub(Cone(L(0.082, -0.034, 0.012), L(0.088, 0.010, 0.013), 0.0007, 0.0007), k=0.0022, tag='distal crease')
    fingers = [
        ('index',  (0.096, 0.025),  5.0, (0.043, 0.025, 0.020), (0.0092, 0.0084, 0.0074, 0.0065)),
        ('middle', (0.101, 0.006),  1.0, (0.047, 0.029, 0.021), (0.0095, 0.0087, 0.0077, 0.0067)),
        ('ring',   (0.097, -0.013), -4.0, (0.045, 0.028, 0.021), (0.0089, 0.0082, 0.0072, 0.0064)),
        ('pinky',  (0.087, -0.030), -9.0, (0.035, 0.020, 0.018), (0.0080, 0.0073, 0.0065, 0.0058)),
    ]
    curl = (12.0, 18.0, 10.0)
    mcps = []
    for name, (mu, mt), spread, lens, rads in fingers:
        p = L(mu, mt, -0.001); mcps.append(p)
        d = rot(n, spread) @ u
        side = np.cross(n, d)
        for i in range(3):
            d = rot(side, -curl[i]) @ d
            q = p + lens[i] * d
            ra, rb = rads[i], rads[i + 1]
            mid = p + 0.5 * lens[i] * d
            rm = 0.5 * (ra + rb) * 0.97                                   # slightly waisted shaft
            k = 0.004 if i else 0.008
            f.add(Cone(p, mid, ra, rm, side=side, sx=1.06, sy=0.90), k=k, tag=f'{name} {i}a')
            f.add(Cone(mid, q, rm, rb, side=side, sx=1.06, sy=0.90), k=0.003, tag=f'{name} {i}b')
            pn = norm(n - d * np.dot(n, d))
            if i < 2:                                                     # joint knuckle (dorsal) at PIP / DIP
                f.add(Ellipsoid(q - pn * rb * 0.40, (rb * 0.62, rb * 0.42, rb * 0.62), np.stack([side, pn, d])),
                      k=0.004, tag=f'{name} knuckle {i}')
            if i == 2:
                Rn = np.stack([side, pn, d])
                f.add(Ellipsoid(p + 0.55 * lens[i] * d + 0.0022 * pn, (rb * 0.98, rb * 0.75, lens[i] * 0.42), Rn),
                      k=0.003, tag=name + ' pad')
                f.add(Ellipsoid(p + 0.62 * lens[i] * d - (rb * 0.80) * pn, (rb * 0.80, rb * 0.24, lens[i] * 0.36), Rn),
                      k=0.0010, tag=name + ' nail', phase=2)
            p = q
    for a_, b_ in zip(mcps[:-1], mcps[1:]):                               # palmar webbing between fingers
        f.add(Ellipsoid(0.5 * (a_ + b_) + 0.011 * u + 0.004 * n, (0.0052, 0.0040, 0.0060), Rh), k=0.0055, tag='web')
    # thumb: proximal CMC, longer metacarpal and phalanges, slimmer
    c = L(0.012, 0.020, 0.008)
    d = norm(rot(n, 20) @ u + 0.34 * n)
    side = norm(np.cross(n, d))
    tl = (0.048, 0.035, 0.029); tr = (0.0125, 0.0106, 0.0094, 0.0080)
    mcp = c + tl[0] * d
    f.add(Cone(L(0.048, 0.012, 0.004), mcp, 0.0115, 0.0085, side=n, sx=0.55), k=0.012, tag='thumb web')
    for i in range(3):
        if i:
            d = rot(side, -(7 if i == 1 else 11)) @ d
        q = c + tl[i] * d
        mid = c + 0.5 * tl[i] * d
        rm = 0.5 * (tr[i] + tr[i + 1]) * (0.96 if i else 1.0)
        f.add(Cone(c, mid, tr[i], rm, side=side, sx=1.05, sy=0.92), k=0.012 if i == 0 else 0.004, tag=f'thumb {i}a')
        f.add(Cone(mid, q, rm, tr[i + 1], side=side, sx=1.05, sy=0.92), k=0.003, tag=f'thumb {i}b')
        nb = norm(np.cross(side, d)); nb = nb * np.sign(np.dot(nb, n))
        if i == 1:
            f.add(Ellipsoid(q - nb * tr[2] * 0.45, (tr[2] * 0.8, tr[2] * 0.55, tr[2] * 0.7), np.stack([side, nb, d])),
                  k=0.003, tag='thumb knuckle')
        if i == 2:
            f.add(Ellipsoid(c + 0.60 * tl[i] * d + 0.0024 * nb, (tr[3] * 0.95, tr[3] * 0.78, tl[i] * 0.42),
                            np.stack([side, nb, d])), k=0.003, tag='thumb pad')
            f.add(Ellipsoid(c + 0.62 * tl[i] * d - (tr[3] * 0.82) * nb, (tr[3] * 0.85, tr[3] * 0.24, tl[i] * 0.36),
                            np.stack([side, nb, d])), k=0.0010, tag='thumb nail', phase=2)
        c = q


def hand_joints(J):
    """Finger and thumb joint positions of hand_v4 (left hand): {finger: [base, j1, j2, tip]} plus the curl axes
    ('<finger>_axis'), for the rig. Mirrors exactly the chain logic above."""
    W = J['wrist.L']
    u, t, n = hand_frame(J)
    L = lambda a, b, c: W + a * u + b * t + c * n
    out = {}
    fingers = [('Index', (0.096, 0.025), 5.0, (0.043, 0.025, 0.020)), ('Middle', (0.101, 0.006), 1.0, (0.047, 0.029, 0.021)),
               ('Ring', (0.097, -0.013), -4.0, (0.045, 0.028, 0.021)), ('Little', (0.087, -0.030), -9.0, (0.035, 0.020, 0.018))]
    curl = (12.0, 18.0, 10.0)
    for name, (mu, mt), spread, lens in fingers:
        p = L(mu, mt, -0.001); pts = [p]
        d = rot(n, spread) @ u
        side = np.cross(n, d)
        for i in range(3):
            d = rot(side, -curl[i]) @ d
            p = p + lens[i] * d; pts.append(p)
        out[name] = pts; out[name + '_axis'] = norm(side)
    c = L(0.012, 0.020, 0.008); d = norm(rot(n, 20) @ u + 0.34 * n); side = norm(np.cross(n, d))
    tl = (0.048, 0.035, 0.029); pts = [c]
    for i in range(3):
        if i:
            d = rot(side, -(7 if i == 1 else 11)) @ d
        c = c + tl[i] * d; pts.append(c)
    out['Thumb'] = pts; out['Thumb_axis'] = side
    out['palm_normal'] = n
    return out
