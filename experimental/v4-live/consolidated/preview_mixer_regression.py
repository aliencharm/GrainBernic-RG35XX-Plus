"""Exercise original SamplePreview handoff with only external players mocked."""
from pathlib import Path
import io
import wave
import numpy as np

class PreviewMixerChecks:
    actions={1:'START',2:'SELECT',3:'START',4:'START',5:'SELECT',6:'START',7:'SELECT',8:'START',9:'START',10:'SELECT',11:'START',12:'SELECT',13:'START',14:'EXIT'}
    def __init__(self,app):self.app=Path(app)
    def prepare(self):
        assert 'work' in self.app.parts or self.app.is_relative_to(Path('/tmp'))
        self.path=self.app/'samples/TEST_PREVIEW_MIXER.wav'
        values=(np.sin(np.arange(48000)*2*np.pi*220/48000)*10000).astype('<i2')
        with wave.open(str(self.path),'wb') as target:
            target.setnchannels(2);target.setsampwidth(2);target.setframerate(48000)
            target.writeframes(np.repeat(values[:,None],2,axis=1).tobytes())
    def first(self,main,c,state):
        import subprocess
        class Player:
            def __init__(self,*args,**kwargs):
                self.returncode=None;self.stdin=io.BytesIO();self.stdout=io.BytesIO();self.stderr=io.BytesIO();self.pid=999999
            def poll(self):return self.returncode
            def terminate(self):self.returncode=0
            def kill(self):self.returncode=-9
            def wait(self,timeout=None):self.returncode=0;return 0
        subprocess.Popen=Player
        main.load_sample(main._ProjectSampleEntry(str(self.path)))
        main.controls.tab_index=main.controls.TABS.index('SAMPLE')
        main.sample_browser.current_dir=str(self.path.parent);main.sample_browser.refresh()
        main.controls.set_sample_count(len(main.sample_browser))
        main.controls.sample_index=next(i for i,e in enumerate(main.sample_browser.entries) if e.path==str(self.path))
        main.params.set('grain.enabled',0);main.params.set('roam.enabled',0);main.params.set('transport.playing',0)
        for key in ('sample.granular_mix','sample.fx_mix','sample.tape_mix'):main.params.set(key,0)
        self.preview=main.sample_preview
    def frame(self,main,state):
        n=state['frames']
        if n==6:
            for key in ('sample.granular_mix','sample.fx_mix','sample.tape_mix'):main.params.set(key,1)
        if n==11:
            main.params.set('grain.enabled',1);main.params.set('sample.granular_mix',0)
            main.params.set('sample.fx_mix',0);main.params.set('sample.tape_mix',0)
        if n in (2,7,12):
            assert main.sample_preview is self.preview
            assert self.preview.playing and not main.audio_worker.running
        if n in (3,8,13):
            assert main.record_mode=='ready' and not self.preview.playing
            assert Path(main.sample.path)==self.path,('Mixer did not load the previewed file',main.sample.path)
            assert main.audio_worker.running
            assert main.params.get('transport.playing')==0
        if n in (4,9,14):
            assert main.audio_worker.running and main.params.get('transport.playing')==1
            peak=max(float(np.max(np.abs(main.dsp.render(512)))) for _ in range(8))
            assert peak>.001,peak
    def after_draw(self,main,state):
        if state['frames'] in (3,4):
            import pygame
            pygame.image.save(main.ui.screen,str(self.app/f'preview-mixer-{state["frames"]}.png'))
    def finish(self,main,state):
        print('PASS original preview player to SAMPLE mixer, loaded-file preview handoff and disabled-processing playback, native DSP sound and repeated cycles',flush=True)
