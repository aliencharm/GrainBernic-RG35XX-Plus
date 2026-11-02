"""No USB input checks in an isolated original-app runtime."""
from pathlib import Path
import json

class InputChecks:
    actions={1:'R2',2:'Y',3:'X',4:'Y',5:'A',6:'X',7:'EXIT'}
    def __init__(self,app):self.app=Path(app)
    def prepare(self):
        assert 'work' in self.app.parts or self.app.is_relative_to(Path('/tmp'))
        (self.app/'config.json').write_text(json.dumps(dict(capture='auto',playback='default')))
        (self.app/'sound_state.json').write_text(json.dumps(dict(sample_path=str(self.app/'samples/sample grainbrick 1.wav'))))
    def first(self,main,c,state):
        self.c=c
        main.controls.tab_index=main.controls.TABS.index('SAMPLE')
        assert len(main.RECORD_SOURCES)==1 and main.current_record_source()['label']=='NO USB INPUT'
        assert main.resolve_output(main.ui.audio_output_id)=='default'
    def frame(self,main,state):
        n=state['frames']
        assert not self.c.active()
        assert main.current_record_source()['label']=='NO USB INPUT'
        if n in (3,5):assert 'NO USB INPUT' in self.c.message,self.c.message
        if n==7:assert main.record_mode=='browser' and self.c.mode=='REC'
    def after_draw(self,main,state):
        if state['frames'] in (1,5):
            import pygame
            pygame.image.save(main.ui.screen,str(self.app/f'no-input-{state["frames"]}.png'))
    def finish(self,main,state):
        assert state['record_start_delegated']==0
        assert main.params.get('live.enabled')==0
        print('PASS no USB with Internal output: no builtin mic, no recording/capture, clear input message, mode navigation',flush=True)
