#!/usr/bin/env bash
#
# Banc d'essai du deplacement : lance le jeu dans l'aire move_test, y fait
# jouer un scenario du banc (unholy_moveTest), et imprime ce qu'il mesure.
#
#   tools/movetest.sh                         les six scenarios courts
#   tools/movetest.sh endurance               un seul scenario
#   tools/movetest.sh tout +pm_accelmode 0    avec un reglage change
#
# Le jeu ecrit son journal ligne a ligne (logFile 2) ; le script le lit et
# arrete le jeu a la fin du banc. Il ne passe pas par `quit` : sous macOS, la
# fermeture du moteur se bloque parfois (VKimp_Shutdown ferme la fenetre hors
# du fil principal, qui l'attend).
#
# Le jeu tourne ici dans le fil principal (com_smp 0) : ce que le fil de jeu
# imprime ne va que sur la sortie standard, jamais dans le journal. La
# simulation, elle, est la meme, au meme pas fixe de 60 Hz.
#
# La fenetre du jeu ne doit pas perdre le focus pendant l'essai : le moteur
# met alors le jeu en pause, et le banc s'arrete de compter.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCENARIO="${1:-tout}"
shift || true

SAVE_DIR="$HOME/Library/Application Support/UNHOLY/content"
LOG_NAME="movetest.log"
LOG="$SAVE_DIR/$LOG_NAME"
TIMEOUT=240

mkdir -p "$SAVE_DIR"
rm -f "$LOG"

# Attention a l'ordre : le moteur applique tous les `+set` de la ligne de
# commande des le demarrage, avant le reste. Une variable qui doit changer a
# son tour s'ecrit `+nom valeur`. Les reglages passes au script arrivent
# ainsi apres le chargement de la carte, donc apres ceux que le militaire
# applique a son apparition, et les remplacent.
"$ROOT/tools/run.sh" +set logFile 2 +set logFileName "$LOG_NAME" +set com_smp 0 \
	+map move_test +wait 120 "$@" +unholy_moveTest "$SCENARIO" > /dev/null 2>&1 &
GAME=$!

finished=0
for _ in $(seq "$TIMEOUT"); do
	if grep -q '^\[mouvement\] fin' "$LOG" 2> /dev/null; then
		finished=1
		break
	fi
	if ! kill -0 "$GAME" 2> /dev/null; then
		break
	fi
	sleep 1
done

kill -9 "$GAME" 2> /dev/null || true
wait "$GAME" 2> /dev/null || true

grep '^\[mouvement\]' "$LOG" || true
if [ "$finished" -ne 1 ]; then
	echo "le banc n'est pas alle au bout (journal : $LOG)" >&2
	exit 1
fi
