# Ce que le prototype savait du ressenti

Les valeurs ci-dessous ont été réglées à l'image, une par une, sous Three.js.
Elles **ne se transposent pas** telles quelles dans id Tech 4 : les unités
diffèrent, le rendu diffère, la courbe de tonalité diffère. Ce qui se transpose,
c'est **la méthode** et **l'intention**. Les nombres sont là pour qu'on sache
d'où l'on part et ce qu'on cherchait.

Les unités de carte du prototype : 40 unités par mètre, et le bâtiment était
mis à l'échelle humaine par un facteur 0,625 appliqué après coup. id Tech 4
travaille en pouces, l'ajustement disparaît.

---

## 1. La règle générale, apprise à ses dépens

**Un chiffre qui converge ne vaut pas validation.** Trois fois dans ce
prototype, un relevé ponctuel a annoncé une image deux fois plus sombre ou deux
fois plus claire qu'elle ne l'était, parce qu'il tombait dans un coin ou sur une
arête. Chaque valeur ci-dessous a fini par être arrêtée en regardant le rendu.

**Une mesure de silhouette ne remplace pas de regarder l'image.** Les bornes
projetées de l'arme disaient où était sa boîte, pas si elle avait l'air tenue.

**Un réglage d'éclairage ne survit pas au changement des matières qu'il
éclaire.** Le passage des surfaces peintes par le code aux surfaces
photographiées a demandé de diviser le plancher de lumière par six.

---

## 2. Le fusil tenu en main

Prise en main, en unités de carte. Le modèle arrivait normalisé à une unité de
long.

| Réglage | Valeur | Intention |
| --- | --- | --- |
| `length` | 26 | Longueur donnée au modèle dans le monde |
| `forward` | 9 | Distance du centre de l'arme à l'œil |
| `right` / `down` | 4 / 7 | Décalage vers l'épaule droite |
| `yaw` / `roll` | 0 / 0 | Arme droite, sans lacet de présentation |

Deux cadrages ont été essayés et le second retenu : un cadrage lointain poussé
dans le coin bas-droit (`forward` 22, `right` 12,5, `yaw` 20) qui coupait la
crosse par le bord, puis celui ci-dessus, plus proche, adopté quand des mains
ont été ajoutées au modèle. **Leçon** : la pose dépend de la présence des bras.

Cible pour id Tech 4, d'après le brief : orientation type Valorant, arme en bas
à droite, silhouette claire, bras gauche de soutien visible, sans occuper
l'écran.

## 3. Les mouvements du porte-arme

Quatre effets, sur quatre points d'accroche distincts, du plus lent au plus vif :
respiration, balancement de marche, inertie du regard, recul.

| Effet | Valeurs | Ce qu'on visait |
| --- | --- | --- |
| Inertie du regard | `shift` 150, `lift` 120, `yaw` 16, `pitch` 12 | Une masse au bout des bras |
| Ses bornes | `maxShift` 0,7 · `maxTurn` 0,045 rad | Un geste brusque ne sort pas l'arme du cadre |
| Balancement | `shift` 26, `lift` 34, `roll` 0,5 | Le pas se sent, il ne se voit pas |
| Respiration | amplitude 0,16 ; périodes 3,7 s et 2,3 s ; rotation 0,004 rad | Deux périodes incommensurables : une respiration périodique devient une horloge |
| Recul | retrait 2,2 · soulèvement 0,7 · cabrage 0,09 rad · écart 0,02 rad | L'arme réagit franchement, la visée non |

**Déplacements réellement obtenus à l'écran**, mesurés sur la projection du
canon, en part de l'image :

| Situation | Horizontal | Vertical |
| --- | --- | --- |
| Au repos (respiration seule) | 0,34 % | 0,65 % |
| En marche | 0,24 % | 1,04 % |
| Demi-tour franc | 0,15 % | 0,98 % |

Ces chiffres sont volontairement petits — c'est le choix qui a été fait en fin
de course. Pour référence, un réglage antérieur donnait 4,2 % au demi-tour, ce
qui se lisait nettement. **La fourchette utile est là : entre 0,3 % et 4 %.**

