#!/bin/sh
# USB/ALSA diagnostic. Writes only its report inside the app folder.
TASK_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
if [ -d "$TASK_ROOT/grainbrick-v4" ]; then
    TASK_APP="$TASK_ROOT/grainbrick-v4"
elif [ -f "$TASK_ROOT/v4_entry.py" ]; then
    TASK_APP="$TASK_ROOT"
else
    printf 'Cannot find grainbrick-v4 beside this script. Put the script in ports.\n' >&2
    exit 1
fi
TASK_REPORT="$TASK_APP/GrainBrick_USB_Report.txt"
# The launcher may run as root; make only this diagnostic report share-readable/writable.
umask 000
exec >"$TASK_REPORT" 2>&1
chmod 0666 "$TASK_REPORT" || exit 1
printf 'GrainBrick USB / ALSA diagnostic v2\n'
printf 'Report path: %s\n' "$TASK_REPORT"
date
uname -a
for item in /proc/asound/cards /proc/asound/devices /proc/asound/pcm; do
    printf '\n%s\n' "$item"
    if [ -r "$item" ]; then cat "$item"; else printf 'Unavailable\n'; fi
done
for card in /proc/asound/card[0-9]*; do
    [ -d "$card" ] || continue
    for item in "$card/id" "$card/usbid" "$card"/stream[0-9]*; do
        [ -r "$item" ] || continue
        printf '\n%s\n' "$item"
        cat "$item"
    done
done
printf '\nUSB devices and topology\n'
if command -v lsusb >/dev/null 2>&1; then lsusb; lsusb -t; else printf 'lsusb unavailable\n'; fi
for item in /sys/class/usb_role/*/role /sys/class/typec/*/data_role /sys/class/typec/*/power_role; do
    [ -r "$item" ] || continue
    printf '\n%s\n' "$item"
    cat "$item"
done
printf '\nUSB and audio kernel messages (last 100 matching lines)\n'
dmesg 2>&1 | grep -iE 'usb|snd|audio|musb|dwc|otg' | tail -100
printf '\nEND OF REPORT\n'
