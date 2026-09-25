# UNHOLY

FPS horror asymétrique. Quatre militaires contre quatre humains possédés, dans
un immeuble résidentiel à l'alimentation défaillante. Une vie chacun, aucune
réapparition.

Les militaires montent chercher un artefact au dernier étage et doivent
redescendre pour l'extraire. Les possédés doivent les tuer. Cinq à dix minutes.

## État

Migration en cours, depuis un prototype Three.js vers **id Tech 4**, sur la base
de [RBDOOM-3-BFG](https://github.com/RobertBeckebans/RBDOOM-3-BFG).

Faites :

- **Milestone 1** : le moteur se construit sur Mac et démarre avec nos seules
  données, sans aucune donnée de Doom 3.
- **Milestone 2** : la migration room, et le militaire qui s'y déplace, lourd
  et précis, sans bunny hop ni strafe jump.
- **Milestone 3** : le fusil en main, bras et animations compris ; le tir, le
  recul, l'épaulé, le rechargement, l'éclat qui éclaire la pièce, les
  impacts, et des cibles qui tombent.

```bash
tools/build.sh                     # construit le jeu
tools/assets/build_retro_weapons.sh ~/Downloads/RetroWeaponPack_V1.zip
                                   # le fusil et les bras, une fois (Blender)
tools/run.sh +map migration_room   # la carte du brief
tools/run.sh +map move_test        # l'aire d'essai du déplacement
tools/movetest.sh                  # le banc d'essai, ses mesures
tools/movetest.sh tir              # le fusil face à la cible
```

Le fusil et les bras viennent du Retro Weapon Pack, qui n'est pas dans le
dépôt : on les convertit sur place depuis l'archive ([`docs/BUILD.md`](docs/BUILD.md)).

À lire :

- [`MIGRATION.md`](MIGRATION.md) : l'audit, la correspondance système par
  système, l'arborescence, les risques, les milestones.
- [`docs/BUILD.md`](docs/BUILD.md) : construire sur macOS, les correctifs du
  moteur, ce qu'il exige pour démarrer sans Doom 3.
- [`docs/FEEL.md`](docs/FEEL.md) : le ressenti, valeurs mesurées et méthode,
  du prototype au déplacement et au fusil du militaire.
- [`docs/DEBUG.md`](docs/DEBUG.md) : les outils de mise au point, l'écoute
  du mixage sans haut-parleurs, et les pièges du moteur pour les essais
  automatiques.
- [`docs/LICENSES.md`](docs/LICENSES.md) : le registre des dépendances et de
  leurs licences. Rien n'entre dans le projet sans y figurer.

Le prototype reste dans `../unholy`, intact et jouable. Il sert de
documentation exécutable, pas de code à traduire.

## Licence

Le moteur est sous GPL-3.0, avec les conditions supplémentaires d'id Software.
Le code de jeu, lié au moteur, en dérive et l'est donc aussi : il sera publié.

Les données du jeu (modèles, textures, sons, cartes, interface) restent sous
nos propres conditions. UNHOLY est destiné à la vente, ce que la GPL autorise.

Aucune donnée de Doom 3 ou de Doom 3 BFG n'est distribuée avec ce jeu.
