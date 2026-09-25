"""
UNHOLY -- le rechargement du fusil, ecrit par script.

Le pack a son propre rechargement ; celui-ci est le notre, releve image par
image sur une video de reference (un rechargement tactique de HK416, sans
toucher a la culasse) et ecrit ici en quelques poses clefs :

  0,0 s   le fusil au repos, la main gauche sur le garde-main
  0,4 s   le fusil monte, pointe en l'air et bascule sur la droite : le flanc
          gauche et le puits font face a l'oeil ; la main gauche descend
  0,8 s   elle empoigne le chargeur
  1,1 s   elle le tire, il sort du puits
  1,5 s   elle l'emporte vers le bas, hors du champ
  1,8 s   elle revient par le bas a gauche avec un chargeur plein
  2,1 s   elle l'engage sous le puits, le pousse, il claque en place (2,4 s)
  3,2 s   elle le tire un peu pour s'assurer qu'il tient
  3,6 s   elle le lache et remonte au garde-main
  4,4 s   le fusil est revenu au repos

Tout s'ecrit sur les deux squelettes du pack : le fusil (os Main et Magazine),
les bras (la cible de la main gauche, liee au chargeur par une contrainte
d'enfant, le pole de son coude, ses doigts). La main droite reste sur la
poignee : sa cible suit le corps du fusil. Chaque image est calculee puis
posee : les courbes passent par les poses clefs sans s'y arreter, sauf la ou
un geste marque un temps.

Reperes : la camera du pack est a l'origine du monde, regarde vers +X, la
droite vers -Y, le haut vers +Z. Les gestes du fusil s'y expriment (bascule
autour de son axe, cabre, lacet, deplacement), autour de la poignee.

    import reload
    reload.make(bras, fusil)   # cree les actions Arms_Reload_HK et Rifle_Reload_HK
"""

import math

import bpy
from mathutils import Matrix, Quaternion, Vector

FPS = 24
ARMS_ACTION = 'Arms_Reload_HK'
RIFLE_ACTION = 'Rifle_Reload_HK'

CAM_RIGHT = Vector((0.0, -1.0, 0.0))
CAM_UP = Vector((0.0, 0.0, 1.0))
CAM_FORWARD = Vector((1.0, 0.0, 0.0))

# Le pivot des gestes du fusil : le haut de la poignee, ou tient la main droite.
PIVOT = Vector((6.0, 0.0, 10.0))
# La main gauche est descendue de ce qu'il faut pour le garde-main HD (rifle.GRIP_DROP).
HAND_DROP = 0.65

# --- les poses clefs ---------------------------------------------------------------
#
# Le fusil : (temps, bascule, cabre, lacet, droite, haut, avant), en degres et en cm.
# La bascule tourne le dessus vers la droite, le cabre leve la bouche, le lacet la
# porte vers la gauche. Un temps suivi de '!' marque un arret (vitesse nulle).
RIFLE = [
    (0.00, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, '!'),
    (0.40, 37.8, 18.0, 10.8, -4.0, 4.0, 1.4, ''),
    (0.62, 43.5, 21.0, 12.5, -4.8, 4.8, 1.7, ''),
    (1.08, 42.0, 20.0, 12.0, -4.5, 4.5, 1.5, ''),
    (1.24, 45.0, 17.8, 12.5, -4.7, 3.6, 1.3, ''),
    (1.46, 42.5, 19.8, 12.2, -4.5, 4.5, 1.5, ''),
    (2.12, 42.5, 20.2, 12.0, -4.5, 4.3, 1.4, ''),
    (2.34, 40.0, 22.0, 12.0, -4.4, 5.2, 1.5, ''),
    (2.48, 41.7, 19.8, 12.0, -4.5, 4.2, 1.4, ''),
    (2.70, 40.3, 21.2, 12.0, -4.4, 4.9, 1.5, ''),
    (2.88, 42.0, 20.0, 12.0, -4.5, 4.5, 1.5, ''),
    (3.26, 42.6, 19.2, 11.8, -4.5, 4.1, 1.5, ''),
    (3.42, 42.0, 20.0, 12.0, -4.5, 4.5, 1.5, ''),
    (3.72, 35.7, 17.0, 10.2, -3.8, 3.8, 1.3, ''),
    (4.14, -2.2, -1.2, -0.6, 0.3, -0.35, 0.0, ''),
    (4.44, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, '!'),
]

