# UNHOLY — migration de Three.js vers id Tech 4

Milestone 0. Ce document est l'audit du prototype Three.js, la correspondance
système par système avec id Tech 4, l'arborescence proposée, les risques, et le
plan de la première milestone compilable. **Rien n'est migré tant que ce plan
n'est pas validé.**

Le prototype reste en place dans `../unholy`, intact et jouable : il sert de
documentation exécutable. On l'ouvre pour répondre à « comment ça se comportait
déjà ? », on ne le traduit pas.

---

## 1. Le moteur retenu

**RBDOOM-3-BFG** (`github.com/RobertBeckebans/RBDOOM-3-BFG`), fork direct des
sources de Doom 3 BFG publiées par id Software.

Pourquoi pas `id-software/doom-3-bfg` directement : ce dépôt livre des projets
Visual Studio 2010, son audio passe par XAudio2, et il est figé depuis 2012
(sept commits). Il ne se compile pas sur macOS. En partir, c'est porter le
moteur avant d'écrire une ligne d'UNHOLY.

Ce que le fork apporte, et qui compte pour ce projet précis :

| Apport | Ce que ça nous évite |
| --- | --- |
| CMake, build macOS maintenu (2023) | Le portage complet du moteur |
| Chargement **glTF2 `.glb`**, statique et skinné | La conversion du fusil et de la réglette, déjà en `.glb` |
| PBR (GGX Cook-Torrance), ombres douces, TAA/SMAA | Réécrire le rendu qu'on vient de régler sous Three.js |
| TrenchBroom pour éditer les maps | L'éditeur de Doom 3, qui n'existe qu'avec le jeu du commerce |
| OBJ, irradiance volumes, cascaded shadow maps | Du temps sur l'éclairage de l'immeuble |

Licence : **GPL-3.0** plus les conditions supplémentaires d'id Software, et un
`LICENSE_EXCEPTIONS.md` qui liste les morceaux non-GPL. Décision prise, voir
§ 1.4.

**Le choix est arrêté.** Ni Doom 3 original, ni le dépôt d'id comme base de
travail. RBDOOM-3-BFG est la fondation d'UNHOLY, et il n'y a pas de repli à
garder sous le coude : un repli, ça pousse à écrire du code qui ménage les deux
moteurs, et ce code ne sert jamais.

### Ce qu'on ne réécrit pas

Le moteur fournit déjà, et on s'en sert tel quel :

rendu Vulkan / DX12 · PBR rugosité-métal (`basecolormap`, `normalmap`,
`rmaomap`) · rendu HDR · courbe ACES · ombres douces · TAA et SMAA · SSAO ·
volumes d'irradiance et grilles de lumière · sondes d'environnement ·
glTF 2.0 / GLB · OpenAL · CMake · TrenchBroomBFG.

Règle de conduite : si une brique de cette liste réapparaît dans le code
d'UNHOLY, c'est une erreur. Le prototype Three.js nous a appris à les faire
nous-mêmes ; la migration consiste justement à arrêter.

### 1.4 Licence et distribution — décidé

**UNHOLY est destiné à la vente sur Steam, et la GPL-3 est acceptée comme
contrainte du projet.**

La GPL n'interdit pas de vendre : elle impose, à la distribution, de fournir la
source correspondante du programme couvert, avec de quoi le construire. Le jeu
peut donc être payant sans rien changer à la licence.

Ce qui tombe sous la GPL et sera publié :

- le moteur RBDOOM-3-BFG et nos modifications éventuelles ;
- **notre code de jeu C++**, puisqu'il est lié au moteur et forme avec lui un
  seul programme dérivé ;
- les scripts de compilation nécessaires à le reconstruire.

Ce qui n'y tombe pas et reste sous nos propres conditions :

- modèles, animations, textures, matières, sons, musiques, cartes, interface.
  Ce sont des données lues à l'exécution, pas des morceaux du programme. C'est
  d'ailleurs ainsi que le dépôt lui-même traite les données de Doom 3 BFG, qui
  ne font pas partie de sa publication GPL et gardent leur propre licence.

Trois règles de conduite qui en découlent, et qui pèsent sur l'architecture :

