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
