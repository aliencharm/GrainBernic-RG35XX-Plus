#!/bin/sh
set -u
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
cd "$HERE/grainbrick-v4" || exit 1
exec python3 -B audio_routing_report.py >> audio-routing-discovery.log 2>&1
