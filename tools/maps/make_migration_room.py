#!/usr/bin/env python3
"""
La migration room : la premiere carte d'UNHOLY sur id Tech 4.

Le brief la definit mot pour mot : une piece, un couloir, un mur, un plafond,
une porte, une lumiere fixe, un neon, une zone sombre. Rien d'autre. Elle sert
a valider la fondation, et chaque milestone y ajoute ce qu'elle valide : le
fusil et la cible avec la 3, la lampe avec la 4.

    piece (6,1 x 4,9 m) --porte-- couloir (19,5 x 2,4 m) ---------+
      plafonnier                    neon            zone sombre   | recoin
                                                                  +

Les cotes sont celles d'un immeuble, un peu genereuses : 2,64 m sous
plafond, une porte de 1,12 x 2,24 m, un couloir ou deux militaires se
croisent. Le recoin au bout du couloir, a gauche, n'a aucune lumiere : c'est
la ou un possede attendrait.

Ecrite par ce script plutot qu'a la main : les cotes restent lisibles, et la
carte se regenere a l'identique. Elle s'ouvre dans TrenchBroomBFG pour etre
retouchee, mais une retouche la ferait diverger du script.
"""

from pathlib import Path

from mapkit import MapFile, box, texmat, vec

ROOT = Path(__file__).resolve().parents[2]

FLOOR = 'textures/unholy/dev/floor'
WALL = 'textures/unholy/dev/wall'
CEILING = 'textures/unholy/dev/ceiling'
DOOR = 'textures/unholy/dev/door'
LAMP = 'textures/unholy/dev/lamp'
NEON = 'textures/unholy/dev/neon'
PORTAL = 'textures/unholy/editor/visportal'
NODRAW = 'textures/unholy/editor/nodraw'

# Hauteur libre, epaisseurs.
HEIGHT = 104        # 2,64 m
SLAB = 16
THICK = 8           # une cloison, 20 cm

# La piece.
ROOM_X0, ROOM_X1 = 0, 240
ROOM_Y0, ROOM_Y1 = -96, 96

# La porte, dans le mur est de la piece.
DOOR_Y0, DOOR_Y1 = -22, 22     # 1,12 m
DOOR_TOP = 88                  # 2,24 m
DOOR_PANEL = 4                 # epaisseur du vantail, au milieu du mur

# Le couloir.
COR_X0 = ROOM_X1 + THICK
COR_X1 = COR_X0 + 768          # 19,5 m
COR_Y0, COR_Y1 = -48, 48       # 2,44 m

# Le recoin, au bout du couloir, a gauche.
NOOK_X0 = COR_X1 - 112
NOOK_Y1 = COR_Y1 + 160

# Le neon, a mi-couloir.
NEON_X = COR_X0 + 272


def main():
    world = MapFile(def_player='player_unholy_military')
    w = world.world

    x_min, x_max = ROOM_X0 - THICK, COR_X1 + THICK
    y_min, y_max = ROOM_Y0 - THICK, NOOK_Y1 + THICK

    # Sol et plafond d'un seul tenant : ce qui depasse des pieces est dehors,
    # et le compilateur l'efface.
    w.add(box((x_min, y_min, -SLAB), (x_max, y_max, 0), FLOOR))
    w.add(box((x_min, y_min, HEIGHT), (x_max, y_max, HEIGHT + SLAB), CEILING))

    def wall(x0, x1, y0, y1, z0=0, z1=HEIGHT):
        w.add(box((x0, y0, z0), (x1, y1, z1), WALL))

    # La piece.
    wall(ROOM_X0 - THICK, ROOM_X0, ROOM_Y0 - THICK, ROOM_Y1 + THICK)       # ouest
    wall(ROOM_X0, ROOM_X1 + THICK, ROOM_Y0 - THICK, ROOM_Y0)               # sud
    wall(ROOM_X0, ROOM_X1 + THICK, ROOM_Y1, ROOM_Y1 + THICK)               # nord
    # Le mur est, perce de la porte.
    wall(ROOM_X1, COR_X0, ROOM_Y0, DOOR_Y0)
    wall(ROOM_X1, COR_X0, DOOR_Y1, ROOM_Y1)
    wall(ROOM_X1, COR_X0, DOOR_Y0, DOOR_Y1, DOOR_TOP, HEIGHT)             # linteau

    # Le couloir, ouvert au nord sur le recoin.
    wall(COR_X0, COR_X1 + THICK, COR_Y0 - THICK, COR_Y0)                   # sud
    wall(COR_X0, NOOK_X0, COR_Y1, COR_Y1 + THICK)                          # nord
    wall(COR_X1, COR_X1 + THICK, COR_Y0 - THICK, NOOK_Y1 + THICK)          # fond, et flanc du recoin
    wall(NOOK_X0 - THICK, NOOK_X0, COR_Y1, NOOK_Y1 + THICK)                # recoin, ouest
    wall(NOOK_X0 - THICK, COR_X1 + THICK, NOOK_Y1, NOOK_Y1 + THICK)        # recoin, nord

    # Le portail de visibilite, dans l'embrasure : piece et couloir sont deux
    # zones, et la porte fermee les separe. Sa matiere ne va que sur la face
    # cote piece.
    w.add(box((ROOM_X1, DOOR_Y0, 0), (COR_X0, DOOR_Y1, DOOR_TOP), NODRAW, faces={'x-': PORTAL}))

    # Le plafonnier de la piece, et la lumiere qu'il motive.
    lamp_x = (ROOM_X0 + ROOM_X1) / 2
    w.add(box((lamp_x - 8, -8, HEIGHT - 4), (lamp_x + 8, 8, HEIGHT), LAMP))
    world.entity('light', name='light_room', origin=vec(lamp_x, 0, HEIGHT - 10),
                 light_radius=vec(180, 150, 110), _color=vec(1, 0.86, 0.68))

    # Le neon du couloir : un tube, et une lumiere allongee comme lui.
    w.add(box((NEON_X - 24, -2, HEIGHT - 3), (NEON_X + 24, 2, HEIGHT), NEON))
    world.entity('light', name='light_neon', origin=vec(NEON_X, 0, HEIGHT - 8),
                 light_radius=vec(210, 64, 110), _color=vec(0.82, 0.9, 1))

    # La porte : un vantail qui rentre dans le mur, vers le nord. L'image de
    # la porte est plaquee sur chaque face, de la base au linteau.
    width = DOOR_Y1 - DOOR_Y0
    fit = texmat(1 / width, 1 / DOOR_TOP, -DOOR_Y0 / width, 1)
    fit_back = texmat(1 / width, 1 / DOOR_TOP, DOOR_Y1 / width, 1)
    mid = (ROOM_X1 + COR_X0) / 2
    world.entity('func_door', name='door_room', movedir=90, lip=2, time=0.6,
                 wait=4, triggersize=64).add(
        box((mid - DOOR_PANEL / 2, DOOR_Y0, 0), (mid + DOOR_PANEL / 2, DOOR_Y1, DOOR_TOP), DOOR,
            matrices={'x+': fit, 'x-': fit_back}))

    # Le militaire entre dans la piece face a la porte.
    world.entity('info_player_start', name='start_military', origin=vec(56, 0, 1), angle=0)

    out = ROOT / 'content' / 'maps' / 'migration_room.map'
    brushes = world.write(out)
    print(f'{out.relative_to(ROOT)} : {brushes} brushes, {len(world.entities)} entites')


if __name__ == '__main__':
    main()
