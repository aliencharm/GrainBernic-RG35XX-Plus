"""Blend around an ORIGINAL DSP stage, without changing its processing or ordering."""
import numpy as np

class StageMix:
    def __init__(self,engine,key):
        self.engine=engine;self.key=key;self._mix=None
        self._dry=None;self._ramp=None;self._weights=None
    def __getattr__(self,name):return getattr(self.engine,name)
    def process(self,audio,parameters,*args,**kwargs):
        if parameters.get('live.enabled')<.5:
            self._mix=None
            return self.engine.process(audio,parameters,*args,**kwargs)
        target=max(0.,min(1.,parameters.get(self.key)))
        current=target if self._mix is None else self._mix
        self._mix=target
        if current==1. and target==1.:return self.engine.process(audio,parameters,*args,**kwargs)
        if self._dry is None or self._dry.shape!=audio.shape:
            self._dry=np.empty_like(audio)
            self._ramp=np.linspace(0.,1.,audio.shape[0],dtype=np.float32)
            self._weights=np.empty((audio.shape[0],1),dtype=np.float32)
        np.copyto(self._dry,audio)
        wet=self.engine.process(audio,parameters,*args,**kwargs)
        # Both native engines process in place and return the audio array.
        # Always run them, including at 0%, to maintain delay/tape state.
        if current==0. and target==0.:
            # DSPChain consumes the in-place audio, not the returned array.
            np.copyto(wet,self._dry)
            return wet
        if current==target:
            wet-=self._dry;wet*=target;wet+=self._dry
        else:
            np.multiply(self._ramp,target-current,out=self._weights[:,0])
            self._weights+=current
            wet-=self._dry;wet*=self._weights;wet+=self._dry
        return wet
