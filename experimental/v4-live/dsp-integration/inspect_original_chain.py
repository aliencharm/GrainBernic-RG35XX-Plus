"""Offline original-library test. No ALSA, GUI startup, recording or user-file writes."""
from pathlib import Path
import importlib
import json
import sys
import types

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'original-ui'))
import native_ui
import pygame as pg
import numpy as np
native_ui.TARGETS=(*native_ui.TARGETS,'engine.dsp_chain','engine.granular_c','engine.control')
v3=Path(sys.argv[1]).resolve()
modules,policy=native_ui.load_classes(v3,HERE/'package/grainbrick-v4-live/v4-live',pg)
parameters=modules['engine.parameters'].create_default_parameters()
params=getattr(parameters,'params',{})
print('PARAM FIELDS',list(vars(parameters)),flush=True)
print('ORIGINAL PARAMETERS',json.dumps({k:{a:getattr(v,a,None) for a in ('value','minimum','maximum')} for k,v in params.items()},indent=2),flush=True)
chain_cls=modules['engine.dsp_chain'].DSPChain
class Source:
    def __init__(self):
        self.phase=0;self.calls=0;self.grains=[];self.parameters=parameters
    def render(self,frames):
        self.calls+=1
        t=(np.arange(frames,dtype=np.float64)+self.phase)/48000.
        self.phase+=frames
        mono=(0.05*np.sin(2*np.pi*440*t)).astype(np.float32)
        return np.repeat(mono[:,None],2,axis=1)
    def roam_position(self):return 0.
    def roam_range_start(self):return 0.
    def roam_range_end(self):return 1.
    def active_grains(self):return 0
source=Source()
parameters.set('transport.playing',1)
chain=chain_cls(source,parameters,48000)
print('CHAIN FIELDS',[(k,type(v).__name__) for k,v in vars(chain).items()],flush=True)
outputs=[]
for _ in range(32):
    out=chain.render(512)
    assert out.shape==(512,2) and out.dtype==np.float32
    assert np.isfinite(out).all()
    outputs.append(out.copy())
print('SOURCE CONTRACT',{'calls':source.calls,'frames':source.phase,'output_peak':float(np.max(np.abs(outputs)))},flush=True)
assert source.calls>0 and np.max(np.abs(outputs))>0
print('PASS original DSPChain renders a Python-provided stereo float32 source',flush=True)

# Prove that changing an ORIGINAL FX parameter changes the inserted source.
class ImpulseSource(Source):
    def render(self,frames):
        out=np.zeros((frames,2),dtype=np.float32)
        target=48000
        if self.phase<=target<self.phase+frames:
            out[target-self.phase,:]=0.2
        self.phase+=frames;self.calls+=1
        return out

def impulse_run(delay_mix):
    bus=modules['engine.parameters'].create_default_parameters()
    for key,value in [('transport.playing',1),('tape.enabled',0),('orbix.enabled',0),
                      ('delay.time',100),('delay.feedback',0),('delay.mix',delay_mix),
                      ('reverb.mix',0),('shimmer.mix',0)]:bus.set(key,value)
    original=chain_cls(ImpulseSource(),bus,48000)
    result=[]
    for _ in range(150):result.append(original.render(512).copy())
    return np.concatenate(result,axis=0)
dry=impulse_run(0)
effected=impulse_run(0.8)
window=slice(48000+4800-512,48000+4800+512)
baseline=float(np.sum(dry[window]**2))
echo=float(np.sum(effected[window]**2))
assert np.isfinite(effected).all()
assert echo>max(1e-8,baseline*10),(baseline,echo)
print('PASS original delay processes inserted audio:',{'dry_echo_window_energy':baseline,'delay_echo_window_energy':echo},flush=True)

# Use the actual original granular wrapper; do not invent native signatures.
bus=modules['engine.parameters'].create_default_parameters()
for key,value in [('grain.enabled',1),('roam.enabled',0),('motion.enabled',0),('grain.pitch',0)]:bus.set(key,value)
sample=types.SimpleNamespace(data=np.full((48000,2),0.05,dtype=np.float32),frames=48000,sample_rate=48000,channels=2)
granular=modules['engine.granular_c'].GranularEngine(sample,bus,48000)
before=[]
for _ in range(32):before.append(granular.render(512).copy())
handle_before=granular._handle
sample.data.fill(-0.05)
after=[]
for _ in range(32):after.append(granular.render(512).copy())
before_mean=float(np.mean(before[-8:]));after_mean=float(np.mean(after[-8:]))
result={'before_mean':before_mean,'after_mean':after_mean,'handle_retained':granular._handle==handle_before}
print('ORIGINAL BUFFER MUTATION',result,flush=True)
assert before_mean>0.001 and after_mean<-0.001,result
assert result['handle_retained']
print('PASS original granular engine sees in-place source updates without recreation',flush=True)

# Verify the existing density control on the original granular engine.
for density in (1,8,32):
    b=modules['engine.parameters'].create_default_parameters()
    for key,value in [('grain.enabled',1),('grain.density',density),('grain.size',0.18),
                      ('grain.spray',0),('roam.enabled',0),('motion.enabled',0)]:b.set(key,value)
    original=modules['engine.granular_c'].GranularEngine(sample,b,48000)
    counts=[]
    for _ in range(94):
        block=original.render(512)
        assert np.isfinite(block).all()
        counts.append(original.active_grains())
    print('ORIGINAL DENSITY',density,'max_active',max(counts),'mean_active',float(np.mean(counts)),flush=True)
