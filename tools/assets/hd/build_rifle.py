"""
UNHOLY -- le fusil HD : construction, depliage, cuisson des textures.

    blender -b FP_Arms_Rifle_01_Anims.blend --python build_rifle.py -- <fusil_hd.blend> <dossier des textures> [taille]

Construit le fusil (rifle.py) sur le squelette du fusil du pack, deplie ses
pieces en deux atlas (les metaux, les polymeres), cuit leurs textures, puis ne
laisse sur les pieces que quatre matieres, celles que le moteur connait :

  models/unholy/fusil_metal       aluminium anodise (noir, gris), acier
  models/unholy/fusil_polymere    polymere, caoutchouc, laiton de la cartouche
  models/unholy/fusil_verre       le verre de la lampe
  models/unholy/bras              les manches et les gants (arms.py)

La cuisson ne fait passer a Cycles que ce qui demande des rayons, une fois : le
masque des aretes, celui des creux, les deux bruits, la matiere de chaque texel
et le relief. La couleur, la rugosite et le metal se composent ensuite ici,
texel par texel, avec les reglages de chaque matiere (materials.PRESETS) : on
change une teinte sans recuire.

Les textures sortent en PNG : <atlas>_basecolor, <atlas>_normal, <atlas>_rmao
(rugosite, metal, occlusion, dans les canaux rouge, vert, bleu : ce que lit le
rendu du moteur). Le .blend garde les pieces, pretes pour la conversion
(retro_rifle.py --fusil-hd).
"""

import os
import sys

import bpy
import numpy as np
from mathutils import Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import arms  # noqa: E402
import materials  # noqa: E402
import rifle  # noqa: E402

ATLASES = {
    'fusil_metal': ('unholy_anodise', 'unholy_anodise_gris', 'unholy_acier'),
    'fusil_polymere': ('unholy_polymere', 'unholy_polymere_grain', 'unholy_caoutchouc', 'unholy_laiton', 'unholy_cuivre'),
    'bras': ('unholy_manche', 'unholy_gant'),
}
PLAIN = {'unholy_verre': 'models/unholy/fusil_verre'}


def parts_on_rig(rig):
    parts = rifle.build()
    objects = []
    for bone, objs in parts.items():
        for obj in objs:
            obj.parent = rig
            obj.matrix_parent_inverse = Matrix.Identity(4)
            group = obj.vertex_groups.new(name=bone)
            group.add(range(len(obj.data.vertices)), 1.0, 'REPLACE')
            mod = obj.modifiers.new('armature', 'ARMATURE')
            mod.object = rig
            objects.append(obj)
    return objects


def select_only(objects):
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


