"""Exercise physical LIVE controls through the real controller translator."""
from pathlib import Path
import json

class LiveControlsChecks:
    actions={1:'Y',2:'X',3:'EXIT'}
    def __init__(self,app):self.app=Path(app)
    def prepare(self):assert 'work' in self.app.parts or self.app.is_relative_to(Path('/tmp'))
    def first(self,main,c,state):
        import pygame
        main.load_sample(main._ProjectSampleEntry(str(self.app/'samples/sample grainbrick 1.wav')))
        main.controls.tab_index=main.controls.TABS.index('SAMPLE')
        mapping=json.loads((self.app/'gb_buttons.json').read_text())['buttons']
        logical={'A':5,'B':4,'X':7,'Y':6}
        def press(label):
            physical=next(int(k) for k,v in mapping.items() if v==logical[label])
            pygame.event.post(pygame.event.Event(pygame.JOYBUTTONDOWN,button=physical,joy=0))
            events=pygame.event.get()
            assert not any(e.type in (pygame.JOYBUTTONDOWN,pygame.JOYBUTTONUP) and e.button==logical[label] for e in events)
            actions=c.filter_record_actions([])
            assert len(actions)==1,actions
            for action,value in actions:assert main.handle_record_action(action,value)
            pygame.event.post(pygame.event.Event(pygame.JOYBUTTONUP,button=physical,joy=0))
            released=pygame.event.get()
            assert not any(e.type==pygame.JOYBUTTONUP and e.button==logical[label] for e in released)
        def live_ready():
            main.handle_record_action('X',None)
            assert c.mode=='LIVE' and main.record_mode=='ready'
        live_ready();press('Y');assert c.active()
        press('A');assert main.params.get('live.freeze')==1
        press('Y');assert not c.active() and c.mode=='LIVE' and main.record_mode=='ready'
        press('Y');assert c.active() and main.params.get('live.freeze')==0
        press('A');assert main.params.get('live.freeze')==1
        assert c.filter_record_actions([('SELECT',None)])==[('SELECT',None)]
        main.params.set('transport.playing',0)
        press('Y');assert not c.active() # Y stops even paused and frozen.
        press('Y');assert c.active()
        press('X');assert c.mode=='REC' and main.record_mode=='browser' and not c.active()
        live_ready();press('Y');press('A');press('X')
        assert c.mode=='REC' and not c.active() and main.record_mode=='browser'
        live_ready();press('Y');press('A');press('B')
        assert c.mode=='LIVE' and not c.active() and main.record_mode=='ready'
        press('B')
        assert c.mode=='REC' and not c.active() and main.record_mode=='browser'
        live_ready();press('Y');press('A')
        print('PASS physical Y starts/stops running, frozen and paused LIVE; A alone freezes; X returns SAMPLE while running/frozen; B stops then backs out; SELECT passes through',flush=True)
    def frame(self,main,state):
        if state['frames']==2:assert not main._v4_controller.active() and main._v4_controller.mode=='LIVE'
        if state['frames']==3:assert main.record_mode=='browser' and main._v4_controller.mode=='REC'
    def after_draw(self,main,state):
        if state['frames']==1:
            import pygame
            pygame.image.save(main.ui.screen,str(self.app/'live-controls-footer.png'))
    def finish(self,main,state):assert not main._v4_controller.active()
