"""Reuse the installed V3 renderer, without starting V3's application/audio loop."""
import hashlib
import importlib
import importlib.util
import os
from pathlib import Path
import sys
import types

EXPECTED_MAIN_SHA256='1481f6525cfbbbf5e9e8f95b622ec7e7edcbed1b7064a79fd01ce9c9dd085846'
TARGETS=('main','ui.renderer','engine.parameters')

class BootstrapStop(BaseException):
    pass


def write_event_paths(event,args):
    if event=='open':
        mode=args[1] if len(args)>1 else None
        flags=args[2] if len(args)>2 else 0
        if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
            return [args[0]]
    if event in {'os.mkdir','os.remove','os.rmdir','os.chmod','os.truncate'}:
        return [args[0]]
    if event in {'os.rename','os.link','os.symlink'}:
        return list(args[:2])
    return []


class BootstrapPolicy:
    """Python-level guard; not an OS sandbox for arbitrary native libraries."""
    def __init__(self,v3,engine):
        self.v3=v3.resolve(); self.engine=engine.resolve()
        self.loading=True; self.boundary=None; self.modules={}
    def stop(self,reason):
        self.boundary=reason
        self.modules={name:sys.modules.get(name) for name in TARGETS if sys.modules.get(name) is not None}
        raise BootstrapStop(reason)
    def audit(self,event,args):
        paths=write_event_paths(event,args)
        if self.loading:
            if paths:
                self.stop('blocked '+event+' during V3 bootstrap')
            if event in {'os.fork','os.forkpty','os.posix_spawn','os.exec','os.system','subprocess.Popen','socket.connect','socket.bind'}:
                self.stop('blocked '+event+' during V3 bootstrap')
        for path in paths:
            if isinstance(path,(str,bytes,os.PathLike)):
                resolved=Path(os.fsdecode(path)).resolve()
                if resolved.is_relative_to(self.v3):
                    raise PermissionError('Original V3 installation is read-only in LIVE UI')
        if not self.loading and event=='subprocess.Popen':
            executable=args[0] if args else None
            if not isinstance(executable,(str,bytes,os.PathLike)) or Path(os.fsdecode(executable)).resolve()!=self.engine:
                raise PermissionError('LIVE UI may start only its own V4 engine')
        if event=='ctypes.dlopen':
            name=str(args[0]).lower() if args else ''
            if any(token in name for token in ('asound','portaudio','pulse')):
                if self.loading:
                    self.stop('blocked audio-library loading during V3 bootstrap')
                raise PermissionError('Audio belongs to the separate V4 process')


def load_classes(v3,engine,pg,allow_fixture=False):
    if not allow_fixture:
        import platform
        if sys.version_info[:2]!=(3,12) or platform.machine().lower() not in ('arm64','aarch64'):
            raise RuntimeError('Original UI requires KNULLI ARM64 Python 3.12')
        library=v3/'main.cpython-312-aarch64-linux-gnu.so'
        if not library.is_file() or hashlib.sha256(library.read_bytes()).hexdigest()!=EXPECTED_MAIN_SHA256:
            raise RuntimeError('Installed V3 main module differs from the inspected beta; use standalone V4')
    sys.dont_write_bytecode=True
    os.environ['GRAINBRICK_ROOT']=str(v3)
    os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
    if not allow_fixture:
        try:
            import numpy
        except ModuleNotFoundError:
            sys.path.insert(0,str(v3/'_vendor'))
            import numpy
        import pygame.surfarray
    sys.path.insert(0,str(v3))
    policy=BootstrapPolicy(v3,engine)
    sys.addaudithook(policy.audit)
    originals=[(pg,'init',pg.init),(pg.display,'init',pg.display.init),
               (pg.display,'set_mode',pg.display.set_mode),(pg.mixer,'init',pg.mixer.init),
               (pg.joystick,'init',pg.joystick.init)]
    def blocked(*args,**kwargs):
        if policy.loading:
            policy.stop('stopped before V3 pygame initialization')
        raise RuntimeError('Global Pygame/mixer initialization is disabled in LIVE UI')
    for owner,name,_ in originals:
        setattr(owner,name,blocked)
    try:
        try:
            imported=importlib.import_module('main')
            policy.modules['main']=imported
        except BootstrapStop:
            pass
        # Never resume main. Its initial directory creation is the observed
        # boundary, before UI/audio worker construction, on the pinned beta.
        classes={name:policy.modules.get(name) or sys.modules.get(name) for name in TARGETS}
        if classes['ui.renderer'] is None or classes['engine.parameters'] is None:
            raise RuntimeError('Original renderer modules were not captured: '+str(policy.boundary))
        print('NATIVE LIVE UI bootstrap:',policy.boundary or 'import returned',flush=True)
        return classes,policy
    finally:
        policy.loading=False
        # Display/joystick are owned by this frontend. Mixer/global init remain
        # disabled; the independent C child is the only audio owner.
        for owner,name,original in originals:
            if owner is not pg and owner is not pg.mixer:
                setattr(owner,name,original)