def select_faces(obj, material_names):
    """Selectionne les faces de ces matieres, leurs aretes et leurs sommets, et rien d'autre.

    L'operateur de selection par matiere ne suit que la matiere active de l'objet du
    contexte : les faces des autres matieres de l'atlas restaient hors du depliage, avec
    les UV par defaut d'une couche neuve (tout le carre), et chacune couvrait l'atlas
    entier a la cuisson. Tout le polymere sortait en cuivre, tout le metal en acier.
    """
    me = obj.data
    slots = [i for i, m in enumerate(me.materials) if m and m.name in material_names]
    material = np.zeros(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get('material_index', material)
    faces = np.isin(material, slots)
    totals = np.zeros(len(me.polygons), dtype=np.int32)
    me.polygons.foreach_get('loop_total', totals)
    loop_face = np.repeat(np.arange(len(me.polygons)), totals)
    loop_vert = np.zeros(len(me.loops), dtype=np.int32)
    loop_edge = np.zeros(len(me.loops), dtype=np.int32)
    me.loops.foreach_get('vertex_index', loop_vert)
    me.loops.foreach_get('edge_index', loop_edge)
    inside = faces[loop_face]
    verts = np.zeros(len(me.vertices), dtype=bool)
    edges = np.zeros(len(me.edges), dtype=bool)
    verts[loop_vert[inside]] = True
    edges[loop_edge[inside]] = True
    me.vertices.foreach_set('select', verts)
    me.edges.foreach_set('select', edges)
    me.polygons.foreach_set('select', faces)
    me.update()
    return int(faces.sum())


def unwrap(objects, material_names):
    """Deplie dans un meme atlas toutes les faces qui portent ces matieres."""
    users = [o for o in objects if any(m and m.name in material_names for m in o.data.materials)]
    for obj in users:
        if not obj.data.uv_layers:
            obj.data.uv_layers.new(name='UVMap')
        select_faces(obj, material_names)
    select_only(users)
    bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
    with bpy.context.temp_override(active_object=users[0], selected_editable_objects=users, selected_objects=users):
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
        bpy.ops.object.mode_set(mode='OBJECT')
    return users


def target(name, size):
    image = bpy.data.images.new(name, size, size, alpha=False, float_buffer=True)
    image.colorspace_settings.name = 'Non-Color'
    return image


def aim_bake_at(material_names, image, dummy):
    """Chaque matiere de l'atlas cuit dans image ; toutes les autres, dans une image jetable."""
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        nodes = mat.node_tree.nodes
        node = nodes.get('cible_cuisson') or nodes.new('ShaderNodeTexImage')
        node.name = 'cible_cuisson'
        node.image = image if mat.name in material_names else dummy
        nodes.active = node


def show(material_names, signal):
    """Fait briller le signal voulu (un noeud nomme, ou l'identifiant de la matiere), le
    temps de le cuire ; signal None rend a chaque matiere son BSDF."""
    for index, name in enumerate(material_names):
        tree = bpy.data.materials[name].node_tree
        out = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL')
        bsdf = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
        if signal is None:
            tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
            continue
        emit = tree.nodes.get('emission_cuisson') or tree.nodes.new('ShaderNodeEmission')
        emit.name = 'emission_cuisson'
        for link in list(emit.inputs['Color'].links):
            tree.links.remove(link)
        if signal == 'id':
            v = (index + 1) / 16.0
            emit.inputs['Color'].default_value = (v, v, v, 1.0)
        elif signal == 'relief':
            # un diffus qui ne porte que le relief : Cycles n'evalue rien d'autre
            diffuse = tree.nodes.get('diffus_cuisson') or tree.nodes.new('ShaderNodeBsdfDiffuse')
            diffuse.name = 'diffus_cuisson'
            tree.links.new(tree.nodes['relief'].outputs['Normal'], diffuse.inputs['Normal'])
            tree.links.new(diffuse.outputs['BSDF'], out.inputs['Surface'])
            continue
        else:
            node = tree.nodes[signal]
            output = node.outputs['Result'] if 'Result' in node.outputs else node.outputs[0]
            if signal == 'occlusion':
                output = node.outputs['AO']
            tree.links.new(output, emit.inputs['Color'])
        tree.links.new(emit.outputs['Emission'], out.inputs['Surface'])


def bake(kind, users, samples, **kwargs):
    bpy.context.scene.cycles.samples = samples
    select_only(users)
    with bpy.context.temp_override(active_object=users[0], selected_editable_objects=users, selected_objects=users):
        bpy.ops.object.bake(type=kind, margin=12, use_clear=True, **kwargs)


def pixels(image):
    return np.array(image.pixels[:], dtype=np.float32).reshape(image.size[1], image.size[0], 4)


def srgb(linear):
    linear = np.clip(linear, 0.0, 1.0)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * np.power(linear, 1 / 2.4) - 0.055)


def save_png(rgb, path):
    h, w = rgb.shape[:2]
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[..., :3] = np.clip(rgb, 0.0, 1.0)
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    img.pixels = rgba.ravel()
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def compose(masks, names):
    """La couleur, la rugosite et le metal, texel par texel : la meme recette que les
    arbres de materials.make, appliquee aux masques cuits."""
    ident = np.clip(np.rint(masks['id'][..., 0] * 16.0) - 1, 0, len(names) - 1).astype(int)
    edge, wear_noise = masks['arete'][..., 0], masks['bruit_usure'][..., 0]
    rough_noise, ao = masks['bruit_rugosite'][..., 0], masks['occlusion'][..., 0]
    h, w = ident.shape
    color = np.zeros((h, w, 3), dtype=np.float32)
    rough = np.zeros((h, w), dtype=np.float32)
    metal = np.zeros((h, w), dtype=np.float32)
    for i, name in enumerate(names):
        p = materials.PRESETS[bpy.data.materials[name]['preset']]
        sel = ident == i
        cavity = (1.0 - p['cavity']) + p['cavity'] * ao[sel]
        wear = np.clip((edge[sel] * wear_noise[sel] - 0.38) / (0.55 - 0.38), 0.0, 1.0) * p['wear']
        base = np.asarray(p['base'], dtype=np.float32)[None, :] * cavity[:, None]
        worn = np.asarray(p.get('wear_color', p['base']), dtype=np.float32)[None, :]
        color[sel] = base * (1.0 - wear[:, None]) + worn * wear[:, None]
        r = p['roughness'] + (np.clip((rough_noise[sel] - 0.3) / 0.4, 0.0, 1.0) * 2.0 - 1.0) * p['rough_var']
        rough[sel] = r * (1.0 - wear) + p.get('wear_rough', p['roughness']) * wear
        bare = 1.0 if p['wear'] > 0 and p['metallic'] > 0.2 else p['metallic']
        metal[sel] = p['metallic'] * (1.0 - wear) + bare * wear
    return color, rough, metal, ao


