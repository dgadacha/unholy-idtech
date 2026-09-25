"""
UNHOLY -- le fusil du militaire, modelise par script.

Un HK416 A5 a canon court : boitiers a rail continu, garde-main a quatre rails
perce de jours, guidon et dioptre rabattables dresses (on vise avec eux : pas
de viseur optique), cache-flamme a fentes, chargeur acier a nervures, poignee
ergonomique, crosse fine a plaque de couche crantee. S'y ajoute une lampe sur
le rail droit (brief, milestone 4).

Les formes libres (crosse, poignee, chargeur, boitier inferieur et pontet,
detente, guidon) sont tendues sur des contours releves sur une photo de profil
(tools/assets/hd/trace.py, outlines/hk416.json) ; le reste est construit a
leurs cotes, relevees sur la meme photo (fonction P). Aucun marquage : ni
logo, ni gravure de fabricant, ni chiffres sur les rails.

Le fusil remplace celui du Retro Weapon Pack mais garde ses animations. Le
releve est recale sur les mains du pack (voir trace.py) : la poignee, la
detente, le garde-main et le puits de chargeur tombent la ou les mains des
animations les attendent, et les pieces mobiles portent le nom des os qui les
animent. Le garde-main garde les proportions de la photo : c'est la main
gauche qui descend de 6,5 mm pour l'empoigner (voir GRIP_DROP, applique par
retro_rifle.py).

Repere du fusil (celui du squelette du pack, en centimetres) : X vers la
bouche, Y vers la gauche, Z vers le haut, l'origine au pied de la poignee.
L'axe du canon passe a z = 16,21 ; l'oeil, epaule, a z = 24,82 : c'est la
hauteur de la pointe du guidon et du centre du dioptre.

Les os et ce qu'ils font dans les animations :
  Main                 le corps du fusil
  Magazine             le chargeur, qui sort et revient au rechargement
  ChargeHandle         le levier d'armement, tire de 5 cm
  DustCover            la culasse, qui recule de 8,5 cm au tir (le nom du pack trompe)
  EjectionCover        la porte de la fenetre d'ejection, qui s'ouvre de 145 degres
  Trigger              la detente, qui pivote autour de son axe
  FrontAssistAssembly  le bouton d'assistance de fermeture
  RearSight, FrontSight  le dioptre et le guidon, dresses, immobiles
"""

import json
import math
import os

from mathutils import Vector

import kit
import materials

HERE = os.path.dirname(os.path.abspath(__file__))
_TRACED = json.load(open(os.path.join(HERE, 'outlines', 'hk416.json')))
OUTLINES = _TRACED['parts']
REG = _TRACED['registration']


def P(px, py):
    """Un point de la photo de reference (pixels), en centimetres du fusil."""
    s = REG['scale']
    return (REG['x_anchor'] + (px - REG['px_anchor']) * s, REG['z_anchor'] + (REG['py_anchor'] - py) * s)


def X(px):
    return P(px, REG['py_anchor'])[0]


def Z(py):
    return P(REG['px_anchor'], py)[1]


BORE_Z = Z(218.5)       # axe du canon (16,21)
EYE_Z = 24.82           # l'oeil, epaule : la pointe du guidon, le centre du dioptre
RAIL_TOP = Z(128)       # le sommet des rails (20,42)
RAIL_BASE = RAIL_TOP - 0.95
SEAM_Z = Z(250)         # la jonction des deux boitiers (14,75)
TUBE_Z = BORE_Z + 0.1   # l'axe du tube de crosse
UPPER_HALF = 1.65
LOWER_HALF = 1.66
WELL_HALF = 1.30        # le creux du puits
UPPER_X0 = 2.3          # la face arriere du boitier superieur
RAIL_X0 = X(568)        # l'arriere du rail du boitier (2,87)
UPPER_X1 = X(1003)      # l'avant du boitier, l'arriere du garde-main (23,10)
HG_X1 = X(1598)         # l'avant du garde-main (50,77)
MUZZLE_X = X(1757)      # la bouche du cache-flamme (58,16)

# Les fentes des rails Picatinny, relevees sur la photo : un pas de 24,1 pixels.
PITCH = 24.11 * REG['scale']
SLOT_PHASE = X(683.5)
SLOT_WIDTH = 0.58

# Le garde-main : flancs a 2,0 cm de l'axe, rails lateraux en saillie jusqu'a 2,5.
HG_HALF = 2.0
HG_TOP = 19.55
HG_BOTTOM = Z(283)      # le dessous du corps, au pied du rail bas (13,2)
SIDE_RAIL_Z = (Z(242), Z(197))

# La main gauche du pack tient un garde-main moins haut : elle descend d'autant.
GRIP_DROP = 0.65
# La crosse, sortie de quelques crans sur son tube.
STOCK_SLIDE = 9.0


# --- les contours releves ------------------------------------------------------------

def outline(name, dx=0.0):
    return [(x + dx, z) for x, z in OUTLINES[name]['outline']]


def outline_holes(name, dx=0.0):
    return [[(x + dx, z) for x, z in hole] for hole in OUTLINES[name]['holes']]


def span(poly, z):
    """L'etendue en x d'un contour a la hauteur z."""
    xs = []
    n = len(poly)
    for i in range(n):
        (x1, z1), (x2, z2) = poly[i], poly[(i + 1) % n]
        if (z1 <= z < z2) or (z2 <= z < z1):
            xs.append(x1 + (z - z1) * (x2 - x1) / (z2 - z1))
    return (min(xs), max(xs)) if len(xs) >= 2 else None


def clip_x(poly, limit, keep_below=True):
    """Coupe un contour par la droite x = limit (Sutherland-Hodgman)."""
    inside = (lambda p: p[0] <= limit) if keep_below else (lambda p: p[0] >= limit)
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if inside(b):
            if not inside(a):
                t = (limit - a[0]) / (b[0] - a[0])
                out.append((limit, a[1] + t * (b[1] - a[1])))
            out.append(b)
        elif inside(a):
            t = (limit - a[0]) / (b[0] - a[0])
            out.append((limit, a[1] + t * (b[1] - a[1])))
    return out


