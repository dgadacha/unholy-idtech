"""
UNHOLY -- boite a outils de modelisation par script, pour Blender.

Les armes d'UNHOLY sont modelisees par du code : des profils extrudes, des
cylindres, des enlevements booleens, puis des chanfreins et des normales
ponderees. Ce module ne fait que ces gestes de base ; les pieces sont
decrites dans leurs propres scripts (rifle.py...).

Unites : le centimetre, comme la scene du pack d'animations sur laquelle les
pieces se posent. Reperes : X vers l'avant, Y vers la gauche, Z vers le haut.
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

# --- creation --------------------------------------------------------------


def link(obj, collection=None):
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def outward(bm):
    """Oriente un solide ferme vers l'exterieur : le signe de son volume ne trompe pas,
    la ou le recalcul des normales se laisse abuser par une forme tres concave."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    volume = sum(f.calc_area() * f.normal.dot(f.calc_center_median()) for f in bm.faces) / 3.0
    if volume < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    return bm


def from_bmesh(name, bm):
    mesh = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    return link(bpy.data.objects.new(name, mesh))


def _plane_point(axis, u, v, w):
    """Un point d'un profil 2D (u, v), pose dans son plan, a la profondeur w."""
    if axis == 'y':          # profil de cote (x, z), epaisseur en y
        return Vector((u, w, v))
    if axis == 'z':          # profil de dessus (x, y), epaisseur en z
        return Vector((u, v, w))
    return Vector((w, u, v))  # profil de face (y, z), epaisseur en x


def prism(name, profile, axis, lo, hi):
    """Un profil 2D ferme, extrude le long d'un axe, de lo a hi."""
    bm = bmesh.new()
    near = [bm.verts.new(_plane_point(axis, u, v, lo)) for u, v in profile]
    far = [bm.verts.new(_plane_point(axis, u, v, hi)) for u, v in profile]
    n = len(profile)
    # Les bouchons restent des faces entieres : triangules, ils donneraient de longs
    # triangles fins que le lissage des normales tordrait en biais.
    bm.faces.new(near)
    bm.faces.new(far[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((near[j], near[i], far[i], far[j]))
    return from_bmesh(name, outward(bm))


def fluted_cylinder(name, start, end, r_outer, r_inner, flutes):
    """Un cylindre cannele (moletage, bague) : les rayons alternent d'une facette a l'autre."""
    start, end = Vector(start), Vector(end)
    axis = end - start
    frame = axis.normalized().to_track_quat('Z', 'Y').to_matrix()
    bm = bmesh.new()
    rings = []
    steps = flutes * 4
    for t in (0.0, axis.length):
        ring = []
        for k in range(steps):
            a = 2 * math.pi * k / steps
            r = r_outer if (k % 4) in (0, 1) else r_inner
            ring.append(bm.verts.new(start + frame @ Vector((math.cos(a) * r, math.sin(a) * r, t))))
        rings.append(ring)
    a, b = rings
    for k in range(steps):
        j = (k + 1) % steps
        bm.faces.new((a[k], a[j], b[j], b[k]))
    bm.faces.new(a[::-1])
    bm.faces.new(b)
    return from_bmesh(name, outward(bm))


def annulus(name, center, normal, r_inner, r_outer, segments=64):
    """Un anneau plat (un reticule), face a la direction normal."""
    center = Vector(center)
    frame = Vector(normal).normalized().to_track_quat('Z', 'Y').to_matrix()
    bm = bmesh.new()
    inner, outer = [], []
    for k in range(segments):
        a = 2 * math.pi * k / segments
        d = Vector((math.cos(a), math.sin(a), 0.0))
        inner.append(bm.verts.new(center + frame @ (d * r_inner)))
        outer.append(bm.verts.new(center + frame @ (d * r_outer)))
    for k in range(segments):
        j = (k + 1) % segments
        bm.faces.new((inner[k], outer[k], outer[j], inner[j]))
    return from_bmesh(name, bm)


def box(name, lo, hi):
    """Un pave entre deux coins opposes, dans n'importe quel ordre."""
    lo, hi = Vector(map(min, lo, hi)), Vector(map(max, lo, hi))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((lo + hi) / 2) @ Matrix.Diagonal((*(hi - lo), 1.0)))
    return from_bmesh(name, bm)


def _axis_matrix(start, end):
    start, end = Vector(start), Vector(end)
    axis = end - start
    rot = axis.normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
    return Matrix.Translation((start + end) / 2) @ rot, axis.length


def cylinder(name, start, end, radius, segments=32, radius_end=None):
    """Un cylindre (ou un tronc de cone) de start a end."""
    bm = bmesh.new()
    matrix, length = _axis_matrix(start, end)
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius if radius_end is None else radius_end,
                          depth=length, matrix=matrix)
    return from_bmesh(name, bm)


