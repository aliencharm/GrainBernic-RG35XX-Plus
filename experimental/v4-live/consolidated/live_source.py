"""Source adapter for the ORIGINAL GranularEngine and DSPChain; no replacement FX."""
import ctypes
import os
import select
import signal
import subprocess
import time
import types
import weakref
from pathlib import Path
import numpy as np

RATE=48000
LIVE_DEFAULTS={'live.enabled':(0.,0.,1.),'live.mix':(0.,0.,1.),'live.freeze':(0.,0.,1.),
               'live.fx_mix':(1.,0.,1.),'live.tape_mix':(1.,0.,1.),
               'sample.granular_mix':(1.,0.,1.),'sample.fx_mix':(1.,0.,1.),'sample.tape_mix':(1.,0.,1.)}

def add_live_parameters(bus):
    for key,(value,lo,hi) in LIVE_DEFAULTS.items():
        if key not in bus.params:bus.add(key,value,lo,hi)
    return bus

class ArecordCapture:
    def __init__(self,pcm,rate=RATE,latency_us=24000):
        parent=os.getpid()
        def parent_death_signal():
            libc=ctypes.CDLL(None,use_errno=True)
            if libc.prctl(1,int(signal.SIGTERM),0,0,0)!=0:os._exit(126)
            if os.getppid()!=parent:os._exit(126)
        self.process=subprocess.Popen(['arecord','-q','-D',pcm,'-t','raw','-f','S16_LE','-r',str(rate),'-c','2','--buffer-time='+str(latency_us),'--period-time='+str(max(1000,latency_us//4))],
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,bufsize=0,preexec_fn=parent_death_signal)
        os.set_blocking(self.process.stdout.fileno(),False)
    def read(self,frames):
        required=frames*4; data=bytearray();deadline=time.monotonic()+2.
        while len(data)<required:
            if self.process.poll() is not None:raise OSError('Live capture exited: '+str(self.process.returncode))
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError('Live capture stalled for two seconds')
            ready,_,_=select.select([self.process.stdout],[],[],min(.1,remaining))
            if not ready:continue
            chunk=os.read(self.process.stdout.fileno(),required-len(data))
            if not chunk:raise OSError('Live capture stream ended')
            data.extend(chunk)
        return np.frombuffer(data,dtype='<i2').reshape(frames,2).astype(np.float32)*(1./32768.)
    def close(self):
        process=self.process
        if process.poll() is None:
            process.terminate()
            try:process.wait(timeout=1.)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=1.)
        process.stdout.close()

class LiveParameterView:
    def __init__(self,source):
        self.source=weakref.proxy(source)
        self._tracking_margin=None;self._frozen_margin=None
    def get(self,key):
        source=self.source
        value=source.parameters.get(key)
        if key=='grain.position':
            size=source.parameters.get('grain.size')
            ratio=2.**(source.parameters.get('grain.pitch')/12.)
            margin=int(size*source.rate*max(1.,ratio))+source.block+int(.02*source.rate)
            if source.parameters.get('live.freeze')>=.5:
                if self._frozen_margin is None:
                    self._frozen_margin=margin if self._tracking_margin is None else self._tracking_margin
                margin=self._frozen_margin
            else:
                self._frozen_margin=None;self._tracking_margin=margin
            # Freeze retains its read anchor while SIZE/PITCH change. POSITION
            # still scans the held buffer; unfrozen input retains safety headroom.
            # 0.5 follows recent input; moving the original position knob scans
            # around that live anchor. Original file-mode semantics are untouched.
            position=(source.writer-margin+(value-.5)*source.capacity)%source.capacity
            return position/(source.capacity-1)
        if key=='grain.spray':
            return value*min(1.,source.written/source.capacity)
        return value

class SampleDryView:
    """Use the original native file player with granular/motion/pitch disabled."""
    OVERRIDES={'grain.enabled':0.,'roam.enabled':0.,'motion.enabled':0.,'grain.pitch':0.}
    def __init__(self,source):self.source=weakref.proxy(source)
    def get(self,key):
        return self.OVERRIDES[key] if key in self.OVERRIDES else self.source.parameters.get(key)

class GrainCount:
    def __init__(self,source):self.source=weakref.proxy(source)
    def __len__(self):return self.source.active_grains()

class SwitchableSource:
    """Original file source, or original granular engine over a live RAM ring."""
    def __init__(self,file_engine,parameters,granular_cls,capture_factory,rate=RATE,seconds=16,storage=None):
        self.file_engine=file_engine;self._parameters=parameters
        self.granular_cls=granular_cls;self.capture_factory=capture_factory
        self.rate=rate;self.capacity=int(rate*seconds);self.block=512
        if self.capacity<rate*12:raise ValueError('Live history must cover original two-second grains at +24 semitones')
        self.data=np.zeros((self.capacity,2),dtype=np.float32) if storage is None else storage
        if self.data.shape!=(self.capacity,2) or self.data.dtype!=np.float32 or not self.data.flags.c_contiguous:
            raise ValueError('Live storage must be contiguous float32 stereo')
        self.sample=types.SimpleNamespace(data=self.data,frames=self.capacity,sample_rate=rate,channels=2,duration=seconds,bit_depth=32,path=Path('LIVE INPUT'))
        self.view=LiveParameterView(self)
        self.live_engine=None;self.capture=None;self.writer=0;self.written=0;self.processed=0;self._last_report=0
        self.grains=GrainCount(self);self.chain=None
        self.sample_dry=None;self._sample_mix=None
    @property
    def parameters(self):return self.chain.parameters if self.chain is not None else self._parameters
    @parameters.setter
    def parameters(self,value):
        self._parameters=value
        self.file_engine.parameters=value
    def enabled(self):return self.parameters.get('live.enabled')>=.5
    def _engine(self):return self.live_engine if self.enabled() and self.live_engine is not None else self.file_engine
    def render(self,frames):
        self.block=frames
        if not self.enabled():
            self.close()
            self.file_engine.parameters=self.parameters
            wet=self.file_engine.render(frames)
            target=max(0.,min(1.,self.parameters.get('sample.granular_mix')))
            current=target if self._sample_mix is None else self._sample_mix
            self._sample_mix=target
            if self.sample_dry is None and current==1. and target==1.:return wet
            if self.sample_dry is None:
                self.sample_dry=self.granular_cls(self.file_engine.sample,SampleDryView(self),self.rate)
            dry=self.sample_dry.render(frames)
            if current==1. and target==1.:return wet
            if current==target:weights=target
            else:weights=np.linspace(current,target,frames,dtype=np.float32)[:,None]
            return (dry+(wet-dry)*weights).astype(np.float32,copy=False)
        if self.parameters.get('transport.playing')<.5:
            self.close()
            return np.zeros((frames,2),dtype=np.float32)
        if self.capture is None:
            self.capture=self.capture_factory()
            # multiprocessing's normal child finalizers run before os._exit.
            from multiprocessing.util import Finalize
            self._finalizer=Finalize(None,self.close,exitpriority=20)
        self._sample_mix=None
        dry=self.capture.read(frames)
        self.processed+=frames
        if dry.shape!=(frames,2):raise ValueError('Invalid capture block shape')
        if self.parameters.get('live.freeze')<.5:
            count=min(frames,self.capacity-self.writer)
            self.data[self.writer:self.writer+count]=dry[:count]
            if count<frames:self.data[:frames-count]=dry[count:]
            self.writer=(self.writer+frames)%self.capacity;self.written+=frames
        if self.live_engine is None:self.live_engine=self.granular_cls(self.sample,self.view,self.rate)
        wet=self.live_engine.render(frames)
        mix=max(0.,min(1.,self.parameters.get('live.mix')))
        if self.processed-self._last_report>=self.rate*2:
            self._last_report=self.processed
            print('ORIGINAL LIVE SOURCE frames=%d input_peak=%.4f grain_peak=%.4f mix=%.2f size_s=%.3f density=%.1f pitch_st=%.1f freeze=%d fx_mix=%.2f tape_mix=%.2f' %
                  (self.processed,float(np.max(np.abs(dry))),float(np.max(np.abs(wet))),mix,
                   self.parameters.get('grain.size'),self.parameters.get('grain.density'),self.parameters.get('grain.pitch'),self.parameters.get('live.freeze')>=.5,
                   self.parameters.get('live.fx_mix'),self.parameters.get('live.tape_mix')),flush=True)
        return (dry*(1.-mix)+wet*mix).astype(np.float32,copy=False)
    def close(self):
        finalizer=getattr(self,'_finalizer',None)
        self._finalizer=None
        if finalizer is not None:finalizer.cancel()
        if self.capture is not None:
            capture=self.capture;self.capture=None
            capture.close()
    def active_grains(self):return self._engine().active_grains()
    def roam_position(self):return self._engine().roam_position()
    def roam_range_start(self):return self._engine().roam_range_start()
    def roam_range_end(self):return self._engine().roam_range_end()
