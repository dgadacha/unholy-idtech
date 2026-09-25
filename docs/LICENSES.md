# Dépendances et licences

Registre tenu au fil de l'eau. **Rien n'entre dans le projet sans une ligne
ici.** Une police libre ajoutée à la va-vite pendant une milestone est
exactement ce qui coûte cher trois ans plus tard, au moment de vendre.

UNHOLY est destiné à la vente. La GPL-3 est acceptée comme contrainte : elle
autorise la vente, et impose de publier la source correspondante du programme
dérivé. Les données du jeu, elles, restent sous nos propres conditions.

## Ce qui est publié sous GPL-3

| Élément | Licence | Origine |
| --- | --- | --- |
| Moteur RBDOOM-3-BFG | GPL-3.0 + conditions supplémentaires d'id Software | `github.com/RobertBeckebans/RBDOOM-3-BFG` |
| Nos modifications du moteur | GPL-3.0 | `patches/` |
| Code de jeu UNHOLY (C++) | GPL-3.0 — lié au moteur, donc programme dérivé | `neo/unholy/` |
| Scripts de compilation | GPL-3.0 | `tools/build.sh`, et le `CMakeLists.txt` du moteur tel que le modifient les `patches/` |

À lire avant toute sortie commerciale : `LICENSE_EXCEPTIONS.md` du dépôt
moteur, qui liste les composants non-GPL, et les conditions supplémentaires de
la publication Doom 3 BFG.

## Ce qui reste sous nos conditions

Données lues à l'exécution : ce ne sont pas des morceaux du programme. Le dépôt
moteur traite d'ailleurs les données de Doom 3 BFG de la même façon — elles ne
font pas partie de sa publication GPL.

| Catégorie | Emplacement | Licence |
| --- | --- | --- |
| Modèles et animations | `content/models/unholy/` | à nous |
| Textures et matières | `content/textures/unholy/`, `content/materials/` | à nous |
| Sons et musiques | `content/sound/unholy/` | à nous |
| Cartes | `content/maps/` | à nous |
| Interface | `content/guis/unholy/` | à nous |

## Assets tiers

Un par ligne, avec la licence **et le lien de la source**, au moment où il
entre. Pas après.