## 4. L'épaulé

| Réglage | Valeur | Intention |
| --- | --- | --- |
| `clearance` | 12 | Garde laissée derrière la crosse |
| `distance` | 13 | Plancher, si l'arme est courte |
| `raise` / `lower` | 0,13 s / 0,10 s | Montée plus lente que la descente, reprise en cours de geste |
| `worldFov` | 62° | Le monde se resserre (depuis 90°) |
| `weaponZoom` | 0,94 | **L'arme, presque pas** |
| `motion` | 0,35 | Ce qui reste des mouvements une fois épaulé |
| `sightDrop` | 0 | On vise au-dessus du boîtier |

Trois pièges rencontrés, qui se reposeront dans id Tech 4 :

1. **Resserrer la caméra de l'arme ne rapproche pas le décor, ça grossit
   l'arme.** À 48° elle couvrait l'écran entier.
2. **L'œil derrière l'optique met la crosse derrière la caméra**, et le plan de
   coupe la tranche en un objet gris plein écran. D'où la garde.
3. **L'optique du modèle est pleine** : sa glace est peinte sur le maillage. On
   vise donc juste au-dessus du boîtier. Un modèle avec une glace percée, ou le
   rendu d'optique d'id Tech 4, lèvera la contrainte.

## 5. La lampe tactique

| Réglage | Valeur |
| --- | --- |
| Portée | 1 600 unités |
| Demi-angle du cône | 0,44 rad (25°) |
| Pénombre | 1 (le cône n'ajoute aucun bord) |
| Puissance | 18 000 cd |
| Décroissance | 1,2 |
| Retard sur le regard | 14 /s |
| Décalage sous l'axe / sur le côté | 6 / 5 unités |

**Le profil du faisceau est l'essentiel**, et c'est lui qu'il faut retrouver :
une gélatine projetée, cœur plein sur un cinquième du rayon, débord large à un
dixième de l'intensité, trois salissures de quelques pour cent pour que l'œil
cesse de lire un cercle calculé.

Profil, du centre au bord : `1 · 0,94 · 0,68 · 0,34 · 0,19 · 0,13 · 0,08 ·
0,035 · 0`.

**Relevé sur la même cloison** : 200 niveaux sur 255 à un mètre, 110 à quatre
mètres, 35 au fond d'un couloir de quatorze. C'est cette décroissance qui donne
sa longueur au couloir.

## 6. L'éclairage de l'immeuble

L'échelle à tenir : **sans lampe, les volumes ; avec la lampe, les détails ; et
le noir total reste un endroit, pas un état.**

| Source | Valeurs |
| --- | --- |
| Plancher plat | 3,5, teinte `#16242f` |
| Ciel / sol (hémisphère) | 4,5, ciel `#16242f`, sol `#15110c` |
| Néon vivant | 62 cd, rayon 380, décroissance 1,15 ; tube émissif `#77887c` |
| Lampe de secours | 90 cd, rayon 400 |
| Baie de la cage d'escalier | 1 800 cd, rayon 900, décroissance 1,25, `#5a7ea8` |

Le plancher vient **surtout du ciel et du sol**, pas d'une ambiante plate :
c'est l'orientation des surfaces qui fait lire l'architecture, pas la clarté.
En id Tech 4, les volumes d'irradiance rendront ça mieux et pour moins cher.

Règles de composition retenues : un tube sur trois éclaire encore, et il change
de place d'un étage à l'autre — aucun étage n'a la même zone sûre. Chaque source
porte sa panne : batterie à bout (longues minutes franches puis à-coups),
starter fatigué (battement rapide), ou rien.

## 7. Où le temps a été perdu

À lire avant de recommencer.

- **Un panneau masqué suspend `requestAnimationFrame`.** Des heures à chercher
  un bug de visée qui n'existait pas : aucune image ne s'affichait entre deux
  mesures.
- **Les cartes de données arrivent en échantillonnage au plus proche et sans
  mipmaps.** Le grain qu'on prenait pour du bruit de rendu venait de là.
- **Le filtrage se règle à la création, pas à l'arrivée de l'image** : les
  matériaux travaillent sur des copies, et une copie ne suit que la matière de
  l'original.
- **Le grain d'une photo n'est pas du relief.** Il faut le lisser avant d'en
  tirer des pentes.
- **La position d'un groupe est dans le repère de son parent**, elle ne se
  divise pas par son échelle. L'arme se posait à une unité de l'œil.
- **Un éclat de tir posé dans le monde ne tombe pas là où le canon est
  dessiné**, l'arme tenue en main étant rendue par une autre caméra.

---

## 8. Le déplacement du militaire

Le prototype n'en savait rien : il se déplaçait comme un joueur de Quake III,
tel qu'hérité de l'arène d'origine (320 unités par seconde, accélération 10,
air 1). Il n'y avait rien à retrouver, tout était à régler. Le brief fixe
l'intention : lourd, précis, contrôlé, bien plus lent qu'un jeu d'arène, sans
bunny hop ni strafe jump.