# Le chargeur, dans le repere du fusil : (temps, x, y, z, inclinaison), en cm et en
# degres (positif : le bas vers l'avant), autour du haut du chargeur. Ou, marque
# 'camera', une position dans le repere de la camera (hors du champ).
MAGAZINE = [
    (0.00, 'fusil', 0.0, 0.0, 0.0, 0.0, '!'),
    (1.10, 'fusil', 0.0, 0.0, 0.0, 0.0, '!'),
    (1.20, 'fusil', 0.0, 0.0, -1.2, 0.0, ''),
    (1.38, 'fusil', -0.8, 0.4, -9.5, -8.0, ''),
    (1.52, 'camera', 30.0, 16.0, -48.0, -30.0, ''),
    (1.64, 'camera', 31.0, 14.0, -47.0, -20.0, ''),
    (1.76, 'camera', 35.0, 11.0, -30.0, 6.0, ''),
    (1.96, 'camera', 37.0, 6.0, -21.0, 9.0, ''),
    (2.14, 'fusil', 0.4, 0.0, -3.6, 7.0, ''),
    (2.30, 'fusil', 0.0, 0.0, -0.5, 1.5, ''),
    (2.37, 'fusil', 0.0, 0.0, 0.15, 0.0, ''),
    (2.46, 'fusil', 0.0, 0.0, 0.0, 0.0, '!'),
    (2.70, 'fusil', 0.0, 0.0, 0.1, 0.0, ''),
    (2.80, 'fusil', 0.0, 0.0, 0.0, 0.0, '!'),
    (3.24, 'fusil', 0.0, 0.0, -0.12, 0.0, ''),
    (3.34, 'fusil', 0.0, 0.0, 0.0, 0.0, '!'),
    (4.44, 'fusil', 0.0, 0.0, 0.0, 0.0, '!'),
]

# La main gauche : (temps, pose), les poses etant definies plus bas ; ses doigts
# suivent la leur : (temps, prise).
HAND = [
    (0.00, 'garde_main', '!'),
    (0.24, 'quitte_garde_main', ''),
    (0.60, 'vers_chargeur', ''),
    (0.80, 'chargeur', '!'),
    (3.52, 'chargeur', '!'),
    (3.70, 'lache_chargeur', ''),
    (4.06, 'vers_garde_main', ''),
    (4.30, 'garde_main', '!'),
    (4.44, 'garde_main', '!'),
]
FINGERS = [
    (0.00, 'garde_main'),
    (0.30, 'ouverte'),
    (0.62, 'ouverte'),
    (0.86, 'chargeur'),
    (3.50, 'chargeur'),
    (3.70, 'ouverte'),
    (4.12, 'ouverte'),
    (4.34, 'garde_main'),
    (4.44, 'garde_main'),
]
# Le coude gauche descend pendant le geste : (temps, decalage du pole dans le repere
# de la camera : droite, haut, avant).
ELBOW = [
    (0.00, 0.0, 0.0, 0.0, '!'),
    (0.60, 3.0, -5.0, 2.0, ''),
    (1.60, 2.0, -9.0, -2.0, ''),
    (2.30, 3.0, -7.0, 0.0, ''),
    (3.60, 3.0, -5.0, 2.0, ''),
    (4.30, 0.0, 0.0, 0.0, '!'),
    (4.44, 0.0, 0.0, 0.0, '!'),
]
# Le coude droit s'abaisse et rentre : l'avant-bras sort du champ par le bas quand la
# poignee remonte. Memes colonnes.
ELBOW_RIGHT = [
    (0.00, 0.0, 0.0, 0.0, '!'),
    (0.50, -18.0, -14.0, 6.0, ''),
    (3.70, -18.0, -14.0, 6.0, ''),
    (4.30, 0.0, 0.0, 0.0, '!'),
    (4.44, 0.0, 0.0, 0.0, '!'),
]

