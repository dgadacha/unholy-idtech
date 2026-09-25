"""
UNHOLY -- apercus des armes modelisees, dans la scene du pack d'animations.

    blender -b FP_Arms_Rifle_01_Anims.blend --python preview.py -- <dossier des rendus> [vues...]

Retire le fusil du pack, pose le notre sur son squelette (chaque piece sur son
os), et rend des vues de studio ainsi que la vue a la premiere personne, bras
compris, dans la pose de base. L'eclairage vient d'une ambiance HDR livree
avec Blender : elle ne sert qu'a juger, jamais au jeu.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import arms as hd_arms  # noqa: E402
import materials  # noqa: E402
import rifle  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
OUT = args[0]
VIEWS = set(args[1:]) or {'droite', 'gauche', 'trois_quarts', 'arriere', 'fps', 'epaule'}
os.makedirs(OUT, exist_ok=True)

scene = bpy.context.scene
rig = bpy.data.objects['Rifle_01_Armature']
arms = bpy.data.objects['Arms_Armature']

# Le fusil du pack s'en va ; les aides a l'animation se cachent.
bpy.data.objects.remove(bpy.data.objects['ChargeHandle_Mesh'], do_unlink=True)
for obj in bpy.data.objects:
    if obj.name.startswith('Ctrl_') or obj.name == 'Cube':
        obj.hide_render = True

parts = rifle.build()
for bone, objects in parts.items():
    for obj in objects:
        obj.parent = rig
        obj.matrix_parent_inverse = Matrix.Identity(4)
        group = obj.vertex_groups.new(name=bone)
        group.add(range(len(obj.data.vertices)), 1.0, 'REPLACE')
        mod = obj.modifiers.new('armature', 'ARMATURE')
        mod.object = rig

triangles = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for objs in parts.values() for o in objs)
print(f'fusil : {triangles} triangles')

# Les bras HD a la place de ceux du pack.
pack_arms = bpy.data.objects['FPS_Arms_Mesh']
arms.data.pose_position = 'REST'
bpy.context.view_layer.update()
arm_obj = hd_arms.build(pack_arms, arms, materials.make('unholy_manche', 'sleeve'), materials.make('unholy_gant', 'glove'))
arm_obj.matrix_parent_inverse = arms.matrix_world.inverted()
arms.data.pose_position = 'POSE'
pack_arms.hide_render = True
# La main gauche a la hauteur du garde-main HD (voir rifle.GRIP_DROP).
rig.animation_data.action = bpy.data.actions['Rifle_BasePose']
scene.frame_set(1)
hd_arms.drop_left_hand(arms, rig, rifle.GRIP_DROP)

# Rendu : Cycles, debruite, ambiance de Blender.
scene.render.engine = 'CYCLES'
materials.use_gpu()
scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Punchy'
world = bpy.data.worlds.new('apercu')
scene.world = world
world.use_nodes = True
nodes = world.node_tree.nodes
links = world.node_tree.links
# Les reflets viennent d'une ambiance de studio ; le fond, lui, reste un gris neutre.
env = nodes.new('ShaderNodeTexEnvironment')
datafiles = os.path.join(os.path.dirname(bpy.app.binary_path), '..', 'Resources', bpy.app.version_string[:3], 'datafiles')
env.image = bpy.data.images.load(os.path.join(datafiles, 'studiolights', 'world', 'studio.exr'))
gray = nodes.new('ShaderNodeBackground')
gray.inputs['Color'].default_value = (0.16, 0.16, 0.17, 1.0)
gray.inputs['Strength'].default_value = 1.0
lit = nodes['Background']
links.new(env.outputs['Color'], lit.inputs['Color'])
lit.inputs['Strength'].default_value = 1.6
path = nodes.new('ShaderNodeLightPath')
mix = nodes.new('ShaderNodeMixShader')
links.new(path.outputs['Is Camera Ray'], mix.inputs['Fac'])
links.new(lit.outputs['Background'], mix.inputs[1])
links.new(gray.outputs['Background'], mix.inputs[2])
links.new(mix.outputs['Shader'], nodes['World Output'].inputs['Surface'])

key_data = bpy.data.lights.new('cle', 'AREA')
key_data.energy = 9000.0
key_data.size = 60.0
key = bpy.data.objects.new('cle', key_data)
scene.collection.objects.link(key)
rim_data = bpy.data.lights.new('contre', 'AREA')
rim_data.energy = 5000.0
rim_data.size = 40.0
rim = bpy.data.objects.new('contre', rim_data)
scene.collection.objects.link(rim)

cam_data = bpy.data.cameras.new('apercu')
cam = bpy.data.objects.new('apercu', cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def aim(obj, position, target):
    direction = (Vector(target) - Vector(position)).normalized()
    obj.matrix_world = Matrix.Translation(position) @ direction.to_track_quat('-Z', 'Y').to_matrix().to_4x4()


def look(eye, target, up=(0, 0, 1)):
    """Place la camera, en coordonnees du fusil, le haut du fusil en haut de l'image,
    la lumiere principale au-dessus et de cote, le contre-jour derriere."""
    M = rig.matrix_world
    eye_w, target_w = M @ Vector(eye), M @ Vector(target)
    up_w = (M.to_3x3() @ Vector(up)).normalized()
    forward = (target_w - eye_w).normalized()
    right = forward.cross(up_w).normalized()
    true_up = right.cross(forward)
    rot = Matrix((right, true_up, -forward)).transposed()
    cam.matrix_world = Matrix.Translation(eye_w) @ rot.to_4x4()
    distance = max((target_w - eye_w).length, 80.0)
    aim(key, target_w - forward * distance * 0.8 + true_up * distance * 0.9 - right * distance * 0.5, target_w)
    aim(rim, target_w + forward * distance * 0.9 + true_up * distance * 0.6 + right * distance * 0.4, target_w)


def render(name, width=1600, height=900):
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.filepath = os.path.join(OUT, f'{name}.png')
    bpy.ops.render.render(write_still=True)


def studio_pose():
    rig.data.pose_position = 'REST'
    arm_obj.hide_render = True


def play(action_arms, action_rifle, frame=1):
    rig.data.pose_position = 'POSE'
    arm_obj.hide_render = False
    for obj, name in ((arms, action_arms), (rig, action_rifle)):
        if obj.animation_data is None:
            obj.animation_data_create()
        obj.animation_data.action = bpy.data.actions[name]
    scene.frame_set(frame)


studio = {
    'droite': ((14, -160, 8), (14, 0, 8), 'ORTHO', 96),
    'gauche': ((14, 160, 8), (14, 0, 8), 'ORTHO', 96),
    'trois_quarts': ((60, 80, 36), (22, 0, 14), 'PERSP', 38),
    'arriere': ((-14, 42, 32), (24, 0, 19), 'PERSP', 45),
    'viseur': ((6, 26, 30), (16, 0, 23), 'PERSP', 40),
    'lampe': ((68, 30, 26), (54, 2, 18), 'PERSP', 40),
    'dessous': ((20, -70, -44), (20, 0, 8), 'PERSP', 38),
}
for name, (eye, target, kind, value) in studio.items():
    if name not in VIEWS:
        continue
    studio_pose()
    cam_data.type = kind
    if kind == 'ORTHO':
        cam_data.ortho_scale = value
    else:
        cam_data.lens = value
    look(eye, target)
    render(name)

# La vue de la photo de reference : profil droit, orthographique, meme echelle et meme
# cadrage que l'image (voir trace.py), pour les comparer pixel a pixel.
if 'reference' in VIEWS:
    studio_pose()
    width, height = 1816, 714
    cx, cz = rifle.P(width / 2, height / 2)
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = width * rifle.REG['scale']
    cam_data.sensor_fit = 'HORIZONTAL'
    look((cx, -200, cz), (cx, 0, cz))
    scene.render.film_transparent = True
    render('reference', width, height)
    scene.render.film_transparent = False
    cam_data.sensor_fit = 'AUTO'

# La vue du joueur : la camera du pack (a l'origine, vers +X, 90 degres de champ).
cam_data.type = 'PERSP'
cam_data.sensor_fit = 'HORIZONTAL'
cam_data.angle = math.radians(90)
for name, arms_action, rifle_action in (('fps', 'Arms_BasePose', 'Rifle_Breathing'), ('epaule', 'Arms_AimPose', 'Rifle_AimPose')):
    if name not in VIEWS:
        continue
    play(arms_action, rifle_action)
    cam.matrix_world = Matrix(((0, 0, -1), (-1, 0, 0), (0, 1, 0))).to_4x4()
    aim(key, Vector((-20, 60, 70)), Vector((40, -8, -15)))
    aim(rim, Vector((120, -40, 30)), Vector((30, -8, -15)))
    render(name, 1280, 720)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'fusil_hd.blend'), compress=True)
print('apercus dans', OUT)
