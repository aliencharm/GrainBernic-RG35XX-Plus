"""Verify a clean V4 standalone deliverable independently of an extracted installation."""
import hashlib
import json
from pathlib import Path,PurePosixPath
import zipfile
from v4_install import EXPECTED_MAIN,MAIN
from packaging_rules import include_vendor


def verify(path):
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist();files={n for n in names if not n.endswith('/')}
        assert len(names)==len(set(names)),'Duplicate archive members'
        assert archive.testzip() is None,'ZIP integrity failure'
        manifest=json.loads(archive.read('grainbrick-v4/RELEASE.json'))
        assert manifest['version'].split('.')[:2] in (['4','1'],['4','2']) and manifest['kind']=='standalone'
        launcher='GrainBrick V'+'.'.join(manifest['version'].split('.')[:2])+'.sh'
        assert {n.split('/')[0] for n in names}=={launcher,'grainbrick-v4'},'Unexpected top-level files'
        assert files==set(manifest['sha256'])|{'grainbrick-v4/RELEASE.json'},'Untracked or missing files'
        for name,digest in manifest['sha256'].items():
            assert not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts
            assert hashlib.sha256(archive.read(name)).hexdigest()==digest,name
        assert hashlib.sha256(archive.read('grainbrick-v4/'+MAIN)).hexdigest()==EXPECTED_MAIN
        assert archive.getinfo(launcher).external_attr>>16&0o111,'Launcher is not executable'
        for name in files:
            relative=PurePosixPath(name)
            assert not {'__pycache__','tests'}&set(relative.parts),name
            assert relative.suffix not in {'.log','.pyc','.pyo'},name
            assert relative.name not in {'config.json','settings.json','sound_state.json','gb_buttons.json','button_mapping.json','.lock','.v4-standalone.json'},name
            if name.startswith('grainbrick-v4/_vendor/'):
                assert include_vendor(name.removeprefix('grainbrick-v4/_vendor/')),name
        assert [n for n in names if n.lower().endswith('.wav')]==['grainbrick-v4/samples/sample grainbrick 1.wav']
        preset=json.loads(archive.read('grainbrick-v4/projects/AMBIENT.json'))
        assert 'grainbrick-v4/'+preset['sample']['path'] in files,'Factory project sample missing'
        for name in ('CREDITS_V4.md','README_V4.md','README_EN.md','THIRD_PARTY_NOTICES.md',
                     'THIRD_PARTY_LICENSES/LGPL-2.1.txt','THIRD_PARTY_SOURCES/SoundTouch_Compliance_Sources.zip',
                     '_vendor/numpy-1.26.4.dist-info/LICENSE.txt','_vendor/numpy/core/include/numpy/random/LICENSE.txt'):
            assert 'grainbrick-v4/'+name in files,name
        print('PASS standalone archive, hashes, original engine, executable launcher, factory preset/demo, runtime exclusions and licenses')
        print(len(files),'files;',sum(i.file_size for i in archive.infolist()),'unpacked bytes;',Path(path).stat().st_size,'ZIP bytes')

if __name__=='__main__':
    import sys
    verify(Path(sys.argv[1]))
