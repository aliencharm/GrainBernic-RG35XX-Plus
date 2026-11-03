"""Offline native Stardust timing probe. Does not open an audio device."""
import fcntl,json,platform,time
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ports=Path(sys.argv[1]).resolve();app=ports/'grainbrick-v4'
sys.path.insert(0,str(app/'_vendor'));sys.path.insert(0,str(app))
import numpy as np
from v4_shimmer import StardustDSP,SHIMMER_DEFAULTS
class Params:
    def __init__(self):
        self.values={k:v[0] for k,v in SHIMMER_DEFAULTS.items()}
        self.values.update({'stardust.size':1.,'stardust.decay':1.,'stardust.depth':1.,'stardust.frequency':5.,'stardust.brightness':1.,'stardust.pitch':12.})
    def get(self,key):return self.values[key]
with (app/'.lock').open('a') as lock:
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit('Close GrainBrick before running this timing test')
    print('STARDUST NATIVE TIMING - NO AUDIO OUTPUT')
    print('Version:',json.loads((app/'RELEASE.json').read_text())['version'])
    print('Platform:',platform.machine(),platform.release())
    engine=StardustDSP();params=Params();n=512;rate=48000
    feed=np.repeat((np.sin(np.arange(n)*2*np.pi*440/rate)*.2).astype(np.float32)[:,None],2,axis=1)
    audio=feed.copy()
    for _ in range(64):np.copyto(audio,feed);engine.process(feed,audio,params)
    times=[]
    for _ in range(512):
        np.copyto(audio,feed);start=time.perf_counter_ns();engine.process(feed,audio,params)
        times.append((time.perf_counter_ns()-start)/1e6)
    engine.close();values=np.array(times);budget=n/rate*1000
    print('Rate:',rate,'frames:',n,'block budget ms:',round(budget,3))
    print('Mean ms:',round(float(values.mean()),4),'median ms:',round(float(np.median(values)),4),'p95 ms:',round(float(np.percentile(values,95)),4),'max ms:',round(float(values.max()),4))
    print('Mean portion of one audio-block budget:',round(float(values.mean())/budget*100,2),'percent')
    print('Stardust only. Granular, other FX, tape, USB, UI and scheduling overhead are excluded.')
    print('For full-app headroom, compare the DSP meter and overruns with Original/Stardust on the handheld.')
