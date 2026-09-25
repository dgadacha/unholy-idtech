"""
Retro Weapon Pack -> id Tech 4 : le fusil et les bras, en un seul modele anime.

Lance dans Blender sans interface par tools/assets/build_retro_weapons.sh :

    blender -b FP_Arms_Rifle_01_Anims.blend --python retro_rifle.py -- sortie.glb

Le pack est fait pour Unity et Unreal : deux squelettes, les bras (63 os) et le
fusil (9 os), chacun ses animations, et les mains accrochees au fusil par
cinematique inverse (la droite a son corps, la gauche a son chargeur). id Tech 4
veut un seul squelette par modele. Le script rejoue donc chaque animation dans
Blender, contraintes comprises, et en recopie le resultat os par os sur un
squelette unique : les os des bras, ceux du fusil, et trois os que le moteur
cherche par leur nom (le canon, l'eclat, l'ejection).

Reperes : la camera du pack est a l'origine, regarde vers +X, le haut vers +Z,
avec 90 degres de champ horizontal en 16/9. C'est le repere du moteur, qui pose
l'arme a l'oeil du joueur, et le champ de vision du jeu : l'arme tombera la ou
son auteur l'a cadree. Le pack compte en centimetres ; le modele sort en
pouces, l'unite du moteur, et se charge donc sans option d'echelle.
"""

import sys

import bpy
from mathutils import Matrix, Vector

INCH_PER_CM = 1.0 / 2.54

# Les animations du moteur, et ce qu'elles rejouent du pack : action des bras,
# action du fusil. Quand le pack n'anime que le fusil, les bras gardent leur
# pose de base et la cinematique inverse les tient accroches.
ANIMS = (
    ('idle', 'Arms_BasePose', 'Rifle_Breathing'),
    ('walk', 'Arms_BasePose', 'Rifle_Walk'),
    ('run', 'Arms_BasePose', 'Rifle_Run_WithPose'),
    ('crouch_idle', 'Arms_BasePose', 'Rifle_Breathing_Crouching'),
    ('crouch_walk', 'Arms_BasePose', 'Rifle_Walk_Crouching'),
    ('aim_in', 'Arms_AimStart', 'Rifle_AimStart'),
    ('aim_idle', 'Arms_AimPose', 'Rifle_Breathing_Aiming'),
    ('aim_walk', 'Arms_AimPose', 'Rifle_Walk_Aiming'),
    ('aim_out', 'Arms_AimEnd', 'Rifle_AimEnd'),
    ('aim_fire', 'Arms_AimFireAiming', 'Rifle_AimFire'),
    ('fire', 'Arms_Fire', 'Rifle_Fire'),
    ('reload', 'Arms_Reload', 'Rifle_Reload'),
    ('raise', 'Arms_Draw', 'Rifle_Draw'),
    ('putaway', 'Arms_Hide', 'Rifle_Hide'),
)

# Les matieres prennent le nom de leur declaration dans content/materials :
# le moteur les retrouve ainsi.
MATERIALS = {
    'Rifle_01_MI': 'models/retro/rifle',
    'Material.001': 'models/retro/arms',
}

ARMS_ARMATURE = 'Arms_Armature'
RIFLE_ARMATURE = 'Rifle_01_Armature'
ARMS_MESH = 'FPS_Arms_Mesh'
# Tout le fusil tient dans cet objet, malgre son nom.
RIFLE_MESH = 'ChargeHandle_Mesh'

OUTPUT_NAME = 'rifle_view'


# L'eclat de tir : un carre de cette taille, en pouces, et sa matiere.
FLASH_SIZE = 7.0
FLASH_MATERIAL = 'models/retro/muzzleflash'


def engine(matrix):
    """D'un repere du pack a celui du moteur : les memes axes, en pouces."""
    location, rotation, scale = matrix.decompose()
    return Matrix.LocRotScale(location * INCH_PER_CM, rotation, scale)


def set_actions(arms, rifle, arms_action, rifle_action):
    arms.animation_data.action = bpy.data.actions[arms_action]
    rifle.animation_data.action = bpy.data.actions[rifle_action]