FINGER_BONES = [f'{finger}_{k}_l' for finger in ('index', 'middle', 'ring', 'pinky', 'thumb') for k in ('01', '02', '03')]
KNUCKLES = [f'{finger}Knuckle_l' for finger in ('index', 'middle', 'ring', 'pinky', 'thumb')]


# --- interpolation -----------------------------------------------------------------

def hermite(keys, t):
    """Une courbe qui passe par les clefs (temps, valeurs..., arret) : tangentes de
    Catmull-Rom, nulles aux arrets. Rend les valeurs au temps t."""
    times = [k[0] for k in keys]
    if t <= times[0]:
        return list(keys[0][1])
    if t >= times[-1]:
        return list(keys[-1][1])
    i = max(j for j in range(len(keys) - 1) if times[j] <= t)
    t0, t1 = times[i], times[i + 1]
    p0, p1 = keys[i][1], keys[i + 1][1]

    def tangent(j):
        if keys[j][2] or j == 0 or j == len(keys) - 1:
            return [0.0] * len(keys[j][1])
        a, b = keys[j - 1], keys[j + 1]
        return [(vb - va) / (b[0] - a[0]) for va, vb in zip(a[1], b[1])]

    m0, m1 = tangent(i), tangent(i + 1)
    h = t1 - t0
    s = (t - t0) / h
    h00, h10, h01, h11 = 2 * s ** 3 - 3 * s ** 2 + 1, s ** 3 - 2 * s ** 2 + s, -2 * s ** 3 + 3 * s ** 2, s ** 3 - s ** 2
    return [h00 * a + h10 * h * ma + h01 * b + h11 * h * mb for a, b, ma, mb in zip(p0, p1, m0, m1)]


def track(rows, first, count, stop_col):
    """Des lignes de table en clefs (temps, valeurs, arret)."""
    return [(r[0], [float(v) for v in r[first:first + count]], r[stop_col] == '!') for r in rows]


def quat_keys(times_quats_stops):
    """Des quaternions en clefs interpolables : tous du meme cote de la sphere."""
    out, prev = [], None
    for t, q, stop in times_quats_stops:
        q = q.copy()
        if prev is not None and prev.dot(q) < 0:
            q.negate()
        out.append((t, list(q), stop))
        prev = q
    return out


def quat_at(keys, t):
    q = Quaternion(hermite(keys, t))
    q.normalize()
    return q


# --- les poses ---------------------------------------------------------------------

def rifle_offset(t, base_main_world, base_rifle_world):
    """Le corps du fusil (son os Main) au temps t, dans le monde. base_rifle_world porte le
    repere de modelisation du fusil au repos (pour le pivot)."""
    roll, pitch, yaw, right, up, forward = hermite(track(RIFLE, 1, 6, 7), t)
    bore = (base_main_world.to_3x3() @ Vector((1.0, 0.0, 0.0))).normalized()
    pivot = base_rifle_world @ PIVOT
    rot = (Matrix.Rotation(math.radians(yaw), 4, CAM_UP) @ Matrix.Rotation(math.radians(pitch), 4, CAM_RIGHT)
           @ Matrix.Rotation(math.radians(roll), 4, bore))
    move = CAM_RIGHT * right + CAM_UP * up + CAM_FORWARD * forward
    return Matrix.Translation(pivot + move) @ rot @ Matrix.Translation(-pivot) @ base_main_world


def magazine_delta(key, rest_to_armature, rifle_obj, mag_rest):
    """Le deplacement du chargeur d'une clef, dans le repere du fusil au repos : une
    translation et une inclinaison autour du haut du chargeur. rest_to_armature porte ce
    repere la ou le fusil se trouve a l'instant de la clef."""
    _, space, a, b, c, tilt, _ = key
    top = mag_rest.translation
    if space == 'fusil':
        return Vector((a, b, c)), tilt
    # Une position de la camera, ramenee dans le repere du fusil a l'instant de la clef.
    local = (rifle_obj.matrix_world @ rest_to_armature).inverted() @ Vector((a, b, c))
    return local - top, tilt


