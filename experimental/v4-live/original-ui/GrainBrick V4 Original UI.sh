#!/bin/sh
set -u
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
APP="$HERE/grainbrick-v4-live"
cd "$APP" || exit 1
chmod +x ./v4-live || exit 1
export SDL_AUDIODRIVER=dummy
exec python3 -B original_ui_entry.py >> v4-native-ui.log 2>&1
