"""
UNHOLY -- relever des contours sur une image de reference, de profil.

    python3 tools/assets/hd/trace.py <image de reference> <sortie.json>

Le fusil se modelise d'apres une photo de profil sur fond blanc : sa
silhouette donne les contours exacts des pieces de forme libre (crosse,
poignee, chargeur, boitier inferieur, detente, guidon). Chaque piece est
decoupee dans la silhouette par un polygone de coupe, en pixels ; son contour
exterieur et ses trous sont suivis pixel par pixel (suivi de bord de Moore),
simplifies (Douglas-Peucker), puis ramenes en centimetres dans le repere du
fusil.

La silhouette : tout ce qui n'est pas du fond. Le fond, c'est le blanc qui
touche le bord de l'image, et les grandes plages blanches qu'il entoure (le
pontet, la fente de la crosse, l'anneau de bretelle) ; les petites (les
marquages peints, les chiffres du rail) sont de la matiere. Une image a canal
alpha est lue par son canal alpha.

Le recalage (voir REGISTRATION) se fait sur les mains du pack : l'axe de la
detente de la reference tombe sur l'os Trigger du fusil du pack, et l'echelle
(4,65 cm pour 100 pixels) est celle ou la main droite du pack enveloppe la
poignee et ou la main gauche tient le garde-main. Le fusil sort ainsi 11 %
plus grand que nature, comme celui du pack ; la pointe du guidon arrive a un
millimetre de l'oeil de la visee.

L'image de reference n'est pas dans le depot ; les contours releves, si.
"""

import json
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageDraw

# Pixels de la reference -> centimetres du fusil. La bouche est a droite sur la photo.
REGISTRATION = dict(scale=0.0465, px_anchor=720.0, x_anchor=9.94, py_anchor=311.7, z_anchor=11.88)

# Les plages blanches enfermees plus petites que cela sont des marquages, pas des jours.
MIN_OPENING = 60
# Et celles-ci, bien que plus grandes, aussi (en pixels : x0, y0, x1, y1).
MARKINGS = [(670, 295, 700, 315)]


def to_local(px, py, reg=REGISTRATION):
    s = reg['scale']
    return (reg['x_anchor'] + (px - reg['px_anchor']) * s, reg['z_anchor'] + (reg['py_anchor'] - py) * s)


def load_mask(path):
    image = Image.open(path)
    if image.mode == 'RGBA':
        return np.asarray(image)[..., 3] > 128
    rgb = np.asarray(image.convert('RGB')).astype(int)
    bright = (rgb.mean(axis=2) > 228) & (rgb.max(axis=2) - rgb.min(axis=2) < 30)
    h, w = bright.shape
    background = np.zeros((h, w), dtype=bool)
    seen = np.zeros((h, w), dtype=bool)
    for y0, x0 in zip(*np.nonzero(bright)):
        if seen[y0, x0]:
            continue
        queue, comp, border = deque([(y0, x0)]), [], False
        seen[y0, x0] = True
        while queue:
            y, x = queue.popleft()
            comp.append((y, x))
            border |= y in (0, h - 1) or x in (0, w - 1)
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < w and bright[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    queue.append((ny, nx))
        ys, xs = np.array(comp).T
        marking = any(x0 <= xs.mean() <= x1 and y0 <= ys.mean() <= y1 for x0, y0, x1, y1 in MARKINGS)
        if border or (len(comp) >= MIN_OPENING and not marking):
            background[ys, xs] = True
    return ~background


def clip(mask, polygon):
    """Ne garde de la silhouette que ce qui tombe dans le polygone de coupe (pixels)."""
    keep = Image.new('1', (mask.shape[1], mask.shape[0]), 0)
    ImageDraw.Draw(keep).polygon([tuple(p) for p in polygon], fill=1)
    return mask & np.asarray(keep, dtype=bool)


NEIGHBOURS = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]  # (dy, dx), sens horaire


def trace_boundary(mask, start):
    """Suivi de bord de Moore depuis un pixel plein dont le voisin de gauche est vide."""
    h, w = mask.shape
    y0, x0 = start
    boundary = [(y0, x0)]
    # on arrive par la gauche : le dernier voisin examine est a l'ouest
    back = 6
    y, x = y0, x0
    for _ in range(4 * h * w):
        found = False
        for k in range(8):
            d = (back + 1 + k) % 8
            ny, nx = y + NEIGHBOURS[d][0], x + NEIGHBOURS[d][1]
            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx]:
                back = (d + 4) % 8
                y, x = ny, nx
                found = True
                break
        if not found:
            break
        if (y, x) == (y0, x0):
            break
        boundary.append((y, x))
    return boundary


def largest(mask):
    """La plus grande tache d'un masque : une coupe peut ramasser des miettes voisines."""
    h, w = mask.shape
    seen = np.zeros_like(mask)
    best = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        queue, comp = deque([(y0, x0)]), []
        seen[y0, x0] = True
        while queue:
            y, x = queue.popleft()
            comp.append((y, x))
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    queue.append((ny, nx))
        if len(comp) > len(best):
            best = comp
    out = np.zeros_like(mask)
    if best:
        ys, xs = np.array(best).T
        out[ys, xs] = True
    return out


def outer_contour(mask):
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return []
    i = np.lexsort((xs, ys))[0]
    return trace_boundary(mask, (ys[i], xs[i]))


