"""Isolated original-app and original-DSP checks for the SAMPLE/LIVE redesign."""
from pathlib import Path
import json
import shutil
import types
import numpy as np

class MixerChecks:
    actions={1:'SELECT',2:'LEFT',3:'DOWN',4:'LEFT',5:'DOWN',6:'LEFT',7:'START',8:'SELECT',
             9:'X',10:'R2',11:'Y',12:'Y',13:'X',14:'SELECT',15:'B',16:'Y',17:'Y',
             19:'START',20:'START',21:'SELECT',22:'X',23:'X',24:'X',25:'Y',26:'A',27:'A',28:'X',29:'EXIT'}
    def __init__(self,app):self.app=Path(app)
    def prepare(self):
        if 'work' not in self.app.parts and not self.app.is_relative_to(Path('/tmp')):
            raise RuntimeError('Use an isolated app under work/ or /tmp/')
        folder=self.app/'samples'/('long_sample_browser_path_'*3)
        folder.mkdir(parents=True,exist_ok=True)
        self.sample=folder/(('recorded_and_mangled_sample_'*4)+'.wav')
        shutil.copyfile(self.app/'samples/sample grainbrick 1.wav',self.sample)
        config=self.app/'config.json'
        if config.exists():
            data=json.loads(config.read_text());data['ui_theme']='AMBER';config.write_text(json.dumps(data))
    def first(self,main,c,state):
        from stage_mix import StageMix
        main.load_sample(main._ProjectSampleEntry(str(self.sample)))
        main.controls.tab_index=main.controls.TABS.index('SAMPLE')
        main.record_mode='browser';main.params.set('transport.playing',1)
        assert c.mode=='REC' and not c.active()
        filtered=c.filter_record_actions([('SELECT',None),('EXIT',None)])
        assert filtered==[('SAMPLE_MIXER',None),('EXIT',None)],filtered
        main.controls.tab_index=main.controls.TABS.index('GRAIN')
        assert c.filter_record_actions([('SELECT',None)])==[('SELECT',None)]
        main.controls.tab_index=main.controls.TABS.index('SAMPLE')
        bus=main.params;source=c.source();engine_cls=type(source.file_engine);original_render=engine_cls.render
        seen={}
        def observe(engine,n):
            result=original_render(engine,n)
            if engine is source.file_engine:seen['wet']=result.copy()
            elif engine is source.sample_dry:seen['dry']=result.copy()
            return result
        engine_cls.render=observe
        try:
            bus.set('sample.granular_mix',1)
            np.testing.assert_array_equal(source.render(512),seen['wet'])
            assert source.sample_dry is None
            for mix in (0.,.5,1.):
                bus.set('sample.granular_mix',mix);source.render(512)
                result=source.render(512)
                expected=seen['dry']+(seen['wet']-seen['dry'])*mix
                np.testing.assert_allclose(result,expected,rtol=1e-6,atol=1e-7)
        finally:engine_cls.render=original_render
        print('PASS original native SAMPLE granular dry/half/full blend and default passthrough',flush=True)
        class Observe:
            def __init__(self,engine):self.engine=engine
            def process(self,audio,p,*a,**kw):
                result=self.engine.process(audio,p,*a,**kw);self.wet=result.copy();return result
        for key,engine in (('live.fx_mix',main.dsp.fx.engine),('live.tape_mix',main.dsp.tape.engine)):
            sample_key=key.replace('live.','sample.')
            for mix in (0.,.5,1.):
                bus.set(sample_key,mix);observer=Observe(engine);stage=StageMix(observer,key)
                raw=np.full((512,2),.05,np.float32)
                result=stage.process(raw.copy(),bus)
                expected=raw+(observer.wet-raw)*mix
                np.testing.assert_allclose(result,expected,rtol=1e-6,atol=1e-7)
            bus.set(sample_key,1.)
        print('PASS original native SAMPLE FX/Tape bypass, half and full mixes',flush=True)
        for key in ('sample.granular_mix','sample.fx_mix','sample.tape_mix'):bus.set(key,1.)
        bus.set('transport.playing',0)
        def start_record():
            state['record_start_delegated']+=1;main.record_mode='recording'
        def stop_record():
            state['record_stop_delegated']=state.get('record_stop_delegated',0)+1;main.record_mode='browser'
        main.start_input_recording=start_record;main.stop_input_recording_to_editor=stop_record
        class Preview:
            playing=False;path=None
            def __init__(self):self.calls=[]
            def toggle(self,path,worker,device):
                self.calls.append(str(path));self.path=str(path);self.playing=not self.playing
            def stop(self,restart=True):self.playing=False
            def update(self,worker,selected_path):pass
        main.sample_preview=Preview()
        # Selected Internal output is valid with a connected USB input.
        internal=next(identifier for identifier,label,pcm in main.ui._audio_outputs if pcm=='default')
        selected=main.ui.audio_output_id
        main.ui.audio_output_id=internal
        assert c.choose_output()=='default'
        main.ui.audio_output_id=selected
        from v4_record_ui import RecordingUI
        ui=RecordingUI(main,c)
        original_sources=main.RECORD_SOURCES
        c.message=''
        ui.start_recording()
        assert 'NO USB INPUT' in c.message and main.record_mode=='browser'
        assert main.RECORD_SOURCES is original_sources
        c.message=''
        print('PASS USB input with Internal output and missing-input recording guard',flush=True)
    def frame(self,main,state):
        import pygame
        c=main._v4_controller;n=state['frames']
        if n==2:assert main.record_mode=='ready' and c.mode=='REC'
        if n==8:assert main.params.get('transport.playing')==1
        if n==9:assert main.record_mode=='browser'
        if n==10:
            assert main.record_mode=='ready' and c.mode=='LIVE' and not c.active()
            assert main.params.get('transport.playing')==0
        if n==12:assert c.active()
        if n==13:assert main.params.get('live.freeze')==1
        if n==14:assert main.record_mode=='browser' and c.mode=='REC' and not c.active()
        if n==15:
            assert main.record_mode=='ready'
            for key in ('sample.granular_mix','sample.fx_mix','sample.tape_mix'):
                assert abs(main.params.get(key)-.95)<1e-6,(key,main.params.get(key))
        if n==17:assert main.record_mode=='recording'
        if n==18:assert main.record_mode=='browser'
        if n==20:assert main.sample_preview.playing
        if n==21:assert not main.sample_preview.playing
        if n==23:assert c.mode=='LIVE' and not c.active() and main.record_mode=='ready'
        if n==24:assert c.mode=='REC' and main.record_mode=='browser'
        if n==26:assert c.active() and main.params.get('live.freeze')==0
        if n==27:assert main.params.get('live.freeze')==1
        if n==28:assert main.params.get('live.freeze')==0
        if n==29:assert c.mode=='REC' and not c.active()
    def after_draw(self,main,state):
        import pygame
        n=state['frames']
        if n in (1,2,8,9,10,12,14,15,23,24):
            pygame.image.save(main.ui.screen,str(self.app/f'mixer-ui-{n}.png'))
    def finish(self,main,state):
        assert len(main.sample_preview.calls)==2
        assert state['record_start_delegated']==1 and state['record_stop_delegated']==1
        print('PASS SAMPLE browser/mixer SELECT footer path, three knobs, X ready transitions, LIVE start/freeze/stop, REC and preview delegation',flush=True)
