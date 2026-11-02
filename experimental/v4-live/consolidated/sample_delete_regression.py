"""Destructive actions are exercised only on synthetic isolated samples."""
from pathlib import Path
import shutil

class DeleteChecks:
    actions={1:'B',2:'A',3:'B',4:'DOWN',5:'UP',6:'B',7:'B',8:'X',9:'X',10:'A',11:'B',12:'B',13:'B',14:'EXIT'}
    def __init__(self,app):self.app=Path(app)
    def prepare(self):
        assert 'work' in self.app.parts or self.app.is_relative_to(Path('/tmp'))
        self.folder=self.app/'samples/TEST_DELETE'
        self.folder.mkdir(exist_ok=True)
        self.files=[self.folder/'a.wav',self.folder/'b.wav']
        for path in self.files:shutil.copyfile(self.app/'samples/sample grainbrick 1.wav',path)
    def first(self,main,c,state):
        main.sample_browser.current_dir=str(self.folder);main.sample_browser.refresh()
        main.controls.set_sample_count(len(main.sample_browser))
        entry=next(e for e in main.sample_browser.entries if e.path==str(self.files[0]))
        main.load_sample(entry)
        main.controls.tab_index=main.controls.TABS.index('SAMPLE')
        assert main.record_mode=='browser'
    def frame(self,main,state):
        n=state['frames']
        if n in (2,3,4,5,6,7):assert self.files[0].exists()
        if n==8:
            assert not self.files[0].exists() and main.sample is None
            assert main.audio_worker is None and main.params.get('transport.playing')==0
            assert self.files[1].exists()
        if n==11:
            assert main.sample is not None and main.audio_worker.running
            main.controls.tab_index=main.controls.TABS.index('SAMPLE')
        if n==13:assert not self.files[1].exists() and main.sample is None
        if n==14:assert main.sample_browser.current_dir!=str(self.folder)
    def after_draw(self,main,state):
        if state['frames'] in (2,3,7,8,13,14):
            import pygame
            pygame.image.save(main.ui.screen,str(self.app/f'delete-ui-{state["frames"]}.png'))
    def finish(self,main,state):
        assert all(not p.exists() for p in self.files)
        print('PASS sample deletion: first press retains file, cancel/navigation, loaded-file unload, reload remaining sample, last-file deletion and folder back',flush=True)
