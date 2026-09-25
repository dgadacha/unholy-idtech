#!/usr/bin/env bash
#
# Construit UNHOLY sur macOS : le moteur RBDOOM-3-BFG en mode autonome, avec
# nos correctifs appliques.
#
# Le moteur est un sous-module qu'on ne modifie pas a la main. Ce qu'on y
# change vit dans patches/, un fichier par raison, et ce script l'applique.
# `git -C engine diff` montre donc toujours exactement ce que le jeu doit au
# moteur, et rien d'autre.
#
# Mode autonome : le moteur lit content/ au lieu du base/ de Doom 3, et les
# textures de lumiere passent en RGBA8. C'est l'option STANDALONE du moteur.
#
#   tools/build.sh            configure si besoin, puis compile
#   tools/build.sh --clean    repart de zero

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build/unholy"
VULKAN_VERSION="1.4.357.1"

if [ "${1:-}" = "--clean" ]; then
	rm -rf "$BUILD"
fi

# SDK Vulkan : DXC pour compiler les shaders, MoltenVK pour les executer.
VULKAN_ENV="$HOME/VulkanSDK/$VULKAN_VERSION/setup-env.sh"
if [ ! -f "$VULKAN_ENV" ]; then
	echo "SDK Vulkan $VULKAN_VERSION introuvable dans ~/VulkanSDK (voir docs/BUILD.md)." >&2
	exit 1
fi
# Le script de LunarG lit des variables qu'il ne definit pas : le mode strict
# est suspendu le temps de le charger.
set +u
# shellcheck disable=SC1090
source "$VULKAN_ENV" > /dev/null
set -u

# Correctifs du moteur, appliques une seule fois chacun.
for patch in "$ROOT"/patches/*.patch; do
	[ -e "$patch" ] || continue
	if git -C "$ROOT/engine" apply --check "$patch" 2> /dev/null; then
		git -C "$ROOT/engine" apply "$patch"
		echo "correctif applique : $(basename "$patch")"
	elif git -C "$ROOT/engine" apply --reverse --check "$patch" 2> /dev/null; then
		: # deja en place
	else
		echo "le correctif $(basename "$patch") ne s'applique plus au moteur" >&2
		exit 1
	fi
done

# Le code du jeu vit dans neo/unholy, hors du moteur : le correctif 0005
# l'ajoute a la compilation quand UNHOLY_GAME_DIR le designe. Un fichier
# ajoute ou retire y est vu tout seul, sans reconfigurer.
GAME_DIR="$ROOT/neo/unholy"

if [ ! -f "$BUILD/Makefile" ] || ! grep -q "^UNHOLY_GAME_DIR:" "$BUILD/CMakeCache.txt"; then
	OPENAL_PREFIX="$(brew --prefix openal-soft)"
	# Cible macOS 11 : c'est le minimum du moteur sur Apple Silicon.
	cmake -G "Unix Makefiles" -S "$ROOT/engine/neo" -B "$BUILD" \
		-DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS_RELEASE="-DNDEBUG" \
		-DCMAKE_OSX_SYSROOT=macosx -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 \
		-DSTANDALONE=ON -DAPP_NAME=Unholy \
		-DFFMPEG=OFF -DBINKDEC=ON -DUSE_MoltenVK=ON \
		-DOPENAL_LIBRARY="$OPENAL_PREFIX/lib/libopenal.dylib" \
		-DOPENAL_INCLUDE_DIR="$OPENAL_PREFIX/include" \
		-DUNHOLY_GAME_DIR="$GAME_DIR" \
		-Wno-dev
fi

make -C "$BUILD" -j"$(sysctl -n hw.ncpu)"

# Les shaders compiles sortent dans engine/content/renderprogs2 : c'est le
# moteur qui fixe cet emplacement. Notre content/ les voit par un lien.
if [ ! -e "$ROOT/content/renderprogs2" ]; then
	ln -s ../engine/content/renderprogs2 "$ROOT/content/renderprogs2"
fi

echo "construit : $BUILD/Unholy"
