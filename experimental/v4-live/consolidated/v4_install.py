"""Clean installation of a self-contained GrainBrick V4; no user media import."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

VERSION='1.1'
MAIN='main.cpython-312-aarch64-linux-gnu.so'
EXPECTED_MAIN='1481f6525cfbbbf5e9e8f95b622ec7e7edcbed1b7064a79fd01ce9c9dd085846'
ADAPTERS=('gb_launch.py','gb_audio.py','gb_buttons.py','gb_display_fit.py')
STATE=('settings.json','sound_state.json','gb_buttons.json','button_mapping.json')
MARKER='.v4-install.json'

def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda:file.read(1024*1024),b''):value.update(block)
    return value.hexdigest()

def write_bytes(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.v4-copy-',delete=False) as file:
        pending=Path(file.name);file.write(data)
    try:pending.replace(path)
    finally:pending.unlink(missing_ok=True)

def write_json(path,data):write_bytes(path,(json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode())

def copy_file(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent,prefix='.v4-copy-',delete=False) as file:pending=Path(file.name)
    try:
        shutil.copy2(source,pending)
        source_hash=digest(source)
        if digest(pending)!=source_hash:raise RuntimeError('Copy verification failed: '+str(source))
        pending.replace(target)
        return source_hash
    finally:pending.unlink(missing_ok=True)

def device_config(path):
    data=json.loads(path.read_text())
    if not isinstance(data,dict):raise ValueError('Device config must be an object')
    for name in ('capture','playback'):
        if not isinstance(data.get(name),str) or not data[name]:raise ValueError('Missing device setting: '+name)
    latency=data.get('latency_us',24000)
    if type(latency) is not int or not 10000<=latency<=100000:raise ValueError('Invalid latency_us')
    return {'capture':data['capture'],'playback':data['playback'],'latency_us':latency}

def valid_original(source):
    return (source/MAIN).is_file() and digest(source/MAIN)==EXPECTED_MAIN

def original_files(source):
    for path in sorted(source.iterdir()):
        if path.is_file() and (path.suffix=='.so' or '.so.' in path.name or path.name in ADAPTERS or path.name in ('README_EN.md','THIRD_PARTY_NOTICES.md','SHA256SUMS.txt')):
            yield path
    for directory in ('_vendor','resources','THIRD_PARTY_LICENSES','THIRD_PARTY_SOURCES'):
        root=source/directory
        if root.is_dir():
            for path in sorted(root.rglob('*')):
                if path.is_file():yield path

def prepare(target):
    target=Path(target).resolve();ports=target.parent
    marker=target/MARKER
    pending=target/'.v4-clean-setup-pending'
    if marker.is_file():
        data=json.loads(marker.read_text())
        if data.get('mode')!='clean':
            raise RuntimeError('This folder has an earlier media-import install. Back up grainbrick-v4 and extract the clean 1.1 package into a fresh folder. No data was deleted.')
        if data.get('main_sha256')!=EXPECTED_MAIN or not valid_original(target):raise RuntimeError('Installed V4 original engine checksum changed')
        device_config(target/'config.json')
        return data
    # A clean install must not silently retain an old user library.
    resuming=pending.is_file() and json.loads(pending.read_text()).get('main_sha256')==EXPECTED_MAIN
    for name in ('samples','recordings','projects'):
        if not resuming and (target/name).is_dir() and any((target/name).rglob('*')):
            raise RuntimeError('Back up the existing grainbrick-v4 folder and extract into a fresh folder for clean setup')
    sources=[ports/'grainbrick-beta',ports/'grainbrick-v4-integrated',ports/'grainbrick-v4-previous']
    original=next((path for path in sources if valid_original(path)),None)
    if original is None:raise RuntimeError('Keep the original V3 or integrated app for the first V4 launch')
    for name in ADAPTERS:
        if not (original/name).is_file():raise RuntimeError('Missing original adapter: '+name)
    config=next((path for path in (target/'config.json',ports/'grainbrick-v4-live/config.json',ports/'grainbrick-v4-previous/config.json') if path.is_file()),target/'config.json')
    device_config(config)
    factory=json.loads((target/'factory-content.json').read_text())
    demos=[]
    for relative,expected in factory.items():
        source=next((path/relative for path in sources if (path/relative).is_file() and digest(path/relative)==expected),None)
        if source is None:raise RuntimeError('Original V3 demo file missing or changed: '+relative)
        demos.append((relative,source))
    core=list(original_files(original))
    required=sum(p.stat().st_size for p in core)+sum(p.stat().st_size*2 for _,p in demos)+32*1024*1024
    if shutil.disk_usage(target).free<required:raise RuntimeError('Not enough space to copy original engine into V4')
    write_json(pending,{'mode':'clean','main_sha256':EXPECTED_MAIN})
    print('V4 CLEAN SETUP: copying original engine/resources; no user samples or recordings',flush=True)
    for path in core:copy_file(path,target/path.relative_to(original))
    if not (target/'_vendor/numpy/__init__.py').is_file():raise RuntimeError('Original bundled NumPy was not copied')
    for name in ('samples','recordings','projects'):(target/name).mkdir(exist_ok=True)
    for relative,path in demos:
        copy_file(path,target/relative)
        copy_file(path,target/'samples'/path.name)
    copy_file(target/'factory-preset.json',target/'projects/AMBIENT.json')
    # Preferences are not media: retain the working device/UI/DSP/button settings.
    for name in STATE:
        source=next((path/name for path in reversed(sources) if (path/name).is_file()),None)
        if source is not None and not (target/name).exists():copy_file(source,target/name)
    if config!=target/'config.json':copy_file(config,target/'config.json')
    data={'mode':'clean','version':VERSION,'main_sha256':EXPECTED_MAIN,'original_source':str(original),'user_media_imported':False}
    write_bytes(target/'SETUP.txt',b'GrainBrick V4 clean setup complete.\nOnly the original V3 demo and starter preset were added.\nNo user samples, recordings or projects were imported.\nV4 now runs from this folder. Test it, then back up old folders to your computer before removing them.\n')
    write_json(marker,data)
    pending.unlink(missing_ok=True)
    print('V4 CLEAN SETUP COMPLETE: original demos only; no user media imported',flush=True)
    return data
