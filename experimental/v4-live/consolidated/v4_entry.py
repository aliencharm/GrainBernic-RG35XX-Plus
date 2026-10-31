#!/usr/bin/env python3
"""Single-folder GrainBrick V4 launcher; audio code matches integrated 0.1.8."""
from contextlib import ExitStack
import fcntl
import os
from pathlib import Path
import runpy
import sys
from v4_install import prepare,device_config


def main():
    app=Path(__file__).resolve().parent
    for proc in Path('/proc').iterdir():
        if proc.name.isdigit() and int(proc.name)!=os.getpid():
            try:
                argv=(proc/'cmdline').read_bytes().split(b'\0')
                if any(Path(os.fsdecode(a)).name in ('gb_launch.py','integrated_entry.py') for a in argv if a):
                    raise RuntimeError('Close other GrainBrick versions before launching V4')
            except OSError:pass
    with ExitStack() as stack:
        locks=[app/'.lock']
        old=app.parent/'grainbrick-v4-live'
        if old.is_dir():locks.append(old/'.lock')
        for path in locks:
            lock=stack.enter_context(path.open('a'))
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        print('GRAINBRICK V4 STANDALONE 1.2:',str(app),flush=True)
        prepare(app)
        config=device_config(app/'config.json')
        if 'V4_USB_NOT_CONNECTED' not in config['capture']:
            os.environ.setdefault('GRAINBRICK_USB_IN',config['capture'])
        sys.dont_write_bytecode=True
        os.environ.update(GRAINBRICK_SCREEN='640x480',GRAINBRICK_SCALE='fast',GRAINBRICK_FIT='1',GRAINBRICK_BUTTONS='1',GRAINBRICK_AUDIO='1')
        os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
        from v4_buttons import prepare_buttons
        prepare_buttons(app)
        state={'installed':False}
        def install(event,args):
            if event!='os.mkdir' or state['installed']:return
            original=sys.modules.get('main')
            if original is None or 'engine.dsp_chain' not in sys.modules:return
            state['installed']=True
            from original_adapter import install_at_boot
            state['controller']=install_at_boot(original,config)
            original._v4_controller=state['controller']
        sys.addaudithook(install)
        try:runpy.run_path(str(app/'gb_launch.py'),run_name='__main__')
        finally:
            controller=state.get('controller')
            if controller is not None:
                controller.stop_record_monitor();controller.restore_live_output()
                for source in list(controller.sources):source.close()
        if not state['installed']:raise RuntimeError('V4 integration failed to install')

if __name__=='__main__':main()
