"""
Petit atelier de cartes au format natif d'id Tech 4 : `.map` version 3,
brushes `brushDef3`. TrenchBroomBFG ouvre ce format tel quel.

Chaque brush est l'intersection de demi-espaces. Chaque face est un plan
`( a b c d )` tel que `a x + b y + c z + d = 0`, normale vers l'exterieur du
volume, suivi de la matrice de texture et du nom de la matiere.

La matrice de texture s'applique dans le repere que le moteur tire de la
normale (`ComputeAxisBase`) : pour une face orientee vers +x, s suit +y et t
suit -z ; pour une face vers +z, s suit +y et t suit +x. En unites de texture :
1 vaut une repetition de l'image.

Une unite vaut un pouce, 2,54 cm.
"""

from pathlib import Path

METER = 39.37
# Une repetition de texture par metre : la trame des matieres de developpement.
PER_METER = 1.0 / METER


def texmat(sx=PER_METER, sy=PER_METER, ox=0.0, oy=0.0):
    return f'( ( {sx:.7g} 0 {ox:.7g} ) ( 0 {sy:.7g} {oy:.7g} ) )'


GRID = texmat()


class Side:
    """Une face : son plan, sa matiere, sa projection de texture."""

    def __init__(self, normal, dist, material, matrix=GRID):
        self.normal = normal
        self.dist = dist
        self.material = material
        self.matrix = matrix

    def write(self):
        a, b, c = (_num(v) for v in self.normal)
        return f'   ( {a} {b} {c} {_num(-self.dist)} ) {self.matrix} "{self.material}" 0 0 0'


def _num(value):
    """Un nombre sans zeros inutiles, pour une carte qui se relit."""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f'{value:.6g}'


class Brush:
    def __init__(self, sides):
        self.sides = sides

    def write(self):
        lines = [' {', '  brushDef3', '  {']
        lines += [side.write() for side in self.sides]
        lines += ['  }', ' }']
        return '\n'.join(lines)


# Les six faces d'un pave, dans l'ordre ou on les nomme.
FACES = ('x+', 'x-', 'y+', 'y-', 'z+', 'z-')


def box(mins, maxs, material, faces=None, matrices=None):
    """
    Un pave aligne sur les axes. `faces` remplace la matiere d'une face par son
    nom ('x+', 'z-', ...), `matrices` sa projection de texture.
    """
    x0, y0, z0 = mins
    x1, y1, z1 = maxs
    assert x0 < x1 and y0 < y1 and z0 < z1, (mins, maxs)
    planes = {
        'x+': ((1, 0, 0), x1),
        'x-': ((-1, 0, 0), -x0),
        'y+': ((0, 1, 0), y1),
        'y-': ((0, -1, 0), -y0),
        'z+': ((0, 0, 1), z1),
        'z-': ((0, 0, -1), -z0),
    }
    faces = faces or {}
    matrices = matrices or {}
    return Brush([
        Side(normal, dist, faces.get(name, material), matrices.get(name, GRID))
        for name, (normal, dist) in ((name, planes[name]) for name in FACES)
    ])


def ramp(x0, x1, y0, y1, z0, height, material):
    """
    Un plan incline qui monte de z0 a z0 + height quand x va de x0 a x1 : un
    prisme couche, cinq faces.
    """
    length = x1 - x0
    # La pente : normale (-h, 0, L) normalisee, passant par (x0, *, z0).
    norm = (height * height + length * length) ** 0.5
    nx, nz = -height / norm, length / norm
    return Brush([
        Side((nx, 0, nz), nx * x0 + nz * z0, material),
        Side((1, 0, 0), x1, material),
        Side((0, 1, 0), y1, material),
        Side((0, -1, 0), -y0, material),
        Side((0, 0, -1), -z0, material),
    ])


class Entity:
    def __init__(self, classname, **keys):
        self.keys = {'classname': classname}
        self.keys.update({key: str(value) for key, value in keys.items()})
        self.brushes = []

    def add(self, *brushes):
        self.brushes.extend(brushes)
        return self

    def write(self, index):
        # Une entite faite de brushes designe son modele par son nom : dmap
        # le compile sous ce nom, et le jeu le cherche par la cle "model".
        # Sans elle, l'entite existe mais n'a ni image ni collision.
        if self.brushes and self.keys['classname'] != 'worldspawn' and 'model' not in self.keys:
            assert 'name' in self.keys, 'une entite de brushes doit avoir un nom'
            self.keys['model'] = self.keys['name']
        lines = [f'// entity {index}', '{']
        lines += [f'"{key}" "{value}"' for key, value in self.keys.items()]
        for number, brush in enumerate(self.brushes):
            lines.append(f'// primitive {number}')
            lines.append(brush.write())
        lines.append('}')
        return '\n'.join(lines)


class MapFile:
    def __init__(self, **world_keys):
        self.world = Entity('worldspawn', **world_keys)
        self.entities = [self.world]

    def entity(self, classname, **keys):
        entity = Entity(classname, **keys)
        self.entities.append(entity)
        return entity

    def write(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        parts = ['Version 3'] + [entity.write(i) for i, entity in enumerate(self.entities)]
        path.write_text('\n'.join(parts) + '\n')
        brushes = sum(len(entity.brushes) for entity in self.entities)
        return brushes


def vec(*values):
    """Une cle vecteur du moteur : "x y z"."""
    return ' '.join(_num(v) for v in values)
