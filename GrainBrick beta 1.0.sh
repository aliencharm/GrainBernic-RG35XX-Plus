#!/bin/sh
# GrainBrick beta 1.0 - RG35XX Plus / KNULLI Scarab 20260511
set -u
BETA_DIR=/userdata/roms/ports/grainbrick-beta
LOG="$BETA_DIR/beta_port_launcher.log"
cd "$BETA_DIR" || exit 1
mkdir -p "$BETA_DIR/samples" "$BETA_DIR/projects" "$BETA_DIR/recordings" || exit 1
for wav in "$BETA_DIR"/demo-samples/*.wav; do
  [ -f "$wav" ] || continue
  name=${wav##*/}; dest="$BETA_DIR/samples/$name"
  if [ ! -e "$dest" ] && [ ! -L "$dest" ]; then
    cp "$wav" "$dest" || exit 1
  fi
done
export GRAINBRICK_ROOT="$BETA_DIR"
export GRAINBRICK_SCREEN=640x480
export GRAINBRICK_SCALE=fast
export GRAINBRICK_FIT=1
export GRAINBRICK_BUTTONS=1
export GRAINBRICK_AUDIO=1
command -v python3 >/dev/null 2>&1 || { echo 'python3 not found' >&2; exit 127; }
printf '\n=== GrainBrick RG35XX Plus / KNULLI Scarab 20260511 ===\n' >> "$LOG"
python3 -B "$BETA_DIR/gb_launch.py" >> "$LOG" 2>&1
RESULT=$?
printf 'GrainBrick exit status: %s\n' "$RESULT" >> "$LOG"
exit "$RESULT"
