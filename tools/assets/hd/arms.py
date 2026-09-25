"""
UNHOLY -- les bras du militaire : gants et manches de treillis.

Ils sont faits du maillage des bras du Retro Weapon Pack, pour garder ses os
et ses poids (les animations les deforment comme les bras du pack) : le miroir
applique, subdivise deux fois, puis rhabille. Les manches gonflent comme une
toile, plissee le long du bras, et finissent en poignet sur le gant ; les
gants epousent la main, un peu plus epais qu'une peau. Aucune peau ne se voit.

Les zones se lisent sur les poids : un sommet que portent surtout les os de la
main et des doigts est gant, les autres sont manche.
"""

import math
import re

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

import kit

HAND = re.compile(r'hand|index|middle|ring|pinky|thumb|knuckle|inhanditem', re.IGNORECASE)

SLEEVE_PUFF = 0.42      # cm : l'ampleur de la manche autour du bras
FOLD_DEPTH = 0.28       # cm : la profondeur des plis
CUFF_LIP = 0.22         # cm : le bourrelet du poignet
GLOVE_THICKNESS = 0.1   # cm : l'epaisseur du gant


def value_noise(points, scale, seed=7):
    """Un bruit de valeurs 3D lisse (interpolation cubique), assez pour des plis."""
    rng = np.random.default_rng(seed)
    table = rng.random(4096).astype(np.float32)
    p = points * scale
    i = np.floor(p).astype(np.int64)
    f = p - i
    f = f * f * (3.0 - 2.0 * f)

    def lattice(ix, iy, iz):
        h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791)
        return table[h & 4095]

    out = np.zeros(len(points), dtype=np.float32)
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out += w * lattice(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz)
    return out


def folds(points):
    """Les plis d'une manche : un bruit etire, qui change vite le long du bras
    (le bras du pack s'allonge vers l'avant, en x) et lentement autour."""
    stretched = points * np.array([1.7, 0.45, 0.45], dtype=np.float32)
    n = 0.62 * value_noise(stretched, 0.55) + 0.38 * value_noise(stretched, 1.3, seed=11)
    return (n - 0.5) * 2.0


def drop_left_hand(arms_rig, rifle_rig, distance):
    """Descend la main gauche de distance (cm, dans le repere du fusil), dans toutes les
    animations : sa cible suit le chargeur par une contrainte d'enfant (Child Of), dont on
    decale l'origine. Le garde-main du fusil HD est plus haut que celui du pack."""
    pose = arms_rig.pose.bones['ctrl_HandIK_l']
    child_of = next(c for c in pose.constraints if c.type == 'CHILD_OF')
    target = child_of.target
    magazine = target.pose.bones[child_of.subtarget]
    world = target.matrix_world @ magazine.matrix
    offset_world = rifle_rig.matrix_world.to_3x3() @ Vector((0.0, 0.0, -distance))
    offset_local = world.to_3x3().inverted() @ offset_world
    child_of.inverse_matrix = Matrix.Translation(offset_local) @ child_of.inverse_matrix


def build(source, armature, mat_sleeve, mat_glove):
    """Les bras HD, depuis le maillage des bras du pack (source), dans sa pose de liaison."""
    # Le miroir applique (le bras droit), sans la triangulation : la subdivision veut des quads.
    saved = {}
    for mod in source.modifiers:
        if mod.type in ('TRIANGULATE', 'ARMATURE'):
            saved[mod.name] = mod.show_viewport
            mod.show_viewport = False
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(source.evaluated_get(depsgraph), preserve_all_data_layers=True, depsgraph=depsgraph)
    for mod in source.modifiers:
        if mod.name in saved:
            mod.show_viewport = saved[mod.name]
    mesh.transform(source.matrix_world)
    obj = kit.link(bpy.data.objects.new('bras_hd', mesh))
    for group in source.vertex_groups:
        if group.name not in obj.vertex_groups:
            obj.vertex_groups.new(name=group.name)

    sub = obj.modifiers.new('subdivision', 'SUBSURF')
    sub.levels = 2
    sub.render_levels = 2
    sub.uv_smooth = 'PRESERVE_BOUNDARIES'
    kit.apply_modifiers(obj)

    # Les zones, d'apres les poids : g vaut 1 sur le gant, 0 sur la manche.
    me = obj.data
    hand_groups = {g.index for g in obj.vertex_groups if HAND.search(g.name)}
    count = len(me.vertices)
    glove = np.zeros(count, dtype=np.float32)
    for v in me.vertices:
        total = sum(g.weight for g in v.groups)
        if total > 0:
            glove[v.index] = sum(g.weight for g in v.groups if g.group in hand_groups) / total
    co = np.array([v.co[:] for v in me.vertices], dtype=np.float32)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.normal_update()
    normals = np.array([v.normal[:] for v in bm.verts], dtype=np.float32)
    bm.free()

    sleeve = np.clip((0.55 - glove) / 0.35, 0.0, 1.0)            # 1 sur la manche, 0 au gant
    cuff = np.exp(-((glove - 0.45) / 0.12) ** 2)                  # la bande du poignet
    fold = folds(co)
    offset = sleeve * (SLEEVE_PUFF + FOLD_DEPTH * fold) + cuff * CUFF_LIP + (1.0 - sleeve) * GLOVE_THICKNESS
    co += normals * offset[:, None]
    me.vertices.foreach_set('co', co.ravel())
    me.update()

    # Deux matieres : la manche et le gant, separes au milieu du poignet.
    me.materials.clear()
    me.materials.append(mat_sleeve)
    me.materials.append(mat_glove)
    glove_face = [int(np.mean(glove[list(p.vertices)]) > 0.42) for p in me.polygons]
    me.polygons.foreach_set('material_index', glove_face)

    obj.parent = armature
    mod = obj.modifiers.new('armature', 'ARMATURE')
    mod.object = armature
    kit.weighted_normals(obj, 60.0)
    print(f'bras : {len(me.polygons)} faces, {count} sommets')
    return obj
