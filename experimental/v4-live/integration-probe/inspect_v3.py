#!/usr/bin/env python3
"""Guarded metadata probe, not a V3 launcher or an audio/UI integration patch."""
import argparse
import importlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import traceback

TARGETS = ('main','engine.parameters','engine.control','engine.audio_worker',
           'engine.audio','engine.granular_c','engine.dsp_chain','ui.renderer')
# Keep this independent of V4 so importing it cannot start the working engine.
class ProbeBoundary(BaseException):
    pass


def simple(value):
    if value is None or isinstance(value,(str,int,float,bool)):
        return value if not isinstance(value,str) else value[:160]
    return {'type':type(value).__name__}


def callable_info(value):
    result={'type':type(value).__name__}
    code=getattr(value,'__code__',None)
    if code is not None:
        count=code.co_argcount+code.co_kwonlyargcount
        result['arguments']=list(code.co_varnames[:count])
        result['positional_count']=code.co_argcount
        result['keyword_only_count']=code.co_kwonlyargcount
        result['flags']=code.co_flags
    defaults=getattr(value,'__defaults__',None)
    if isinstance(defaults,tuple):
        result['defaults']=[simple(v) for v in defaults]
    doc=getattr(value,'__doc__',None)
    if isinstance(doc,str) and doc:
        result['doc']=doc[:800]
    return result


def module_info(module):
    namespace=vars(module)
    result={'file':str(namespace.get('__file__','')), 'classes':{}, 'functions':{}, 'constants':{}}
    for name,value in sorted(namespace.items()):
        if name.startswith('__'):
            continue
        if isinstance(value,type) and str(getattr(value,'__module__','')).startswith(('engine','ui','main')):
            methods={}
            for key,method in sorted(vars(value).items()):
                if isinstance(method,(staticmethod,classmethod)):
                    method=method.__func__
                if callable(method) and (not key.startswith('__') or key=='__init__'):
                    methods[key]=callable_info(method)
                elif isinstance(method,property):
                    methods[key]={'type':'property','getter':callable_info(method.fget) if method.fget else None}
            result['classes'][name]={'module':value.__module__,'methods':methods}
        elif callable(value) and getattr(value,'__module__',None)==namespace.get('__name__'):
            result['functions'][name]=callable_info(value)
        elif name.isupper():
            if isinstance(value,(tuple,list)) and len(value)<100:
                result['constants'][name]=[simple(v) for v in value]
            elif isinstance(value,dict) and len(value)<200:
                result['constants'][name]={str(k):simple(v) for k,v in value.items() if isinstance(k,(str,int,float))}
            elif isinstance(value,(str,int,float,bool)):
                result['constants'][name]=simple(value)
    return result


