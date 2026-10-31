#!/bin/sh
set -u
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
cd "$HERE/grainbrick-v4" || exit 1
exec python3 -B v4_entry.py >> v4.log 2>&1
