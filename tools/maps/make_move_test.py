#!/usr/bin/env python3
"""
L'aire d'essai du deplacement : move_test.

Une grande salle vide, 65 m de cote, pour que le banc d'essai
(unholy_moveTest) coure, saute et tourne sans jamais toucher un mur : six
secondes et demie de course font 35 m. Le long du mur ouest, de quoi eprouver
le reste a la main :

- un escalier aux cotes de l'immeuble, 8 marches de 18 cm, et son palier a
  1,42 m, dont on saute pour la chute ;
- trois blocs de 25, 46 et 66 cm : une marche, un saut, trop haut ;
- un passage de 1,42 m sous plafond, qu'on ne franchit qu'accroupi ;
- deux pentes, 30 et 50 degres : la premiere se monte, la seconde non.

Le sol porte la trame d'un metre : on y lit les distances.
"""

import math
from pathlib import Path

from mapkit import MapFile, box, ramp, vec

ROOT = Path(__file__).resolve().parents[2]

FLOOR = 'textures/unholy/dev/floor'
WALL = 'textures/unholy/dev/wall'
CEILING = 'textures/unholy/dev/ceiling'
BLOCK = 'textures/unholy/dev/block'

HALF = 1280         # la salle va de -HALF a +HALF, 65 m
HEIGHT = 256        # 6,5 m sous plafond
THICK = 16

# Escalier : les cotes d'une cage d'immeuble.
RISER = 7           # 18 cm
TREAD = 11          # 28 cm
STEPS = 8
STAIR_WIDTH = 48

# Les installations, alignees pres du mur ouest.
FEATURES_X = -HALF + 80


def main():
    world = MapFile(def_player='player_unholy_military')
    w = world.world

    outer = HALF + THICK
    w.add(box((-outer, -outer, -THICK), (outer, outer, 0), FLOOR))
    w.add(box((-outer, -outer, HEIGHT), (outer, outer, HEIGHT + THICK), CEILING))
    w.add(box((-outer, -outer, 0), (-HALF, outer, HEIGHT), WALL))
    w.add(box((HALF, -outer, 0), (outer, outer, HEIGHT), WALL))
    w.add(box((-HALF, -outer, 0), (HALF, -HALF, HEIGHT), WALL))
    w.add(box((-HALF, HALF, 0), (HALF, outer, HEIGHT), WALL))

    # L'escalier monte vers le nord, puis un palier dont le bord nord tombe.
    x0, y0 = FEATURES_X, -520
    for step in range(STEPS):
        w.add(box((x0, y0 + step * TREAD, 0),
                  (x0 + STAIR_WIDTH, y0 + (step + 1) * TREAD, (step + 1) * RISER), BLOCK))
    top = STEPS * RISER
    landing_y = y0 + STEPS * TREAD
    w.add(box((x0, landing_y, 0), (x0 + 96, landing_y + 96, top), BLOCK))

    # Trois blocs : une marche, un saut, trop haut.
    for index, height in enumerate((10, 18, 26)):
        bx = FEATURES_X + index * 112
        w.add(box((bx, -200, 0), (bx + 48, -152, height), BLOCK))

    # Le passage bas : deux murets et une dalle, 1,22 m de large, 1,42 m sous
    # la dalle. Debout, le militaire mesure 1,83 m ; accroupi, 1,22 m.
    tx, ty, length = FEATURES_X, 120, 128
    low = 56
    w.add(box((tx - 8, ty, 0), (tx, ty + length, low), WALL))
    w.add(box((tx + 48, ty, 0), (tx + 56, ty + length, low), WALL))
    w.add(box((tx - 8, ty, low), (tx + 56, ty + length, low + 16), BLOCK))

    # Deux pentes de 1,22 m de haut.
    for index, degrees in enumerate((30, 50)):
        rise = 48
        run = rise / math.tan(math.radians(degrees))
        ry = 440 + index * 120
        w.add(ramp(FEATURES_X, FEATURES_X + run, ry, ry + 64, 0, rise, BLOCK))

    # Neuf plafonniers en carre : une lumiere franche partout, les mesures
    # n'ont pas besoin d'ambiance.
    spacing = 2 * HALF / 3
    for ix in (-1, 0, 1):
        for iy in (-1, 0, 1):
            world.entity('light', name=f'light_{ix + 1}{iy + 1}',
                         origin=vec(ix * spacing, iy * spacing, HEIGHT - 16),
                         light_radius=vec(spacing * 0.75, spacing * 0.75, 280), _color=vec(0.9, 0.9, 0.88))

    # Le depart des essais : 40 m de champ libre vers l'est, et le grand
    # cercle de l'endurance (12 m de rayon, vers le nord) passe loin des
    # installations.
    world.entity('info_player_start', name='start_military', origin=vec(-300, -600, 1), angle=0)

    out = ROOT / 'content' / 'maps' / 'move_test.map'
    brushes = world.write(out)
    print(f'{out.relative_to(ROOT)} : {brushes} brushes, {len(world.entities)} entites')


if __name__ == '__main__':
    main()