def action_end(name):
    return int(round(bpy.data.actions[name].frame_range[1]))


def ordered(bones, parents):
    """Les os dans un ordre ou chaque parent precede ses enfants."""
    done, order = set(), []

    def visit(name):
        if name in done:
            return
        parent = parents[name]
        if parent is not None:
            visit(parent)
        done.add(name)
        order.append(name)

    for name in bones:
        visit(name)
    return order


def rest_mesh(source, depsgraph):
    """
    Le maillage au repos, dans le repere du monde : les modificateurs appliques
    (le miroir qui fabrique le bras droit, la triangulation), sauf l'armature.
    """
    armature_mods = [mod for mod in source.modifiers if mod.type == 'ARMATURE']
    for mod in armature_mods:
        mod.show_viewport = False
    depsgraph.update()
    evaluated = source.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
    mesh.transform(evaluated.matrix_world)
    for mod in armature_mods:
        mod.show_viewport = True
    depsgraph.update()
    return mesh


def muzzle_and_axis(mesh, rear_sight, front_sight):
    """
    Le bout du canon : les sommets les plus en avant le long de l'axe du fusil,
    pris de la hausse vers le guidon. La moyenne des derniers millimetres donne
    l'ame du canon, pas le haut du guidon.
    """
    forward = (front_sight - rear_sight).normalized()
    along = [v.co.dot(forward) for v in mesh.vertices]
    tip = max(along)
    front = [v.co for v, a in zip(mesh.vertices, along) if a > tip - 1.0]
    center = sum(front, Vector()) / len(front)
    return center, forward


def frame_matrix(origin, forward):
    """Un repere pose en `origin`, x le long de `forward`, z vers le haut."""
    x = forward.normalized()
    z = Vector((0.0, 0.0, 1.0))
    y = z.cross(x).normalized()
    z = x.cross(y).normalized()
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = origin
    return m


