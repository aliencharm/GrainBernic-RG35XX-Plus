"""Build an overlay ZIP containing only differences between two verified packages."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def build_update(base,target,output):
    with zipfile.ZipFile(base) as old,zipfile.ZipFile(target) as new:
        prior=json.loads(old.read('grainbrick-v4/RELEASE.json'))
        current=json.loads(new.read('grainbrick-v4/RELEASE.json'))
        if prior['original_main_sha256']!=current['original_main_sha256']:
            raise ValueError('Original engine changed; an overlay requires the same engine')
        if set(old.namelist())-set(new.namelist()):
            raise ValueError('Removed package files require an explicit migration')
        for archive,manifest in ((old,prior),(new,current)):
            if archive.testzip() is not None:raise ValueError('Invalid ZIP')
            for name,digest in manifest['sha256'].items():
                if hashlib.sha256(archive.read(name)).hexdigest()!=digest:
                    raise ValueError('Package checksum mismatch: '+name)
        changed=[name for name in new.namelist() if not name.endswith('/') and
                 (name not in old.namelist() or old.read(name)!=new.read(name))]
        for name in changed:
            if name=='grainbrick-v4/config.json' or name.startswith(tuple('grainbrick-v4/'+folder+'/' for folder in ('samples','recordings','projects'))):
                raise ValueError('Overlay must not replace user data: '+name)
        with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as overlay:
            for name in changed:overlay.writestr(new.getinfo(name),new.read(name))
        # Simulate applying the overlay and verify every target manifest entry.
        with zipfile.ZipFile(output) as overlay:
            for name,digest in current['sha256'].items():
                archive=overlay if name in changed else old
                if hashlib.sha256(archive.read(name)).hexdigest()!=digest:
                    raise ValueError('Overlay integrity mismatch: '+name)
    print('Requires installed UI Test',prior['version'],'->',current['version'])
    print(output,Path(output).stat().st_size,'bytes;',len(changed),'changed files')
    print('\n'.join(changed))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,required=True)
    parser.add_argument('--target',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    build_update(args.base,args.target,args.output)
