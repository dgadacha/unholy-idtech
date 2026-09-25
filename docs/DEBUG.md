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
| `tools/movetest.sh [scénario] [+réglage valeur ...]` | le banc depuis le terminal, dans l'aire `move_test`, sans son |
| `tools/movetest.sh tir` | le fusil : une rafale, une rafale épaulée, un rechargement, face à la cible de la migration room ; le chargeur et la réserve relevés à chaque étape |
| `unholy_pressKey <touche>` | presse puis relâche une touche, comme le clavier, avec les noms de `bind` (`ESCAPE`, `TAB`, `MOUSE1`...) : un essai automatique ne peut pas taper dans la fenêtre du jeu |

Le banc prend le clavier et la souris, replace le joueur au départ entre deux
scénarios, arrêté, endurance pleine. Ses chiffres sont consignés dans
[`FEEL.md`](FEEL.md), § 8. Pour comparer un réglage :

```bash
tools/movetest.sh tout +pm_accelmode 0
```

## Écouter le mixage sans le jouer

Les essais tournent sans son (`+set s_noSound 1`) : un banc qui tire n'a rien
à faire dans les haut-parleurs. Mais sans son, le moteur ne charge aucun
fichier, et rien ne dit si les sons partent, quand, et à quel niveau.

Le moteur joue par OpenAL Soft, qui sait écrire son mixage dans un fichier au
lieu de la carte son. Un fichier de réglages le lui demande :

```ini
# alsoft.ini
[general]
drivers = wave

[wave]
file = /chemin/vers/mixage.wav
```

```bash
ALSOFT_CONF=alsoft.ini ALSOFT_DRIVERS=wave tools/run.sh +set logFile 2 +set com_smp 0 \
	+map migration_room +wait 120 +setviewpos 56 0 66 23 +wait 30 +unholy_moveTest tir
```

Le journal doit dire `No capture backend available`, le signe que seule la
sortie fichier est ouverte. Le fichier grossit en temps réel, en 32 bits
flottants, stéréo, 48 kHz ; au-delà de 1, le son saturerait. C'est ainsi
qu'ont été réglés les volumes du fusil ([`FEEL.md`](FEEL.md), § 9).

## Pièges du moteur, déjà payés

Ils ont tous coûté du temps, pendant les milestones 2 et 3. Ils valent pour
tout essai automatique.

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
- **Pas plus de 32 commandes `+` sur la ligne de commande.** Le moteur les
  range dans un tableau de 32 places sans vérifier, et plante au démarrage
  au-delà, avant d'avoir rien écrit. Une suite de captures passe par un
  `.cfg` déposé dans `~/Library/Application Support/UNHOLY/content/` et lancé
  par `+exec`.
- **La sortie standard redirigée arrive par paquets.** Un essai qui attend
  une ligne sur la sortie standard l'attend pour rien, et l'arrêt du jeu la
  perd. Attendre sur le journal (`+set logFile 2`), écrit ligne à ligne.
- **Une capture d'écran dure environ 200 ms**, pendant lesquelles le jeu
  continue. Une suite de `screenshot` séparés d'une image donne une image
  tous les cinq ou six pas de jeu, pas des images consécutives.
- **`rotate` dans une matière demande les tables `sinTable` et `cosTable`.**
  Sans elles, la matière est abandonnée et ne dessine plus rien, avec pour seul
  message `no sinTable for rotate defined`, qui ne nomme pas la matière. Elles
  sont dans `content/materials/engine.mtr`.
- **Le blanc et le noir du moteur doivent se mélanger** (`blend blend`,
  `colored`) pour servir en 2D. Déclarés comme une simple image, `_white`
  dessinait un réticule invisible.
- **Un script ne connaît que les événements qu'on lui déclare.** Doom 3 les
  déclarait tous dans ses propres scripts ; les nôtres les déclarent un à un
  (`content/script/unholy_events.script`), sinon la compilation échoue sur
  `Unknown value`. Le langage n'a pas non plus `true` ni `false`
  (`doom_defs.script` les définit), et ne compare pas deux booléens : une
  variable que le code C++ écrit est un nombre.
- **`idWeapon` n'avance pas sans script.** L'arme du moteur tient son
  automate d'états dans un objet de script ; c'est là que vit le comportement
  du fusil, les valeurs restant dans sa déclaration.
- **La première recharge du chargeur vient de deux endroits** : la
  déclaration du joueur (`clip0`) et celle de l'arme. Sans `clip0`, le moteur
  remplit le chargeur deux fois sur la réserve, et la partie commence avec
  60 cartouches de réserve au lieu de 90.
- **Une animation glTF a besoin d'une piste sur l'os racine**, sans quoi le
  moteur ne la trouve pas (`Could not find action`). Mais une rotation ou une
  translation sur cette racine le fait passer par un chemin qui compose deux
  fois les rotations : l'arme sort à l'envers, dans la main gauche. La
  conversion ne laisse donc à la racine qu'une piste d'échelle, immobile
  (`tools/assets/retro_rifle.py`, `root_scale_only`).
- **Sans corps, le militaire fait signaler trois os** (`bone_hips`,
  `bone_chest`, `bone_head`) à chaque carte. C'est attendu, jusqu'à ce qu'il
  ait un modèle.
- **Les menus de BFG n'existent pas chez nous.** Échap en partie ouvrait le
  menu de pause, invisible faute de son SWF, et le jeu restait en pause pour
  de bon. Le correctif 0010 l'empêche : en partie, Échap ne fait plus rien
  jusqu'au menu d'UNHOLY (milestone 9). Même chemin pour le menu que BFG
  ouvre à la mort du joueur, qui ne peut pas encore mourir : il n'a pas été
  essayé. Pour quitter : `quit` à la console, ou Cmd+Q.
