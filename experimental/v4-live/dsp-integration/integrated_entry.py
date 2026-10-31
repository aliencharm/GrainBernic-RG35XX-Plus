#!/usr/bin/env python3
"""Prepare an isolated installation and run the ORIGINAL app with a REC/LIVE adapter."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import sys
import tempfile

EXPECTED_MAIN='1481f6525cfbbbf5e9e8f95b622ec7e7edcbed1b7064a79fd01ce9c9dd085846'

def prepare_original(source,target):
    library=source/'main.cpython-312-aarch64-linux-gnu.so'
    if not library.is_file() or hashlib.sha256(library.read_bytes()).hexdigest()!=EXPECTED_MAIN:
        raise RuntimeError('The installed original app differs from the inspected beta')
    marker=target/'.v4-original-copy.json'
    if target.exists():
        if not marker.is_file() or json.loads(marker.read_text()).get('main_sha256')!=EXPECTED_MAIN:
            raise RuntimeError('Existing integrated directory is not the managed original-app copy')
        if hashlib.sha256((target/library.name).read_bytes()).hexdigest()!=EXPECTED_MAIN:
            raise RuntimeError('Integrated original main library checksum changed')
        return
    stage=Path(tempfile.mkdtemp(prefix='.v4-original-stage-',dir=target.parent))
    try:
        # Static original files only. User audio/projects remain in V3 unchanged.
        for path in source.iterdir():
            if path.is_file() and (path.suffix in ('.so','.py','.md','.txt') or '.so.' in path.name or path.name in ('settings.json','gb_buttons.json','button_mapping.json')):
                shutil.copy2(path,stage/path.name)
        for name in ('_vendor','resources','demo-samples','THIRD_PARTY_LICENSES','THIRD_PARTY_SOURCES'):
            if (source/name).is_dir():shutil.copytree(source/name,stage/name)
        for name in ('samples','recordings','projects'):(stage/name).mkdir(exist_ok=True)
        if (source/'projects/AMBIENT.json').is_file():shutil.copy2(source/'projects/AMBIENT.json',stage/'projects/AMBIENT.json')
        for wav in (stage/'demo-samples').glob('*.wav'):shutil.copy2(wav,stage/'samples'/wav.name)
        (stage/'.v4-original-copy.json').write_text(json.dumps({'version':1,'main_sha256':EXPECTED_MAIN})+'\n')
        os.replace(stage,target)
    finally:
        if stage.exists():shutil.rmtree(stage)

def load_device_config(control):
    data=json.loads((control/'config.json').read_text())
    if not isinstance(data,dict):raise ValueError('V4 device config must be a JSON object')
    for name in ('capture','playback'):
        if not isinstance(data.get(name),str) or not data[name]:raise ValueError('Set '+name+' in the working V4 config.json')
    latency=data.get('latency_us',24000)
    if type(latency) is not int or not 10000<=latency<=100000:raise ValueError('latency_us must be 10000..100000')
    return {'capture':data['capture'],'playback':data['playback'],'latency_us':latency}

def main():
    control=Path(__file__).resolve().parent
    ports=control.parent;source=ports/'grainbrick-beta';runtime=ports/'grainbrick-v4-integrated'
    for proc in Path('/proc').iterdir():
        if proc.name.isdigit():
            try:
                argv=(proc/'cmdline').read_bytes().split(b'\0')
                if any(a.endswith(b'/gb_launch.py') or a==b'gb_launch.py' for a in argv):
                    raise RuntimeError('Close the original V3 app before launching integrated LIVE')
            except OSError:pass
    with (control/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        config=load_device_config(control)
        print('V4 INTEGRATED ORIGINAL APP 0.1.4 preparing',str(runtime),flush=True)
        prepare_original(source,runtime)
        sys.dont_write_bytecode=True
        os.environ.update(GRAINBRICK_SCREEN='640x480',GRAINBRICK_SCALE='fast',GRAINBRICK_FIT='1',GRAINBRICK_BUTTONS='1',GRAINBRICK_AUDIO='1')
        os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
        sys.path.insert(0,str(control))
        state={'installed':False}
        def install_hook(event,args):
            if event!='os.mkdir' or state['installed']:return
            original=sys.modules.get('main')
            if original is None or 'engine.dsp_chain' not in sys.modules:return
            state['installed']=True
            from original_adapter import install_at_boot
            state['controller']=install_at_boot(original,config)
        sys.addaudithook(install_hook)
        try:
            # This executes the supplied original V3 launcher and original main.
            runpy.run_path(str(runtime/'gb_launch.py'),run_name='__main__')
        finally:
            controller=state.get('controller')
            if controller is not None:
                for live_source in list(controller.sources):live_source.close()
        if not state['installed']:raise RuntimeError('Original-app source switch was not installed')

if __name__=='__main__':main()