Réglé à la milestone 2, sous id Tech 4. Les valeurs vivent dans
`content/def/unholy_base.def` : chaque clé `pm_` y règle la variable du même
nom à l'apparition du militaire, si bien qu'on essaie une valeur à la console
avant de l'y reporter. Une unité vaut un pouce, 2,54 cm.

| Réglage | UNHOLY | Moteur | Intention |
| --- | --- | --- | --- |
| Marche | 125 u/s, 3,2 m/s | 140 | Le pas d'une progression |
| Course | 210 u/s, 5,3 m/s | 220 | Vers l'avant seulement |
| Accroupi | 65 u/s, 1,65 m/s | 80 | |
| Endurance | 8 s, seuil 2 s, recharge 0,8/s | 24, 45, 0,75 | Six secondes de course pleine, deux pour retomber au pas |
| Accélération, frottement, arrêt | 8, 7,5, 50 | 10, 6, 100 | Un tiers de seconde pour prendre l'allure, un arrêt net |
| Calcul de l'accélération | la vitesse suit la direction voulue | Quake 2 | Jamais plus vite que l'allure voulue : le strafe jump disparaît |
| Contrôle en l'air | 0,5 | 1 | Presque rien à corriger une fois parti |
| Saut | 20 u, 51 cm | 48 u, 1,22 m | Enjamber, pas bondir |
| Avant de ressauter | 400 ms au sol, bouton relâché | rien | C'est ce qui tue le bunny hop |
| Réception | 70 % de la vitesse gardée | 100 % | Le poids de l'équipement |
| Marche franchie sans sauter | 12 u, 30 cm | 16 u | Une marche, pas un meuble |
| Gabarit debout | 72 u, yeux à 66 | 74, 68 | 1,83 m, les yeux à 1,68 m |
| Gabarit accroupi | 48 u, yeux à 42 | 38, 32 | 1,22 m, les yeux à 1,07 m |
| Balancement de la vue | 2,5 pas/s en marche, 3,3 en course ; tangage et roulis réduits de 60 à 75 %, montée de 20 % | 2,3 et 3,1 pas/s | Le pas se sent, il ne se voit pas |

Le champ de vision par défaut passe à 90° (`g_fov`, horizontal en 16/9 pour
ce moteur). Le prototype tournait à 90° **vertical**, soit 121° horizontal :
un réglage hérité, jamais choisi.

### Ce que mesure le banc d'essai

`tools/movetest.sh` pilote le militaire par gestes fixes dans l'aire
`move_test`. À droite, les mêmes gestes avec les réglages de mouvement du
moteur et les mêmes allures, pour voir ce que chaque réglage change.