1. **La frontière passe entre le code et les données, pas ailleurs.** D'où la
   séparation ci-dessous, et le choix de mettre la logique de jeu en C++ plutôt
   qu'en `.script` : la logique est de toute façon GPL, autant qu'elle soit là
   où c'est clair, et garder `base/` pour du contenu. Une exception, imposée
   par le moteur : `idWeapon` tient son automate d'états dans un objet de
   script, et n'avance pas sans lui. Le fusil a donc son `.script`
   (milestone 3), réduit à un aiguillage : quand tirer, recharger, épauler,
   quelle animation jouer. Les valeurs restent dans sa déclaration, les
   règles de déplacement dans le C++.
2. **Jamais un octet de Doom 3 ou de Doom 3 BFG dans le jeu distribuable.**
   Localement, pour vérifier que le moteur tourne, c'est autre chose ; ça ne
   franchit pas la porte.
3. **Chaque dépendance est inscrite avec sa licence**, au fur et à mesure, dans
   [`docs/LICENSES.md`](docs/LICENSES.md). Une police libre ajoutée à la va-vite
   en milestone 1 est exactement ce qui coûte cher trois ans plus tard.

Avant la sortie commerciale, et pas avant : faire relire la structure finale
par quelqu'un dont c'est le métier, `LICENSE_EXCEPTIONS.md` et les conditions
supplémentaires d'id comprises. Ce n'est pas un obstacle au prototype, c'est
une case à cocher avant d'encaisser.

### Steam et Steamworks

La publication GPL **n'inclut pas l'intégration Steamworks** de Doom 3 BFG :
succès, classements, mise en relation, surcouche. Vendre sur Steam n'en dépend
pas — un jeu se publie sans aucune de ces fonctions.

Mais lier une bibliothèque propriétaire à un programme GPL est précisément le
genre de question qui ne s'improvise pas. Steamworks est donc **reporté à une
milestone dédiée, après un audit de compatibilité de licence**, et n'entre dans
aucune des milestones de gameplay.

### La séparation à tenir dès maintenant

```
RBDOOM-3-BFG / code moteur
          │
          ├── UNHOLY, code de jeu en C++
          │
          └── UNHOLY, données
                ├── models
                ├── animations
                ├── textures
                ├── materials
                ├── maps
                ├── sounds
                └── UI
```

UNHOLY doit devenir un jeu autonome, pas un mod de Doom 3 BFG suspendu à ses
données et à son gameplay. Les modifications du moteur restent identifiables,
séparément du code du jeu.

---

## 2. Audit du prototype Three.js

28 285 lignes de TypeScript, 122 fichiers, plus les assets. Mesuré au jour de
l'audit.

### 2.1 Ce que le prototype contient

| Sous-système | Fichiers | Lignes | Rôle |
| --- | --- | --- | --- |
| `src/renderer/**` | 42 | 7 502 | Pipeline Three.js : passes, matériaux, lumières, effets, post-traitement |
| `src/game/weapons/**` | 13 | 3 249 | Porte-arme, prise en main, recul, épaulé, tirs, projectiles |
| `src/game/**` (racine) | 8 | 3 462 | Session, collision, physique pmove, niveau, entrée |
| `src/formats/**` | 6 | 2 257 | Lecteurs Quake III : BSP, MD3, PK3, scripts de matière, AAS |
| `src/ui/**` | 19 | 2 587 | HUD, menu, réglages, styles |
| `src/game/match/**` | 3 | 1 732 | Arène, score, gibs, modèles de joueur |
| `src/bsp/**` | 8 | 1 556 | Rendu des cartes Quake III, lightmaps, grille de lumière, PVS |
| `src/game/unholy/**` | 4 | 1 056 | **L'immeuble**, décor résidentiel, échelle, réglettes |
| `src/game/bots/**` | 2 | 757 | Cerveau des bots et navigation AAS |
| `src/audio/**` | 2 | 648 | Sons synthétisés par le code, audio de jeu |
| `src/game/entities/**` | 4 | 959 | Objets à ramasser, effets de carte (entités Quake III) |
| `src/game/benchmark`, `demo` | 3 | 662 | Banc de mesure, arène de démonstration |
| Reste (camera, build, light, util, md3) | 12 | 2 129 | Effets de caméra, constructeur de blocs, lampe, vision nocturne |

### 2.2 Les assets

