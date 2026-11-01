"""Persisted UI themes around the original controls/renderer; no audio changes."""
import functools
import json
from pathlib import Path
import pygame
import numpy as np
from v4_install import write_json

ROLES=('BG','WHITE','DIM','VERY_DIM','ACCENT','WAVE')
PALETTES={
    'AMBER':((5,7,8),(235,238,238),(100,110,112),(42,48,50),(210,142,78),(85,95,100)),
    'MINT':((10,17,16),(142,189,170),(86,117,104),(40,62,52),(155,232,192),(78,157,130)),
    'ICE':((8,17,30),(143,175,203),(81,107,132),(35,54,79),(131,213,243),(63,142,175)),
    'VIOLET':((15,11,23),(174,151,195),(111,91,131),(58,42,76),(206,165,242),(130,89,166)),
    'SAGE':((21,26,16),(170,169,130),(110,117,81),(57,65,43),(224,207,141),(163,149,86)),
    'SPRUCE':((7,26,29),(117,173,176),(60,106,110),(26,61,64),(56,205,208),(40,127,135)),
}

class TapeFrames:
    """Theme one requested texture at a time instead of duplicating all 96 frames."""
    def __init__(self,original,theme):
        self.original=original;self.theme=theme;self.index=None;self.frame=None
    def __len__(self):return len(self.original)
    def __getitem__(self,index):
        if index!=self.index:
            self.frame=self.theme.tint_surface(self.original[index]);self.index=index
        return self.frame


class Themes:
    def __init__(self,app,main,controller):
        self.app=Path(app);self.main=main;self.controller=controller
        try:data=json.loads((self.app/'config.json').read_text())
        except (OSError,ValueError):data={}
        selected=data.get('ui_theme','AMBER')
        if selected=='PAPER':selected='SAGE'  # Retire the light palette without overwriting user config.
        self.name=selected if isinstance(selected,str) and selected in PALETTES else 'AMBER'
        self.initialized=False;self._colors={};self._visual_depth=0;self._tape_original=None
    def apply(self):
        cls=type(self.main.ui)
        self.roles=dict(zip(ROLES,PALETTES[self.name]))
        self._protected=set(self.roles.values());self._colors={}
        for key,value in self.roles.items():setattr(cls,key,value)
        self._visual_lut=np.array([self.visual_color(i) for i in range(256)],dtype=np.uint8)
        ui=self.main.ui
        if self._tape_original is None:self._tape_original=getattr(ui,'tape_grain_frames',None)
        if self._tape_original is not None:
            ui.tape_grain_frames=self._tape_original if self.name=='AMBER' else TapeFrames(self._tape_original,self)
        if getattr(ui,'visualizer',None) is not None:ui.visualizer.accent=self.roles['ACCENT']
    def visual_color(self,value):
        # Graphics use only the theme family. Peak graphics stay below selection brightness.
        low,high,t=(self.roles['BG'],self.roles['WAVE'],value/160.) if value<=160 else (self.roles['WAVE'],self.roles['WHITE'],(value-160)/95.)
        return tuple(round(a+(b-a)*t) for a,b in zip(low,high))
    def tint_surface(self,surface):
        values=pygame.surfarray.array3d(surface).max(axis=2)
        return pygame.surfarray.make_surface(self._visual_lut[values])
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
        cache_key=(rgb,bool(self._visual_depth))
        if cache_key not in self._colors:
            r,g,b=rgb
            if self._visual_depth:
                mapped=self.visual_color(max(rgb))
            elif r>g+15 and g>b+10:
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
            self._colors[cache_key]=mapped
        mapped=self._colors[cache_key]
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
                if self.initialized and (self._visual_depth or surface is getattr(main.ui,'screen',None)):color=self.color(color)
                return _original(surface,color,*args,**kwargs)
            setattr(pygame.draw,name,wrapped)
        original_visual=ui_cls.draw_visualizer
        def visual(ui,*args,**kwargs):
            if not self.initialized or self.name=='AMBER':return original_visual(ui,*args,**kwargs)
            self._visual_depth+=1
            try:return original_visual(ui,*args,**kwargs)
            finally:self._visual_depth-=1
        ui_cls.draw_visualizer=visual
        waveform_cls=__import__('ui.waveform',fromlist=['WaveformView']).WaveformView
        original_wave=waveform_cls.draw
        def wave(view,surface,rect,*args,**kwargs):
            if self.initialized and self.name!='AMBER' and surface is getattr(main.ui,'screen',None):
                args=list(args)
                for index,key,role in ((7,'color','WAVE'),(8,'active','ACCENT')):
                    if len(args)>index:args[index]=self.roles[role]
                    else:kwargs[key]=self.roles[role]
            return original_wave(view,surface,rect,*args,**kwargs)
        waveform_cls.draw=wave
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