def main():
    out = sys.argv[sys.argv.index('--') + 1]
    scene = bpy.context.scene
    arms = bpy.data.objects[ARMS_ARMATURE]
    rifle = bpy.data.objects[RIFLE_ARMATURE]
    arms_mesh = bpy.data.objects[ARMS_MESH]
    rifle_mesh = bpy.data.objects[RIFLE_MESH]

    # La pose de reference, celle ou les maillages sont lies aux os.
    set_actions(arms, rifle, 'Arms_BasePose', 'Rifle_BasePose')
    scene.frame_set(1)
    depsgraph = bpy.context.evaluated_depsgraph_get()

    # Les os des bras qui portent le maillage, et leurs ascendants. Les
    # controleurs de la cinematique inverse et l'os de la camera restent dans le
    # pack : leur effet est deja dans les poses recopiees.
    groups = {group.name for group in arms_mesh.vertex_groups}
    keep_arms = set()
    for bone in arms.data.bones:
        if bone.name in groups and bone.use_deform:
            walker = bone
            while walker is not None:
                keep_arms.add(walker.name)
                walker = walker.parent
    keep_rifle = {bone.name for bone in rifle.data.bones}
    assert not keep_arms & keep_rifle, 'des os portent le meme nom dans les deux squelettes'

    parents = {'origin': None}
    source = {}
    for name in keep_arms:
        parent = arms.data.bones[name].parent
        parents[name] = parent.name if parent is not None and parent.name in keep_arms else 'origin'
        source[name] = arms
    for name in keep_rifle:
        parent = rifle.data.bones[name].parent
        parents[name] = parent.name if parent is not None else 'origin'
        source[name] = rifle

    # Au repos, dans le repere du moteur.
    rest = {'origin': Matrix.Identity(4)}
    for name, obj in source.items():
        evaluated = obj.evaluated_get(depsgraph)
        rest[name] = engine(evaluated.matrix_world @ obj.data.bones[name].matrix_local)

    arms_rest = rest_mesh(arms_mesh, depsgraph)
    rifle_rest = rest_mesh(rifle_mesh, depsgraph)
    for mesh in (arms_rest, rifle_rest):
        mesh.transform(Matrix.Scale(INCH_PER_CM, 4))

    # Les trois os du moteur, fixes sur le corps du fusil.
    rear = rest['RearSight'].translation
    front = rest['FrontSight'].translation
    muzzle, forward = muzzle_and_axis(rifle_rest, rear, front)
    barrel = frame_matrix(muzzle, forward)
    eject = frame_matrix(rest['EjectionCover'].translation, forward)
    for name, matrix in (('barrel', barrel), ('flash', barrel), ('eject', eject)):
        rest[name] = matrix
        parents[name] = 'Main'

    order = ordered(list(parents), parents)

    # Le squelette unique.
    data = bpy.data.armatures.new(OUTPUT_NAME)
    armature = bpy.data.objects.new(OUTPUT_NAME, data)
    scene.collection.objects.link(armature)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    for name in order:
        bone = data.edit_bones.new(name)
        bone.head = (0.0, 0.0, 0.0)
        bone.tail = (0.0, 1.0, 0.0)
        bone.matrix = rest[name]
        if parents[name] is not None:
            bone.parent = data.edit_bones[parents[name]]
            bone.use_connect = False
    bpy.ops.object.mode_set(mode='OBJECT')

    meshes = []
    for source_mesh, mesh in ((arms_mesh, arms_rest), (rifle_mesh, rifle_rest)):
        for index, material in enumerate(mesh.materials):
            if material is None:
                continue
            target = MATERIALS[material.name]
            mesh.materials[index] = bpy.data.materials.get(target) or bpy.data.materials.new(target)
        obj = bpy.data.objects.new(f'{OUTPUT_NAME}_{source_mesh.name}', mesh)
        scene.collection.objects.link(obj)
        # Les noms des groupes de sommets suivent le maillage depuis Blender 3.
        missing = [g for g in (vg.name for vg in obj.vertex_groups) if g not in parents]
        if missing:
            print(f'groupes sans os : {missing}')
        obj.parent = armature
        modifier = obj.modifiers.new('armature', 'ARMATURE')
        modifier.object = armature
        meshes.append(obj)

    # L'eclat : un carre face a l'oeil au bout du canon, porte par l'os du meme
    # nom. Sa matiere ne l'allume que quelques centiemes de seconde apres
    # chaque tir, et le tourne au hasard d'un coup a l'autre.
    flash_mesh = bpy.data.meshes.new('flash')
    half = FLASH_SIZE / 2
    # Un pouce devant la bouche : dans le canon, il serait masque.
    corners = [(1.0, -half, -half), (1.0, half, -half), (1.0, half, half), (1.0, -half, half)]
    flash_mesh.from_pydata([rest['flash'] @ Vector(c) for c in corners], [], [(0, 1, 2, 3)])
    uv = flash_mesh.uv_layers.new(name='UVMap')
    for loop, coords in zip(flash_mesh.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[loop.index].uv = coords
    flash_mesh.materials.append(bpy.data.materials.get(FLASH_MATERIAL) or bpy.data.materials.new(FLASH_MATERIAL))
    flash = bpy.data.objects.new(f'{OUTPUT_NAME}_flash', flash_mesh)
    scene.collection.objects.link(flash)
    group = flash.vertex_groups.new(name='flash')
    group.add(range(4), 1.0, 'REPLACE')
    flash.parent = armature
    modifier = flash.modifiers.new('armature', 'ARMATURE')
    modifier.object = armature
    meshes.append(flash)

    # Les animations : chaque image rejouee dans le pack, recopiee os par os.
    armature.animation_data_create()
    local_rest = {}
    for name in order:
        parent = parents[name]
        local_rest[name] = rest[name] if parent is None else rest[parent].inverted() @ rest[name]

    for anim, arms_action, rifle_action in ANIMS:
        set_actions(arms, rifle, arms_action, rifle_action)
        last = max(action_end(arms_action), action_end(rifle_action))
        action = bpy.data.actions.new(anim)
        armature.animation_data.action = action
        for frame in range(1, last + 1):
            scene.frame_set(frame)
            depsgraph = bpy.context.evaluated_depsgraph_get()
            evaluated = {obj: obj.evaluated_get(depsgraph) for obj in (arms, rifle)}
            pose = {'origin': Matrix.Identity(4)}
            for name in order:
                parent = parents[name]
                if name in source:
                    obj = evaluated[source[name]]
                    pose[name] = engine(obj.matrix_world @ obj.pose.bones[name].matrix)
                elif parent is not None:
                    # Os du moteur : ils suivent leur parent sans bouger.
                    pose[name] = pose[parent] @ local_rest[name]
                parent_pose = Matrix.Identity(4) if parent is None else pose[parent]
                basis = local_rest[name].inverted() @ parent_pose.inverted() @ pose[name]
                if name == 'origin':
                    # Immobile. Ses pistes, l'exporteur les ecrit quand meme ;
                    # le fichier est retouche ensuite (voir root_scale_only).
                    continue
                bone = armature.pose.bones[name]
                bone.matrix_basis = basis
                for path in ('location', 'rotation_quaternion', 'scale'):
                    bone.keyframe_insert(path, frame=frame, group=name)
        track = armature.animation_data.nla_tracks.new()
        track.name = anim
        track.strips.new(anim, 1, action)
        armature.animation_data.action = None
        print(f'animation {anim} : {last} images ({arms_action} + {rifle_action})')

    # Les actions du pack s'appliqueraient aussi a notre squelette, les noms
    # d'os etant les memes : l'exporteur les emporterait. Elles ont servi.
    ours = {anim for anim, _, _ in ANIMS}
    for action in list(bpy.data.actions):
        if action.name not in ours:
            bpy.data.actions.remove(action)

    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj == armature or obj in meshes)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.export_scene.gltf(
        filepath=out,
        export_format='GLB',
        use_selection=True,
        export_yup=True,
        export_apply=True,
        export_materials='EXPORT',
        export_image_format='NONE',
        export_skins=True,
        export_def_bones=False,
        export_leaf_bone=False,
        export_animations=True,
        export_animation_mode='ACTIONS',
        export_force_sampling=True,
        export_optimize_animation_size=False,
        export_anim_slide_to_zero=True,
        export_reset_pose_bones=True,
        export_rest_position_armature=True,
        export_anim_single_armature=True,
    )
    root_scale_only(out)
    print(f'{out} : {len(order)} os, {len(ANIMS)} animations')