| Mesure | UNHOLY | Réglages du moteur |
| --- | --- | --- |
| Marche : 90 % puis 99 % de l'allure | 0,25 s puis 0,35 s | 0,17 s puis 0,18 s |
| Marche : arrêt | 0,25 s, sur 30 cm | 0,22 s, sur 29 cm |
| Course : 90 % puis 99 % de l'allure | 0,25 s puis 0,33 s | 0,13 s puis 0,15 s |
| Course : arrêt | 0,32 s, sur 55 cm | 0,28 s, sur 61 cm |
| Accroupi : 90 % de l'allure | 0,38 s | 0,98 s |
| S'accroupir, se relever | 0,38 s chaque fois | 0,38 s |
| Saut | 51 cm, 0,38 s en l'air | 51 cm, 0,38 s |
| Appuis répétés pendant 4 s | 5 sauts, 0,80 s au plus court entre deux | 10 sauts, 0,40 s |
| Bunny hop : vitesse moyenne | 202 u/s, sous la course | 210 u/s, la course conservée |
| Strafe jump : vitesse maximale | 210 u/s, jamais au-dessus de la course | 249 u/s, 19 % de mieux |
| Endurance | 6,1 s de course pleine, retour au pas à 7,95 s, pleine après 8 s d'arrêt | |

Deux lectures :

- **Sauter ne rapporte rien.** Le strafe jump ne dépasse jamais l'allure de
  course, et le bunny hop va moins vite que courir, avec deux fois moins de
  sauts.
- **L'accroupi du moteur était pris dans le frottement.** Son seuil d'arrêt
  (100) dépasse l'allure accroupie (65) : sous ce seuil, le frottement mange
  presque toute l'accélération, et il fallait une seconde pour avancer. Le
  seuil à 50 le libère.

Ce que ces chiffres ne disent pas : si c'est juste. Ils disent que les
exploits sont fermés et que les temps sont ceux qu'on a visés. Le reste se
juge en jouant, relevé affiché (`F3`), et les valeurs se reprennent à la
console. Le banc est là pour que la retouche suivante se compare à celle-ci.

---

## 9. Le fusil du militaire

Posé à la milestone 3, sous id Tech 4. Le fusil et les bras viennent du Retro
Weapon Pack, avec leurs animations : c'est lui qui donne la prise en main, pas
un réglage. Le prototype avait appris que la pose dépend de la présence des
bras (section 2) ; le pack règle la question, les bras sont dessinés et
animés avec l'arme. Le fusil tient en bas à droite, le bras gauche de soutien
reste visible sous le garde-main.

Les valeurs vivent dans `content/def/unholy_weapons.def`, le comportement
dans `content/script/weapon_unholy_rifle.script`, les règles de déplacement
dans le joueur (`neo/unholy/player/UnholyPlayer.cpp`).

### Le tir

| Réglage | Valeur | Intention |
| --- | --- | --- |
| Cadence | 700 coups/min, soit 86 ms | Automatique, chaque coup compté |
| Chargeur, réserve | 30, 90 au départ (240 au plus) | Trois chargeurs : chaque rechargement compte |
| Dégâts | 25 par balle | La cible tombe en trois balles |
| Dispersion à la hanche | 2,2°, 3,7° en se déplaçant | On touche à courte distance, on arrose au-delà |
| Dispersion épaulé | 0,15° | La balle part où l'on vise |
| Recul de la vue | 0,9° vers le haut, 0,15° de côté, revenu en 90 ms | Le nez se relève à chaque coup, la visée reste |
| Munitions basses | 8 cartouches | Le compteur passe à l'orange |
| Rechargement | 3,5 s, l'animation du pack | Long : on le choisit, on ne le subit pas |

Le tir se compte d'un coup à l'autre, pas d'une image à l'autre : ce qui
dépasse d'un intervalle se reporte sur le suivant. Sans cela, 700 coups par
minute tombaient à 600, l'intervalle s'arrondissant à six images de 60 Hz.

**On ne tire pas en courant.** Tirer ou épauler coupe la course, et l'arme
attend d'être revenue en main pour partir. C'est ce qui fait choisir entre se
déplacer et combattre.

### L'arme dans la main

| Réglage | Valeur | Intention |
| --- | --- | --- |
| Balancement et dérive du moteur | coupés | Les animations respirent et marchent déjà : les deux s'ajoutaient |
| Retard sur le regard | moyenne sur 10 images, 0,12 par degré, 4° au plus | Une masse au bout des bras |
| Retard sur le déplacement | 350 ms, 0,003 | À peine : le corps porte l'arme |
| Épauler, relâcher | 0,13 s, 0,10 s (fondus des animations) | Les durées du prototype, qui se sentaient justes |
| Champ épaulé | 72°, depuis 90° | Grossissement de 1,38 ; le prototype allait à 1,66, avec une optique |