class NativeRenderer:
    def __init__(self,root,pg,classes,install_scaling=True):
        self.pg=pg
        self.root=root
        if install_scaling:
            path=root.parent/'grainbrick-beta'/'gb_display_fit.py'
            os.environ.update(GRAINBRICK_SCREEN='640x480',GRAINBRICK_SCALE='fast',GRAINBRICK_FIT='1')
            spec=importlib.util.spec_from_file_location('v4_live_display_fit',path)
            adapter=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(adapter)
            adapter.install()
        cls=classes['ui.renderer'].UIEngine
        original_refresh=cls.refresh_audio_outputs
        cls.refresh_audio_outputs=lambda self:None
        try:
            self.ui=cls(None)
        finally:
            cls.refresh_audio_outputs=original_refresh
        self.screen=self.ui.screen
        bus=classes['engine.parameters'].ParameterBus()
        bus.add('transport.playing',0,0,1)
        self.controls=types.SimpleNamespace(TABS=['LIVE'],tab_index=0,current_tab='LIVE',parameters=bus)
        self.bus=bus
        print('NATIVE LIVE UI renderer ready:',self.screen.get_size(),flush=True)
    def draw_header(self,playing):
        self.bus.set('transport.playing',1 if playing else 0)
        self.ui.draw_tabs(self.controls)
        self.draw_text('LIVE INPUT / V4 ENGINE 0.1.1',49,(224,148,58),True)
    def draw_text(self,text,y,color=(218,226,231),small_font=False):
        # Frontend layout uses 640x480 coordinates; the native renderer keeps
        # its original 1024x768 canvas, scaled by V3's known display adapter.
        scale=3 if small_font else 4
        columns=52 if small_font else 39
        if color==(255,213,100):
            color=(224,148,58)
        for start in range(0,len(text),columns):
            self.ui.text(text[start:start+columns].upper(),32,round(y*1.6),scale,color)
            y+=19
    def draw_parameters(self,params,selected):
        specs=[('mix','WET MIX',0.,1.),('gain','OUTPUT',0.,1.),
               ('grain','GRAIN MS',10.,250.),('delay','DELAY MS',10.,1000.),
               ('pitch','PITCH',.5,2.),('scatter','SCATTER MS',0.,100.)]
        for i,(key,label,lo,hi) in enumerate(specs):
            cx=(180,512,844)[i%3]; cy=252+192*(i//3)
            color=(224,148,58) if i==selected else (198,207,204)
            self.ui.text(label,cx-len(label)*9,cy-78,3,color)
            value=params[key]
            normalized=max(0.,min(1.,(value-lo)/(hi-lo)))
            # Actual native GrainBrick knob widget, not a redrawn imitation.
            self.ui._draw_comp_knob(cx,cy,48,normalized,i==selected)
            text=f'{value:.0f}' if key in ('grain','delay','scatter') else f'{value:.2f}'
            self.ui.text(text,cx-len(text)*12,cy+62,4,color)
    def draw_footer(self,status,device,latest):
        for row,text in enumerate((status[:74],device[:74])):
            self.ui.text(text.upper(),36,566+38*row,2,(157,185,173))
        stats={}
        for token in latest.split():
            if '=' in token:
                key,value=token.split('=',1); stats[key]=value
        text='PEAK '+stats.get('peak','--')+'  /  XRUN '+stats.get('recoveries','0')+'  /  DSP '+stats.get('dsp_max_ms','--')+' MS'
        self.ui.text(text,36,646,2,(144,156,151))
        self.ui.text('D-PAD SELECT / CHANGE   A START   B STOP',36,702,2,(206,211,206))
        self.ui.text('START EXIT / LIVE ONLY / ENGINE 0.1.1',36,736,2,(144,156,151))
    def close(self):
        # UIEngine.close saves original settings. This frontend deliberately
        # delegates device cleanup to pygame.quit and does not call that method.
        pass


def ensure_v3_closed():
    for proc in Path('/proc').iterdir():
        if proc.name.isdigit():
            try:
                args=(proc/'cmdline').read_bytes().split(b'\0')
                if any(a.endswith(b'/gb_launch.py') or a==b'gb_launch.py' for a in args):
                    raise RuntimeError('Close GrainBrick V3 before launching Original UI LIVE')
            except OSError:
                pass


def create_renderer(root,pg):
    ensure_v3_closed()
    v3=root.parent/'grainbrick-beta'
    classes,policy=load_classes(v3,root/'v4-live',pg)
    return NativeRenderer(root,pg,classes)
