#!/bin/sh
# GrainBrick: collect RG35XX Plus/KNULLI audio diagnostics.
OUT=/userdata/roms/ports/grainbrick-beta/audio_check.txt
{
  echo "=== date"; date
  echo "=== uname"; uname -a
  echo "=== /proc/asound/cards"; cat /proc/asound/cards
  echo "=== /proc/asound/pcm"; cat /proc/asound/pcm
  echo "=== aplay -l"; aplay -l 2>&1
  echo "=== arecord -l"; arecord -l 2>&1
  echo "=== lsusb"; lsusb 2>&1
  echo "=== modules"; lsmod 2>/dev/null | grep -iE 'snd|usb|audio'
  echo "=== dmesg audio/usb"; dmesg 2>/dev/null | grep -iE 'usb|audio|snd' | tail -n 120
} > "$OUT" 2>&1
sync