def clip_line(poly, a, b):
    """Ne garde d'un contour que ce qui est a gauche de la droite a -> b (Sutherland-Hodgman)."""
    (ax, az), (bx, bz) = a, b
    side = lambda p: (bx - ax) * (p[1] - az) - (bz - az) * (p[0] - ax)
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        sp, sq = side(p), side(q)
        if sq >= 0:
            if sp < 0:
                t = sp / (sp - sq)
                out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
            out.append(q)
        elif sp >= 0:
            t = sp / (sp - sq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def clip_z(poly, limit, keep_below=True):
    """Coupe un contour par la droite z = limit."""
    swapped = [(z, x) for x, z in poly]
    return [(x, z) for z, x in clip_x(swapped, limit, keep_below)]


def loft_outline(name, poly, tilt_deg, steps, half_width, exponent=2.6, segments=40):
    """Tend une piece de forme libre sur son contour de profil : des sections ovales,
    perpendiculaires a son axe (incline de tilt_deg sur la verticale, le bas vers
    l'arriere si positif), dont la profondeur suit le contour. half_width(t) donne la
    demi-largeur, t allant de 0 (en bas) a 1 (en haut)."""
    a = math.radians(tilt_deg)
    ca, sa = math.cos(a), math.sin(a)
    cx = sum(p[0] for p in poly) / len(poly)
    cz = sum(p[1] for p in poly) / len(poly)
    upright = [((x - cx) * ca - (z - cz) * sa, (x - cx) * sa + (z - cz) * ca) for x, z in poly]
    zs = [p[1] for p in upright]
    z0, z1 = min(zs), max(zs)
    rings = []
    for k in range(steps + 1):
        t = k / steps
        z = z0 + (z1 - z0) * (0.004 + 0.992 * t)
        s = span(upright, z)
        if s is None:
            continue
        mid, depth = (s[0] + s[1]) / 2, (s[1] - s[0]) / 2
        ring = kit.superellipse(mid, 0.0, depth, half_width(t), exponent=exponent, segments=segments, start=math.pi)
        rings.append([(u * ca + z * sa + cx, v, -u * sa + z * ca + cz) for u, v in ring])
    return kit.loft(name, rings)


def mirrored(profile):
    """Un profil (y, z) dessine du cote droit (y < 0), complete de son miroir."""
    return profile + [(-y, z) for y, z in reversed(profile)]


# --- les rails -------------------------------------------------------------------

def picatinny(height, half=1.18):
    """Coupe d'un rail Picatinny en (u, v) : u en travers, v depuis sa base (0) jusqu'a
    son sommet (height). Tete de 2,4 cm, queues d'aronde a 45 degres, sommet chanfreine."""
    h = height
    stem = max(h - 0.62, 0.0)
    return [(-0.94, 0.0), (0.94, 0.0), (0.94, stem), (half, stem + 0.24), (half, h - 0.12), (half - 0.12, h),
            (-(half - 0.12), h), (-half, h - 0.12), (-half, stem + 0.24), (-0.94, stem)]


def slot_positions(x0, x1, m0=0.3, m1=0.3):
    """Les centres des fentes de rail entre x0 et x1, au pas et a la phase de la photo.
    Une marge negative laisse une fente deborder du bout (a la jonction de deux rails)."""
    first = math.ceil((x0 + m0 + SLOT_WIDTH / 2 - SLOT_PHASE) / PITCH)
    last = math.floor((x1 - m1 - SLOT_WIDTH / 2 - SLOT_PHASE) / PITCH)
    return [SLOT_PHASE + k * PITCH for k in range(first, last + 1)]


def rail(name, x0, x1, place, height=0.95, depth=0.33, mat=None, margins=(0.3, 0.3), extra=()):
    """Un rail de x0 a x1. place((u, v)) -> (y, z) pose la coupe ; les fentes sont
    creusees depuis le sommet sur depth ; extra : d'autres outils a enlever."""
    profile = [place(p) for p in picatinny(height)]
    body = kit.prism(name, profile, 'x', x0, x1)
    cutters = list(extra)
    for xc in slot_positions(x0, x1, *margins):
        corners = [place(p) for p in ((-1.4, height - depth), (1.4, height - depth), (1.4, height + 0.2), (-1.4, height + 0.2))]
        cutters.append(kit.prism(name + '_fente', corners, 'x', xc - SLOT_WIDTH / 2, xc + SLOT_WIDTH / 2))
    if cutters:
        kit.boolean(body, kit.join(name + '_fentes', cutters))
    if mat is not None:
        kit.assign(body, mat)
    return kit.finish(body, bevel=0.03)


def top_rail(name, x0, x1, mat, margins=(0.3, 0.3)):
    return rail(name, x0, x1, lambda p: (p[0], RAIL_BASE + p[1]), mat=mat, margins=margins)


# --- le boitier superieur --------------------------------------------------------------

def upper(mat_alu, mat_steel):
    section = kit.fillet(mirrored([(-UPPER_HALF, SEAM_Z), (-UPPER_HALF, 18.85), (-1.2, RAIL_BASE + 0.08)]), 0.12, 3)
    body = kit.prism('boitier_sup', section, 'x', UPPER_X0, UPPER_X1)
    cutters = [
        # La fenetre d'ejection, que la porte ferme.
        kit.box('fenetre', (X(785), -2.3, Z(237)), (X(972), -0.6, Z(186))),
        # L'encoche du levier d'armement, a l'arriere du rail.
        kit.box('logement_levier', (UPPER_X0 - 0.2, -0.95, 18.35), (RAIL_X0 + 0.5, 0.95, RAIL_BASE + 0.2)),
    ]
    # Les cannelures du flanc droit, entre l'assistance et la fenetre, et leurs jumelles a gauche.
    for z in (Z(193), Z(222)):
        cutters.append(kit.prism('cannelure', kit.rounded_rect(X(590), z - 0.13, X(718), z + 0.13, 0.12, 3), 'y', UPPER_HALF - 0.09, UPPER_HALF + 0.5))
    kit.boolean(body, cutters)
    kit.assign(body, mat_alu)
    kit.finish(body, bevel=0.06)
    parts = [body]

    # Le deflecteur de douilles, en coin, derriere la fenetre.
    deflector = kit.prism('deflecteur', [(X(722), -UPPER_HALF + 0.05), (X(785) - 0.05, -UPPER_HALF + 0.05),
                                         (X(785) - 0.05, -2.45), (X(758), -2.45)], 'z', Z(218), Z(158))
    side = kit.prism('deflecteur_profil', kit.fillet([P(722, 166), P(758, 159), P(785, 172), P(785, 216), P(750, 216)], 0.15, 2), 'y', -3.0, 0.0)
    kit.boolean(deflector, side, operation='INTERSECT')
    kit.assign(deflector, mat_alu)
    parts.append(kit.finish(deflector, bevel=0.08))
    # Le fourreau de l'assistance de fermeture, en biais vers l'arriere droit.
    housing = kit.cylinder('fourreau_assistance', FA_START, FA_START + FA_AXIS * FA_LENGTH, 0.8, 32)
    kit.assign(housing, mat_alu)
    parts.append(kit.finish(housing, bevel=0.06))
    # Le renflement du flanc droit, autour de la culasse, et ses deux cannelures.
    zc, h = (Z(172) + Z(248)) / 2, (Z(172) - Z(248)) / 2
    d_shape = [(-UPPER_HALF + 0.05 - 0.36 * math.cos(math.radians(a)), zc + h * math.sin(math.radians(a))) for a in range(-90, 91, 10)]
    bulge = kit.prism('renflement', d_shape + [(-UPPER_HALF + 0.3, zc + h), (-UPPER_HALF + 0.3, zc - h)][::-1], 'x', X(578), X(738))
    grooves = [kit.box('cannelure_renflement', (X(588), -2.4, z - 0.12), (X(730), -1.75, z + 0.12)) for z in (Z(195), Z(222))]
    kit.boolean(bulge, grooves)
    kit.assign(bulge, mat_alu)
    parts.append(kit.finish(bulge, bevel=0.08))
    # Le bossage de la charniere et la butee avant de la porte.
    for x0, x1 in ((X(768), X(785)), (X(972), X(988))):
        lug = kit.cylinder('charniere_palier', (x0, -UPPER_HALF, 15.45), (x1, -UPPER_HALF, 15.45), 0.26, 20)
        kit.assign(lug, mat_alu)
        parts.append(kit.finish(lug, bevel=0.03))
    parts.append(top_rail('rail_boitier', RAIL_X0, UPPER_X1, mat_alu, margins=(0.3, -0.3)))
    # L'ecrou du canon, vu par les jours du garde-main.
    nut = kit.fluted_cylinder('ecrou_canon', (UPPER_X1 - 0.05, 0, BORE_Z), (UPPER_X1 + 1.6, 0, BORE_Z), 1.55, 1.42, 24)
    kit.assign(nut, mat_steel)
    parts.append(kit.finish(nut, bevel=0.03, angle=60))
    return kit.join('boitier_sup', parts)


FA_AXIS = Vector((-0.64, -0.77, 0.0)).normalized()
FA_START = Vector((4.2, -1.1, Z(216)))
FA_LENGTH = 2.4


# --- le boitier inferieur --------------------------------------------------------------

def lower(mat_alu, mat_steel):
    body = kit.prism('boitier_inf', outline('lower'), 'y', -LOWER_HALF, LOWER_HALF)
    well = kit.prism('puits', kit.rounded_rect(14.45, 5.0, 21.95, 15.3, 0.25, 3), 'y', -WELL_HALF, WELL_HALF)
    # Le pontet est plus mince que le boitier : on le degage de chaque cote.
    guard_sides = [kit.box('pontet_flanc', (X(686), side * 0.7, Z(445)), (12.6, side * 3.0, Z(338) - 0.05)) for side in (1.0, -1.0)]
    # Les panneaux du puits, en leger retrait (la ou le fabricant grave ses marquages : nus ici).
    panels = [kit.prism('panneau', kit.rounded_rect(X(852), Z(373), X(978), Z(307), 0.3, 3), 'y', *sorted((side * (LOWER_HALF - 0.05), side * 2.5)))
              for side in (1.0, -1.0)]
    openings = [kit.prism('pontet_jour', hole, 'y', -3.0, 3.0) for hole in outline_holes('lower')]
    kit.boolean(body, [well] + guard_sides + panels + openings)
    kit.assign(body, mat_alu)
    kit.finish(body, bevel=0.06)
    parts = [body]

    # La tour du tube de crosse, a l'arriere, sous le levier d'armement.
    tower = kit.prism('tour', kit.fillet([(X(522), 12.9), (UPPER_X0 + 0.02, 12.9), (UPPER_X0 + 0.02, 18.45), (X(522), 18.45)], 0.35, 3),
                      'y', -LOWER_HALF, LOWER_HALF)
    kit.assign(tower, mat_alu)
    parts.append(kit.finish(tower, bevel=0.06))

    # L'evasement du puits, plus large que le boitier.
    flare = kit.prism('evasement', kit.fillet([(X(800), Z(380)), (X(975), Z(380)), (X(978), Z(413)), (X(800), Z(413))], 0.15, 2),
                      'y', -1.85, 1.85)
    hole = kit.prism('evasement_creux', kit.rounded_rect(14.45, 5.0, 21.95, 10.0, 0.25, 3), 'y', -WELL_HALF - 0.02, WELL_HALF + 0.02)
    kit.boolean(flare, hole)
    kit.assign(flare, mat_alu)
    parts.append(kit.finish(flare, bevel=0.16, segments=4))

    # Les goupilles : demontage, pivot, detente, chien.
    for (x, z), r in ((P(600, 270), 0.42), (P(992, 270), 0.42), ((9.94, 11.88), 0.2), ((8.75, 12.85), 0.2)):
        pin = kit.lathe('goupille', (x, -LOWER_HALF - 0.08, z), (x, LOWER_HALF + 0.08, z),
                        [(0.0, r * 0.85), (0.08, r), (2 * LOWER_HALF + 0.08, r), (2 * LOWER_HALF + 0.16, r * 0.85)], 24)
        kit.assign(pin, mat_steel)
        parts.append(kit.smooth(pin))

    # Le selecteur ambidextre : a droite le levier court, pointe en bas ; a gauche le grand.
    hub = P(652, 290)
    for side in (-1.0, 1.0):
        y0, y1 = sorted((side * LOWER_HALF, side * (LOWER_HALF + 0.22)))
        disc = kit.lathe('selecteur', (hub[0], side * LOWER_HALF, hub[1]), (hub[0], side * (LOWER_HALF + 0.22), hub[1]),
                         [(0.0, 0.58), (0.22, 0.52)], 32)
        kit.assign(disc, mat_steel)
        parts.append(kit.finish(disc, bevel=0.03))
    right_lever = kit.prism('levier_selecteur_d', kit.fillet([(hub[0] - 0.4, hub[1] + 0.2), (hub[0] + 0.45, hub[1] + 0.2), (X(665), Z(330)),
                                                             (X(660), Z(343)), (X(645), Z(343)), (X(640), Z(330))], 0.15, 3),
                            'y', -LOWER_HALF - 0.42, -LOWER_HALF - 0.14)
    left_lever = kit.prism('levier_selecteur_g', kit.fillet([(hub[0] - 0.35, hub[1] - 0.3), (hub[0] + 2.55, hub[1] - 0.2), (hub[0] + 2.75, hub[1] + 0.1),
                                                            (hub[0] + 2.55, hub[1] + 0.38), (hub[0] - 0.35, hub[1] + 0.32)], 0.14, 3),
                           'y', LOWER_HALF + 0.14, LOWER_HALF + 0.44)
    # L'arret de culasse : palette a droite (ambidextre), levier classique a gauche.
    paddle = kit.prism('palette_culasse', kit.fillet([P(750, 283), P(790, 278), P(823, 262), P(823, 256), P(790, 262), P(750, 272)], 0.1, 2),
                       'y', -LOWER_HALF - 0.36, -LOWER_HALF - 0.06)
    boss = kit.prism('bossage_arret', kit.fillet([(12.9, 12.5), (15.4, 12.8), (15.55, 14.55), (13.2, 14.7)], 0.5, 4),
                     'y', LOWER_HALF - 0.05, LOWER_HALF + 0.14)
    catch = kit.prism('arret_culasse', kit.fillet([(13.2, 12.8), (15.0, 13.0), (15.15, 14.2), (13.7, 14.5), (13.2, 14.0)], 0.15, 3),
                      'y', LOWER_HALF + 0.1, LOWER_HALF + 0.4)
    # L'arretoir de chargeur, ovale, dans sa garde.
    release = kit.prism('arretoir', kit.superellipse(X(803), Z(306.5), 0.46, 0.62, exponent=2.3, segments=32), 'y', -LOWER_HALF - 0.28, -LOWER_HALF + 0.05)
    fence_outer = kit.prism('garde_arretoir', kit.rounded_rect(X(780), Z(340), X(835), Z(285), 0.35, 3), 'y', -LOWER_HALF - 0.32, -LOWER_HALF + 0.05)
    fence_inner = kit.prism('garde_arretoir_creux', kit.rounded_rect(X(787), Z(333), X(826), Z(290), 0.3, 3), 'y', -LOWER_HALF - 0.5, -LOWER_HALF - 0.1)
    kit.boolean(fence_outer, fence_inner)
    for piece, mat in ((right_lever, mat_steel), (left_lever, mat_steel), (paddle, mat_steel), (boss, mat_alu), (catch, mat_steel),
                       (release, mat_steel), (fence_outer, mat_alu)):
        kit.assign(piece, mat)
        parts.append(kit.finish(piece, bevel=0.04))
    ribs = [kit.box('strie', (13.55 + 0.38 * k, LOWER_HALF + 0.38, 13.1), (13.72 + 0.38 * k, LOWER_HALF + 0.47, 14.2)) for k in range(3)]
    stripes = kit.join('stries', ribs)
    kit.assign(stripes, mat_steel)
    parts.append(kit.finish(stripes, bevel=0.02))
    return kit.join('boitier_inf', parts)


def grip(mat, mat_poly):
    """La poignee, tendue sur son contour : sections ovales le long de son axe incline,
    son talon ferme par un bouchon."""
    body = loft_outline('poignee', outline('grip'), 20.0, 44, lambda t: 1.3 + 0.18 * min(1.0, t * 3.0), exponent=2.4)
    kit.assign(body, mat)
    kit.smooth(body, 50)
    xs = span(outline('grip'), Z(588))
    cap = kit.prism('bouchon', kit.fillet([(xs[0] + 0.3, Z(593) - 0.02), (xs[1] - 0.3, Z(593) - 0.02), (xs[1] - 0.25, Z(586)), (xs[0] + 0.25, Z(586))], 0.1, 2),
                    'y', -1.1, 1.1)
    notch = kit.box('bouchon_encoche', (X(518), -0.3, Z(593) - 0.1), (X(558), 0.3, Z(589)))
    kit.boolean(cap, notch)
    kit.assign(cap, mat_poly)
    return kit.join('poignee', [body, kit.finish(cap, bevel=0.05)])


def trigger(mat):
    """La detente : son profil releve, prolonge jusqu'a son pivot (cache dans le boitier)."""
    blade = kit.prism('detente', outline('trigger'), 'y', -0.28, 0.28)
    stem = kit.box('detente_axe', (9.55, -0.28, 10.4), (10.3, 0.28, 12.2))
    kit.assign(blade, mat)
    kit.assign(stem, mat)
    return kit.join('detente', [kit.finish(blade, bevel=0.05), kit.finish(stem, bevel=0.03)])


# --- le tube et la crosse ---------------------------------------------------------------

def buffer_and_stock(mat_gray, mat_poly, mat_rubber, mat_steel):
    """Le tube de crosse, et la crosse sortie de STOCK_SLIDE sur lui (elle est rentree sur
    la photo) : rentree, elle viendrait sous l'oeil des que le fusil bascule."""
    parts = []
    tube = kit.cylinder('tube_amortisseur', (-19.5 - STOCK_SLIDE, 0, TUBE_Z), (X(522), 0, TUBE_Z), 1.9, 48)
    kit.assign(tube, mat_gray)
    parts.append(kit.finish(tube, bevel=0.05))
    # L'ecrou et la plaque d'appui, contre la tour.
    nut = kit.fluted_cylinder('ecrou_crenele', (X(505), 0, TUBE_Z), (X(522), 0, TUBE_Z), 2.1, 1.96, 30)
    kit.assign(nut, mat_steel)
    parts.append(kit.finish(nut, bevel=0.03, angle=60))
    fixed = len(parts)

    # La plaque de couche est une bande en biais le long de l'arriere : le voile s'arrete
    # a son bord avant.
    pad_front = (P(74, 165), P(100, 470))
    web = clip_line(outline('stock'), *pad_front)
    slot = kit.rounded_rect(X(139), Z(294), X(227), Z(284), 0.2, 3)
    body = kit.prism('crosse_voile', web, 'y', -1.7, 1.7)
    cutters = [kit.prism('fente', slot, 'y', -3, 3)]
    # La bande en biais, en leger creux, et ses stries serrees.
    band = [P(265, 236), P(348, 236), P(234, 462), P(150, 462)]
    for side in (-1.0, 1.0):
        cutters.append(kit.prism('bande', band, 'y', *sorted((side * 1.62, side * 3.0))))
    (ax, az), (bx, bz) = P(306, 236), P(192, 462)
    length = math.hypot(bx - ax, bz - az)
    angle = math.degrees(math.atan2(ax - bx, az - bz))
    across = (math.cos(math.radians(angle)), -math.sin(math.radians(angle)))
    mx, mz = (ax + bx) / 2, (az + bz) / 2
    for k in range(21):
        g = kit.box('strie_crosse', (-0.03, -3.0, -length / 2), (0.03, 3.0, length / 2))
        kit.rotate(g, angle, 'Y')
        off = (k - 10) * 0.15
        kit.translate(g, (mx + across[0] * off, 0.0, mz + across[1] * off))
        cutters.append(g)
    kit.boolean(body, cutters)
    # Les stries ne mordent que la surface : on rebouche le coeur du voile.
    core = kit.prism('crosse_coeur', web, 'y', -1.57, 1.57)
    kit.boolean(core, kit.prism('fente', slot, 'y', -3, 3))
    for piece in (body, core):
        kit.assign(piece, mat_poly)
    parts.append(kit.finish(body, bevel=0.1, segments=3, angle=30))
    parts.append(kit.smooth(core))

    # Le corps haut, autour du tube : plus large, arrondi.
    top = kit.prism('crosse_corps', clip_z(web, Z(256), keep_below=False), 'y', -2.2, 2.2)
    channel = kit.cylinder('canal', (-26.0, 0, TUBE_Z), (0.0, 0, TUBE_Z), 1.94, 48)
    pockets = [kit.prism('logement', kit.rounded_rect(X(x0), Z(252), X(x1), Z(240), 0.15, 3), 'y', *sorted((side * 1.95, side * 3.0)))
               for x0, x1 in ((110, 150), (242, 285)) for side in (-1.0, 1.0)]
    kit.boolean(top, [channel] + pockets)
    kit.assign(top, mat_poly)
    parts.append(kit.finish(top, bevel=0.55, segments=5, angle=30))

    # La plaque de couche en caoutchouc, et sa colonne d'alveoles le long du bord arriere.
    pad = kit.prism('plaque_couche', kit.fillet([P(43, 172), P(76, 170), P(101, 465), P(67, 466)], 0, 3, [0.4, 0.1, 0.1, 0.35]), 'y', -2.3, 2.3)
    (ax, az), (bx, bz) = P(50, 184), P(73, 452)
    count = 19
    cells = [kit.cylinder('alveole', (ax + (bx - ax) * k / (count - 1), -3.0, az + (bz - az) * k / (count - 1)),
                          (ax + (bx - ax) * k / (count - 1), 3.0, az + (bz - az) * k / (count - 1)), 0.2, 16) for k in range(count)]
    kit.boolean(pad, cells)
    kit.assign(pad, mat_rubber)
    parts.append(kit.finish(pad, bevel=0.25, segments=4, angle=30))

    # La douille de bretelle.
    socket = kit.lathe('douille_bretelle', (X(390), -1.7, Z(290)), (X(390), -2.0, Z(290)), [(0.0, 0.52), (0.3, 0.45)], 24)
    kit.assign(socket, mat_steel)
    parts.append(kit.finish(socket, bevel=0.05))
    for piece in parts[fixed:]:
        kit.translate(piece, (-STOCK_SLIDE, 0.0, 0.0))
    return kit.join('crosse', parts)


# --- le garde-main, le canon, le cache-flamme -----------------------------------------------

def handguard(mat_alu, mat_steel):
    """Le garde-main a quatre rails, aux proportions de la photo. Deux rangees de jours
    par flanc, au-dessus et au-dessous du rail lateral ; l'anneau de bretelle a l'avant
    droit ; la vis de serrage a l'arriere ; le dessus de l'avant chanfreine."""
    c = 0.45
    # Dans le sens trigonometrique (y vers la droite de l'image, z vers le haut).
    section = mirrored([(-HG_HALF + c, HG_TOP), (-HG_HALF, HG_TOP - c), (-HG_HALF, HG_BOTTOM + c), (-HG_HALF + c, HG_BOTTOM)])
    x0, x1 = UPPER_X1, HG_X1

    def front_chamfer():
        # La droite du sommet du rail, au droit du guidon, au haut de la face avant.
        (xa, za), (xb, zb) = (X(1555), RAIL_TOP), (HG_X1, Z(160))
        slope = (zb - za) / (xb - xa)
        top, right = RAIL_TOP + 0.3, HG_X1 + 0.3
        return kit.prism('chanfrein_avant', [(xa + (top - za) / slope, top), (right, top), (right, zb + (right - xb) * slope)], 'y', -3.0, 3.0)

    body = kit.prism('garde_main', section, 'x', x0, x1)
    inner = kit.prism('garde_main_creux', kit.offset_convex(section, 0.3), 'x', x0 - 0.2, x1 + 0.2)
    cutters = [inner, front_chamfer()]
    upper_row = [(1135, 1175), (1215, 1295), (1335, 1415), (1455, 1540)]
    lower_row = [(1135, 1175), (1215, 1295), (1335, 1415), (1435, 1470)]
    for row, zc in ((upper_row, Z(188)), (lower_row, Z(248))):
        for a, b in row:
            cutters.append(kit.prism('jour', kit.rounded_rect(X(a), zc - 0.3, X(b), zc + 0.3, 0.29, 4), 'y', -3.0, 3.0))
    # L'anneau de bretelle : une lumiere en U et son trou.
    cutters.append(kit.prism('bretelle', kit.fillet([P(1484, 258), P(1533, 258), P(1533, 273), P(1484, 273)], 0.3, 3), 'y', -3.0, -1.2))
    cutters.append(kit.cylinder('bretelle_trou', (X(1508.5), -3.0, Z(252)), (X(1508.5), -1.2, Z(252)), 0.36, 20))
    kit.boolean(body, cutters)
    kit.assign(body, mat_alu)
    parts = [kit.finish(body, bevel=0.05)]

    parts.append(rail('rail_haut', x0, x1, lambda p: (p[0], RAIL_BASE + p[1]), mat=mat_alu, margins=(-0.3, 0.3), extra=[front_chamfer()]))
    parts.append(rail('rail_bas', x0, x1, lambda p: (p[0], HG_BOTTOM + 0.12 - p[1]), height=0.62, mat=mat_alu))
    zc = (SIDE_RAIL_Z[0] + SIDE_RAIL_Z[1]) / 2
    for side in (-1.0, 1.0):
        parts.append(rail('rail_flanc', x0, x1, lambda p, s=side: (s * (HG_HALF - 0.1 + p[1]), zc + p[0]), height=0.6, mat=mat_alu))

    # La vis de serrage, sur son bossage, de chaque cote.
    for side in (-1.0, 1.0):
        boss = kit.prism('bossage_vis', kit.rounded_rect(X(1060), Z(282), X(1100), Z(255), 0.15, 3), 'y', *sorted((side * (HG_HALF - 0.1), side * (HG_HALF + 0.22))))
        cx, cz = P(1080, 268.5)
        screw = kit.cylinder('vis', (cx, side * (HG_HALF + 0.2), cz), (cx, side * (HG_HALF + 0.42), cz), 0.42, 24)
        slot = kit.box('fente_vis', (cx - 0.05, side * (HG_HALF + 0.3) - 0.2, cz - 0.5), (cx + 0.05, side * (HG_HALF + 0.3) + 0.2, cz + 0.5))
        kit.rotate(slot, 35.0, 'Y', (cx, 0.0, cz))
        kit.boolean(screw, slot)
        kit.assign(boss, mat_alu)
        kit.assign(screw, mat_steel)
        parts += [kit.finish(boss, bevel=0.04), kit.finish(screw, bevel=0.03)]
    return kit.join('garde_main', parts)


def barrel(mat_steel):
    """Le canon, le bloc d'emprunt et le tube du piston, l'ecrou et le cache-flamme."""
    parts = []
    tube = kit.cylinder('canon', (20.0, 0, BORE_Z), (X(1672), 0, BORE_Z), 1.09, 40)
    kit.assign(tube, mat_steel)
    parts.append(kit.finish(tube, bevel=0.04))
    block = kit.prism('bloc_emprunt', kit.fillet(mirrored([(-1.15, 14.95), (-1.15, 18.5)]), 0.35, 3), 'x', HG_X1 - 1.2, X(1628))
    piston = kit.lathe('tube_piston', (HG_X1 - 1.0, 0, Z(162.5)), (X(1636), 0, Z(162.5)),
                       [(0.0, 0.44), (X(1636) - HG_X1 + 0.6, 0.44), (X(1636) - HG_X1 + 1.0, 0.36)], 32)
    vent = kit.cylinder('event', (X(1620), -1, Z(162.5)), (X(1620), 1, Z(162.5)), 0.09, 12)
    kit.boolean(piston, vent)
    for piece in (block, piston):
        kit.assign(piece, mat_steel)
        parts.append(kit.finish(piece, bevel=0.05))
    nut = kit.cylinder('ecrou_cache_flamme', (X(1645), 0, BORE_Z), (X(1668), 0, BORE_Z), 1.36, 6)
    kit.rotate(nut, 30.0, 'X', (0, 0, BORE_Z))
    kit.assign(nut, mat_steel)
    parts.append(kit.finish(nut, bevel=0.08))

    # Le cache-flamme : deux gorges a l'arriere, six fentes, la bouche ouverte.
    x0, x1 = X(1668), MUZZLE_X
    r = (Z(192) - Z(245)) / 2
    hider = kit.lathe('cache_flamme', (x0, 0, BORE_Z), (x1, 0, BORE_Z),
                      [(0.0, r - 0.05), (0.35, r - 0.05), (0.4, r - 0.2), (0.55, r - 0.2), (0.6, r), (0.85, r), (0.9, r - 0.2),
                       (1.05, r - 0.2), (1.1, r), (x1 - x0 - 0.12, r), (x1 - x0, r - 0.1)], 48)
    bore = kit.cylinder('ame', (x0 + 1.2, 0, BORE_Z), (x1 + 0.3, 0, BORE_Z), r - 0.28, 32)
    slots = []
    for k in range(6):
        s = kit.box('fente_cf', (X(1700), -0.18, 0.3), (x1 - 0.35, 0.18, r + 0.3))
        kit.rotate(s, 60 * k, 'X')
        kit.translate(s, (0, 0, BORE_Z))
        slots.append(s)
    kit.boolean(hider, [bore] + slots)
    kit.assign(hider, mat_steel)
    parts.append(kit.finish(hider, bevel=0.04))
    return kit.join('canon', parts)


# --- le chargeur ------------------------------------------------------------------------

def rib_along(name, poly, u, z0, z1, y, width=0.32, height=0.06, steps=28):
    """Une nervure qui suit la courbe du chargeur : a la fraction u de sa profondeur,
    de z0 a z1, en saillie de height sur le flanc y."""
    rings = []
    sign = 1.0 if y > 0 else -1.0
    for k in range(steps + 1):
        z = z0 + (z1 - z0) * k / steps
        s = span(poly, z)
        if s is None:
            continue
        xc = s[0] + u * (s[1] - s[0])
        ring = [(xc - width / 2, y - sign * 0.05, z), (xc + width / 2, y - sign * 0.05, z),
                (xc + width / 2 - 0.06, y + sign * height, z), (xc - width / 2 + 0.06, y + sign * height, z)]
        rings.append(ring)
    return kit.loft(name, rings)


def magazine(mat_steel, mat_brass, mat_copper):
    """Le chargeur acier de trente coups, sur le contour de la reference : ses trois
    nervures par flanc suivent sa courbe, sa semelle deborde, son col entre dans le
    puits, sa cartouche du dessus se voit quand il sort."""
    poly = outline('magazine')
    half = 1.22
    body = loft_outline('chargeur', poly, -10.0, 48, lambda t: half, exponent=5.0, segments=56)
    kit.assign(body, mat_steel)
    kit.smooth(body, 35)
    parts = [body]
    top = span(poly, Z(416))
    neck = kit.prism('col', kit.fillet([(top[0] + 0.05, Z(418)), (top[1] - 0.05, Z(418)), (top[1] - 0.25, 14.25), (top[0] + 0.2, 14.25)], 0.3, 3),
                     'y', -half + 0.03, half - 0.03)
    kit.assign(neck, mat_steel)
    parts.append(kit.finish(neck, bevel=0.1, segments=3))
    zs = [z for _, z in poly]
    zlow = min(zs)
    for u in (0.24, 0.5, 0.76):
        for side in (1.0, -1.0):
            rib = rib_along('nervure', poly, u, zlow + 1.6, Z(420), side * half)
            kit.assign(rib, mat_steel)
            parts.append(kit.smooth(rib, 40))
    # La semelle, le long du fond en biais, un peu plus large que le corps.
    sole = kit.prism('semelle', kit.fillet([P(880, 699), P(1029, 634), P(1024, 622), P(875, 687)], 0.12, 2), 'y', -half - 0.1, half + 0.1)
    kit.assign(sole, mat_steel)
    parts.append(kit.finish(sole, bevel=0.1, segments=3))
    # Les levres et la cartouche du dessus.
    lips = kit.prism('levres', kit.fillet([(top[0] + 0.3, 14.1), (top[1] - 0.4, 14.1), (top[1] - 0.8, 14.8), (top[0] + 0.9, 15.0), (top[0] + 0.3, 14.8)], 0.1, 2),
                     'y', -0.98, 0.98)
    well = kit.prism('levres_creux', kit.rounded_rect(top[0] + 0.55, 14.55, top[1] - 0.55, 15.5, 0.1, 2), 'y', -0.58, 0.58)
    kit.boolean(lips, well)
    kit.assign(lips, mat_steel)
    parts.append(kit.finish(lips, bevel=0.04))
    x0 = top[0] + 0.7
    case = kit.lathe('douille', (x0, 0, 14.6), (x0 + 4.5, 0, 14.6),
                     [(0.0, 0.47), (0.12, 0.47), (0.16, 0.40), (0.3, 0.47), (3.55, 0.45), (3.95, 0.31), (4.5, 0.31)], 32)
    bullet = kit.lathe('balle', (x0 + 4.5, 0, 14.6), (x0 + 6.75, 0, 14.6),
                       [(0.0, 0.285), (0.9, 0.285), (1.6, 0.22), (2.0, 0.11), (2.25, 0.02)], 32)
    kit.assign(case, mat_brass)
    kit.assign(bullet, mat_copper)
    parts += [kit.smooth(case), kit.smooth(bullet)]
    return kit.join('chargeur', parts)


# --- les pieces mobiles de la culasse ----------------------------------------------------------

def charging_handle(mat_alu):
    x0, x1 = X(548), X(577)
    shaft = kit.box('tige', (x1 - 0.1, -0.55, 18.5), (14.0, 0.55, 19.1))
    handle = kit.prism('poignee_levier', kit.fillet([(x0, -1.95), (x1, -1.3), (x1, 1.3), (x0, 1.95)], 0.25, 3), 'z', 18.45, 19.38)
    parts = []
    for side in (-1.0, 1.0):
        latch = kit.prism('loquet', kit.fillet([(x0 + 0.05, side * 1.35), (x1 - 0.1, side * 1.25), (x1 - 0.2, side * 2.1), (x0 + 0.12, side * 2.2)], 0.2, 3),
                          'z', 18.5, 19.3)
        kit.assign(latch, mat_alu)
        parts.append(kit.finish(latch, bevel=0.05))
    for piece in (shaft, handle):
        kit.assign(piece, mat_alu)
        parts.append(kit.finish(piece, bevel=0.05))
    return kit.join('levier_armement', parts)


def bolt_carrier(mat_steel):
    carrier = kit.cylinder('porte_culasse', (12.3, 0, BORE_Z), (21.4, 0, BORE_Z), 1.18, 48)
    bolt = kit.cylinder('tete_culasse', (21.4, 0, BORE_Z), (22.5, 0, BORE_Z), 0.9, 36)
    groove = kit.box('rainure', (13.6, -1.45, BORE_Z - 0.18), (20.8, -0.95, BORE_Z + 0.18))
    kit.boolean(carrier, groove)
    parts = []
    for piece in (carrier, bolt):
        kit.assign(piece, mat_steel)
        parts.append(kit.finish(piece, bevel=0.04))
    return kit.join('culasse', parts)


def dust_cover(mat_alu, mat_steel):
    """La porte de la fenetre d'ejection : deux panneaux en creux, le verrou au milieu,
    la charniere en bas et son ressort."""
    x0, x1, z0, z1 = X(783), X(975), Z(237.5), Z(186)
    door = kit.prism('porte', kit.fillet([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], 0.22, 3), 'y', -1.83, -1.66)
    recesses = [kit.prism('porte_creux', kit.rounded_rect(a, Z(230), b, Z(193), 0.18, 3), 'y', -2.0, -1.79)
                for a, b in ((X(790), X(855)), (X(902), X(968)))]
    window = kit.box('porte_fenetre', (X(875), -2.0, Z(212)), (X(886), -1.6, Z(200)))
    kit.boolean(door, recesses + [window])
    latch = kit.prism('porte_verrou', kit.rounded_rect(X(862), Z(222), X(898), Z(196), 0.12, 2), 'y', -1.9, -1.8)
    kit.boolean(latch, kit.box('porte_verrou_creux', (X(875), -2.0, Z(212)), (X(886), -1.7, Z(200))))
    rod = kit.cylinder('charniere', (X(768), -UPPER_HALF, 15.45), (X(988), -UPPER_HALF, 15.45), 0.14, 16)
    coils = [(0.08 * k, 0.21 if k % 2 else 0.17) for k in range(int((X(900) - X(857)) / 0.08))]
    spring = kit.lathe('ressort', (X(857), -UPPER_HALF, 15.45), (X(900), -UPPER_HALF, 15.45), coils, 16)
    parts = []
    for piece, mat in ((door, mat_alu), (latch, mat_alu), (rod, mat_steel), (spring, mat_steel)):
        kit.assign(piece, mat)
        parts.append(kit.finish(piece, bevel=0.03) if piece is not spring else kit.smooth(piece))
    return kit.join('porte_ejection', parts)


def forward_assist(mat_alu):
    start = FA_START + FA_AXIS * FA_LENGTH
    button = kit.lathe('assistance', start, start + FA_AXIS * 1.1,
                       [(0.0, 0.62), (0.55, 0.62), (0.6, 0.84), (1.0, 0.84), (1.1, 0.7)], 36)
    kit.assign(button, mat_alu)
    return kit.finish(button, bevel=0.04)


# --- le dioptre et le guidon, dresses --------------------------------------------------------

def rear_sight(mat_alu, mat_steel):
    """Le dioptre rabattable, dresse : une embase sur le rail, un pied, un tambour a
    oeilletons (celui du milieu a hauteur de l'oeil epaule) et deux oreilles."""
    parts = []
    xa, xb = 3.45, 7.9
    base = kit.prism('dioptre_embase', kit.fillet([(xa, RAIL_TOP - 0.05), (xb, RAIL_TOP - 0.05), (xb, 21.05), (xb - 0.4, 21.35), (xa + 0.4, 21.35), (xa, 21.05)],
                                                  0.12, 2), 'y', -1.25, 1.25)
    jaw = kit.box('dioptre_machoire', (xa + 0.35, -1.45, 19.4), (xb - 0.35, -1.22, 20.6))
    screw = kit.lathe('dioptre_vis', (5.7, -1.42, 20.0), (5.7, -1.9, 20.0), [(0.0, 0.42), (0.48, 0.4)], 20)
    xc = 5.35
    foot = kit.prism('dioptre_pied', kit.fillet([(xc - 0.75, 21.2), (xc + 0.75, 21.2), (xc + 0.5, EYE_Z - 0.6), (xc - 0.5, EYE_Z - 0.6)], 0.15, 2),
                     'y', -0.55, 0.55)
    drum = kit.cylinder('dioptre_tambour', (xc, 0, EYE_Z - 0.62), (xc, 0, EYE_Z + 0.62), 0.9, 40)
    # L'oeilleton de combat, large : a quinze centimetres de l'oeil, on y voit le guidon
    # et sa cible. Le tambour en porte un plus fin en travers.
    holes = [kit.cylinder('oeilleton', (xc - 1.5, 0, EYE_Z), (xc + 1.5, 0, EYE_Z), 0.42, 32),
             kit.cylinder('oeilleton_2', (xc, -1.5, EYE_Z), (xc, 1.5, EYE_Z), 0.16, 20)]
    kit.boolean(drum, holes)
    ears = []
    for side in (-1.0, 1.0):
        ear = kit.prism('dioptre_oreille', kit.fillet([(xc - 1.05, 21.2), (xc + 1.05, 21.2), (xc + 0.8, EYE_Z + 1.0), (xc - 0.8, EYE_Z + 1.0)], 0, 4,
                                                      [0.1, 0.1, 0.45, 0.45]), 'y', *sorted((side * 1.02, side * 1.25)))
        ears.append(ear)
    bridge = kit.prism('dioptre_pont', kit.fillet([(xc - 0.8, 21.2), (xc + 0.8, 21.2), (xc + 0.8, 21.9), (xc - 0.8, 21.9)], 0.1, 2), 'y', -1.25, 1.25)
    for piece, mat in ((base, mat_alu), (jaw, mat_alu), (screw, mat_steel), (foot, mat_alu), (drum, mat_steel), (bridge, mat_alu)):
        kit.assign(piece, mat)
        parts.append(kit.finish(piece, bevel=0.04))
    for ear in ears:
        kit.assign(ear, mat_alu)
        parts.append(kit.finish(ear, bevel=0.05))
    return kit.join('dioptre', parts)


def front_sight(mat_alu, mat_steel):
    """Le guidon rabattable, dresse, sur son contour releve : l'embase serree sur le
    rail, la molette de reglage a droite, la lame et sa pointe a hauteur de l'oeil."""
    xa, xb = X(1480), X(1555)
    base = kit.prism('guidon_embase', kit.fillet([(xa, RAIL_TOP - 0.05), (xb, RAIL_TOP - 0.05), (xb, Z(110)), (xb - 0.25, Z(104)), (xa + 0.25, Z(104)), (xa, Z(110))],
                                                 0.12, 2), 'y', -1.25, 1.25)
    jaw = kit.box('guidon_machoire', (xa + 0.35, -1.45, 19.4), (xb - 0.35, -1.22, 20.6))
    cx, cz = P(1518, 119)
    knob = kit.fluted_cylinder('guidon_molette', (cx, -1.25, cz), (cx, -1.55, cz), 0.46, 0.42, 24)
    # La lame : large au pied, fine a la pointe, qui arrive a l'oeil.
    tip = X(1519)
    blade = kit.prism('guidon_lame', [(tip - 0.32, Z(104) - 0.1), (tip + 0.3, Z(104) - 0.1), (tip + 0.1, EYE_Z), (tip - 0.1, EYE_Z)], 'y', -0.2, 0.2)
    parts = []
    for piece, mat in ((base, mat_alu), (jaw, mat_alu), (knob, mat_steel), (blade, mat_steel)):
        kit.assign(piece, mat)
        parts.append(kit.finish(piece, bevel=0.03))
    return kit.join('guidon', parts)


# --- la lampe ---------------------------------------------------------------------------

LAMP_Y, LAMP_Z = -3.55, (SIDE_RAIL_Z[0] + SIDE_RAIL_Z[1]) / 2   # sur le rail droit, a trois heures
LAMP_X0, LAMP_X1 = 44.6, 53.6                                    # de l'interrupteur au verre, devant la main


def lamp(mat_alu, mat_rubber, mat_glass):
    """La lampe tactique sur le rail droit, en avant de la main. L'os "lamp" (ajoute par
    la conversion) prendra la place du verre : c'est de la que partira le faisceau."""
    y, z = LAMP_Y, LAMP_Z
    parts = []
    body = kit.lathe('lampe_corps', (LAMP_X0 + 0.9, y, z), (LAMP_X1 - 2.0, y, z), [(0.0, 0.92), (LAMP_X1 - LAMP_X0 - 2.9, 0.92)], 40)
    head = kit.lathe('lampe_tete', (LAMP_X1 - 2.0, y, z), (LAMP_X1, y, z), [(0.0, 0.92), (0.35, 1.18), (1.8, 1.2), (2.0, 1.08)], 48)
    notches = []
    for k in range(6):
        n = kit.box('creneau', (LAMP_X1 - 0.18, -0.2, 0.95), (LAMP_X1 + 0.1, 0.2, 1.4))
        kit.rotate(n, 60 * k, 'X')
        kit.translate(n, (0, y, z))
        notches.append(n)
    kit.boolean(head, notches)
    tail = kit.lathe('lampe_queue', (LAMP_X0, y, z), (LAMP_X0 + 0.9, y, z), [(0.0, 0.6), (0.25, 0.85), (0.9, 0.87)], 40)
    fins = []
    for k in range(8):
        f = kit.box('ailette', (LAMP_X0 + 1.8, -0.11, 0.8), (LAMP_X1 - 2.6, 0.11, 1.0))
        kit.rotate(f, 45 * k + 22.5, 'X')
        kit.translate(f, (0, y, z))
        fins.append(f)
    for piece, bevel in ((body, 0.0), (head, 0.04), (tail, 0.04)):
        kit.assign(piece, mat_alu)
        parts.append(kit.finish(piece, bevel=bevel) if bevel else kit.smooth(piece))
    finset = kit.join('lampe_ailettes', fins)
    kit.assign(finset, mat_alu)
    parts.append(kit.finish(finset, bevel=0.03))
    pad = kit.lathe('lampe_bouton', (LAMP_X0 - 0.3, y, z), (LAMP_X0, y, z), [(0.0, 0.48), (0.3, 0.56)], 32)
    kit.assign(pad, mat_rubber)
    parts.append(kit.smooth(pad))
    lens = kit.cylinder('lampe_verre', (LAMP_X1 - 0.25, y, z), (LAMP_X1 - 0.1, y, z), 0.98, 48)
    kit.assign(lens, mat_glass)
    parts.append(lens)
    m0, m1 = 46.4, 50.3
    mount = kit.prism('lampe_embase', kit.fillet([(m0, -HG_HALF - 0.55), (m1, -HG_HALF - 0.55), (m1, y + 0.75), (m0, y + 0.75)], 0.1, 2), 'z', z - 1.3, z + 1.3)
    collar = kit.lathe('lampe_collier', (m0 + 0.3, y, z), (m1 - 0.3, y, z), [(0.0, 1.02), (m1 - m0 - 0.6, 1.02)], 40)
    screw = kit.lathe('lampe_vis', ((m0 + m1) / 2, -HG_HALF - 0.8, z + 1.3), ((m0 + m1) / 2, -HG_HALF - 0.8, z + 1.8), [(0.0, 0.34), (0.5, 0.3)], 20)
    for piece in (mount, collar, screw):
        kit.assign(piece, mat_alu)
        parts.append(kit.finish(piece, bevel=0.05))
    return kit.join('lampe', parts)


# --- l'ensemble -------------------------------------------------------------------------

def build():
    """Toutes les pieces, par os. Rend {nom d'os: [objets]}."""
    alu = materials.make('unholy_anodise', 'anodized')
    gray = materials.make('unholy_anodise_gris', 'anodized_gray')
    steel = materials.make('unholy_acier', 'steel')
    poly = materials.make('unholy_polymere', 'polymer')
    stipple = materials.make('unholy_polymere_grain', 'polymer_stipple')
    rubber = materials.make('unholy_caoutchouc', 'rubber')
    brass = materials.make('unholy_laiton', 'brass')
    copper = materials.make('unholy_cuivre', 'copper')
    glass = materials.glass('unholy_verre')

    body = [upper(alu, steel), lower(alu, steel), grip(stipple, poly), buffer_and_stock(gray, poly, rubber, steel),
            handguard(alu, steel), barrel(steel), lamp(alu, rubber, glass)]
    return {
        'Main': body,
        'Trigger': [trigger(steel)],
        'Magazine': [magazine(steel, brass, copper)],
        'ChargeHandle': [charging_handle(alu)],
        'DustCover': [bolt_carrier(steel)],
        'EjectionCover': [dust_cover(alu, steel)],
        'FrontAssistAssembly': [forward_assist(alu)],
        'RearSight': [rear_sight(alu, steel)],
        'FrontSight': [front_sight(alu, steel)],
    }
