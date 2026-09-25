#!/usr/bin/env python3
"""
Retro Weapon Pack -> id Tech 4 : les textures.

    retro_textures.py <dossier RetroWeaponsPack extrait> <content/textures/retro>

Des images en pixels, faites pour etre vues sans filtrage : on les recopie
telles quelles, en TGA, sans les redimensionner. C'est la matiere qui leur
interdit le filtrage (content/materials/retro_weapons.mtr).
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

# source dans le pack -> nom dans content/textures/retro
TEXTURES = {
    'Guns/Rifle_01/Textures/Rifle_01_Albedo.png': 'rifle.tga',
    'FP_Arms/Texture/FPS_Arms_Albedo.png': 'arms.tga',
    # Une flamme en niveaux de gris sur fond noir : elle s'ajoute a l'image.
    'FX/Textures/MuzzleFlash.png': 'muzzleflash.tga',
}

# Sa lueur touche presque le bord de l'image. Le moteur la fait tourner d'un
# tir a l'autre, et le bord du carre se devinerait : elle s'eteint donc en
# douceur avant le cercle inscrit.
FADED = {'muzzleflash.tga'}
FADE_START = 0.36   # rayon, en fraction du cote, ou la lueur commence a baisser
FADE_END = 0.5      # rayon ou elle s'eteint


def fade_to_circle(image):
    pixels = np.asarray(image).astype(np.float32)
    size = pixels.shape[0]
    centers = (np.arange(size) + 0.5) / size - 0.5
    radius = np.hypot(*np.meshgrid(centers, centers))
    t = np.clip((FADE_END - radius) / (FADE_END - FADE_START), 0.0, 1.0)
    weight = t * t * (3.0 - 2.0 * t)
    return Image.fromarray((pixels * weight[..., None]).round().astype(np.uint8))


def main():
    pack = Path(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for source, name in TEXTURES.items():
        image = Image.open(pack / source).convert('RGB')
        if name in FADED:
            image = fade_to_circle(image)
        image.save(out / name, compression='tga_rle')
        print(f'{out.name}/{name} : {image.size[0]}x{image.size[1]}')


if __name__ == '__main__':
    main()
