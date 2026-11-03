"""Full frozen-buffer export in the isolated original ARM application."""
from pathlib import Path
import wave
import numpy as np

class FrozenChecks:
    actions={1:'X',2:'SELECT',3:'Y',4:'SELECT',5:'A',6:'SELECT',7:'SELECT',8:'A',9:'SELECT',10:'X',11:'EXIT'}
    def __init__(self,app):self.app=Path(app)
    def prepare(self):
        assert 'work' in self.app.parts or self.app.is_relative_to(Path('/tmp'))
    def first(self,main,c,state):
        self.c=c
        main.load_sample(main._ProjectSampleEntry(str(self.app/'samples/sample grainbrick 1.wav')))
        main.controls.tab_index=main.controls.TABS.index('SAMPLE')
        self.folder=Path(main.RECORDINGS_SAMPLE_DIR)
        assert self.folder.resolve().is_relative_to(self.app.resolve())
        self.before=set(self.folder.glob('LIVE_FREEZE_*.wav'))
        class Capture:
            offset=0
            def read(self,n):
                values=((np.arange(n)+self.offset)%2000-1000).astype(np.float32)/32768
                self.offset+=n
                return np.column_stack((values,-values))
            def close(self):pass
        c.capture_factory=Capture;c.source().capture_factory=Capture
        self.loaded=main.sample
        self.expected=None
    def files(self):return set(self.folder.glob('LIVE_FREEZE_*.wav'))-self.before
    def frame(self,main,state):
        n=state['frames'];c=self.c
        if n==3:assert not self.files() and 'FREEZE' in c.message
        if n==4:
            for _ in range(64):main.dsp.render(512)
            self.worker=main.audio_worker
        if n==5:assert not self.files() and 'FREEZE' in c.message
        if n==6:
            assert main.params.get('live.freeze')==1
            main.dsp.render(512)
            self.expected=c.source().frozen_snapshot()
            assert self.expected.shape==(16*48000,2)
            main.params.set('grain.size',.02);main.params.set('roam.range',.1)
        if n in (7,8):
            assert len(self.files())==n-6
            assert main.audio_worker is self.worker and self.worker.running
            assert c.active() and main.params.get('live.freeze')==1
            assert main.sample is self.loaded
            for path in self.files():
                with wave.open(str(path),'rb') as saved:
                    assert (saved.getframerate(),saved.getnchannels(),saved.getsampwidth(),saved.getnframes())==(48000,2,2,16*48000)
                    pcm=np.frombuffer(saved.readframes(saved.getnframes()),dtype='<i2').reshape(-1,2)
                    np.testing.assert_array_equal(pcm,np.rint(self.expected*32768).astype('<i2'))
        if n==10:assert len(self.files())==2 and 'FREEZE' in c.message
        if n==11:assert main.record_mode=='browser' and c.mode=='REC'
    def after_draw(self,main,state):
        if state['frames'] in (6,7):
            import pygame
            pygame.image.save(main.ui.screen,str(self.app/f'frozen-save-{state["frames"]}.png'))
    def finish(self,main,state):
        assert len(self.files())==2
        print('PASS full 16-second frozen WAV export, unique names, exact input PCM, no grain/range truncation, retained LIVE/freeze and unfrozen guards',flush=True)
