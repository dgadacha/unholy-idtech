#!/usr/bin/env python3
"""
Fabrique une police au format d'id Tech 4 BFG a partir d'un fichier TrueType.

Le moteur lit `newfonts/<Nom>/48.dat` et l'image `48.tga` qui l'accompagne.
Le format se lit entierement dans `renderer/Font.cpp`, `idFont::LoadFont` :

  en-tete, gros-boutiste
    uint32  magique : 42 | 'i' << 24 | 'd' << 16 | 'f' << 8
    int16   taille en points, toujours 48
    int16   ascendant, int16 descendant
    int16   nombre de glyphes
  glyphes, petit-boutiste, dix octets chacun (un octet de bourrage apres xSkip)
    uint8 largeur, uint8 hauteur, int8 haut, int8 gauche, uint8 avance,
    uint16 s, uint16 t
  points de code, petit-boutiste, uint32 chacun, tries par ordre croissant

`haut` se compte au-dessus de la ligne de base, `s` et `t` en pixels depuis le
coin haut-gauche de l'image. L'image porte les glyphes en blanc, leur
couverture dans l'alpha.

Les polices du jeu du commerce sont hors de question : ce script sert a en
produire depuis des polices libres, dont la licence est tenue dans
docs/LICENSES.md.
"""

import argparse
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

POINT_SIZE = 48
MAGIC = 42 | (ord('i') << 24) | (ord('d') << 16) | (ord('f') << 8)

# ASCII imprimable, le supplement latin (le jeu parle francais), et la
# typographie courante : tirets, guillemets, points de suspension, euro.
EXTRA = [0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x20AC]
CODEPOINTS = list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)) + EXTRA

ATLAS_WIDTH = 1024
PADDING = 2


def build(ttf: Path, out_dir: Path) -> None:
    font = ImageFont.truetype(str(ttf), POINT_SIZE)
    ascent, descent = font.getmetrics()

    glyphs = []
    for code in CODEPOINTS:
        char = chr(code)
        # Boite du glyphe par rapport a l'origine posee sur la ligne de base.
        x0, y0, x1, y1 = font.getbbox(char, anchor='ls')
        advance = round(font.getlength(char))
        glyphs.append({
            'code': code,
            'char': char,
            'box': (x0, y0, x1, y1),
            'width': max(0, x1 - x0),
            'height': max(0, y1 - y0),
            'top': -y0,
            'left': x0,
            'advance': advance,
        })

    # Rangement par lignes, du plus haut au plus bas : peu de place perdue.
    order = sorted(glyphs, key=lambda glyph: -glyph['height'])
    x = PADDING
    y = PADDING
    row_height = 0
    for glyph in order:
        if x + glyph['width'] + PADDING > ATLAS_WIDTH:
            x = PADDING
            y += row_height + PADDING
            row_height = 0
        glyph['s'] = x
        glyph['t'] = y
        x += glyph['width'] + PADDING
        row_height = max(row_height, glyph['height'])
    used_height = y + row_height + PADDING
    atlas_height = 1
    while atlas_height < used_height:
        atlas_height *= 2

    coverage = Image.new('L', (ATLAS_WIDTH, atlas_height), 0)
    draw = ImageDraw.Draw(coverage)
    for glyph in glyphs:
        if glyph['width'] == 0 or glyph['height'] == 0:
            continue
        x0, y0, _, _ = glyph['box']
        # Le glyphe est dessine de facon que sa boite tombe sur (s, t).
        draw.text((glyph['s'] - x0, glyph['t'] - y0), glyph['char'], font=font, fill=255, anchor='ls')

    image = Image.merge('RGBA', (
        Image.new('L', coverage.size, 255),
        Image.new('L', coverage.size, 255),
        Image.new('L', coverage.size, 255),
        coverage,
    ))

    out_dir.mkdir(parents=True, exist_ok=True)
    image.save(out_dir / '48.tga')

    with open(out_dir / '48.dat', 'wb') as data:
        data.write(struct.pack('>I', MAGIC))
        data.write(struct.pack('>hhhh', POINT_SIZE, ascent, -descent, len(glyphs)))
        for glyph in glyphs:
            data.write(struct.pack(
                '<BBbbBxHH',
                min(255, glyph['width']),
                min(255, glyph['height']),
                max(-128, min(127, glyph['top'])),
                max(-128, min(127, glyph['left'])),
                min(255, glyph['advance']),
                glyph['s'],
                glyph['t'],
            ))
        for glyph in glyphs:
            data.write(struct.pack('<I', glyph['code']))

    print(f'{out_dir}: {len(glyphs)} glyphes, image {ATLAS_WIDTH}x{atlas_height}, '
          f'ascendant {ascent}, descendant {-descent}')


def build_charset(ttf: Path, out_file: Path, cell: int = 32) -> None:
    """
    Jeu de caracteres de la console : une grille de seize par seize, un octet
    par case, dans l'ordre ASCII. C'est la vieille console de Doom 3, qui
    decoupe l'image en seize colonnes et seize lignes sans autre information.
    """
    size = cell * 16
    font = ImageFont.truetype(str(ttf), int(cell * 0.8))
    coverage = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(coverage)
    for code in range(32, 256):
        col, row = code % 16, code // 16
        cx = col * cell + cell / 2
        cy = row * cell + cell / 2
        draw.text((cx, cy), chr(code), font=font, fill=255, anchor='mm')
    image = Image.merge('RGBA', (
        Image.new('L', coverage.size, 255),
        Image.new('L', coverage.size, 255),
        Image.new('L', coverage.size, 255),
        coverage,
    ))
    out_file.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_file)
    print(f'{out_file}: grille 16x16, cases de {cell} px')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    parser.add_argument('ttf', type=Path)
    parser.add_argument('out', type=Path, help='dossier newfonts/<Nom>, ou fichier .tga avec --charset')
    parser.add_argument('--charset', action='store_true', help='grille 16x16 de la console')
    args = parser.parse_args()
    if args.charset:
        build_charset(args.ttf, args.out)
    else:
        build(args.ttf, args.out)
