#!/usr/bin/env bash
#
# Le fusil HD d'UNHOLY, du script au modele anime, sur cette machine.
#
#   tools/assets/build_hd_weapons.sh [chemin/vers/RetroWeaponPack_V1.zip] [taille des textures]
#
# Le fusil est a nous : modelise par tools/assets/hd/rifle.py sur des contours
# releves d'une photo de profil (tools/assets/hd/outlines/), ses matieres
# cuites par tools/assets/hd/build_rifle.py. Ses animations, et pour l'instant
# les bras, viennent du Retro Weapon Pack : le modele exporte les porte, il
# n'entre donc pas dans le depot (docs/LICENSES.md), pas plus que les textures
# cuites, que ce script refait a l'identique.
#
# Sorties : content/models/hd/rifle_view.glb, content/textures/unholy/fusil/.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PACK="${1:-${RETRO_PACK:-$HOME/Downloads/RetroWeaponPack_V1.zip}}"
SIZE="${2:-2048}"
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
WORK="$ROOT/build/assets"
MODELS="$ROOT/content/models/hd"
TEXTURES="$ROOT/content/textures/unholy/fusil"

# Le pack converti d'abord : ses textures de bras, et son dossier extrait.
"$ROOT/tools/assets/build_retro_weapons.sh" "$PACK"
BLEND="$WORK/retro/Assets/RetroWeaponsPack/FP_Arms/BlendFiles/FP_Arms_Rifle_01_Anims.blend"

mkdir -p "$WORK/hd" "$MODELS" "$TEXTURES"
echo "fusil HD : construction et cuisson (textures de ${SIZE} px)"
"$BLENDER" -b "$BLEND" --python "$ROOT/tools/assets/hd/build_rifle.py" -- \
	"$WORK/hd/fusil_hd.blend" "$WORK/hd/textures" "$SIZE" > "$WORK/hd/bake.log" 2>&1 || {
	tail -20 "$WORK/hd/bake.log" >&2
	exit 1
}
grep -E "^fusil|cuit|ecrites" "$WORK/hd/bake.log"
cp "$WORK/hd/textures/"*.png "$TEXTURES/"

echo "fusil HD : export, animations du pack"
"$BLENDER" -b "$BLEND" --python "$ROOT/tools/assets/retro_rifle.py" -- \
	"$MODELS/rifle_view.glb" --fusil-hd "$WORK/hd/fusil_hd.blend" > "$WORK/hd/export.log" 2>&1 || {
	tail -20 "$WORK/hd/export.log" >&2
	exit 1
}
grep -E "^animation|os, |fusil HD" "$WORK/hd/export.log"
echo "fusil HD pret : content/models/hd/rifle_view.glb"
