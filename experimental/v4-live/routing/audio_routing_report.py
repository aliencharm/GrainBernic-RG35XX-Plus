#!/usr/bin/env python3
"""USB routing discovery only: never starts capture/playback or changes ALSA config."""
import datetime
import json
from pathlib import Path
import platform
import subprocess

app=Path(__file__).resolve().parent
lines=['GrainBrick V4 audio routing discovery',datetime.datetime.now(datetime.timezone.utc).isoformat(),platform.platform()]
root=Path('/proc/asound')
for path in [root/'cards',root/'pcm',root/'version',*sorted(root.glob('card[0-9]*/id')),*sorted(root.glob('card[0-9]*/usbid')),*sorted(root.glob('card[0-9]*/stream[0-9]*'))]:
    lines.append('\n=== '+str(path)+' ===')
    try:lines.append(path.read_text(errors='replace'))
    except OSError as exc:lines.append(str(exc))
for command in (['arecord','-l'],['aplay','-l'],['arecord','-L'],['aplay','-L']):
    lines.append('\n=== '+' '.join(command)+' ===')
    try:
        result=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=10)
        lines.append(result.stdout);lines.append('exit='+str(result.returncode))
    except (OSError,subprocess.TimeoutExpired) as exc:lines.append(str(exc))
for name in ('config.json','RELEASE.json'):
    path=app/name
    if path.is_file():
        lines.append('\n=== '+name+' ===')
        try:
            data=json.loads(path.read_text())
            if name=='RELEASE.json':data={key:data.get(key) for key in ('version','kind')}
            lines.append(json.dumps(data,indent=2))
        except (OSError,ValueError) as exc:lines.append(str(exc))
output=app/'audio-routing-report.txt'
output.write_text('\n'.join(lines)+'\n')
print('Routing report saved:',output)