| Asset | Taille | Sort |
| --- | --- | --- |
| `assault_rifle.glb` (+ `_high`) | 23 + 28 Mo | **À convertir** — chargé tel quel par RBDOOM |
| `fluorescent_fixture.glb` | 6 Mo | **À convertir** — idem |
| `wall.jpg`, `floor.jpg`, `ceiling.jpg`, `glass.png` | 1,9 Mo | **À convertir** en `.mtr` + jeu PBR complet (voir ci-dessous) |
| `logo.png`, `favicon.png` | 188 Ko | **À convertir** pour le GUI du menu |
| `machine_gun.glb` + `.png` | 28 Mo | **À abandonner** — arme du moteur d'origine |
| Sons | 0 octet | **À créer** — tout est synthétisé par le code aujourd'hui |

Aucun asset de Doom 3 dans le jeu distribuable. Les assets du commerce peuvent
servir localement à vérifier que le moteur tourne, jamais au-delà.

**Les textures changent de nature.** Sous Three.js, le prototype ne disposait
que d'une couleur et en déduisait le relief et la rugosité par un seuil sur la
clarté — une approximation, et elle se voyait. RBDOOM attend le vrai jeu PBR :
`basecolormap`, `normalmap`, `rmaomap` (rugosité, métal, occlusion). Les
matières de l'immeuble sont donc à produire pour ce pipeline plutôt qu'à
convertir : c'est un gain de qualité, pas une perte de travail. La déduction
par la clarté meurt avec le prototype, et c'est une bonne nouvelle.

---

## 3. Correspondance système par système

Colonnes : ce que fait le prototype → l'équivalent natif d'id Tech 4 → ce qu'on
en fait → fichiers de référence → difficulté → ce dont ça dépend.

### 3.1 Fondations moteur — à abandonner en bloc

| Prototype | id Tech 4 | Sort | Fichiers | Diff. |
| --- | --- | --- | --- | --- |
| Pipeline de rendu, passes, composer | `idRenderSystem` | **Abandon** | `src/renderer/*.ts`, `postprocessing/` | — |
| Graphe de scène Three.js | `idRenderWorld` + entités | **Abandon** | tout `THREE.Scene` | — |
| Matériaux procéduraux, shaders WebGL | `.mtr` + renderprogs | **Abandon** | `renderer/materials/**` | — |
| Lumières Three.js, ombres | Lumières du moteur, shadow maps | **Abandon** | `renderer/lighting/**` | — |
| Post-traitement (AO, bloom, tone map) | Natif RBDOOM (PBR, TAA, bloom) | **Abandon** | `postprocessing/`, `grading/` | — |
| Lecteurs BSP / MD3 / PK3 / AAS / shader | `.map`/`.proc`, `.md5mesh`, `.pk4`, `.aas` | **Abandon** | `src/formats/**`, `src/bsp/**`, `src/md3/**` | — |
| Collision par brushes, trace | `idClipModel`, `idCollisionModelManager` | **Abandon** | `game/collision.ts` | — |
| Physique pmove 125 Hz | `idPhysics_Player` | **Abandon** (voir 3.2) | `game/physics.ts` (669 l.) | — |
| Arène, gibs, modèles MD3 | `idMultiplayerGame`, `idAI` | **Abandon** | `game/match/**` | — |
| Bots + navigation AAS | `idAI` + `idAAS` | **Abandon** | `game/bots/**` | — |
| Banc de mesure, arène de démo | `com_showFPS`, `r_show*` | **Abandon** | `benchmark/`, `demo/` | — |

Environ **19 000 lignes disparaissent**. C'est le but : ces briques existent
dans le moteur, mieux faites, et c'est la raison de la migration.

### 3.2 Gameplay — à recréer, le prototype servant de cahier des charges

