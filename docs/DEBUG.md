# Outils de mise au point

Tout se tape dans la console (touche sous Échap), ou se passe au lancement :
`tools/run.sh +map migration_room +com_showFPS 2`.

## Ce que le moteur fournit déjà

Le brief (§ 20) demande de quoi voir les images par seconde, les triangles,
les lumières, les ombres, les collisions, les boîtes, l'état de l'IA, la
navigation, les noms des entités et les normales. RBDOOM a tout cela ; on ne
refait rien.

| Pour voir | Commande | Ce qu'elle montre |
| --- | --- | --- |
| Images par seconde | `com_showFPS 1` | le compteur seul |
| Temps d'image | `com_showFPS 2` | la fenêtre de performances : temps processeur et carte graphique |
| Triangles, appels de dessin | `r_showPrimitives 1` | surfaces, index et sommets dessinés |
| Lumières | `r_showLights 1` à `3` | numéro de chaque volume, puis ses plans, puis ses arêtes |
| Lumières par surface | `r_showLightCount 1` à `3` | les surfaces colorées selon le nombre de lumières qui les touchent |
| Ombres | `r_showShadows 1` ou `2` | les volumes d'ombre, quand elles passent par le stencil |
| Collisions | `g_showCollisionWorld 1`, `g_showCollisionModels 1` | le monde et les modèles tels que la physique les voit |
| Boîtes englobantes | `r_showViewEntitys 1` | les boîtes des modèles affichés (`2` : leurs numéros) |
| Noms des entités | `g_showEntityInfo 1` | boîtes et noms des entités |
| État de l'IA | `ai_debugMove 1`, `ai_debugTrajectory 1` | déplacements et trajectoires des monstres |
| Navigation | `aas_showAreas 1`, `aas_showPath <aire>` | les aires de navigation, un chemin |
| Normales | `r_showNormals <longueur>`, `r_showTangentSpace 1` | normales en fil de fer, repère tangent |
| Filaire | `r_showTris 1` à `4` | le maillage du monde |
| Matière visée | `r_showSurfaceInfo 1` | le nom de la matière sous le viseur |
| Portails et zones | `r_showPortals 1` | les portails, en couleur selon qu'ils laissent voir |
| Grille de lumière | `r_showLightGrid 1` | les points de la grille d'éclairage |

Le debug propre au wall crawl (surface, normale, orientation, transitions)
viendra avec la milestone 6 : rien de natif ne le couvre.

## Ce qu'UNHOLY ajoute

| Commande | Rôle |
| --- | --- |
| `F3`, ou `toggle unholy_showMove` | le relevé du déplacement, en haut à gauche : vitesse en m/s et en unités, allure, endurance, attente avant le prochain saut, hauteur des yeux |
| `unholy_logMove 1` | le déplacement imprimé à chaque image : position, vitesse, chute, allure |
| `unholy_moveTest <scénario>` | le banc d'essai : il pilote le joueur par gestes fixes et imprime ses mesures. Un nom inconnu liste les scénarios |
| `tools/movetest.sh [scénario] [+réglage valeur ...]` | le banc depuis le terminal, dans l'aire `move_test` |

Le banc prend le clavier et la souris, replace le joueur au départ entre deux
scénarios, arrêté, endurance pleine. Ses chiffres sont consignés dans
[`FEEL.md`](FEEL.md), § 8. Pour comparer un réglage :

```bash
tools/movetest.sh tout +pm_accelmode 0
```

## Pièges du moteur, déjà payés

Ils ont tous coûté du temps pendant la milestone 2. Ils valent pour tout essai
automatique.

- **`+set` s'applique au démarrage, avant tout le reste.** Le moteur exécute
  tous les `+set` de la ligne de commande d'abord, quel que soit leur rang.
  Pour qu'une variable change à son tour, après le chargement d'une carte par
  exemple, écrire `+nom valeur`.
- **Les `wait` s'écoulent pendant le chargement.** L'écran de chargement
  compte des images comme les autres.
- **Ce que le fil de jeu imprime ne va pas au journal.** Avec `com_smp 1`, le
  réglage normal, le jeu tourne dans son propre fil, et ses impressions ne
  vont que sur la sortie standard ; ses avertissements sont jetés. Pour lire
  un essai dans le journal (`+set logFile 2`), lancer avec `+set com_smp 0` :
  la simulation est la même, au même pas de 60 Hz.
- **La perte du focus met le jeu en pause** (`com_pause 1`), et un jeu sans
  focus tourne à 15 Hz. Un essai automatique ne doit pas perdre le focus.
- **Quitter peut se bloquer sous macOS** : `VKimp_Shutdown` ferme la fenêtre
  hors du fil principal, qui l'attend. Les essais arrêtent donc le jeu
  eux-mêmes plutôt que de passer par `quit`.
- **`setviewpos` laisse le joueur suspendu** en l'air, sans gravité, tant qu'il
  ne bouge pas. Pour placer le joueur dans un essai, le banc déplace sa
  physique directement.
- **`content/default.cfg` ne vaut que pour un profil neuf.** Le profil du
  joueur (`savegame/profile.bin`) garde les touches et toutes les variables
  archivées, et les réapplique après `default.cfg`. Après avoir changé
  `default.cfg`, on l'applique à la console (`exec default.cfg`), ou l'on
  écarte `profile.bin` et `unholy.cfg`, dans
  `~/Library/Application Support/UNHOLY/content/`.
- **Un mot inconnu dans une matière la fait rejeter entière** : elle retombe
  sur la matière par défaut, avec un simple avertissement. `qer_trans`,
  courant chez Doom 3, en est un.
- **Une entité faite de brushes doit porter une clé `model`** égale à son nom.
  Sans elle, elle existe mais n'a ni image ni collision : une porte devient
  un trou. `tools/maps/mapkit.py` l'ajoute.
