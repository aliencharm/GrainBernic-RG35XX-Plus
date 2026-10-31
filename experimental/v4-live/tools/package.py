#!/usr/bin/env python3
"""Package an explicitly built ARM64 executable, never a host/test binary."""
import argparse
import hashlib
from pathlib import Path
import stat
import zipfile
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--binary',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
binary=a.binary.read_bytes()
if binary[:4]!=b'\x7fELF' or binary[4:6]!=b'\x02\x01' or int.from_bytes(binary[18:20],'little')!=183:
    raise SystemExit('Package requires a little-endian ELF64 AArch64 executable')
files={}
for rel in ['INSTALL-V4.txt','GrainBrick V4 Live.sh','grainbrick-v4-live/frontend.py','grainbrick-v4-live/config.example.json']:
    files[rel]=(root/'package'/rel).read_bytes()
files['grainbrick-v4-live/v4-live']=binary
for rel in ['README.md','VALIDATION.md','Makefile']:
    files['grainbrick-v4-live/source/'+rel]=(root/rel).read_bytes()
for folder in ['src','tests','tools','package']:
    for source in (root/folder).rglob('*'):
        if source.is_file() and source.suffix in {'.c','.h','.py','.sh','.json','.txt'} and '__pycache__' not in source.parts:
            # Only documented package templates, never runtime calibration/config or logs.
            if folder=='package' and source.relative_to(root/'package').as_posix() not in {'INSTALL-V4.txt','GrainBrick V4 Live.sh','grainbrick-v4-live/frontend.py','grainbrick-v4-live/config.example.json'}:
                continue
            files['grainbrick-v4-live/source/'+source.relative_to(root).as_posix()]=source.read_bytes()
manifest=''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in sorted(files.items()))
files['V4-SHA256SUMS.txt']=manifest.encode()
a.output.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.output,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for name,data in sorted(files.items()):
        info=zipfile.ZipInfo(name,(2026,10,31,0,0,0))
        info.compress_type=zipfile.ZIP_DEFLATED
        info.create_system=3
        info.external_attr=(stat.S_IFREG | (0o755 if name.endswith('.sh') or name=='grainbrick-v4-live/v4-live' else 0o644))<<16
        z.writestr(info,data)
print(str(a.output))
print('SHA256',hashlib.sha256(a.output.read_bytes()).hexdigest())
print('FILES',len(files))
