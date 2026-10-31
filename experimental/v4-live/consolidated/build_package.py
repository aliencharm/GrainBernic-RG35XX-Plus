"""Package one final launcher/folder, reusing byte-identical tested audio modules."""
import hashlib
import json
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parent
baseline=json.loads((root/'audio-baseline.json').read_text())
files={'GrainBrick V4.sh':root/'GrainBrick V4.sh','INSTALL-V4.txt':root/'README.md',
       'grainbrick-v4/README_V4.md':root/'README.md',
       'grainbrick-v4/v4_entry.py':root/'v4_entry.py','grainbrick-v4/v4_install.py':root/'v4_install.py'}
for name,expected in baseline['files'].items():
    path=root.parent/'dsp-integration'/name
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,'Audio baseline changed: '+name
    files['grainbrick-v4/'+name]=path
manifest={'version':'1.0','audio_baseline':baseline,'sha256':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in files.items()}}
release=root.parent/'releases/GrainBrick_V4_Final_1.0.zip'
with zipfile.ZipFile(release,'w',zipfile.ZIP_DEFLATED) as archive:
    for name,path in files.items():
        info=zipfile.ZipInfo(name,(2026,10,31,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        info.external_attr=(0o100755 if name.endswith('.sh') else 0o100644)<<16
        archive.writestr(info,path.read_bytes())
    archive.writestr('grainbrick-v4/RELEASE.json',json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(release) as archive:
    assert archive.testzip() is None
    for name,digest in manifest['sha256'].items():assert hashlib.sha256(archive.read(name)).hexdigest()==digest
checksums=release.parent/'SHA256SUMS.txt'
lines=[line for line in checksums.read_text().splitlines() if not line.endswith('  '+release.name)]
lines.append(hashlib.sha256(release.read_bytes()).hexdigest()+'  '+release.name)
checksums.write_text('\n'.join(lines)+'\n')
print(release,release.stat().st_size,'bytes; audio baseline unchanged')
