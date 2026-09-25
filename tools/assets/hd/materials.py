"""
UNHOLY -- matieres des armes, procedurales, pour Blender (Cycles).

Chaque matiere est un Principled BSDF nourri de quelques gestes : une
variation de rugosite (aucune surface reelle n'a une rugosite unique),
l'usure des aretes (le metal nu revient la ou la main et l'etui frottent),
la salete des creux (l'occlusion), et un grain fin en relief. Tout se cuit
ensuite en textures (couleur, rugosite, metal, relief, occlusion) pour le
rendu du moteur : ces arbres ne servent qu'a les fabriquer.
"""

import bpy

PRESETS = {
    # aluminium anodise noir : boitiers, garde-main, rails, viseur
    'anodized': dict(base=(0.042, 0.042, 0.045), metallic=0.6, roughness=0.44, rough_var=0.10,
                     wear=0.55, wear_color=(0.55, 0.55, 0.57), wear_rough=0.28, cavity=0.35,
                     grain=0.025, grain_scale=1600.0),
    # aluminium anodise gris : le chargeur
    'anodized_gray': dict(base=(0.075, 0.077, 0.08), metallic=0.6, roughness=0.4, rough_var=0.08,
                          wear=0.6, wear_color=(0.6, 0.6, 0.62), wear_rough=0.28, cavity=0.35,
                          grain=0.02, grain_scale=1600.0),
    # acier phosphate : canon, cache-flamme, goupilles, culasse
    'steel': dict(base=(0.055, 0.056, 0.054), metallic=1.0, roughness=0.52, rough_var=0.12,
                  wear=0.45, wear_color=(0.50, 0.50, 0.49), wear_rough=0.25, cavity=0.40,
                  grain=0.03, grain_scale=1200.0),
    # polymere : poignee, crosse, chargeur, lampe
    'polymer': dict(base=(0.026, 0.026, 0.026), metallic=0.0, roughness=0.62, rough_var=0.08,
                    wear=0.18, wear_color=(0.075, 0.075, 0.075), wear_rough=0.5, cavity=0.30,
                    grain=0.12, grain_scale=1400.0),
    # polymere granite (grip) : le meme, avec une texture de preheension marquee
    'polymer_stipple': dict(base=(0.024, 0.024, 0.024), metallic=0.0, roughness=0.75, rough_var=0.06,
                            wear=0.12, wear_color=(0.07, 0.07, 0.07), wear_rough=0.55, cavity=0.30,
                            grain=0.45, grain_scale=260.0, stipple=True),
    'rubber': dict(base=(0.022, 0.022, 0.022), metallic=0.0, roughness=0.86, rough_var=0.05,
                   wear=0.05, wear_color=(0.05, 0.05, 0.05), wear_rough=0.8, cavity=0.25,
                   grain=0.20, grain_scale=600.0),
    # le gant : synthetique noir, grain de cuir, use aux jointures et au creux de la paume
    'glove': dict(base=(0.035, 0.034, 0.032), metallic=0.0, roughness=0.6, rough_var=0.1,
                  wear=0.2, wear_color=(0.1, 0.098, 0.092), wear_rough=0.7, cavity=0.4,
                  grain=0.18, grain_scale=700.0),
    # la manche : toile vert armee, delavee aux plis
    'sleeve': dict(base=(0.052, 0.062, 0.042), metallic=0.0, roughness=0.88, rough_var=0.06,
                   wear=0.12, wear_color=(0.11, 0.12, 0.09), wear_rough=0.92, cavity=0.55,
                   grain=0.3, grain_scale=2200.0),
    'brass': dict(base=(0.78, 0.56, 0.26), metallic=1.0, roughness=0.30, rough_var=0.10,
                  wear=0.0, cavity=0.2, grain=0.02, grain_scale=900.0),
    'copper': dict(base=(0.78, 0.44, 0.30), metallic=1.0, roughness=0.34, rough_var=0.10,
                   wear=0.0, cavity=0.2, grain=0.02, grain_scale=900.0),
}


def _node(tree, kind, x, y, **inputs):
    node = tree.nodes.new(kind)
    node.location = (x, y)
    for key, value in inputs.items():
        node.inputs[key].default_value = value
    return node


