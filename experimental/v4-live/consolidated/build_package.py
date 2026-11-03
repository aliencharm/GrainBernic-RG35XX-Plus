"""Build a standalone ZIP from the verified original beta and RG35XX adapters."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from v4_install import EXPECTED_MAIN,MAIN,ADAPTERS,VERSION
from packaging_rules import include_vendor

root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--original',type=Path,required=True,help='Extracted original grainbrick-beta directory')
source=parser.parse_args().original.resolve()
assert hashlib.sha256((source/MAIN).read_bytes()).hexdigest()==EXPECTED_MAIN,'Unexpected original native application'
baseline=json.loads((root/'audio-baseline.json').read_text())
launcher_version='.'.join(VERSION.split('.')[:2])
files={f'GrainBrick V{launcher_version}.sh':root/'GrainBrick V4.sh',
       'grainbrick-v4/README_V4.md':root/'README.md',
       'grainbrick-v4/CREDITS_V4.md':root/'CREDITS.md',
       'grainbrick-v4/config.example.json':root/'config.example.json',
       'grainbrick-v4/v4_record_ui.py':root/'v4_record_ui.py',
       'grainbrick-v4/v4_projects.py':root/'v4_projects.py',
       'grainbrick-v4/v4_waveform.py':root/'v4_waveform.py',
       'grainbrick-v4/v4_themes.py':root/'v4_themes.py',
       'grainbrick-v4/audio_inventory.py':root.parent/'routing/audio_inventory.py',
       'grainbrick-v4/channel_routes.py':root.parent/'routing/channel_routes.py',
       'grainbrick-v4/v4_buttons.py':root/'v4_buttons.py',
       'grainbrick-v4/v4_entry.py':root/'v4_entry.py','grainbrick-v4/v4_install.py':root/'v4_install.py',
       'grainbrick-v4/projects/AMBIENT.json':root/'factory-preset.json'}
for name,expected in baseline['files'].items():
    path=root.parent/'dsp-integration'/name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,'Audio baseline changed: '+name
    files['grainbrick-v4/'+name]=(root/name) if name in ('record_monitor.py','live_source.py','stage_mix.py') else path
for path in sorted(source.iterdir()):
    if path.is_file() and (path.suffix=='.so' or '.so.' in path.name or path.name in ('README_EN.md','THIRD_PARTY_NOTICES.md')):
        files['grainbrick-v4/'+path.name]=path
for name in ADAPTERS:
    # These are the repository's existing RG35XX Plus / working V3 adapters.
    files['grainbrick-v4/'+name]=root.parents[2]/'grainbrick-beta'/name
for name in ('_vendor','resources','THIRD_PARTY_LICENSES','THIRD_PARTY_SOURCES'):
    assert (source/name).is_dir(),'Missing original '+name
    for path in sorted((source/name).rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc':
            if name=='_vendor' and not include_vendor(path.relative_to(source/name).as_posix()):continue
            files['grainbrick-v4/'+str(path.relative_to(source))]=path
for relative,expected in json.loads((root/'factory-content.json').read_text()).items():
    path=source/relative
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,'Original demo differs'
    files['grainbrick-v4/samples/'+path.name]=path
manifest={'version':VERSION,'kind':'standalone','original_main_sha256':EXPECTED_MAIN,
          'release_name':f'GrainBrick V{VERSION}','consolidates':'UI Test 1.13',
          'packaging':'Runtime only; NumPy tests, compiler tools, headers and typing stubs omitted',
          'audio_baseline':baseline,'sha256':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in files.items()}}
manifest['audio_overrides']={'stage_mix.py':'Separate sample FX/Tape blends default to original 100%; LIVE blends unchanged','live_source.py':'Frozen LIVE read anchor preserved; full-buffer export shares cursor/freeze acknowledgement; sample granular blend defaults to original 100%','record_monitor.py':'Output-only 10 ms monitor startup fade; saved recordings unchanged'}
manifest['immutable_paths']=[name for name in files if name.startswith('grainbrick-v4/') and not name.startswith(('grainbrick-v4/samples/','grainbrick-v4/projects/'))]
release=root.parent/f'releases/GrainBrick_V{VERSION}_Standalone.zip'
with zipfile.ZipFile(release,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for name,path in files.items():
        info=zipfile.ZipInfo(name,(2026,11,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=(0o100755 if name.endswith('.sh') else 0o100644)<<16
        archive.writestr(info,path.read_bytes())
    archive.writestr('grainbrick-v4/recordings/','')
    archive.writestr('grainbrick-v4/RELEASE.json',json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(release) as archive:
    assert archive.testzip() is None
    for name,digest in manifest['sha256'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==digest
checksums=release.parent/'SHA256SUMS.txt'
lines=[line for line in checksums.read_text().splitlines() if not line.endswith('  '+release.name)]
lines.append(hashlib.sha256(release.read_bytes()).hexdigest()+'  '+release.name)
checksums.write_text('\n'.join(lines)+'\n')
print(release,release.stat().st_size,'bytes;',len(files),'bundled files; original V3 adapters and V4 audio baseline verified')