def holes(mask, min_area=40):
    """Les trous d'une piece : les zones vides qu'elle entoure (remplissage par diffusion)."""
    h, w = mask.shape
    outside = np.zeros_like(mask)
    queue = deque([(y, x) for y in (0, h - 1) for x in range(w)] + [(y, x) for y in range(h) for x in (0, w - 1)])
    while queue:
        y, x = queue.popleft()
        if y < 0 or y >= h or x < 0 or x >= w or outside[y, x] or mask[y, x]:
            continue
        outside[y, x] = True
        queue.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    inner = ~mask & ~outside
    result = []
    seen = np.zeros_like(mask)
    for y, x in zip(*np.nonzero(inner)):
        if seen[y, x]:
            continue
        comp = []
        queue = deque([(y, x)])
        while queue:
            cy, cx = queue.popleft()
            if cy < 0 or cy >= h or cx < 0 or cx >= w or seen[cy, cx] or not inner[cy, cx]:
                continue
            seen[cy, cx] = True
            comp.append((cy, cx))
            queue.extend(((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)))
        if len(comp) >= min_area:
            hole = np.zeros_like(mask)
            ys, xs = np.array(comp).T
            hole[ys, xs] = True
            result.append(outer_contour(hole))
    return result


def simplify(points, epsilon):
    """Douglas-Peucker, sur une polyligne fermee."""
    pts = np.asarray(points, dtype=float)
    if len(pts) < 4:
        return pts.tolist()

    def rdp(a):
        start, end = a[0], a[-1]
        line = end - start
        norm = np.hypot(*line)
        if norm == 0:
            d = np.hypot(*(a - start).T)
        else:
            rel = a - start
            d = np.abs(line[0] * rel[:, 1] - line[1] * rel[:, 0]) / norm
        i = int(np.argmax(d))
        if d[i] > epsilon:
            return np.vstack((rdp(a[:i + 1])[:-1], rdp(a[i:])))
        return np.vstack((start, end))

    far = int(np.argmax(np.hypot(*(pts - pts[0]).T)))
    first = rdp(pts[:far + 1])
    second = rdp(np.vstack((pts[far:], pts[:1])))
    return np.vstack((first[:-1], second[:-1])).tolist()


def part(mask, polygon, epsilon=1.0, drop=()):
    """Le contour (et les trous) d'une piece, en centimetres du fusil. drop : des zones
    a retirer de la coupe (une piece voisine qui la touche)."""
    m = clip(mask, polygon)
    for zone in drop:
        m &= ~clip(np.ones_like(mask), zone)
    m = largest(m)
    contour = [(x, y) for y, x in outer_contour(m)]
    out = [to_local(x, y) for x, y in simplify(contour, epsilon)]
    inner = [[to_local(x, y) for x, y in simplify([(x, y) for y, x in h], epsilon)] for h in holes(m)]
    return {'outline': out, 'holes': inner}


# Les pieces relevees : polygone de coupe, et zones retirees (pixels de la reference).
PARTS = {
    # La crosse : jusqu'au tube, qui sort a x 468.
    'stock': ([(30, 150), (468, 150), (468, 480), (30, 480)], ()),
    # La poignee : sous le boitier inferieur, sa queue d'aronde comprise.
    'grip': ([(470, 330), (535, 285), (590, 285), (605, 338), (688, 342), (688, 360), (672, 420), (640, 610), (470, 610)], ()),
    # Le chargeur : sous l'evasement du puits.
    'magazine': ([(805, 413), (1040, 413), (1040, 705), (805, 705)], ()),
    # Le boitier inferieur : de la jonction au bas du puits, le pontet compris, sans la
    # poignee ni la detente.
    'lower': ([(522, 251), (1003, 251), (1003, 413), (815, 413), (812, 445), (660, 445), (672, 420), (688, 360),
               (688, 342), (605, 338), (590, 285), (535, 285), (522, 300)],
              [[(705, 330), (760, 330), (760, 412), (705, 412)]]),
    # La detente, dans le pontet.
    'trigger': ([(705, 330), (760, 330), (760, 412), (705, 412)], ()),
    # Le boitier superieur, rail compris, jusqu'a la jonction.
    'upper': ([(528, 110), (1003, 110), (1003, 251), (528, 251)], ()),
    # Le garde-main : ses dents, ses jours, l'anneau de bretelle.
    'rail': ([(1003, 110), (1598, 110), (1598, 300), (1003, 300)], ()),
    # Le guidon, au-dessus du rail.
    'front_sight': ([(1470, 25), (1562, 25), (1562, 127), (1470, 127)], ()),
    # Le bloc d'emprunt de gaz, le canon et le cache-flamme.
    'gas_block': ([(1598, 140), (1642, 140), (1642, 250), (1598, 250)], ()),
    'flash_hider': ([(1642, 185), (1762, 185), (1762, 252), (1642, 252)], ()),
}


def main():
    mask = load_mask(sys.argv[1])
    out = {'registration': REGISTRATION,
           'parts': {name: part(mask, poly, drop=drop) for name, (poly, drop) in PARTS.items()}}
    with open(sys.argv[2], 'w') as f:
        json.dump(out, f, indent=1)
    for name, data in out['parts'].items():
        print(f"{name}: {len(data['outline'])} points, {len(data['holes'])} trou(s)")


if __name__ == '__main__':
    main()