def make(name, preset):
    """Une matiere procedurale d'apres un preset de PRESETS."""
    p = dict(PRESETS[preset])
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat['preset'] = preset
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    links = tree.links

    out = _node(tree, 'ShaderNodeOutputMaterial', 1400, 0)
    bsdf = _node(tree, 'ShaderNodeBsdfPrincipled', 1100, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    coords = _node(tree, 'ShaderNodeTexCoord', -1400, 0)

    # Variation de rugosite : un bruit large, discret.
    rough_noise = _node(tree, 'ShaderNodeTexNoise', -1100, 300, Scale=6.0, Detail=6.0, Roughness=0.6)
    rough_noise.name = 'bruit_rugosite'
    links.new(coords.outputs['Object'], rough_noise.inputs['Vector'])
    rough = _node(tree, 'ShaderNodeMapRange', -850, 300)
    rough.inputs['From Min'].default_value = 0.3
    rough.inputs['From Max'].default_value = 0.7
    rough.inputs['To Min'].default_value = p['roughness'] - p['rough_var']
    rough.inputs['To Max'].default_value = p['roughness'] + p['rough_var']
    links.new(rough_noise.outputs['Fac'], rough.inputs['Value'])

    # Aretes : l'ecart entre la normale arrondie (Bevel) et la vraie.
    bevel = _node(tree, 'ShaderNodeBevel', -1100, -200)
    bevel.samples = 8
    bevel.inputs['Radius'].default_value = 0.05
    geometry = _node(tree, 'ShaderNodeNewGeometry', -1100, -450)
    dot = _node(tree, 'ShaderNodeVectorMath', -850, -300)
    dot.operation = 'DOT_PRODUCT'
    links.new(bevel.outputs['Normal'], dot.inputs[0])
    links.new(geometry.outputs['Normal'], dot.inputs[1])
    edge = _node(tree, 'ShaderNodeMapRange', -650, -300)
    edge.name = 'arete'
    edge.inputs['From Min'].default_value = 0.985
    edge.inputs['From Max'].default_value = 0.90
    links.new(dot.outputs['Value'], edge.inputs['Value'])

    # Usure : les aretes, rongees par un bruit fin (le metal part par eclats).
    wear_noise = _node(tree, 'ShaderNodeTexNoise', -850, -550, Scale=45.0, Detail=10.0, Roughness=0.7)
    wear_noise.name = 'bruit_usure'
    links.new(coords.outputs['Object'], wear_noise.inputs['Vector'])
    wear_mul = _node(tree, 'ShaderNodeMath', -450, -400)
    wear_mul.operation = 'MULTIPLY'
    links.new(edge.outputs['Result'], wear_mul.inputs[0])
    links.new(wear_noise.outputs['Fac'], wear_mul.inputs[1])
    wear = _node(tree, 'ShaderNodeMapRange', -250, -400)
    wear.inputs['From Min'].default_value = 0.38
    wear.inputs['From Max'].default_value = 0.55
    wear.inputs['To Max'].default_value = p['wear']
    links.new(wear_mul.outputs['Value'], wear.inputs['Value'])

    # Salete des creux : occlusion locale.
    ao = _node(tree, 'ShaderNodeAmbientOcclusion', -850, 0)
    ao.name = 'occlusion'
    ao.samples = 12
    ao.only_local = True
    ao.inputs['Distance'].default_value = 0.9
    cavity = _node(tree, 'ShaderNodeMapRange', -600, 0)
    cavity.inputs['From Min'].default_value = 0.0
    cavity.inputs['From Max'].default_value = 1.0
    cavity.inputs['To Min'].default_value = 1.0 - p['cavity']
    cavity.inputs['To Max'].default_value = 1.0
    links.new(ao.outputs['AO'], cavity.inputs['Value'])

    # Couleur : la teinte, assombrie dans les creux, eclaircie aux aretes usees.
    base = _node(tree, 'ShaderNodeRGB', -600, 250)
    base.outputs[0].default_value = (*p['base'], 1.0)
    dirty = _node(tree, 'ShaderNodeMix', -300, 150)
    dirty.data_type = 'RGBA'
    dirty.blend_type = 'MULTIPLY'
    dirty.inputs['Factor'].default_value = 1.0
    links.new(base.outputs[0], dirty.inputs['A'])
    links.new(cavity.outputs['Result'], dirty.inputs['B'])
    worn = _node(tree, 'ShaderNodeMix', 0, 150)
    worn.data_type = 'RGBA'
    links.new(wear.outputs['Result'], worn.inputs['Factor'])
    links.new(dirty.outputs['Result'], worn.inputs['A'])
    worn.inputs['B'].default_value = (*p.get('wear_color', p['base']), 1.0)
    links.new(worn.outputs['Result'], bsdf.inputs['Base Color'])

    metal = _node(tree, 'ShaderNodeMix', 0, -50)
    metal.data_type = 'FLOAT'
    links.new(wear.outputs['Result'], metal.inputs['Factor'])
    metal.inputs['A'].default_value = p['metallic']
    metal.inputs['B'].default_value = 1.0 if p['wear'] > 0 and p['metallic'] > 0.2 else p['metallic']
    links.new(metal.outputs['Result'], bsdf.inputs['Metallic'])

    rough_final = _node(tree, 'ShaderNodeMix', 0, 350)
    rough_final.data_type = 'FLOAT'
    links.new(wear.outputs['Result'], rough_final.inputs['Factor'])
    links.new(rough.outputs['Result'], rough_final.inputs['A'])
    rough_final.inputs['B'].default_value = p.get('wear_rough', p['roughness'])
    links.new(rough_final.outputs['Result'], bsdf.inputs['Roughness'])

    # Relief : le grain de la surface, pose sur la normale arrondie des aretes.
    if p.get('stipple'):
        grain_tex = _node(tree, 'ShaderNodeTexVoronoi', -600, -750, Scale=p['grain_scale'])
        grain_out = grain_tex.outputs['Distance']
    else:
        grain_tex = _node(tree, 'ShaderNodeTexNoise', -600, -750, Scale=p['grain_scale'], Detail=4.0)
        grain_out = grain_tex.outputs['Fac']
    links.new(coords.outputs['Object'], grain_tex.inputs['Vector'])
    bump = _node(tree, 'ShaderNodeBump', 700, -400)
    bump.name = 'relief'
    bump.inputs['Strength'].default_value = p['grain']
    bump.inputs['Distance'].default_value = 0.02
    links.new(grain_out, bump.inputs['Height'])
    links.new(bevel.outputs['Normal'], bump.inputs['Normal'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def glass(name, tint=(0.75, 0.85, 0.8)):
    """Pour les apercus seulement : un verre transparent a peine teinte, avec son reflet.
    (Un verre qui refracte montrerait l'ambiance, pas le fond gris des apercus.)"""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*tint, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.03
    bsdf.inputs['Alpha'].default_value = 0.12
    return mat


def use_gpu():
    """Cycles sur la puce graphique (Metal), quelles que soient les preferences de Blender."""
    prefs = bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for device in prefs.devices:
            device.use = device.type == 'METAL'
    except Exception as error:  # pas de Metal : le processeur fera
        print('Cycles sans Metal :', error)
    bpy.context.scene.cycles.device = 'GPU'
