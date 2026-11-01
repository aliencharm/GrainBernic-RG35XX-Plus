"""Persisted UI themes around the original controls/renderer; no audio changes."""
import functools
import json
from pathlib import Path
import pygame
from v4_install import write_json

ROLES=('BG','WHITE','DIM','VERY_DIM','ACCENT')
PALETTES={
    'AMBER':((5,7,8),(235,238,238),(100,110,112),(42,48,50),(210,142,78)),
    'MINT':((10,17,16),(225,242,235),(112,147,135),(40,65,55),(104,224,174)),
    'ICE':((8,17,30),(228,240,253),(113,142,171),(35,54,79),(80,201,244)),
    'VIOLET':((15,11,23),(240,232,250),(144,124,164),(58,42,76),(190,145,245)),
    'PAPER':((244,240,232),(28,35,47),(85,97,113),(178,182,184),(32,80,132)),
}

class Themes:
    def __init__(self,app,main,controller):
        self.app=Path(app);self.main=main;self.controller=controller
        try:data=json.loads((self.app/'config.json').read_text())
        except (OSError,ValueError):data={}
        selected=data.get('ui_theme','AMBER')
        self.name=selected if isinstance(selected,str) and selected in PALETTES else 'AMBER'
        self.initialized=False;self._colors={}
    def apply(self):
        cls=type(self.main.ui)
        self.roles=dict(zip(ROLES,PALETTES[self.name]))
        self._protected=set(self.roles.values());self._colors={}
        for key,value in self.roles.items():setattr(cls,key,value)
    def cycle(self,step):
        names=list(PALETTES);name=names[(names.index(self.name)+step)%len(names)]
        # Merge the latest settings so audio/routes are retained.
        path=self.app/'config.json';data=json.loads(path.read_text());data['ui_theme']=name
        write_json(path,data)
        self.name=name;self.apply()
        print('V4 THEME:',name,flush=True)
    def color(self,color):
        if self.name=='AMBER' or not isinstance(color,(tuple,list,pygame.Color)) or len(color)<3:return color
        rgb=tuple(color[:3])
        if rgb in self._protected:return color
        if rgb not in self._colors:
            r,g,b=rgb
            if r>g+15 and g>b+10:
                # Original amber highlights include darker shades for ranges.
                weight=min(1.,max(rgb)/210.)
                mapped=tuple(round(bg+(accent-bg)*weight) for bg,accent in zip(self.roles['BG'],self.roles['ACCENT']))
            elif max(rgb)-min(rgb)<=35:
                value=max(rgb)
                if value>=185:mapped=self.roles['WHITE']
                elif value>=75:mapped=self.roles['DIM']
                elif value>=25:mapped=self.roles['VERY_DIM']
                else:mapped=self.roles['BG']
            else:mapped=rgb  # Preserve signal/status colors and colorful visualizers.
            self._colors[rgb]=mapped
        mapped=self._colors[rgb]
        return (*mapped,color[3]) if len(color)==4 else mapped
    def install(self):
        main=self.main;c=self.controller
        before=c.before_input
        def input_poll():
            before()
            if self.initialized:return
            self.initialized=True
            controls=main.controls;cls=type(controls)
            rows=list(cls.SETTINGS_PARAMS)
            if 'settings.theme' not in rows:rows.insert(3,'settings.theme')
            cls.SETTINGS_PARAMS=rows
            self.apply()
            original=cls.handle
            def handle(ctrl,action,value):
                if ctrl.current_tab=='SETTINGS' and ctrl.current_param=='settings.theme' and action in ('A','B'):
                    if value!=0:
                        try:self.cycle(1 if action=='A' else -1)
                        except (OSError,ValueError) as exc:
                            print('V4 THEME SAVE FAILED:',str(exc),flush=True)
                    return
                return original(ctrl,action,value)
            cls.handle=handle
        c.before_input=input_poll
        ui_cls=__import__('ui.renderer',fromlist=['UIEngine']).UIEngine
        original_settings=ui_cls.draw_settings_page
        def settings(ui,controls):
            # Retain original language/output/save controls and their consumption.
            selected=controls.current_param
            theme_selected=selected=='settings.theme'
            if theme_selected:
                index=controls.settings_param_index;controls.settings_param_index=0
            try:result=original_settings(ui,controls)
            finally:
                if theme_selected:controls.settings_param_index=index
            if theme_selected:
                pygame.draw.rect(ui.screen,ui.BG,(35,105,960,195))
                ui.text('THEME',55,123,4,ui.ACCENT)
                ui.text('CHANGES INTERFACE COLORS.',55,197,3,ui.WHITE,letter_spacing=2)
                ui.text('A / B SELECT  -  SAVED AUTOMATICALLY',55,233,2,ui.DIM)
            pygame.draw.rect(ui.screen,ui.BG,(35,380,960,312))
            rows=[('settings.info_language','INFO LANGUAGE',ui.info_language),
                  ('settings.save_params_on_exit','SAVE PARAMS ON EXIT','ON' if ui.save_params_on_exit else 'OFF'),
                  ('settings.audio_output','AUDIO OUTPUT (LIVE)',ui.audio_output_label()),
                  ('settings.theme','THEME',self.name),
                  ('settings.button_mapping','BUTTON MAPPING','>'),
                  ('settings.reset_sound_params','RESET SOUND PARAMS','>')]
            for i,(key,label,value) in enumerate(rows):
                y=390+i*48;color=ui.ACCENT if key==selected else ui.WHITE
                if key==selected:ui.text('>',35,y,3,color)
                ui.text(label,65,y,3,color);ui.text(value,483,y,3,color)
            return result
        ui_cls.draw_settings_page=settings
        # Map legacy literal colors as well as the named palette. Only the UI's
        # own surface is affected; capture, DSP arrays and unrelated surfaces are not.
        for name in ('line','lines','aaline','aalines','rect','polygon','circle','ellipse','arc'):
            original=getattr(pygame.draw,name)
            def wrapped(surface,color,*args,_original=original,**kwargs):
                if self.initialized and surface is getattr(main.ui,'screen',None):color=self.color(color)
                return _original(surface,color,*args,**kwargs)
            setattr(pygame.draw,name,wrapped)
        original_text=ui_cls.text
        @functools.wraps(original_text)
        def text(ui,value,*args,**kwargs):
            if self.initialized:
                args=list(args)
                if len(args)>=4:args[3]=self.color(args[3])
                if 'color' in kwargs:kwargs['color']=self.color(kwargs['color'])
            return original_text(ui,value,*args,**kwargs)
        ui_cls.text=text
        return self
