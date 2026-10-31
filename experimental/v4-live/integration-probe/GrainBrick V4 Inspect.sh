#!/bin/sh
# Separate metadata inspection; never launches the GrainBrick audio engine.
set -u
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
APP="$HERE/grainbrick-v4-live"
exec python3 -B "$APP/inspect_v3.py" --v3 "$HERE/grainbrick-beta" --output "$APP/v3-api-report.json" >> "$APP/v3-inspect.log" 2>&1
