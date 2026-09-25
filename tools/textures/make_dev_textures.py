#!/usr/bin/env python3
"""
Textures de developpement : une teinte et une trame, rien d'autre.

Elles tiennent la place des vraies matieres PBR le temps que les systemes se
valident. Les teintes sont celles que le prototype avait arretees pour
l'immeuble (docs/FEEL.md) : franchement sombres, parce que sous une lampe une
teinte moyenne remonte vite au blanc. Le sol est un peu eclairci, sans quoi la
migration room n'a pas de sol lisible avant que l'eclairage soit regle.

La trame compte un metre par repetition : un trait appuye au metre, un trait
fin tous les vingt-cinq centimetres. La carte projette l'image a raison d'une
repetition par metre, si bien qu'on lit les distances au sol.
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'content' / 'textures' / 'unholy' / 'dev'

SIZE = 512          # pixels par metre
MINOR = SIZE // 4   # un trait fin tous les vingt-cinq centimetres


def hex_color(value):
    value = value.lstrip('#')
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def shade(color, factor):
    return tuple(max(0, min(255, round(c * factor))) for c in color)


def grid(base, name):
    color = hex_color(base)
    image = Image.new('RGB', (SIZE, SIZE), color)
    draw = ImageDraw.Draw(image)
    for offset in range(MINOR, SIZE, MINOR):
        draw.line([(offset, 0), (offset, SIZE)], fill=shade(color, 0.88))
        draw.line([(0, offset), (SIZE, offset)], fill=shade(color, 0.88))
    # Le trait du metre, sur les bords de l'image : d'une repetition a la
    # suivante, il ne se dedouble pas.
    major = shade(color, 0.68)
    draw.rectangle([0, 0, 1, SIZE], fill=major)
    draw.rectangle([0, 0, SIZE, 1], fill=major)
    image.save(OUT / f'{name}.tga', compression='tga_rle')


def flat(base, name, size=64):
    Image.new('RGB', (size, size), hex_color(base)).save(OUT / f'{name}.tga', compression='tga_rle')


def door(base, name):
    """Une porte a deux panneaux, a plaquer sur un vantail entier."""
    color = hex_color(base)
    width, height = 256, 512
    image = Image.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(image)
    edge = shade(color, 0.7)
    draw.rectangle([0, 0, width - 1, height - 1], outline=edge, width=6)
    for top, bottom in ((40, 230), (270, 470)):
        draw.rectangle([36, top, width - 37, bottom], outline=edge, width=4)
    # La poignee, cote ouverture.
    draw.rectangle([width - 34, 248, width - 22, 262], fill=hex_color('#b8b0a0'))
    image.save(OUT / f'{name}.tga', compression='tga_rle')


def editor(name, rgba, size=64):
    """Image de l'editeur seulement : le jeu ne la dessine jamais."""
    Image.new('RGBA', (size, size), rgba).save(OUT / f'{name}.tga', compression='tga_rle')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    grid('#3c3a36', 'floor')        # beton du sol
    grid('#817764', 'wall')         # platre des cloisons
    grid('#6f6b63', 'ceiling')      # faux plafond
    grid('#4f5a63', 'block')        # obstacles de l'aire d'essai
    door('#594632', 'door')         # bois
    flat('#ffe2bf', 'lamp')         # verre d'un plafonnier allume
    flat('#e6f0f7', 'neon')         # tube fluorescent allume
    editor('visportal', (200, 40, 160, 110))
    print(f'{OUT.relative_to(ROOT)} : textures de developpement ecrites')


if __name__ == '__main__':
    main()
