"""Build the add-on without redistributing original app binaries or user config."""
import hashlib
import json
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parent
release=root.parent/'releases/GrainBrick_V4_Integrated_0.1.2.zip'
files={
    'GrainBrick V4 Integrated.sh':root/'GrainBrick V4 Integrated.sh',
    'grainbrick-v4-live/integrated_entry.py':root/'integrated_entry.py',
    'grainbrick-v4-live/original_adapter.py':root/'original_adapter.py',
    'grainbrick-v4-live/live_source.py':root/'live_source.py',
    'grainbrick-v4-live/record_monitor.py':root/'record_monitor.py',
    'V4-INTEGRATED-README.md':root/'README.md',
}
manifest={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in files.items()}
with zipfile.ZipFile(release,'w',zipfile.ZIP_DEFLATED) as archive:
    for name,path in files.items():
        info=zipfile.ZipInfo(name,(2026,10,31,0,0,0))
        info.external_attr=(0o100755 if name.endswith('.sh') else 0o100644)<<16
        info.compress_type=zipfile.ZIP_DEFLATED
        archive.writestr(info,path.read_bytes())
    archive.writestr('V4-INTEGRATED-MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(release) as archive:
    assert archive.testzip() is None
    for name,digest in manifest.items():assert hashlib.sha256(archive.read(name)).hexdigest()==digest
checksums=release.parent/'SHA256SUMS.txt'
lines=[line for line in checksums.read_text().splitlines() if not line.endswith('  '+release.name)]
lines.append(hashlib.sha256(release.read_bytes()).hexdigest()+'  '+release.name)
checksums.write_text('\n'.join(lines)+'\n')
print(release,release.stat().st_size,'bytes')
