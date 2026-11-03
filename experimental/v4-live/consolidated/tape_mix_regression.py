"""Check SAMPLE Tape mix through the real native DSP chain."""
from pathlib import Path
import wave
import numpy as np

class TapeMixChecks:
    actions={3:'EXIT'}
    def __init__(self,app):self.app=Path(app)
    def prepare(self):
        assert 'work' in self.app.parts or self.app.is_relative_to(Path('/tmp'))
        self.path=self.app/'samples/TEST_TAPE_MIX.wav'
        values=(np.sin(np.arange(48000)*2*np.pi*440/48000)*22000).astype('<i2')
        with wave.open(str(self.path),'wb') as out:
            out.setnchannels(2);out.setsampwidth(2);out.setframerate(48000)
            out.writeframes(np.repeat(values[:,None],2,axis=1).tobytes())
    def first(self,main,c,state):
        main.load_sample(main._ProjectSampleEntry(str(self.path)))
        main.controls.tab_index=main.controls.TABS.index('SAMPLE')
        class Observe:
            def __init__(self,engine):self.engine=engine;self.calls=[]
            def __getattr__(self,name):return getattr(self.engine,name)
            def process(self,audio,parameters,*args,**kwargs):
                self.before=audio.copy();self.calls.append((args,kwargs))
                result=self.engine.process(audio,parameters,*args,**kwargs)
                self.wet=result.copy();return result
        def run(grain,mix,enabled=1):
            bus=main.create_default_parameters()
            for key in bus.params:
                if key.endswith('.enabled'):bus.set(key,0)
            for key,value in (('transport.playing',1),('grain.enabled',grain),('sample.granular_mix',0),('sample.fx_mix',0),('sample.tape_mix',mix),('tape.enabled',enabled),('tape.saturation',.9),('level.input_db',0),('level.master_db',0)):
                bus.set(key,value)
            for key in ('tape.wow','tape.flutter','tape.hiss','tape.dropout','tape.crinkle','tape.bit8'):bus.set(key,0)
            engine=main.GranularEngine(main.sample,bus,output_rate=main.RATE)
            chain=main.DSPChain(engine,bus,output_rate=main.RATE)
            observer=Observe(chain.tape.engine);chain.tape.engine=observer
            blocks=[]
            for _ in range(16):
                out=chain.render(512);blocks.append(out.copy())
                expected=observer.before+(observer.wet-observer.before)*mix
                np.testing.assert_allclose(out,expected,rtol=1e-5,atol=1e-6)
            effect=float(np.max(np.abs(observer.wet-observer.before)))
            print('TAPE DIAGNOSTIC grain',grain,'mix',mix,'effect difference',effect,'arguments',observer.calls[-1],flush=True)
            return np.concatenate(blocks),effect
        for grain in (0,1):
            dry,_=run(grain,0)
            disabled,_=run(grain,1,enabled=0)
            for mix in (.25,.5,.75,1):
                wet,effect=run(grain,mix)
                assert effect>.001,('Native Tape did not process sample',grain,mix,effect)
                assert float(np.max(np.abs(wet-dry)))>.001
                assert float(np.max(np.abs(wet-disabled)))>.001
        print('PASS native SAMPLE TAPE at 0/25/50/75/100 percent with grain ON/OFF; saturation changes actual output',flush=True)
    def frame(self,main,state):pass
    def finish(self,main,state):pass
