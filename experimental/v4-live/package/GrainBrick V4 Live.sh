#!/bin/sh
# Separate experimental V4: does not write the V3 installation.
set -u
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
APP="$HERE/grainbrick-v4-live"
cd "$APP" || exit 1
chmod +x ./v4-live || exit 1
export SDL_AUDIODRIVER=dummy
exec python3 -B frontend.py >> v4-ui.log 2>&1
