# UNHOLY

FPS horror asymétrique. Quatre militaires contre quatre humains possédés, dans
un immeuble résidentiel à l'alimentation défaillante. Une vie chacun, aucune
réapparition.

Les militaires montent chercher un artefact au dernier étage et doivent
redescendre pour l'extraire. Les possédés doivent les tuer. Cinq à dix minutes.

## État

Migration en cours, depuis un prototype Three.js vers **id Tech 4**, sur la base
de [RBDOOM-3-BFG](https://github.com/RobertBeckebans/RBDOOM-3-BFG).

Rien n'est migré pour l'instant : la milestone 0 est un audit.

- [`MIGRATION.md`](MIGRATION.md) — l'audit, la correspondance système par
  système, l'arborescence, les risques, et le plan de la première milestone.
- [`docs/FEEL.md`](docs/FEEL.md) — ce que le prototype savait du ressenti :
  valeurs mesurées, méthode, et les pièges déjà payés.
- [`docs/LICENSES.md`](docs/LICENSES.md) — le registre des dépendances et de
  leurs licences. Rien n'entre dans le projet sans y figurer.

Le prototype reste dans `../unholy`, intact et jouable. Il sert de
documentation exécutable, pas de code à traduire.

## Licence

Le moteur est sous GPL-3.0, avec les conditions supplémentaires d'id Software.
Le code de jeu, lié au moteur, en dérive et l'est donc aussi : il sera publié.

Les données du jeu — modèles, textures, sons, cartes, interface — restent sous
nos propres conditions. UNHOLY est destiné à la vente, ce que la GPL autorise.

Aucune donnée de Doom 3 ou de Doom 3 BFG n'est distribuée avec ce jeu.