def build_hand_poses(arms, rifle, mag_rest):
    """Les poses de la cible de la main gauche, en valeurs de son os (donc dans le repere
    que lui donne la contrainte d'enfant : celui du chargeur).

    La prise du chargeur se deduit de celle du garde-main : la main tenait une barre
    couchee le long du fusil, elle tient maintenant une barre debout, le chargeur. On
    tourne donc sa pose de 90 degres autour de l'axe transversal du fusil, en passant du
    centre du garde-main au milieu du chargeur."""
    pb = arms.pose.bones['ctrl_HandIK_l']
    loc0, quat0 = pb.location.copy(), pb.rotation_quaternion.copy()
    basis0 = Matrix.LocRotScale(loc0, quat0, Vector((1, 1, 1)))
    # La pose finale de l'os, a base identite : F0. Sa pose finale vaut F0 @ base.
    pb.location, pb.rotation_quaternion = Vector(), Quaternion()
    bpy.context.view_layer.update()
    to_rifle = rifle.matrix_world.inverted() @ arms.matrix_world
    f0 = to_rifle @ pb.matrix           # dans le repere du fusil
    pb.location, pb.rotation_quaternion = loc0, quat0
    bpy.context.view_layer.update()
    hand0 = f0 @ basis0                 # la main sur le garde-main, repere du fusil

    def basis_for(target):
        m = f0.inverted() @ target
        loc, rot, _ = m.decompose()
        return loc, rot

    # Le centre de la barre que tient la main : le garde-main du pack (16,79), descendu
    # avec elle ; le milieu du chargeur, sous le puits.
    grip_hg = Vector((hand0.translation.x + 4.5, 0.0, 16.79 - HAND_DROP))
    grip_mag = Vector((mag_rest.translation.x + 0.45, 0.0, 2.6))
    turn = Matrix.Rotation(math.radians(-90.0), 4, 'Y')
    on_mag = Matrix.Translation(grip_mag) @ turn @ Matrix.Translation(-grip_hg) @ hand0

    def moved(m, dx=0.0, dy=0.0, dz=0.0):
        return Matrix.Translation((dx, dy, dz)) @ m

    poses = {
        'garde_main': (loc0, quat0),
        'quitte_garde_main': basis_for(moved(hand0, -2.5, 2.5, -4.0)),
        'vers_chargeur': basis_for(moved(on_mag, 2.5, 2.0, -3.5)),
        'chargeur': basis_for(on_mag),
        'lache_chargeur': basis_for(moved(on_mag, 2.0, 2.5, -2.5)),
        'vers_garde_main': basis_for(moved(hand0, -1.5, 2.5, -3.0)),
    }
    return poses


def finger_poses(arms):
    """Les prises des doigts : celle du garde-main (la pose de base), que la main garde sur
    le chargeur, et la main entrouverte entre les deux."""
    base = {name: arms.pose.bones[name].rotation_quaternion.copy() for name in FINGER_BONES + KNUCKLES}
    open_hand = {}
    for name, q in base.items():
        if name in KNUCKLES:
            open_hand[name] = q.copy()
        else:
            open_hand[name] = Quaternion().slerp(q, 0.3 if name.startswith('thumb') else 0.4)
    return {'garde_main': base, 'ouverte': open_hand, 'chargeur': base}


# --- l'ecriture ---------------------------------------------------------------------

