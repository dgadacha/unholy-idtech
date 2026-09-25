#!/usr/bin/env bash
#
# Lance UNHOLY depuis l'arbre de travail, fenetre, sans videos d'intro.
# Les arguments supplementaires passent au moteur : tools/run.sh +map test

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Le script de LunarG lit des variables qu'il ne definit pas.
set +u
# shellcheck disable=SC1090
source "$HOME/VulkanSDK/1.4.357.1/setup-env.sh" > /dev/null
set -u
exec "$ROOT/build/unholy/Unholy" \
	+set fs_basepath "$ROOT" \
	+set r_fullscreen 0 +set r_windowWidth 1280 +set r_windowHeight 720 \
	+set com_skipIntroVideos 1 \
	"$@"