def write_flat(tex_dir, atlas, names):
    """Des textures de 8 pixels, a la teinte, la rugosite et au metal de la premiere
    matiere de l'atlas : rien que la forme, en attendant la cuisson."""
    p = materials.PRESETS[bpy.data.materials[names[0]]['preset']]
    flat = lambda value: np.tile(np.asarray(value, dtype=np.float32), (8, 8, 1))
    save_png(srgb(flat(p['base'])), os.path.join(tex_dir, f'{atlas}_basecolor.png'))
    save_png(flat((0.5, 0.5, 1.0)), os.path.join(tex_dir, f'{atlas}_normal.png'))
    save_png(flat((p['roughness'], p['metallic'], 1.0)), os.path.join(tex_dir, f'{atlas}_rmao.png'))
    print(f'  {atlas} : textures unies')


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    quick = '--sans-cuisson' in args
    args = [a for a in args if a != '--sans-cuisson']
    out_blend, tex_dir = args[0], args[1]
    size = int(args[2]) if len(args) > 2 else 2048
    os.makedirs(tex_dir, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    materials.use_gpu()
    rig = bpy.data.objects['Rifle_01_Armature']
    rig.data.pose_position = 'REST'
    bpy.data.objects.remove(bpy.data.objects['ChargeHandle_Mesh'], do_unlink=True)
    objects = parts_on_rig(rig)
    print(f'fusil : {sum(len(o.data.polygons) for o in objects)} faces, {len(objects)} pieces')
    arms_rig = bpy.data.objects['Arms_Armature']
    arms_rig.data.pose_position = 'REST'
    sleeve = materials.make('unholy_manche', 'sleeve')
    glove = materials.make('unholy_gant', 'glove')
    arm_obj = arms.build(bpy.data.objects['FPS_Arms_Mesh'], arms_rig, sleeve, glove)
    arm_obj.matrix_parent_inverse = arms_rig.matrix_world.inverted()
    dummy = target('jetable', 16)

    for atlas, names in ATLASES.items():
        if quick:
            # Pour juger la forme dans le jeu sans attendre la cuisson : des textures unies.
            write_flat(tex_dir, atlas, names)
            continue
        users = unwrap(objects + [arm_obj], set(names))
        print(f'{atlas} : {len(users)} pieces depliees')
        masks = {}
        for signal, samples in (('id', 1), ('arete', 16), ('bruit_usure', 4), ('bruit_rugosite', 4), ('occlusion', 32)):
            image = target(f'{atlas}_{signal}', size)
            aim_bake_at(set(names), image, dummy)
            show(names, signal)
            bake('EMIT', users, samples)
            masks[signal] = pixels(image)
            print(f'  masque {signal} cuit')
        image = target(f'{atlas}_normal', size)
        aim_bake_at(set(names), image, dummy)
        show(names, 'relief')
        bake('NORMAL', users, 16, normal_space='TANGENT')
        normal = pixels(image)[..., :3]
        show(names, None)
        print('  relief cuit')

        color, rough, metal, ao = compose(masks, names)
        # Les images de Blender se lisent du bas vers le haut ; les PNG s'ecrivent tels quels.
        save_png(srgb(color), os.path.join(tex_dir, f'{atlas}_basecolor.png'))
        save_png(normal, os.path.join(tex_dir, f'{atlas}_normal.png'))
        save_png(np.stack((rough, metal, ao), axis=-1), os.path.join(tex_dir, f'{atlas}_rmao.png'))
        print(f'  {atlas} : textures ecrites')

    # Les matieres du moteur : une par atlas, et les deux qui ne se cuisent pas.
    engine_materials = {}
    for atlas, names in ATLASES.items():
        mat = bpy.data.materials.new(f'models/unholy/{atlas}')
        for name in names:
            engine_materials[name] = mat
    for name, engine_name in PLAIN.items():
        engine_materials[name] = bpy.data.materials.new(engine_name)
    for obj in objects + [arm_obj]:
        for index, mat in enumerate(obj.data.materials):
            if mat is not None and mat.name in engine_materials:
                obj.data.materials[index] = engine_materials[mat.name]

    for name, members in (('fusil_hd', objects), ('bras_hd', [arm_obj])):
        collection = bpy.data.collections.new(name)
        scene.collection.children.link(collection)
        for obj in members:
            for c in obj.users_collection:
                c.objects.unlink(obj)
            collection.objects.link(obj)
    bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=True)
    print('fusil HD enregistre dans', out_blend)


main()
