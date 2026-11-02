"""Native project-playback regressions for an isolated test installation only."""
from pathlib import Path
import json
import wave
import numpy as np

class ProjectChecks:
    def __init__(self,app):self.app=Path(app)
    def prepare(self):
        app=self.app.resolve()
        if 'work' not in app.parts and not app.is_relative_to(Path('/tmp')):
            raise RuntimeError('Project regression checks require an isolated app under work/ or /tmp/')
        factory=json.loads((app/'projects/AMBIENT.json').read_text())
        fixtures=(('TEST_FILE',{},'samples/sample grainbrick 1.wav'),
                  ('TEST_LIVE',{'live.enabled':1,'live.freeze':1,'live.mix':1},'samples/sample grainbrick 1.wav'),
                  ('TEST_MISSING',{},'samples/no-such-sample.wav'),
                  ('TEST_MOVED',{},'/userdata/roms/ports/old-version/samples/alternate.wav'),
                  ('TEST_DEMO',{},'demo-samples/sample grainbrick 1.wav'))
        for name,values,path in fixtures:
            project=json.loads(json.dumps(factory));project['name']=name
            project['parameters'].update(values)
            project['sample']={'type':'absolute' if path.startswith('/') else 'relative','path':path}
            (app/'projects'/f'{name}.json').write_text(json.dumps(project))
        saved=app/'projects/TEST_SAVED.json'
        if saved.exists():saved.unlink()
        audio=np.round(np.sin(np.arange(48000)*2*np.pi*220/48000)*10000).astype('<i2')
        with wave.open(str(app/'samples/alternate.wav'),'wb') as target:
            target.setnchannels(2);target.setsampwidth(2);target.setframerate(48000)
            target.writeframes(np.repeat(audio[:,None],2,axis=1).tobytes())
        (app/'sound_state.json').write_text(json.dumps({'live.enabled':1,'live.freeze':1,'live.mix':1,
            'grain.enabled':1,'grain.position':.2,'sample_path':str(app/'samples/sample grainbrick 1.wav')}))
    def first(self,main,controller,state):
        app=self.app
        assert main.record_mode=='browser'
        assert main.sample_browser.get(main.controls.sample_index).path==str(main.sample.path)
        assert state['start_modes'][0]==0,state['start_modes']
        originals={p:p.read_bytes() for p in (app/'projects').glob('TEST_*.json')}
        main.open_project('TEST_LIVE')
        assert main.params.get('live.enabled')==0 and main.params.get('live.freeze')==0
        assert main.record_mode=='browser'
        controller.start_live()
        main.open_project('TEST_LIVE')
        assert not controller.active()
        assert main.audio_worker.running
        assert main.params.get('transport.playing')==0
        main.controls.tab_index=main.controls.TABS.index('SAMPLE');controller.before_input()
        assert main.record_mode=='browser'
        assert main.sample_browser.get(main.controls.sample_index).path==str(main.sample.path)
        print('PASS same-sample saved LIVE project returns to browser and restarts file worker',flush=True)
        for name,expected in (('TEST_MOVED','alternate.wav'),('TEST_DEMO','sample grainbrick 1.wav')):
            main.open_project(name)
            assert Path(main.sample.path).name==expected,(name,main.sample.path)
            assert main.controls.project_status.startswith('LOADED')
            assert main.params.get('transport.playing')==0
            print('PASS relocated project',name,main.sample.path,flush=True)
        main.open_project('TEST_MISSING')
        assert main.controls.project_status=='SAMPLE NOT FOUND',main.controls.project_status
        assert main.record_mode=='browser'
        main.open_project('TEST_FILE')
        for p,raw in originals.items():assert p.read_bytes()==raw,p
        for key,value in (('transport.playing',1),('grain.enabled',1),('roam.enabled',1),('roam.speed',1),('orbix.enabled',0)):
            main.params.set(key,value)
        peaks=[];positions=[]
        for i in range(64):
            peaks.append(float(np.max(np.abs(main.dsp.render(512)))))
            positions.append(main.dsp.roam_position())
        assert max(peaks)>.001,peaks
        assert abs(positions[-1]-positions[31])>1e-5,positions
        print('PASS loaded-file native DSP audio and moving playhead',max(peaks),positions[31],positions[-1],flush=True)
        main.project_manager.save_project('TEST_SAVED',main.params,str(main.sample.path))
        saved=json.loads((app/'projects/TEST_SAVED.json').read_text())
        assert 'live.enabled' not in saved['parameters'] and 'live.freeze' not in saved['parameters']
        main.params.set('transport.playing',0)
        main.controls.tab_index=main.controls.TABS.index('SAMPLE')
        class Preview:
            playing=False;path=None
            def __init__(self):self.calls=[];self.worker=None
            def toggle(self,path,worker,device):
                self.calls.append(str(path))
                if self.playing:self.stop()
                else:
                    self.path=str(path);self.worker=worker if worker and worker.running else None
                    if self.worker:self.worker.stop()
                    self.playing=True
            def stop(self,restart=True):
                self.playing=False
                if restart and self.worker:self.worker.start()
                self.worker=None
            def update(self,worker,selected_path):
                if self.playing and str(selected_path)!=self.path:self.stop()
        main.sample_preview=Preview()
    def frame(self,main,state):
        if state['frames']==3:
            assert len(main.sample_preview.calls)==1 and main.sample_preview.playing
            print('PASS actual START browser preview dispatch',main.sample_preview.path,flush=True)
        if state['frames']==5:
            assert len(main.sample_preview.calls)==2 and not main.sample_preview.playing
            assert main.audio_worker.running
        if state['frames']==9:
            assert main.params.get('transport.playing')==1
            print('PASS actual GRAIN START play dispatch',flush=True)
    def finish(self,main,state):
        assert len(main.sample_preview.calls)==2
        saved=json.loads((self.app/'sound_state.json').read_text())
        assert 'live.enabled' not in saved and 'live.freeze' not in saved
        print('PASS project/session/preview native regressions; original DSP rendered, OS audio mocked',flush=True)
