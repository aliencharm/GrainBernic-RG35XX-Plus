"""Offline original Settings UI regression; never run on user data."""
import json
from pathlib import Path


class RecoveryChecks:
    actions={3:'EXIT'}
    def __init__(self,app):self.app=Path(app)
    def prepare(self):
        assert 'work' in self.app.parts or self.app.is_relative_to(Path('/tmp'))
        path=self.app/'config.json';data=json.loads(path.read_text());data.pop('live_recovery_enabled',None)
        path.write_text(json.dumps(data))
    def first(self,main,controller,state):
        self.controller=controller;self.setting=controller.recovery_settings
        assert not self.setting.enabled
        controls=main.controls;controls.tab_index=controls.TABS.index('SETTINGS')
        controls.settings_param_index=controls.SETTINGS_PARAMS.index('settings.live_recovery')
        assert controls.current_param=='settings.live_recovery'
        controls.handle('A',1);assert self.setting.enabled
        controls.handle('B',1);assert not self.setting.enabled
        assert json.loads((self.app/'config.json').read_text())['live_recovery_enabled'] is False
        self.texts=[];original=main.ui.text
        def text(value,*args,**kwargs):self.texts.append(str(value));return original(value,*args,**kwargs)
        main.ui.text=text
    def frame(self,main,state):
        if state['frames']==2:
            main.controls.handle('A',1);assert self.setting.enabled
    def after_draw(self,main,state):
        import pygame
        assert main.controls.current_param=='settings.live_recovery'
        assert any('DAW RECORDING' in text for text in self.texts)
        assert any('NO RECOVERY SKIPS' in text for text in self.texts)
        pygame.image.save(main.ui.screen,str(self.app/f'recovery-settings-{state["frames"]}.png'))
    def finish(self,main,state):
        main.controls.handle('B',1);assert not self.setting.enabled
        print('PASS native Settings recovery row: default OFF, A ON / B OFF, persisted state, explanation and cursor retained',flush=True)