Couper le balancement et la dérive du moteur demande un réglage que
`idWeapon` n'avait pas : deux clés de l'arme, `weaponBobScale` et
`weaponDriftScale`, ajoutées par le correctif 0009 (défaut 1, le
comportement d'origine).

### Ce que le joueur lit

| Élément | Valeur | Intention |
| --- | --- | --- |
| Réticule | quatre branches de 5 px, écart suivant la dispersion réelle (2 px au moins) | Il dit où partira la balle, pas une décoration |
| Réticule masqué | épaulé, en course, en rechargement | On vise par l'arme, ou on ne vise pas |
| Compteur | chargeur en grand, réserve en petit, en bas à droite | Lisible d'un coup d'œil, loin de l'arme |

L'écart du réticule est la dispersion projetée à l'écran :
`tan(dispersion) / tan(champ / 2) × demi-largeur`. Il s'ouvre donc en marchant
et se referme à l'arrêt, comme la balle.

### L'éclat, les impacts, la cible

| Élément | Valeur | Intention |
| --- | --- | --- |
| Lumière de l'éclat | rayon 220 u (5,6 m), teinte `1 0,72 0,42`, 50 ms | Le tir éclaire l'arme, les mains et la pièce |
| Flamme au canon | 45 ms, tournée au hasard à chaque coup, 1,8 fois plus forte que l'image | À 1, dans le rendu HDR, elle ne faisait qu'un halo |
| Trous de balle | 3 u, 30 s | Le mur garde la trace de la rafale |
| Son de l'impact | selon la matière touchée : pierre, métal, bois | |
| Cible | 75 points, tombe en 0,35 s, reste 4 s, se relève en 0,6 s | De quoi s'entraîner sans recharger la carte |

### Le mixage

Tous les sons sont synthétisés par `tools/sounds/make_weapon_sounds.py` et
normalisés au même niveau ; c'est le volume de chaque son qui fait le mixage.

| Son | Volume | Pourquoi |
| --- | --- | --- |
| Tir | -3 dB | Les queues de coups se superposent en rafale |
| Impacts | -8 dB | Le moteur n'atténue que de 3 dB un son à cinq mètres |
| Choc sur la cible | -6 dB | |
| Chute de la cible | -4 dB | Entendue seule |
| Mécanique (chargeur, levier, clic à vide) | 0 dB | Entendue seule |

Sans ces volumes, le premier coup montait à 1,38 fois le plein niveau : le
tir, l'impact et le choc sur la cible partent au même instant. Relevé sur le
mixage du moteur, enregistré sans passer par les haut-parleurs
(`docs/DEBUG.md`) : la rafale plafonne à 0,82, le rechargement à 0,54.

### Ce que mesure le banc

`tools/movetest.sh tir`, face à la cible de la pièce principale : une rafale
de 1,5 s à la hanche, une rafale épaulée, un rechargement.

| Mesure | Relevé |
| --- | --- |
| Rafale de 1,5 s | chargeur 30 → 12 : 18 coups, 700 par minute |
| Rafale épaulée | chargeur 12 → 0 |
| Rechargement | chargeur 0 → 30, réserve 90 → 60 |
| Intervalle entre deux coups, à l'oreille | 87 ms en moyenne, pour 86 attendues |
| Sons du rechargement | chargeur sorti, remis, levier tiré, relâché : 0,92, 0,78 et 0,39 s d'écart à l'oreille, pour 0,92, 0,79 et 0,38 d'après les images relevées sur les os du pack |

Ce que ces chiffres ne disent pas : si le fusil a du poids. Le recul, le
retard sur le regard et le champ épaulé se jugent en jouant ; ils se
reprennent dans la déclaration de l'arme, puis `reloadDecls` à la console et
la carte relancée.
