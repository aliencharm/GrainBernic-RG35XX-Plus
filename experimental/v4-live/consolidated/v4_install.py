"""Verify the self-contained package and resolve its USB device configuration."""
import hashlib
import json
from pathlib import Path
import re
import tempfile

VERSION='4.2.13'
MAIN='main.cpython-312-aarch64-linux-gnu.so'
EXPECTED_MAIN='1481f6525cfbbbf5e9e8f95b622ec7e7edcbed1b7064a79fd01ce9c9dd085846'
ADAPTERS=('gb_launch.py','gb_audio.py','gb_buttons.py','gb_display_fit.py')
NO_USB='plughw:CARD=V4_USB_NOT_CONNECTED,DEV=0'


def digest(path):
    result=hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda:file.read(1024*1024),b''):result.update(block)
    return result.hexdigest()


def write_json(path,data):
    with tempfile.NamedTemporaryFile(mode='w',dir=path.parent,prefix='.v4-setup-',delete=False) as file:
        pending=Path(file.name);json.dump(data,file,indent=2);file.write('\n')
    try:pending.replace(path)
    finally:pending.unlink(missing_ok=True)


def usb_devices(asound):
    """First USB card with capture and playback; no ALSA streams are opened."""
    try:cards=(asound/'cards').read_text()
    except OSError:return None
    for match in re.finditer(r'(?m)^\s*(\d+)\s+\[([^\]]+?)\s*\]:\s*(.+)$',cards):
        number=int(match.group(1));card=asound/('card'+str(number))
        if not (card/'usbid').exists() and 'usb' not in match.group(3).lower():continue
        capture=sorted(int(m.group(1)) for p in card.glob('pcm*c') if (m:=re.fullmatch(r'pcm(\d+)c',p.name)))
        playback=sorted(int(m.group(1)) for p in card.glob('pcm*p') if (m:=re.fullmatch(r'pcm(\d+)p',p.name)))
        if not capture or not playback:continue
        try:identifier=(card/'id').read_text().strip()
        except OSError:identifier=match.group(2).strip()
        if re.fullmatch(r'[A-Za-z0-9_]+',identifier):
            return 'plughw:CARD='+identifier+',DEV='+str(capture[0]),'plughw:CARD='+identifier+',DEV='+str(playback[0])
        return 'plughw:'+str(number)+','+str(capture[0]),'plughw:'+str(number)+','+str(playback[0])
    return None


def device_config(path,asound=Path('/proc/asound')):
    data=json.loads(path.read_text())
    if not isinstance(data,dict):raise ValueError('Device config must be an object')
    for name in ('capture','playback'):
        if not isinstance(data.get(name),str) or not data[name]:raise ValueError('Missing device setting: '+name)
    latency=data.get('latency_us',24000)
    if type(latency) is not int or not 10000<=latency<=100000:raise ValueError('Invalid latency_us')
    capture=data['capture'];playback=data['playback']
    if 'auto' in (capture,playback):
        devices=usb_devices(asound)
        if devices is None:
            devices=(NO_USB,NO_USB)
            print('V4 USB: no USB duplex interface detected; connect USB before launching LIVE/REC. Sample playback and ORBIX remain available.',flush=True)
        else:print('V4 USB AUTO:',devices[0],'->',devices[1],flush=True)
        if capture=='auto':capture=devices[0]
        if playback=='auto':playback=devices[1]
    return {'capture':capture,'playback':playback,'latency_us':latency}


def prepare(app):
    """No imports from previous versions, no copying media, no deleting data."""
    app=Path(app).resolve()
    release=app/'RELEASE.json';metadata=json.loads(release.read_text())
    if metadata.get('kind')!='standalone':raise RuntimeError('Use the complete standalone V4 ZIP')
    if not (app/MAIN).is_file() or digest(app/MAIN)!=EXPECTED_MAIN:raise RuntimeError('Original application checksum mismatch; extract the complete V4 ZIP again')
    marker=app/'.v4-standalone.json'
    current=json.loads(marker.read_text()) if marker.is_file() else {}
    release_hash=digest(release)
    if current.get('release_sha256')!=release_hash:
        print('V4 STANDALONE: checking bundled engine, libraries, adapters and resources',flush=True)
        for member in metadata['immutable_paths']:
            relative=Path(member).relative_to('grainbrick-v4')
            if '..' in relative.parts:raise ValueError('Invalid release path')
            path=app/relative
            if not path.is_file() or digest(path)!=metadata['sha256'][member]:
                raise RuntimeError('Incomplete or changed V4 file: '+str(relative)+'; re-extract the ZIP')
    for name in ADAPTERS:
        if not (app/name).is_file():raise RuntimeError('Missing adapter: '+name)
    for name in ('samples','recordings','projects'):(app/name).mkdir(exist_ok=True)
    if not (app/'config.json').is_file():
        write_json(app/'config.json',json.loads((app/'config.example.json').read_text()))
    # Validate shape here; hardware auto-detection occurs once in the launcher.
    config=json.loads((app/'config.json').read_text())
    for key in ('capture','playback'):
        if not isinstance(config.get(key),str) or not config[key]:raise ValueError('Invalid config.json '+key)
    write_json(marker,{'version':VERSION,'release_sha256':release_hash,'standalone':True})
    return metadata
