#!/usr/bin/env bash
#
# Convertit les armes du Retro Weapon Pack pour le moteur, sur cette machine.
#
#   tools/assets/build_retro_weapons.sh [chemin/vers/RetroWeaponPack_V1.zip]
#
# Le pack n'est pas dans le depot, ni ce qui en sort : son Readme autorise
# l'usage dans un jeu, commercial compris, mais ne dit rien de sa
# redistribution, et le depot est public. Ce script le lit la ou il a ete
# telecharge et depose le resultat dans content/models/retro et
# content/textures/retro, deux dossiers ignores par git (docs/LICENSES.md).
#
# Il faut Blender (brew install --cask blender) : le pack est en FBX et en
# .blend, que le moteur ne lit pas, et ses bras suivent le fusil par
# cinematique inverse, ce que seul Blender sait rejouer.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PACK="${1:-${RETRO_PACK:-$HOME/Downloads/RetroWeaponPack_V1.zip}}"
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
WORK="$ROOT/build/assets/retro"
MODELS="$ROOT/content/models/retro"
TEXTURES="$ROOT/content/textures/retro"

if [ ! -f "$PACK" ]; then
	echo "pack introuvable : $PACK" >&2
	exit 1
fi
if [ ! -x "$BLENDER" ]; then
	echo "Blender introuvable : $BLENDER (brew install --cask blender)" >&2
	exit 1
fi

mkdir -p "$WORK" "$MODELS" "$TEXTURES"
unzip -o -q "$PACK" -d "$WORK" \
	'Assets/RetroWeaponsPack/FP_Arms/BlendFiles/FP_Arms_Rifle_01_Anims.blend' \
	'Assets/RetroWeaponsPack/FP_Arms/Texture/*' \
	'Assets/RetroWeaponsPack/Guns/Rifle_01/Textures/*' \
	'Assets/RetroWeaponsPack/FX/Textures/*' \
	'Assets/RetroWeaponsPack/Readme.pdf'
PACK_DIR="$WORK/Assets/RetroWeaponsPack"

"$BLENDER" -b "$PACK_DIR/FP_Arms/BlendFiles/FP_Arms_Rifle_01_Anims.blend" \
	--python "$ROOT/tools/assets/retro_rifle.py" -- "$MODELS/rifle_view.glb" \
	> "$WORK/blender.log" 2>&1 || {
	tail -20 "$WORK/blender.log" >&2
	exit 1
}
grep -E "^animation|os, " "$WORK/blender.log"

python3 "$ROOT/tools/assets/retro_textures.py" "$PACK_DIR" "$TEXTURES"

echo "armes du Retro Weapon Pack converties dans content/models/retro et content/textures/retro"