| Asset | Usage | Licence | Source | Entré en |
| --- | --- | --- | --- | --- |
| Barlow Condensed Medium | Police par défaut du moteur (`newfonts/Unholy`) | SIL OFL 1.1 | github.com/google/fonts, `ofl/barlowcondensed` — licence dans `tools/fontgen/sources/` | M1 |
| IBM Plex Mono Regular | Jeu de caractères de la console (`bigchars`) | SIL OFL 1.1 | github.com/google/fonts, `ofl/ibmplexmono` — licence dans `tools/fontgen/sources/` | M1 |
| Retro Weapon Pack V1, par kuptchi | Fusil, bras et leurs animations, flamme du tir (`content/models/retro/`, `content/textures/retro/`) | Gratuit pour les projets personnels et commerciaux, attribution non requise mais appréciée (`Readme.pdf` de l'archive) | archive `RetroWeaponPack_V1.zip` ; auteur joignable sur Discord, `kuptchi` ; page de téléchargement à consigner | M3 |

La licence OFL impose de livrer le texte de la licence avec la police, et
interdit de vendre la police seule. Les deux sont respectés tant que le texte
voyage dans le paquet.

**Le Retro Weapon Pack n'est pas dans le dépôt.** Son Readme autorise l'usage
dans un jeu, commercial compris, mais ne dit rien de la redistribution de ses
fichiers, et le dépôt est public. Seuls le script de conversion
(`tools/assets/`) et nos déclarations (`content/def/unholy_weapons.def`,
`content/materials/retro_weapons.mtr`) sont versionnés ; les fichiers
convertis sont produits sur chaque machine depuis l'archive et ignorés par
git. Le jeu vendu les embarquera convertis : c'est l'usage que le Readme
autorise. La conversion les modifie (squelettes des bras et du fusil réunis,
animations recalculées, unités, flamme estompée vers le bord), ce que le
Readme ne défend pas : il conseille lui-même un outil pour retoucher les
textures. L'auteur sera crédité au générique, même sans obligation.

Assets du prototype Three.js à requalifier avant reprise :

| Asset | Usage | À vérifier |
| --- | --- | --- |
| `assault_rifle.glb` | Fusil du militaire | Abandonné en M3, jamais repris : le Retro Weapon Pack le remplace, avec les bras et les animations |
| `fluorescent_fixture.glb` | Réglette de plafond | Générée par Meshy AI — conditions du service |
| `wall/floor/ceiling/glass` | Matières de l'immeuble | Origine et conditions ; à reproduire en PBR complet de toute façon |
| `logo.png` | Titre | À nous |

## Bibliothèques livrées avec le jeu

| Bibliothèque | Rôle | Licence | Origine |
| --- | --- | --- | --- |
| MoltenVK | Vulkan sur Metal | Apache-2.0 | SDK Vulkan de LunarG 1.4.357.1 |
| Chargeur Vulkan | Vulkan | Apache-2.0 | SDK Vulkan de LunarG |
| OpenAL Soft | Audio | LGPL-2.0 | Homebrew — lien dynamique, à livrer remplaçable |
| SDL2 | Fenêtre, entrées | zlib | Homebrew (`sdl2-compat`) |

Outils de construction, non livrés : DXC (compilateur de shaders, NCSA), ispc,
CMake, Blender (GPL-2.0 ou ultérieure ; il convertit le pack d'armes, et sa
licence ne s'étend pas à ce qu'il produit), Python avec Pillow et NumPy.
OpenAL Soft est sous LGPL : il doit rester une bibliothèque dynamique que
l'utilisateur peut remplacer, ce qui est le cas aujourd'hui.

## Contenu écrit ou généré par nous

Tout ce qui est versionné dans `content/` est à nous : écrit à la main
(déclarations, matières, scripts, commandes) ou généré par nos outils. Rien
n'est repris du `base/` livré avec le moteur, dont les `.def` et `.script`
sont ceux de Doom 3 et ne font pas partie de la publication GPL d'id. Les deux
dossiers `retro/`, modèles et textures, ne sont pas versionnés et ne sont pas
à nous : ils sortent du Retro Weapon Pack (plus haut).

| Contenu | Outil | Entré en |
| --- | --- | --- |
| Police, jeu de caractères de la console | `tools/fontgen/` depuis les polices libres ci-dessus | M1 |
| Lumières par défaut, grille de test | écrites à la main, images générées | M1 |
| Textures de développement (teintes et trame d'un mètre) | `tools/textures/make_dev_textures.py` | M2 |
| Cartes `test_box`, `migration_room`, `move_test` | `tools/maps/` | M1, M2 |
| Cible d'entraînement, trou de balle | `tools/textures/make_dev_textures.py` | M3 |
| Sons du fusil, des impacts et de la cible | `tools/sounds/make_weapon_sounds.py`, synthèse à graine fixe | M3 |
| Comportement du fusil, événements du moteur déclarés pour les scripts | `content/script/`, écrits à la main | M3 |
| Tables de sinus et de cosinus que demande `rotate` | `content/materials/engine.mtr`, calculées | M3 |

Les teintes des textures de développement sont celles arrêtées pour l'immeuble
du prototype : des valeurs, pas des images reprises.

## Interdits

- **Aucun octet de Doom 3 ou de Doom 3 BFG dans le jeu distribuable.** Ni
  modèle, ni texture, ni son, ni carte, ni police, ni GUI. Localement, pour
  vérifier que le moteur tourne, c'est autre chose : ça ne franchit pas la
  porte du paquet.
- Aucun asset dont la licence n'est pas écrite ci-dessus.

## Reporté

**Steamworks.** La publication GPL n'inclut pas l'intégration Steam de Doom 3
BFG. Vendre sur Steam n'en dépend pas, mais lier une bibliothèque propriétaire
à un programme GPL demande un examen sérieux : milestone 14, après audit, et
aucune milestone de gameplay n'en dépend.
