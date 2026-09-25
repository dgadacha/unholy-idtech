#!/usr/bin/env python3
"""
Carte de validation de la milestone 1 : une boite, une lumiere, un point
d'apparition. Rien d'autre.

Elle ne sert qu'a verifier que le moteur charge une carte faite par nous, la
compile avec son `dmap` integre, eclaire ce qu'elle contient et y pose le
joueur sans qu'il tombe au travers du sol. La migration room viendra de
TrenchBroom en milestone 2 ; celle-ci est ecrite par le code pour ne dependre
d'aucun outil.

Format : `.map` version 3, le format natif d'id Tech 4. Chaque brush est
l'intersection de demi-espaces ; chaque face est un plan `( a b c d )` tel que
`a x + b y + c z + d = 0`, normale vers l'exterieur du volume.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Interieur de la piece, en unites du moteur (un pouce chacune).
HALF_X = 256
HALF_Y = 256
HEIGHT = 192
WALL = 16

MATERIAL = 'textures/unholy/test_grid'
# Une repetition de la texture tous les 128 pouces.
TEXTURE = '( ( 0.0078125 0 0 ) ( 0 0.0078125 0 ) )'


def box(mins, maxs):
    """Un brush en forme de pave, face par face."""
    x0, y0, z0 = mins
    x1, y1, z1 = maxs
    planes = [
        (1, 0, 0, -x1),
        (-1, 0, 0, x0),
        (0, 1, 0, -y1),
        (0, -1, 0, y0),
        (0, 0, 1, -z1),
        (0, 0, -1, z0),
    ]
    lines = [' {', '  brushDef3', '  {']
    for a, b, c, d in planes:
        lines.append(f'   ( {a} {b} {c} {d} ) {TEXTURE} "{MATERIAL}" 0 0 0')
    lines += ['  }', ' }']
    return '\n'.join(lines)


def main():
    hx, hy, h, w = HALF_X, HALF_Y, HEIGHT, WALL
    brushes = [
        box((-hx - w, -hy - w, -w), (hx + w, hy + w, 0)),        # sol
        box((-hx - w, -hy - w, h), (hx + w, hy + w, h + w)),     # plafond
        box((-hx - w, -hy - w, 0), (-hx, hy + w, h)),            # mur ouest
        box((hx, -hy - w, 0), (hx + w, hy + w, h)),              # mur est
        box((-hx, -hy - w, 0), (hx, -hy, h)),                    # mur sud
        box((-hx, hy, 0), (hx, hy + w, h)),                      # mur nord
    ]

    # Le monde designe la classe du joueur : c'est la cle que le moteur lit
    # avant de retomber sur le marine de Doom 3.
    parts = ['Version 3', '// entity 0', '{', '"classname" "worldspawn"',
             '"def_player" "player_unholy_military"']
    for index, brush in enumerate(brushes):
        parts.append(f'// primitive {index}')
        parts.append(brush)
    parts.append('}')

    parts += [
        '// entity 1',
        '{',
        '"classname" "info_player_start"',
        '"name" "info_player_start_1"',
        '"origin" "-160 0 1"',
        '"angle" "0"',
        '}',
        '// entity 2',
        '{',
        '"classname" "light"',
        '"name" "light_1"',
        f'"origin" "0 0 {h - 24}"',
        '"light_radius" "320 320 220"',
        '"_color" "1 0.92 0.8"',
        '}',
    ]

    out = ROOT / 'content' / 'maps' / 'test_box.map'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(parts) + '\n')
    print(f'{out.relative_to(ROOT)} : {len(brushes)} brushes, une lumiere, un point d apparition')


if __name__ == '__main__':
    main()