print('PASS native density accepts its original parameter values',flush=True)

sys.path.insert(0,str(Path(__file__).resolve().parent))
from live_source import SwitchableSource,add_live_parameters
class SyntheticCapture:
    def __init__(self):self.frame=0;self.closed=False
    def read(self,frames):
        t=(np.arange(frames)+self.frame)/48000.
        self.frame+=frames
        return np.repeat((.05*np.sin(2*np.pi*220*t)).astype(np.float32)[:,None],2,axis=1)
    def close(self):self.closed=True
p=add_live_parameters(modules['engine.parameters'].create_default_parameters())
for key,value in [('transport.playing',1),('live.enabled',1),('live.mix',1),
                  ('grain.size',.02),('grain.density',32),('grain.spray',0),('tape.enabled',0)]:p.set(key,value)
file_source=modules['engine.granular_c'].GranularEngine(sample,p,48000)
capture=SyntheticCapture()
sw=SwitchableSource(file_source,p,modules['engine.granular_c'].GranularEngine,lambda:capture)
full_chain=chain_cls(sw,p,48000);sw.chain=full_chain
live_peak=0
for _ in range(180):
    out=full_chain.render(512)
    assert out.shape==(512,2) and np.isfinite(out).all()
    live_peak=max(live_peak,float(np.max(np.abs(out))))
assert live_peak>1e-4,live_peak
assert sw.view.get('grain.density')==32 and sw.view.get('grain.pitch')==p.get('grain.pitch')
frozen=sw.data.copy();position=sw.writer;p.set('live.freeze',1)
for _ in range(32):full_chain.render(512)
assert sw.writer==position and np.array_equal(frozen,sw.data)
p.set('live.freeze',0);full_chain.render(512);assert sw.writer!=position
p.set('live.enabled',0);full_chain.render(512);assert capture.closed
print('PASS original DSP chain + original live-buffer granular engine, native density/pitch passthrough, freeze/resume and file-source return',{'peak':live_peak},flush=True)

# Execute the ORIGINAL audio-worker setup and loop, mocking only OS process,
# thread scheduling and the actual playback device. Keep its shared-parameter
# reader, original DSP chain and original granular library real.
import multiprocessing as mp
import multiprocessing.heap
multiprocessing.heap.Arena._dir_candidates=[]
import threading
worker_module=sys.modules['engine.audio_worker']
real_ctx=mp.get_context('fork')
created=[]
class Event:
    def __init__(self):self.polls=0;self.stopped=False
    def clear(self):self.polls=0;self.stopped=False
    def set(self):self.stopped=True
    def is_set(self):
        self.polls+=1
        return self.stopped or self.polls>48
    def wait(self,timeout=None):return self.is_set()
class Process:
    def __init__(self,target,args=(),**kwargs):self.target=target;self.args=args;self.alive=False;self.exitcode=None;created.append(self)
    def start(self):self.alive=True
    def is_alive(self):return self.alive
    def join(self,timeout=None):pass
    def terminate(self):self.alive=False
    def close(self):pass
class Thread:
    def __init__(self,*args,**kwargs):pass
    def start(self):pass
    def is_alive(self):return False
    def join(self,timeout=None):pass
class Context:
    def Event(self):return Event()
    def Value(self,*args,**kwargs):kwargs['lock']=False;return real_ctx.Value(*args,**kwargs)
    def Array(self,*args,**kwargs):kwargs['lock']=False;return real_ctx.Array(*args,**kwargs)
    def RawArray(self,*args,**kwargs):return real_ctx.RawArray(*args,**kwargs)
    def RawValue(self,*args,**kwargs):return real_ctx.RawValue(*args,**kwargs)
    def Process(self,*args,**kwargs):return Process(*args,**kwargs)
class Output:
    device='default'
    def __init__(self):self.blocks=[];self.process=types.SimpleNamespace(poll=lambda:None);self.stopped=False
    def start(self):pass
    def write(self,audio):self.blocks.append(audio.copy())
    def stop(self):self.stopped=True
    def switch_device(self,pcm):self.device=pcm
p=add_live_parameters(modules['engine.parameters'].create_default_parameters())
for key,value in [('transport.playing',1),('live.enabled',1),('live.mix',1),('grain.size',.02),('grain.density',32)]:p.set(key,value)
capture=SyntheticCapture()
sw=SwitchableSource(modules['engine.granular_c'].GranularEngine(sample,p,48000),p,modules['engine.granular_c'].GranularEngine,lambda:capture)
full_chain=chain_cls(sw,p,48000);sw.chain=full_chain
old_ctx=mp.get_context;old_thread=threading.Thread;old_app_path=worker_module.app_path
worker_module.app_path=lambda name:Path('/workspace/arm-dsp-lab')/name
try:
    mp.get_context=lambda *a:Context();threading.Thread=Thread
    output=Output()
    worker=worker_module.AudioWorker(full_chain,output,block_size=512)
    worker.start()
    process=created[-1]
    process.target(*process.args)
    process.alive=False;process.exitcode=0
    worker.stop()
finally:
    mp.get_context=old_ctx;threading.Thread=old_thread;worker_module.app_path=old_app_path
    sw.close()
assert len(output.blocks)>0 and np.isfinite(np.stack(output.blocks)).all()
assert max(float(np.max(np.abs(b))) for b in output.blocks)>1e-5
assert output.stopped and capture.closed
print('PASS original AudioWorker setup/shared-parameter-reader/processing loop with live source and original DSP;',len(output.blocks),'blocks; OS audio/process boundaries mocked',flush=True)
