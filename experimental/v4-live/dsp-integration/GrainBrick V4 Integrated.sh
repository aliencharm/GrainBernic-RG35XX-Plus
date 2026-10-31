#!/bin/sh
set -u
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
APP="$HERE/grainbrick-v4-live"
cd "$APP" || exit 1
exec python3 -B integrated_entry.py >> v4-integrated.log 2>&1
