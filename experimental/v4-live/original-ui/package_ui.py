#!/usr/bin/env python3
import hashlib
from pathlib import Path
import stat
import zipfile
import argparse
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
r=Path(__file__).resolve().parent
files={'GrainBrick V4 Original UI.sh':(r/'GrainBrick V4 Original UI.sh').read_bytes(),
       'grainbrick-v4-live/native_ui.py':(r/'native_ui.py').read_bytes(),
       'grainbrick-v4-live/original_ui_entry.py':(r/'original_ui_entry.py').read_bytes(),
       'grainbrick-v4-live/live_frontend.py':(r.parent/'package/grainbrick-v4-live/frontend.py').read_bytes(),
       'ORIGINAL-UI-README.txt':(r/'README.txt').read_bytes()}
for name,data in files.items():
 if name.endswith('.py'):compile(data,name,'exec')
files['ORIGINAL-UI-SHA256SUMS.txt']=''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n' for name,data in sorted(files.items())).encode()
args.output.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(args.output,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for name,data in sorted(files.items()):
  info=zipfile.ZipInfo(name,(2026,10,31,0,0,0));info.create_system=3;info.compress_type=zipfile.ZIP_DEFLATED
  info.external_attr=(stat.S_IFREG|(0o755 if name.endswith('.sh') else 0o644))<<16
  z.writestr(info,data)
print(args.output)
print('SHA256',hashlib.sha256(args.output.read_bytes()).hexdigest())
