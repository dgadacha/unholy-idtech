# Construire UNHOLY sur macOS

Commandes vérifiées le 25 septembre 2026 sur un MacBook Pro M3 Pro, macOS 26.6,
Xcode et clang 17, CMake 4.4. Le moteur est RBDOOM-3-BFG 1.6.0, commit
`ea29c00`.

## Une fois

```bash
# Outils de compilation et bibliothèques
brew install cmake ispc openal-soft sdl2
```

Le **SDK Vulkan de LunarG** est obligatoire : il est le seul à fournir DXC, le
compilateur qui transforme les shaders HLSL du moteur en SPIR-V, et MoltenVK,
qui exécute Vulkan sur Metal. Homebrew a MoltenVK et le chargeur Vulkan, mais
pas DXC. L'installation se fait dans le dossier personnel, sans droits
d'administrateur :

```bash
curl -L -o vulkansdk.zip https://sdk.lunarg.com/sdk/download/1.4.357.1/mac/vulkansdk-macos-1.4.357.1.zip
unzip vulkansdk.zip
./vulkansdk-macOS-1.4.357.1.app/Contents/MacOS/vulkansdk-macOS-1.4.357.1 \
  --root "$HOME/VulkanSDK/1.4.357.1" --accept-licenses --default-answer \
  --confirm-command install copy_only=1
```

`copy_only=1` n'écrit rien hors de `~/VulkanSDK`.

```bash
# Le moteur et ses sous-modules
git submodule update --init --recursive --depth 1
```

## À chaque fois

```bash
tools/build.sh           # applique les correctifs, configure si besoin, compile
tools/run.sh             # lance le jeu, fenêtré
tools/run.sh +map migration_room
```

`tools/build.sh --clean` repart de zéro. Compter deux à trois minutes sur un
M3 Pro.

Les cartes se compilent avec le `dmap` intégré au moteur, après un clone et à
chaque modification du `.map` :

```bash
tools/run.sh +dmap migration_room +dmap move_test +dmap test_box +quit
```

Les trois cartes sont écrites par des scripts (`tools/maps/`), les textures
de développement aussi (`tools/textures/`). On les relance après avoir changé
une cote ou une teinte :

```bash
python3 tools/maps/make_migration_room.py
python3 tools/textures/make_dev_textures.py
```

| Carte | Rôle |
| --- | --- |
| `migration_room` | La carte du brief : une pièce, un couloir, une porte, une lumière fixe, un néon, une zone sombre |
| `move_test` | L'aire d'essai du déplacement, 65 m de côté, escalier, obstacles, passage bas, pentes |
| `test_box` | La boîte de la milestone 1 |

Ses sorties (`.proc`, `.cm`) ne sont pas versionnées, pas plus que
`content/generated/`, où le moteur range les images et les cartes converties
au premier chargement. Tout se reconstruit seul.

## Ce que fait la construction

- **Mode autonome** (`-DSTANDALONE=ON`) : le moteur lit `content/` au lieu du
  `base/` de Doom 3, et stocke les textures de lumière en RGBA8.
- **Nom du binaire** (`-DAPP_NAME=Unholy`) : le moteur le prévoit, aucun
  correctif n'est nécessaire.
- **Le code du jeu** vit dans `neo/unholy/`, hors du moteur. Le correctif 0005
  l'ajoute à la compilation quand `UNHOLY_GAME_DIR` le désigne ; un fichier
  ajouté y est vu tout seul.
- **Vulkan par MoltenVK** (`-DUSE_MoltenVK=ON`), cible macOS 11.
- Les **shaders** sont compilés par le moteur dans
  `engine/content/renderprogs2`, emplacement qu'il fixe lui-même ; notre
  `content/renderprogs2` y pointe par un lien.

## Les correctifs du moteur

Le sous-module `engine/` n'est jamais modifié à la main. Ce qu'on y change vit
dans `patches/`, un fichier par raison, appliqué par `tools/build.sh`.
`git -C engine diff` montre donc exactement ce que le jeu doit au moteur.

