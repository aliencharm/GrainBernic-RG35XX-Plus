#!/bin/sh
# Read-only USB/ALSA diagnostic. Writes only the report beside this launcher.
TASK_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
exec >"$TASK_ROOT/GrainBrick_USB_Report.txt" 2>&1
printf 'GrainBrick USB / ALSA diagnostic\n'
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