| Prototype | id Tech 4 | Sort | Référence | Diff. | Dépend de |
| --- | --- | --- | --- | --- | --- |
| Déplacement du militaire | `idPhysics_Player` réglé, pas hérité | **Recréer** | `game/physics.ts`, §7 du brief | Moyenne | M2 |
| Prise en main du fusil (`VIEWMODEL.hold`) | `idWeapon` + `.def` de vue | **Recréer** | `weapons/ViewmodelFeel.ts` (163 l., toutes les valeurs mesurées) | Faible | M3 |
| Inertie, balancement, respiration, recul | `idWeapon` sway natif + script | **Recréer** | `ViewmodelFeel.ts`, `camera/FPSCameraEffects.ts` | Moyenne | M3 |
| Épaulé (optique sur l'axe, FOV resserré) | `idWeapon::Event_WeaponZoom` | **Recréer** | `GlbWeaponRig.applyHold`, `ViewModel.updateAim` | Moyenne | M3 |
| Éclat de tir au canon dessiné | `idWeapon` muzzle flash + `idLight` | **Recréer** | `ViewModel.updateFlash`, `fixtures.ts` | Faible | M3 |
| Lampe tactique (cône, gélatine, portée) | `idLight` projetée + `flashlight.def` | **Recréer** | `game/light/Flashlight.ts` (les valeurs sont mesurées) | Moyenne | M4 |
| Éclairage de l'immeuble, pannes, néons | Lumières de map + `idLight` scriptées | **Recréer** | `unholy/building.ts`, `residential.ts` | Moyenne | M4 |
| HUD (santé, munitions, voile de blessure) | `idUserInterface` (`.gui`) | **Recréer** | `ui/hud/**`, `ui/styles/hud.css` | Moyenne | M3 |
| Menu | `.gui` + `idMenuHandler` | **Recréer** | `ui/menu/**` | Moyenne | M9 |
| Règles de partie, score, chrono | `idGameLocal` + `idMultiplayerGame` | **Recréer** | `match/Arena.ts` | Élevée | M9 |
| Artefact, extraction | Entités `idItem` / `idTrigger` UNHOLY | **Créer** | brief §14 | Moyenne | M9 |
| Spectateur | `idPlayer::Spectate` natif | **Adapter** | brief §15 | Faible | M9 |
| Possédé : griffes, pounce | `idAI` + `idPhysics_Monster` | **Créer** | brief §11 | Élevée | M5, M7 |
| Wall / ceiling crawl | **Rien de natif** — physique dédiée | **Créer** | brief §12 | **Très élevée** | M6 |
| IA militaire, IA possédé | `idAI` + `idAAS` | **Créer** | brief §16-17 | Élevée | M10-11 |

Ce que la milestone 3 a fait autrement que prévu :

- **La prise en main, la respiration et le balancement viennent des
  animations du Retro Weapon Pack**, fusil et bras ensemble, et non des
  valeurs du prototype : le pack dessine la pose, et le balancement du moteur
  est coupé (correctif 0009) pour ne pas s'y ajouter. L'inertie du regard et
  le recul restent ceux d'`idWeapon`, réglés dans la déclaration du fusil.
- **L'épaulé passe par les organes de visée du pack**, pas par une optique :
  le fusil n'a pas de viseur holographique. Le brief en demande un ; il reste
  à faire.
- **Le HUD n'est pas un `.gui`.** Le joueur d'UNHOLY dessine son réticule et
  son compteur de munitions en C++ (correctif 0007) : les interfaces de BFG
  sont des SWF que nous n'avons pas, et deux éléments ne justifient pas encore
  un système d'interface. La santé et le voile de blessure viendront avec les
  dégâts reçus.
- **Le tir est un projectile très rapide, pas un tir instantané** : `idWeapon`
  n'a pas de hitscan en solo. À 120 000 unités par seconde, la balle traverse
  un couloir de vingt mètres dans l'image du tir.

### 3.3 Décor — le cas particulier

L'immeuble n'est pas un fichier : c'est **du code** (`building.ts`, 612 lignes)
qui pose en même temps la géométrie et les volumes de collision, bloc par bloc.
Il n'y a ni éditeur, ni fichier de carte.

Deux chemins :

1. **Le refaire dans TrenchBroom**, à la main, en lisant le code comme un plan.
   Les cotes y sont toutes : trame de 192 unités par étage, couloir large de
   192, cage au sud-ouest, deux appartements au nord. Le facteur d'échelle
   humaine 0,625 disparaît — id Tech 4 travaille déjà en pouces.
2. **Écrire un exportateur** : `building.ts` sait déjà énumérer ses blocs, il
   suffit d'écrire des brushes au format `.map` au lieu de géométrie Three.js.
   Une centaine de lignes de TypeScript, jetables après usage.

Le second chemin donne l'immeuble entier en une fois et garde le plan vérifié
par les essais. Recommandé, mais pas avant la milestone 8.

*Milestone 2* : la migration room n'a finalement pas été faite à la main mais
écrite par un script (`tools/maps/make_migration_room.py`, sur un petit
atelier de brushes, `tools/maps/mapkit.py`), comme l'aire d'essai
`move_test`. Les cotes restent lisibles et la carte se régénère à
l'identique. Le fichier produit est un `.map` que TrenchBroomBFG ouvre, mais
l'éditeur n'est pas encore configuré pour UNHOLY (déclarations d'entités,
dossier des textures) : c'est un préalable au travail à la main.

---

## 4. Arborescence proposée

```
unholy-idtech/
├── engine/                    sous-module git : RBDOOM-3-BFG, jamais modifié
│                              (si une correction est nécessaire, elle vit dans
│                               patches/ et on sait pourquoi)
├── patches/                   correctifs moteur, un fichier par raison
├── neo/                       code jeu UNHOLY, compilé avec le moteur
│   └── unholy/
│       ├── UnholyGame.cpp/.h              idGameLocal spécialisé
│       ├── player/
│       │   ├── UnholyPlayer.cpp/.h        base commune
│       │   ├── UnholyMilitary.cpp/.h      déplacement lourd, lampe, fusil
│       │   └── UnholyDemon.cpp/.h         griffes, pounce, crawl
│       ├── weapons/
│       │   ├── UnholyWeapon.cpp/.h
│       │   ├── UnholyRifle.cpp/.h
│       │   └── UnholyFlashlight.cpp/.h
│       ├── ai/
│       │   ├── UnholyMilitaryAI.cpp/.h
│       │   └── UnholyDemonAI.cpp/.h
│       ├── match/
│       │   ├── UnholyMatch.cpp/.h         règles, camps, victoire
│       │   ├── UnholyArtifact.cpp/.h
│       │   └── UnholyExtraction.cpp/.h
│       └── physics/
│           └── UnholySurfaceWalk.cpp/.h   wall/ceiling crawl
├── content/                   données du jeu, aucune donnée de Doom 3
│                              (le mode autonome du moteur lit content/,
│                               pas base/)
│   ├── def/                   entités, armes, personnages
│   ├── maps/                  migration_room, demon_movement_test, immeuble
│   ├── materials/             .mtr
│   ├── textures/unholy/       nos quatre textures, converties
│   ├── models/unholy/         fusil, réglette, personnages
│   ├── sounds/unholy/
│   ├── guis/unholy/           HUD, menu
│   └── script/                scripts d'armes et d'IA
├── tools/
│   └── building-export/       exportateur .map depuis le prototype (M8)
├── MIGRATION.md               ce document
├── docs/
│   ├── FEEL.md                valeurs mesurées du prototype, à retrouver
│   └── BUILD.md               comment compiler sur macOS (livré en M1)
└── reference/                 lien vers ../unholy, le prototype
```

Règle : `engine/` ne bouge pas. Tout ce qui est à nous est dans `neo/unholy/`
et `content/`. On doit pouvoir répondre à « qu'est-ce que j'ai modifié du
moteur ? » en listant `patches/`.

État à la milestone 2 : `neo/unholy/player/UnholyPlayer` (le militaire) et
`neo/unholy/debug/UnholyMoveTest` (le banc d'essai du déplacement). Le reste de
l'arbre arrive avec les milestones qui en ont besoin ; le militaire n'a pas
encore de classe à lui, `UnholyPlayer` en tient lieu jusqu'à l'arrivée du
possédé.

---

## 5. Risques et blocages

Par ordre de ce qui peut arrêter le projet.

| # | Risque | Pourquoi c'est sérieux | Comment on le lève |
| --- | --- | --- | --- |
| 1 | **Démarrer sans les données de Doom 3** | Le moteur attend des polices, des GUI, des matériaux par défaut et des `.resources`. Le dépôt livre `base/def`, `materials`, `script`, `textures`, mais pas tout. Un jeu standalone sans une seule ligne de Doom 3 n'est pas le cas d'usage prévu. | **Milestone 1.** On mesure exactement ce qui manque pour afficher une console et une map vide, et on remplace un à un. C'est le premier livrable, avant tout gameplay. |
| 2 | **Vulkan via MoltenVK sur macOS** | RBDOOM a retiré OpenGL. Sur Mac, Vulkan passe par MoltenVK : une couche de traduction de plus, un SDK à installer, et un point de panne hors de notre code. | Milestone 1, et il se règle **dans** RBDOOM : version du SDK Vulkan, variables d'environnement MoltenVK, drapeaux de compilation. Changer de moteur n'est pas une sortie. Si la machine bloque, la question devient « sur quelle machine on développe », pas « quel moteur ». |
| 3 | **Wall / ceiling crawl** | Rien de natif. `idPhysics_Player` suppose une gravité vers le bas et un sol. Réorienter la gravité par la normale de surface touche la physique, la caméra, l'animation et l'IA. | Milestone 6, isolée, sur sa propre map, avant toute IA démon. C'est le brief §12 et c'est le bon découpage. |
| 4 | ~~GPL-3~~ **Décidé** | La GPL-3 est acceptée. Le jeu sera vendu ; la source du programme dérivé sera publiée, les assets restent à nous. | Voir § 1.4. Reste à faire relire la structure avant la sortie commerciale. |
| 4b | **Steamworks et GPL** | Lier une bibliothèque propriétaire à un programme GPL demande un examen sérieux. | Milestone dédiée, après audit. Aucune milestone de gameplay n'en dépend. |
| 5 | **C++ et outils** | Le projet passe de TypeScript à du C++ de 2012, avec `.def`, `.script`, `.mtr`, `.gui` — quatre langages de données à apprendre. | Le découpage en milestones sert à ça : la 2 ne demande qu'un `.def` et un `.map`. |
| 6 | **Perdre le réglage du ressenti** | Des dizaines de valeurs ont été mesurées à l'image (prise en main, faisceau, plancher de lumière, inertie). Elles ne se transposent pas telles quelles : unités et rendu diffèrent. | `docs/FEEL.md` les consigne avec **la méthode** qui les a produites, pas seulement les nombres. On les retrouve par la même méthode. |
| 7 | **Les `.glb` sont lourds** | 23 Mo pour le fusil, 6 Mo pour la réglette, avec des normales en 4096². | À la conversion : réduire les textures, garder le maillage. |

---

## 6. Les milestones

L'ordre du brief, avec deux ajouts en fin de course.

| # | Contenu | État |
| --- | --- | --- |
| 0 | **Audit** — ce document. | fait |
| 1 | Compiler et lancer UNHOLY en jeu autonome. | fait |
| 2 | Migration room et contrôleur joueur. | fait |
| 3 | Fusil, viewmodel, tir. | fait |
| 4 | Lampe, éclairage, ombres. | |
| 5 | Possédé au sol. | |
| 6 | Wall / ceiling crawl, sur sa propre map. | |
| 7 | Pounce et combat du possédé. | |
| 8 | Prototype d'un étage. | |
| 9 | Artefact, extraction, règles de partie. | |
| 10 | Bots militaires. | |
| 11 | Bots possédés. | |
| 12 | Immeuble complet. | |
| 13 | Éclairage, audio, finition, optimisation. | |
| **14** | **Audit de licence et intégration Steamworks.** | |
| **15** | **Préparation de la sortie** : publication de la source, page Steam, empaquetage. | |

## 7. Milestone 1 — le plan exact

**Objectif : un binaire `unholy` qui démarre sur ta machine, affiche sa console,
et charge une map vide. Aucun gameplay.**

C'est la milestone qui valide ou invalide le choix du moteur. Elle ne code
rien du jeu.

1. **Cloner le moteur en sous-module.**
   `git submodule add https://github.com/RobertBeckebans/RBDOOM-3-BFG engine`
2. **Compiler tel quel, sans UNHOLY**, avec les dépendances Homebrew
   (CMake, Vulkan SDK / MoltenVK, OpenAL, ffmpeg optionnel).
   *Critère : le binaire se lance et ouvre une fenêtre.*
3. **Mesurer ce qu'il réclame** au démarrage sans données de Doom 3 : lire la
   console, lister chaque fichier manquant. C'est le livrable le plus important
   de la milestone — il chiffre le risque n°1.
4. **Fournir le minimum vital** : police de console libre, matériau par défaut,
   `default.gui`, damier de texture manquante.
   *Critère : la console s'affiche sans erreur fatale.*
5. **Renommer le jeu** : binaire `unholy`, dossier `base/` à nous, identité de
   fenêtre. C'est le chemin de modding recommandé pour un standalone.
6. **Charger une map vide** — une boîte, une lumière, un point d'apparition —
   compilée depuis TrenchBroom.
   *Critère : on voit la boîte, on ne tombe pas au travers.*
7. **`docs/BUILD.md`** : les commandes exactes qui ont marché sur ta machine.

Ce qui n'est **pas** dans cette milestone : le contrôleur joueur, le fusil, la
lampe, l'immeuble, le moindre asset d'UNHOLY.

Fin de milestone : on sait ce que coûte le standalone, et on a une image à
l'écran. Les deux inconnues qui pouvaient coûter des semaines — démarrer sans
les données de Doom 3, et faire tourner Vulkan sur un Mac — sont levées avant
qu'une ligne de gameplay soit écrite.