| Correctif | Pourquoi |
| --- | --- |
| `0001-police-par-defaut` | La police par défaut était `Arial_Narrow`, une police commerciale de Monotype, en dur dans le code, et toute police introuvable y retombe. Elle devient `Unholy`, générée depuis une police libre. |
| `0002-joueur-sans-arme` | Le rendu de l'arme lisait sa déclaration sans vérifier qu'elle existait. Le marine de Doom 3 avait toujours ses poings, donc ce chemin ne servait jamais ; un joueur sans arme plantait au premier cycle. |
| `0003-joueur-sans-lampe-epaule` | La lampe d'épaule de BFG est une arme à part entière, avec sa déclaration et son script. Une clé `no_flashlight` permet au joueur de s'en passer : celle d'UNHOLY est montée sur le fusil. |
| `0004-identite-unholy` | Nom du jeu, dossier de sauvegarde, fichier de configuration. Le moteur garde son nom dans la version affichée. |
| `0005-code-du-jeu-hors-moteur` | La compilation reprend les sources de `neo/unholy/` quand `UNHOLY_GAME_DIR` les désigne. Notre code reste hors du sous-module. |
| `0006-physique-joueur-reglable` | L'accélération, le frottement, le seuil d'arrêt et le contrôle en l'air du joueur étaient des constantes : ils deviennent des variables `pm_`, aux mêmes valeurs par défaut. Et le second calcul d'accélération, déjà écrit par id et coupé par un `#if`, devient un choix (`pm_accelmode`). |
| `0007-interface-du-joueur-surchargeable` | `idPlayer::DrawHUD` devient virtuelle : le joueur d'UNHOLY dessine sa propre interface. |
| `0008-battement-de-coeur-sans-son` | Quand l'endurance baisse, le cœur accélère et son volume se réglait sur l'émetteur sonore du joueur sans vérifier qu'il existe. Un joueur qui n'a encore joué aucun son n'en a pas : le jeu tombait dès la première course. |

Le joueur d'UNHOLY hérite de celui du moteur : les correctifs 0002 et 0003
restent nécessaires tant qu'il n'a ni arme ni lampe, c'est-à-dire jusqu'aux
milestones 3 et 4. Les 0002 et 0008 corrigent de vrais défauts, qui méritent
d'être proposés en amont à RBDOOM.

**Défaut connu, non corrigé** : `idWeapon::Save` écrit aussi la déclaration de
l'arme sans la vérifier. La sauvegarde automatique de début de niveau est
coupée dans `content/default.cfg` — c'est un choix de conception : une partie
de dix minutes à une vie n'a rien à reprendre. L'arme d'UNHOLY aura toujours
une déclaration, le chemin ne se présentera plus.

## Ce que le moteur exige pour démarrer sans Doom 3

C'est le livrable principal de la milestone 1 : la mesure du risque n°1. Tout
a été relevé en lançant le moteur et en lisant sa console, un manque à la fois.

| Donnée | Fichier chez nous | Nature |
| --- | --- | --- |
| Police par défaut | `content/newfonts/Unholy/48.dat` + `.tga` | générée, `tools/fontgen` |
| Jeu de caractères de la console | `content/textures/bigchars.tga` | généré |
| Commandes par défaut | `content/default.cfg` | écrit à la main |
| Matières exigées par le moteur | `content/materials/engine.mtr` | `_default`, `_white`, `_black`, `_tracemodel` |
| Lumières par défaut | `content/materials/lights.mtr`, `content/lights/*.tga` | générées |
| Blanc des interfaces | `content/guis/assets/white.tga` | généré |
| Scripts de base | `content/script/doom_defs.script`, `doom_main.script` | vides, à dessein |
| Variables d'état du joueur | `content/script/unholy_player.script` | déclarations seules |
| Entités de base | `content/def/unholy_base.def` | monde, départ, lumière, porte, joueur |
| Règles appelées par leur nom | `content/def/unholy_rules.def` | munitions, dégâts |

Ce qui manque encore et ne bloque rien : les interfaces SWF de BFG (menu,
HUD, écran de chargement), les icônes de manettes, les écrans légaux, le modèle
du joueur et ses os. Le menu et le HUD d'UNHOLY seront les nôtres. Le modèle
du militaire n'a pas encore de source : la vue à la première personne n'en a
pas besoin, les bras viendront avec le fusil.

## Vérifier

```bash
tools/movetest.sh
```

Le banc d'essai du déplacement lance le jeu dans `move_test`, fait jouer six
scénarios au militaire et imprime ses mesures, à comparer à celles de
[`FEEL.md`](FEEL.md), § 8. Une quarantaine de secondes ; la fenêtre du jeu ne
doit pas perdre le focus pendant ce temps.

Les captures d'écran (`F12`, ou `screenshot` à la console) arrivent dans
`~/Library/Application Support/UNHOLY/content/screenshots/`.

Les essais automatiques ont leurs pièges, tous consignés dans
[`DEBUG.md`](DEBUG.md) : les `+set` appliqués au démarrage, les impressions du
fil de jeu absentes du journal, la pause à la perte du focus, la fermeture qui
se bloque sous macOS.
