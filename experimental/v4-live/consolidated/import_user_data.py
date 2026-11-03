"""Import only user data from a preserved V4 installation into a clean build."""
import hashlib
import json
from pathlib import Path
import shutil
import fcntl
from contextlib import ExitStack

DATA_DIRS=('samples','recordings','projects')
PREFERENCES=('config.json','settings.json','sound_state.json','gb_buttons.json','button_mapping.json')
def digest(path):
    result=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):result.update(block)
    return result.hexdigest()

def import_data(ports):
    ports=Path(ports).resolve();old=ports/'grainbrick-v4-backup';new=ports/'grainbrick-v4'
    if old.is_symlink() or new.is_symlink():raise RuntimeError('App folders must be real directories')
    if not old.is_dir() or not new.is_dir():raise RuntimeError('Need grainbrick-v4-backup and the new grainbrick-v4 beside this script')
    release=json.loads((new/'RELEASE.json').read_text())
    if release.get('kind')!='standalone' or release.get('version','').split('.')[:2]!=['4','1']:
        raise RuntimeError('Destination must be a complete GrainBrick V4.1 installation')
    with ExitStack() as locks:
        for folder in (old,new):
            handle=locks.enter_context((folder/'.lock').open('a'))
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise RuntimeError('Close GrainBrick before importing')
        marker=new/'.v4-user-data-import.json'
        if marker.exists():return 'ALREADY IMPORTED: backup retained; no files changed'
        files=[];skipped=0
        for directory in DATA_DIRS:
            root=old/directory
            if root.is_symlink():skipped+=1;continue
            if not root.is_dir():continue
            for source in sorted(root.rglob('*')):
                relative=source.relative_to(old)
                if source.is_symlink() or '__pycache__' in relative.parts:
                    skipped+=1;continue
                if not source.is_file():continue
                if any(parent.is_symlink() for parent in source.parents if parent!=old and parent.is_relative_to(old)):
                    skipped+=1;continue
                target=new/relative
                if target.is_symlink() or any(p.is_symlink() for p in target.parents if p!=new and p.is_relative_to(new)):
                    raise RuntimeError('Destination contains a symbolic link: '+str(relative))
                expected=release.get('sha256',{}).get('grainbrick-v4/'+relative.as_posix())
                if target.exists():
                    if not target.is_file():raise RuntimeError('Destination path conflict: '+str(relative))
                    actual=digest(target)
                    if actual==digest(source):continue
                    if expected!=actual:raise RuntimeError('New personal file conflicts with backup: '+str(relative)+'; import into a fresh installation')
                files.append((source,target))
        for name in PREFERENCES:
            source=old/name;target=new/name
            if source.is_symlink() or target.is_symlink():raise RuntimeError('Preference file is a symbolic link: '+name)
            if source.is_file():
                json.loads(source.read_text()) # Reject damaged preferences before copying any files.
                files.append((source,target))
        for source,target in files:
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
        marker.write_text(json.dumps({'source':str(old),'files_copied':len(files),'skipped':skipped},indent=2)+'\n')
        return f'IMPORT COMPLETE: {len(files)} files copied; {skipped} links/cache entries skipped. Backup retained.'

if __name__=='__main__':
    import sys
    try:print(import_data(sys.argv[1]))
    except Exception as exc:
        print('IMPORT FAILED:',str(exc));raise SystemExit(1)