def root_scale_only(path):
    """
    Ne laisse a l'os racine que sa piste d'echelle.

    Le chargeur du moteur (renderer/Model_gltf.cpp) a deux exigences qui se
    contrarient. Il ne rattache une animation a un squelette que si elle anime
    l'os racine. Mais si cet os a une piste de rotation ou de translation, il
    le croit porteur du repere de l'armature et convertit tous les os par un
    autre chemin, qui double leurs rotations : le fusil sortait retourne, le
    chargeur en l'air. Une piste d'echelle suffit a la premiere exigence sans
    declencher le second chemin.
    """
    import json
    import struct

    with open(path, 'rb') as glb:
        data = glb.read()
    json_length, = struct.unpack_from('<I', data, 12)
    document = json.loads(data[20:20 + json_length])
    rest = data[20 + json_length:]

    root = document['skins'][0]['joints'][0]
    for animation in document.get('animations', []):
        keep = [c for c in animation['channels']
                if c['target']['node'] != root or c['target']['path'] == 'scale']
        used = sorted({c['sampler'] for c in keep})
        remap = {old: new for new, old in enumerate(used)}
        animation['samplers'] = [animation['samplers'][i] for i in used]
        for channel in keep:
            channel['sampler'] = remap[channel['sampler']]
        animation['channels'] = keep

    text = json.dumps(document, separators=(',', ':')).encode()
    text += b' ' * (-len(text) % 4)
    header = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(text) + len(rest))
    with open(path, 'wb') as glb:
        glb.write(header + struct.pack('<II', len(text), 0x4E4F534A) + text + rest)


main()