def install_guard(snapshot):
    """Block Python-level writes/process/device startup; not an OS sandbox."""
    def stop(reason):
        snapshot['boundary']=reason
        snapshot['modules_at_boundary']={k:v for k,v in sys.modules.items() if k in TARGETS and v is not None}
        raise ProbeBoundary(reason)
    def audit(event,args):
        if event=='open':
            mode=args[1] if len(args)>1 else None
            flags=args[2] if len(args)>2 else 0
            write_mode=isinstance(mode,str) and any(c in mode for c in 'wax+')
            write_flags=isinstance(flags,int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            if write_mode or write_flags:
                stop('blocked Python file write')
        if event in {'os.mkdir','os.remove','os.rename','os.rmdir','os.link','os.symlink','os.chmod',
                     'os.truncate','os.chdir','os.fork','os.forkpty','os.posix_spawn','os.exec',
                     'os.system','subprocess.Popen','socket.connect','socket.bind'}:
            stop('blocked '+event)
        if event=='ctypes.dlopen':
            name=str(args[0]) if args else ''
            if any(token in name.lower() for token in ('asound','portaudio','pulse')):
                stop('blocked native audio-library load')
    sys.addaudithook(audit)
    return stop


def worker(v3,report_fd,fixture=False):
    # Parent opens the output file first. The guard blocks subsequent path writes.
    report={'probe_version':'0.1','python':platform.python_version(),'machine':platform.machine(),
            'v3_directory':str(v3),'status':'initializing','modules':{},'boundary':None}
    snapshot={}
    try:
        if not fixture:
            if sys.version_info[:2]!=(3,12) or platform.machine().lower() not in ('aarch64','arm64'):
                raise RuntimeError('Inspection requires KNULLI ARM64 Python 3.12')
            if not (v3/'main.cpython-312-aarch64-linux-gnu.so').is_file():
                raise RuntimeError('Installed V3 main extension not found')
        sys.dont_write_bytecode=True
        os.environ.update(GRAINBRICK_ROOT=str(v3),OPENBLAS_NUM_THREADS='1',
                          SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',PYGAME_HIDE_SUPPORT_PROMPT='1')
        sys.path[:]=[p for p in sys.path if Path(p or os.getcwd()).resolve()!=v3]
        if not fixture:
            import pygame
            try:
                import numpy
            except ModuleNotFoundError:
                sys.path.insert(0,str(v3/'_vendor'))
                import numpy
            import pygame.surfarray
            report['dependencies']={'pygame':pygame.version.ver,'numpy':numpy.__version__}
        sys.path.insert(0,str(v3))
        stop=install_guard(snapshot)
        if not fixture:
            def blocked(*args,**kwargs):
                stop('stopped before pygame startup')
            pygame.init=blocked
            pygame.display.init=blocked
            pygame.display.set_mode=blocked
            pygame.mixer.init=blocked
            pygame.joystick.init=blocked
        try:
            module=importlib.import_module('main')
            snapshot['modules_at_boundary']={k:v for k,v in sys.modules.items() if k in TARGETS and v is not None}
            snapshot['modules_at_boundary']['main']=module
            report['status']='import_returned_without_startup'
        except ProbeBoundary:
            report['status']='guarded_boundary_reached'
        except BaseException as exc:
            report['status']='import_failed'
            report['error']=type(exc).__name__+': '+str(exc)
        report['boundary']=snapshot.get('boundary')
        collected=snapshot.get('modules_at_boundary',{})
        for name in TARGETS:
            module=collected.get(name) or sys.modules.get(name)
            if module is not None:
                report['modules'][name]=module_info(module)
        report['missing_modules']=[name for name in TARGETS if name not in report['modules']]
        report['interpretation']='Metadata only: attribute replacement and compiled call behavior are not verified.'
    except BaseException as exc:
        report['status']='probe_failed'
        report['error']=type(exc).__name__+': '+str(exc)
    # Write only to the parent's already-open report descriptor, without a new open().
    data=(json.dumps(report,indent=2,ensure_ascii=True)+'\n').encode()
    while data:
        n=os.write(report_fd,data)
        data=data[n:]
    return 0 if report['modules'] else 1


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--v3',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--worker-fd',type=int)
    parser.add_argument('--test-python-fixture',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker_fd is not None:
        return worker(args.v3.resolve(),args.worker_fd,args.test_python_fixture)
    if args.output is None:
        parser.error('--output is required')
    # Never write to the V3 tree, including an accidentally selected output path.
    output=args.output.resolve(); v3=args.v3.resolve()
    if output.is_relative_to(v3):
        parser.error('Output must be outside the V3 installation')
    for proc in Path('/proc').iterdir():
        if proc.name.isdigit():
            try:
                argv=(proc/'cmdline').read_bytes().split(b'\0')
                if any(a.endswith(b'/gb_launch.py') or a==b'gb_launch.py' or a.endswith(b'/v4-live') for a in argv):
                    raise RuntimeError('Close GrainBrick V3 and V4 before inspection')
            except OSError:
                pass
    command=[sys.executable,'-B',str(Path(__file__).resolve()),'--v3',str(v3)]
    if args.test_python_fixture:
        command.append('--test-python-fixture')
    with output.open('wb') as report:
        command+=['--worker-fd',str(report.fileno())]
        try:
            child=subprocess.run(command,pass_fds=(report.fileno(),),timeout=20,check=False)
        except subprocess.TimeoutExpired:
            print('Probe timed out; no integration readiness established',flush=True)
            return 2
    print('Probe exit:',child.returncode,'report:',str(output),flush=True)
    return child.returncode

if __name__=='__main__':
    raise SystemExit(main())