def make(arms, rifle):
    """Cree les deux actions du rechargement et les rend (bras, fusil)."""
    scene = bpy.context.scene
    arms.animation_data.action = bpy.data.actions['Arms_BasePose']
    rifle.animation_data.action = bpy.data.actions['Rifle_BasePose']
    scene.frame_set(1)
    bpy.context.view_layer.update()

    main = rifle.pose.bones['Main']
    magazine = rifle.pose.bones['Magazine']
    base_main_world = rifle.matrix_world @ main.matrix
    mag_rest = rifle.data.bones['Magazine'].matrix_local.copy()
    main_rest = rifle.data.bones['Main'].matrix_local.copy()

    # Ce que la pose de base donne a chaque os : on le recopie la ou l'on n'anime rien.
    arms_base = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(), pb.scale.copy()) for pb in arms.pose.bones}
    rifle_base = {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(), pb.scale.copy()) for pb in rifle.pose.bones}
    hand = build_hand_poses(arms, rifle, mag_rest)
    fingers = finger_poses(arms)
    poles = []
    for side, keys in (('l', ELBOW), ('r', ELBOW_RIGHT)):
        pb = arms.pose.bones[f'ctrl_pole_elbow_{side}']
        poles.append((pb, pb.location.copy(), track(keys, 1, 3, 4)))

    hand_loc_keys = [(t, list(hand[name][0]), stop == '!') for t, name, stop in HAND]
    hand_rot_keys = quat_keys([(t, hand[name][1], stop == '!') for t, name, stop in HAND])
    finger_keys = {}
    for bone in FINGER_BONES + KNUCKLES:
        finger_keys[bone] = quat_keys([(t, fingers[pose][bone], False) for t, pose in FINGERS])

    # Le chargeur : chaque clef ramenee dans le repere du fusil, a l'instant de la clef.
    mag_keys = []
    for key in MAGAZINE:
        main_at = rifle.matrix_world.inverted() @ rifle_offset(key[0], base_main_world, rifle.matrix_world)
        delta, tilt = magazine_delta(key, main_at @ main_rest.inverted(), rifle, mag_rest)
        mag_keys.append((key[0], [delta.x, delta.y, delta.z, tilt], key[6] == '!'))

    arms_action = bpy.data.actions.get(ARMS_ACTION) or bpy.data.actions.new(ARMS_ACTION)
    rifle_action = bpy.data.actions.get(RIFLE_ACTION) or bpy.data.actions.new(RIFLE_ACTION)
    arms.animation_data.action = arms_action
    rifle.animation_data.action = rifle_action
    last = int(round(RIFLE[-1][0] * FPS)) + 1

    for frame in range(1, last + 1):
        t = (frame - 1) / FPS
        # Le fusil.
        for pb in rifle.pose.bones:
            pb.location, pb.rotation_quaternion, pb.scale = rifle_base[pb.name]
        world = rifle_offset(t, base_main_world, rifle.matrix_world)
        main.matrix = rifle.matrix_world.inverted() @ world
        bpy.context.view_layer.update()
        dx, dy, dz, tilt = hermite(mag_keys, t)
        top = mag_rest.translation
        delta = (Matrix.Translation(Vector((dx, dy, dz)) + top) @ Matrix.Rotation(math.radians(tilt), 4, 'Y')
                 @ Matrix.Translation(-top))
        magazine.matrix = main.matrix @ main_rest.inverted() @ delta @ mag_rest
        bpy.context.view_layer.update()
        for pb in rifle.pose.bones:
            for path in ('location', 'rotation_quaternion', 'scale'):
                pb.keyframe_insert(path, frame=frame, group=pb.name)

        # Les bras.
        for pb in arms.pose.bones:
            pb.location, pb.rotation_quaternion, pb.scale = arms_base[pb.name]
        ctrl = arms.pose.bones['ctrl_HandIK_l']
        ctrl.location = Vector(hermite(hand_loc_keys, t))
        ctrl.rotation_quaternion = quat_at(hand_rot_keys, t)
        for bone, keys in finger_keys.items():
            arms.pose.bones[bone].rotation_quaternion = quat_at(keys, t)
        for pole, base_loc, keys in poles:
            r, u, f = hermite(keys, t)
            shift = CAM_RIGHT * r + CAM_UP * u + CAM_FORWARD * f
            pole.location = base_loc + (arms.matrix_world @ pole.bone.matrix_local).to_3x3().inverted() @ shift
        for pb in arms.pose.bones:
            for path in ('location', 'rotation_quaternion', 'scale'):
                pb.keyframe_insert(path, frame=frame, group=pb.name)

    for action in (arms_action, rifle_action):
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:
                        for k in fc.keyframe_points:
                            k.interpolation = 'LINEAR'
    return arms_action, rifle_action
