"""Non-destructive, restartable migration into a self-contained GrainBrick V4 folder."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

VERSION='1.0'
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
        if path.is_file() and (path.suffix=='.so' or '.so.' in path.name or path.name in ADAPTERS or path.suffix in ('.md','.txt')):
            yield path
    for directory in ('_vendor','resources','demo-samples','THIRD_PARTY_LICENSES','THIRD_PARTY_SOURCES'):
        root=source/directory
        if root.is_dir():
            for path in sorted(root.rglob('*')):
                if path.is_file():yield path

def collision_path(path,label,data_hash):
    if not path.exists() or (path.is_file() and digest(path)==data_hash):return path
    index=1
    while True:
        suffix=' ['+label+(' '+str(index) if index>1 else '')+']'
        candidate=path.with_name(path.stem+suffix+path.suffix)
        if not candidate.exists() or (candidate.is_file() and digest(candidate)==data_hash):return candidate
        index+=1

def migrate(target):
    target=Path(target).resolve();ports=target.parent
    marker=target/MARKER
    if marker.is_file():
        data=json.loads(marker.read_text())
        if data.get('main_sha256')!=EXPECTED_MAIN or not valid_original(target):raise RuntimeError('Installed V4 original engine checksum changed')
        device_config(target/'config.json')
        return json.loads((target/'migration-report.json').read_text())
    integrated=ports/'grainbrick-v4-integrated';v3=ports/'grainbrick-beta';control=ports/'grainbrick-v4-live'
    sources=[(label,path) for label,path in (('Integrated',integrated),('V3',v3)) if path.is_dir()]
    original=next((path for _,path in sources if valid_original(path)),None)
    if original is None:raise RuntimeError('Keep grainbrick-v4-integrated or grainbrick-beta installed for the first V4 launch')
    for name in ADAPTERS:
        if not (original/name).is_file():raise RuntimeError('Missing original compatibility adapter: '+name)
    config=target/'config.json' if (target/'config.json').is_file() else control/'config.json'
    device_config(config)
    core=list(original_files(original))
    media=[];projects=[]
    for label,source in sources:
        for directory in ('samples','recordings','projects'):
            root=source/directory
            if root.is_dir():
                if any(p.is_symlink() and p.is_dir() for p in root.rglob('*')):
                    raise RuntimeError('Back up linked media directories before migration: '+str(root))
                for path in sorted(root.rglob('*')):
                    if path.is_file():
                        item=(label,source,path)
                        (projects if directory=='projects' and path.suffix.lower()=='.json' else media).append(item)
    required=sum(p.stat().st_size for p in core)+sum(p.stat().st_size for _,_,p in media+projects)+32*1024*1024
    if shutil.disk_usage(target).free<required:raise RuntimeError('Not enough free space to copy V4 and preserve old versions; free at least '+str(required//(1024*1024)+1)+' MiB')
    report={'version':VERSION,'original_source':str(original),'sources':[str(p) for _,p in sources],
            'files':[],'external_references':[],'ready_for_cleanup':False}
    mapping={}
    print('V4 MIGRATION: copying original engine and resources',flush=True)
    for path in core:
        destination=target/path.relative_to(original)
        if destination.exists() and digest(destination)==digest(path):continue
        copy_file(path,destination)
    if not (target/'_vendor/numpy/__init__.py').is_file():
        raise RuntimeError('Original bundled NumPy was not copied; keep old folders and retry')
    def record(path,destination,sha,rewritten=False):
        report['files'].append({'source':str(path),'destination':str(destination.relative_to(target)),
                                'sha256':sha,'rewritten':rewritten})
    print('V4 MIGRATION: preserving samples, recordings and projects',flush=True)
    for _,source in sources:
        mapping[str(source.resolve())]=target
        for directory in ('samples','recordings','projects','resources','demo-samples'):
            root=source/directory
            if root.is_dir():
                mapping[str(root.resolve())]=target/directory
                for path in root.rglob('*'):
                    if path.is_dir():mapping[str(path.resolve())]=target/path.relative_to(source)
    # Plan all media before rewriting project sample paths. Different files with
    # the same name get a source suffix; matching files can share one copy.
    for label,source,path in media:
        sha=digest(path);destination=collision_path(target/path.relative_to(source),label,sha)
        if not destination.exists():copy_file(path,destination)
        mapping[str(path.resolve())]=destination
        record(path,destination,sha)
    def rewrite(value,source):
        if isinstance(value,dict):return {k:rewrite(v,source) for k,v in value.items()}
        if isinstance(value,list):return [rewrite(v,source) for v in value]
        if not isinstance(value,str):return value
        path=Path(value)
        is_absolute=path.is_absolute()
        candidate=path if is_absolute else source/path
        destination=mapping.get(str(candidate.resolve()))
        if destination is not None:return str(destination) if is_absolute else str(destination.relative_to(target))
        for _,old in sources:
            if value.startswith(str(old)+'/'):
                report['external_references'].append(value)
        return value
    for label,source,path in projects:
        try:
            data=rewrite(json.loads(path.read_text()),source)
            content=(json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode()
        except (ValueError,UnicodeError):
            content=path.read_bytes();report['external_references'].append('Unparsed project: '+str(path))
        sha=hashlib.sha256(content).hexdigest()
        destination=collision_path(target/path.relative_to(source),label,sha)
        if not destination.exists():write_bytes(destination,content)
        mapping[str(path.resolve())]=destination
        record(path,destination,sha,content!=path.read_bytes())
    # Prefer the working integrated settings; retain V3 alternatives as backups.
    for label,source in sources:
        for name in STATE:
            path=source/name
            if not path.is_file():continue
            raw=path.read_bytes()
            try:content=(json.dumps(rewrite(json.loads(raw),source),indent=2,ensure_ascii=False)+'\n').encode()
            except (ValueError,UnicodeError):content=raw
            destination=target/name
            if destination.exists():
                destination=collision_path(target/'migration-backups'/label/name,label,hashlib.sha256(content).hexdigest())
            if not destination.exists():write_bytes(destination,content)
            record(path,destination,digest(destination),content!=raw)
    if config!=target/'config.json':copy_file(config,target/'config.json')
    for name in ('samples','recordings','projects'):(target/name).mkdir(exist_ok=True)
    # V3 packages may keep demos only in demo-samples. Supply them if not imported.
    if not any((target/'samples').iterdir()):
        for path in (target/'demo-samples').glob('*.wav'):copy_file(path,target/'samples'/path.name)
    for item in report['files']:
        if digest(target/item['destination'])!=item['sha256']:raise RuntimeError('Migrated data verification failed: '+item['destination'])
    report['external_references']=sorted(set(report['external_references']))
    report['ready_for_cleanup']=not report['external_references']
    write_json(target/'migration-report.json',report)
    message='GrainBrick V4 migration complete.\nVerified data files: '+str(len(report['files']))+'\n'
    message+='Cleanup ready: '+('YES' if report['ready_for_cleanup'] else 'NO - keep old folders; see external_references in migration-report.json')+'\n'
    message+='Old folders have NOT been deleted or changed.\nTest V4, then back up old folders to your computer before removing them from ports.\n'
    write_bytes(target/'MIGRATION.txt',message.encode())
    write_json(marker,{'version':VERSION,'main_sha256':EXPECTED_MAIN})
    print('V4 MIGRATION COMPLETE:',len(report['files']),'verified data files; old folders unchanged; cleanup_ready=',report['ready_for_cleanup'],flush=True)
    return report
