"""Read ALSA USB stream descriptors; names describe USB channels, not physical jacks."""
from pathlib import Path
import re

def parse_stream(text):
    name=text.splitlines()[0] if text.splitlines() else ''
    direction=None;interface=None;alternate=None;result=[];current=None
    for raw in text.splitlines():
        line=raw.strip()
        if line in ('Playback:','Capture:'):
            direction=line[:-1].lower();current=None
        elif line.startswith('Interface '):interface=line.split()[-1]
        elif line.startswith('Altset '):
            alternate=line.split()[-1];current={'direction':direction,'interface':interface,'altset':alternate,'device_name':name}
            result.append(current)
        elif current is not None:
            if line.startswith('Channels:'):current['channels']=int(line.split(':',1)[1].strip())
            elif line.startswith('Format:'):current['format']=line.split(':',1)[1].strip()
            elif line.startswith('Rates:'):current['rates']=line.split(':',1)[1].strip()
    return [item for item in result if item.get('direction') and item.get('channels')]

def channel_choices(channels,include_mono=False):
    choices=[]
    if include_mono:
        choices.extend({'label':'USB channel '+str(i+1)+' (mono)','channels':[i]} for i in range(channels))
    choices.extend({'label':'USB channels '+str(i+1)+'-'+str(i+2),'channels':[i,i+1]} for i in range(0,channels-1,2))
    return choices

def inventory(asound=Path('/proc/asound')):
    result=[]
    for card in sorted(asound.glob('card[0-9]*')):
        if not (card/'usbid').exists():continue
        identifier=(card/'id').read_text().strip() if (card/'id').exists() else card.name
        for stream in sorted(card.glob('stream[0-9]*')):
            text=stream.read_text(errors='replace')
            result.append({'card':card.name,'id':identifier,'stream':stream.name,'descriptors':parse_stream(text),'raw':text})
    return result