def lathe(name, start, end, section, segments=48):
    """Une piece de revolution : section = [(position le long de l'axe, rayon)]."""
    start, end = Vector(start), Vector(end)
    axis = end - start
    length = axis.length
    frame = axis.normalized().to_track_quat('Z', 'Y').to_matrix()
    bm = bmesh.new()
    rings = []
    for t, r in section:
        ring = []
        for k in range(segments):
            a = 2 * math.pi * k / segments
            local = Vector((math.cos(a) * r, math.sin(a) * r, t))
            ring.append(bm.verts.new(start + frame @ local))
        rings.append(ring)
    for ring_a, ring_b in zip(rings, rings[1:]):
        for k in range(segments):
            j = (k + 1) % segments
            bm.faces.new((ring_a[k], ring_a[j], ring_b[j], ring_b[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    del length
    return from_bmesh(name, outward(bm))


def loft(name, rings, cap=True):
    """Une surface tendue d'anneau en anneau (memes nombres de points), fermee aux bouts."""
    bm = bmesh.new()
    verts = [[bm.verts.new(Vector(p)) for p in ring] for ring in rings]
    n = len(rings[0])
    for a, b in zip(verts, verts[1:]):
        for k in range(n):
            j = (k + 1) % n
            bm.faces.new((a[k], a[j], b[j], b[k]))
    if cap:
        bm.faces.new(verts[0][::-1])
        bm.faces.new(verts[-1])
        return from_bmesh(name, outward(bm))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return from_bmesh(name, bm)


def superellipse(cu, cv, ru, rv, exponent=2.5, segments=32, start=0.0):
    """Un ovale aux flancs plus ou moins droits (exposant 2 : ellipse ; plus : rectangle arrondi)."""
    pts = []
    for k in range(segments):
        a = start + 2 * math.pi * k / segments
        c, s = math.cos(a), math.sin(a)
        pts.append((cu + ru * math.copysign(abs(c) ** (2 / exponent), c),
                    cv + rv * math.copysign(abs(s) ** (2 / exponent), s)))
    return pts


# --- profils 2D -------------------------------------------------------------


def fillet(points, radius, segments=4, radii=None):
    """Arrondit les coins d'un polygone 2D. radii donne un rayon par sommet."""
    out = []
    n = len(points)
    for i in range(n):
        p0, p1, p2 = Vector(points[i - 1]), Vector(points[i]), Vector(points[(i + 1) % n])
        r = radius if radii is None else radii[i]
        d1, d2 = p0 - p1, p2 - p1
        if r <= 0 or d1.length < 1e-6 or d2.length < 1e-6:
            out.append(p1)
            continue
        d1.normalize()
        d2.normalize()
        angle = d1.angle(d2)
        if angle < 1e-3 or abs(angle - math.pi) < 1e-3:
            out.append(p1)
            continue
        t = min(r / math.tan(angle / 2), (Vector(points[i - 1]) - p1).length * 0.49,
                (Vector(points[(i + 1) % n]) - p1).length * 0.49)
        r = t * math.tan(angle / 2)
        a, b = p1 + d1 * t, p1 + d2 * t
        center = p1 + (d1 + d2).normalized() * (r / math.sin(angle / 2))
        va, vb = a - center, b - center
        sweep = va.angle_signed(vb)
        for k in range(segments + 1):
            out.append(center + Matrix.Rotation(-sweep * k / segments, 2) @ va)
    return [(p.x, p.y) for p in out]


def offset_convex(points, distance):
    """Decale vers l'interieur les cotes d'un polygone convexe (sens trigonometrique)."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    lines = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        d = (b - a).normalized()
        normal = Vector((-d.y, d.x))  # vers l'interieur pour un polygone trigonometrique
        lines.append((a + normal * distance, d))
    out = []
    for i in range(n):
        p1, d1 = lines[i - 1]
        p2, d2 = lines[i]
        # intersection des deux droites decalees
        cross = d1.x * d2.y - d1.y * d2.x
        if abs(cross) < 1e-9:
            out.append(p2)
            continue
        t = ((p2.x - p1.x) * d2.y - (p2.y - p1.y) * d2.x) / cross
        out.append(p1 + d1 * t)
    return [(p.x, p.y) for p in out]


def rounded_rect(u0, v0, u1, v1, radius, segments=4):
    return fillet([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], radius, segments)


def circle(cu, cv, radius, segments=32):
    return [(cu + radius * math.cos(2 * math.pi * k / segments), cv + radius * math.sin(2 * math.pi * k / segments))
            for k in range(segments)]


# --- operations ---------------------------------------------------------------


def apply_modifiers(obj):
    """Fige les modificateurs dans le maillage."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
    old = obj.data
    obj.modifiers.clear()
    obj.data = mesh
    mesh.name = obj.name
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return obj


def boolean(target, cutters, operation='DIFFERENCE'):
    """Enleve (ou ajoute) des pieces a une autre, puis jette les outils."""
    if not isinstance(cutters, (list, tuple)):
        cutters = [cutters]
    for cutter in cutters:
        mod = target.modifiers.new('bool', 'BOOLEAN')
        mod.object = cutter
        mod.operation = operation
        mod.solver = 'EXACT'
        mod.use_self = True
        cutter.hide_render = True
    apply_modifiers(target)
    for cutter in cutters:
        bpy.data.objects.remove(cutter, do_unlink=True)
    return target


def join(name, objects):
    """Reunit des objets en un seul. Passe par l'operateur de fusion de Blender, qui
    garde les normales durcies des chanfreins (bmesh les perdrait)."""
    objects = [o for o in objects if o is not None]
    active = objects[0]
    if len(objects) > 1:
        for obj in bpy.context.view_layer.objects:
            obj.select_set(False)
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active
        with bpy.context.temp_override(active_object=active, object=active,
                                       selected_objects=objects, selected_editable_objects=objects):
            bpy.ops.object.join()
    active.name = name
    active.data.name = name
    return active


def array(obj, count, offset):
    """Repete une piece count fois, decalee de offset a chaque fois."""
    mod = obj.modifiers.new('array', 'ARRAY')
    mod.count = count
    mod.use_relative_offset = False
    mod.use_constant_offset = True
    mod.constant_offset_displace = offset
    return apply_modifiers(obj)


def mirror_y(obj):
    mod = obj.modifiers.new('mirror', 'MIRROR')
    mod.use_axis = (False, True, False)
    mod.use_bisect_axis = (False, True, False)
    return apply_modifiers(obj)


def weighted_normals(obj, angle=35.0):
    """Les normales de chaque coin de face : la moyenne des faces voisines qui ne s'en
    ecartent pas de plus de angle degres, ponderee par leur aire. Une grande face plane
    reste plane, les chanfreins et les arrondis s'appuient sur elle. (Le modificateur de
    Blender fait de meme, mais perd les coins pris entre une grande face et une petite
    creusee par un enlevement.)"""
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    limit = math.cos(math.radians(angle))
    weights = {f.index: f.calc_area() for f in bm.faces}
    normals = [None] * len(mesh.loops)
    for face in bm.faces:
        for loop in face.loops:
            acc = Vector()
            for other in loop.vert.link_faces:
                if other.normal.dot(face.normal) >= limit:
                    acc += other.normal * weights[other.index]
            normals[loop.index] = (acc.normalized() if acc.length > 1e-12 else face.normal).to_tuple()
    bm.free()
    mesh.shade_smooth()
    mesh.normals_split_custom_set(normals)
    return obj


def finish(obj, bevel=0.06, segments=2, angle=35.0):
    """Chanfreins sur les aretes vives, puis normales ponderees : les faces planes
    restent planes, les aretes accrochent la lumiere."""
    if bevel > 0:
        mod = obj.modifiers.new('bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = max(segments, 3)
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(angle)
        mod.miter_outer = 'MITER_ARC'
        mod.use_clamp_overlap = True
        apply_modifiers(obj)
    return weighted_normals(obj, 34.0)


def smooth(obj, angle=40.0):
    return weighted_normals(obj, angle)


def assign(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)
    return obj


def translate(obj, offset):
    obj.data.transform(Matrix.Translation(Vector(offset)))
    return obj


def rotate(obj, angle_deg, axis, pivot=(0, 0, 0)):
    pivot = Vector(pivot)
    obj.data.transform(Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(angle_deg), 4, axis) @ Matrix.Translation(-pivot))
    return obj
