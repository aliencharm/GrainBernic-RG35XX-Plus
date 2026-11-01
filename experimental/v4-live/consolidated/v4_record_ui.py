"""REC/LIVE presentation and shortcuts around the original app's recording actions."""
import pygame

class RecordingUI:
    def __init__(self,main,controller,router=None):
        self.main=main;self.controller=controller;self.router=router;self.initialized=False
    def source_label(self):
        try:return self.main.current_record_source()['label']
        except (AttributeError,KeyError,IndexError):return 'USB INPUT'
    def draw_source_label(self,ui,x,y,width,scale):
        label=self.source_label()
        # Original bitmap text uses a six-pixel character advance.
        while scale>1 and len(label)*6*scale>width:scale-=1
        ui.text(label,x,y,scale,ui.ACCENT)
    def install(self):
        main=self.main;c=self.controller
        before=c.before_input
        def before_input():
            before()
            if self.initialized:return
            self.initialized=True
            original=main.handle_record_action
            def handle(action,value):
                if main.controls.current_tab!='SAMPLE':return original(action,value)
                mode=main.record_mode
                if mode=='browser' and action=='X':
                    if value!=0:
                        c.mode='LIVE' if c.mode=='REC' else 'REC'
                        c.message=''
                    return True
                if mode=='browser' and action=='START':
                    if value!=0:main.controls.request_sample_preview()
                    return True
                if mode=='browser' and action in ('L2','R2'):
                    if value!=0:
                        main.select_record_source(-1 if action=='L2' else 1)
                        if self.router:self.router.sync_input(main)
                    return True
                if action=='Y' and mode in ('browser','ready'):
                    if value==0:return True
                    if mode=='browser':
                        selected=main.record_source_index
                        main.open_input_recording_page();main.record_source_index=selected
                        if self.router:self.router.sync_input(main)
                    if c.mode=='REC':
                        main.start_input_recording()
                        return True
                    if c.active() and c.bus().get('transport.playing')>=.5:return original('Y',value)  # Freeze while LIVE is running.
                    return original('A',value)  # Original guarded LIVE start.
                if mode=='recording' and action=='Y':
                    if value!=0:main.stop_input_recording_to_editor()
                    return True
                return original(action,value)
            main.handle_record_action=handle
        c.before_input=before_input
        cls=__import__('ui.renderer',fromlist=['UIEngine']).UIEngine
        original_sample=cls.draw_sample_page
        def sample(ui,*args,**kwargs):
            result=original_sample(ui,*args,**kwargs)
            if main.record_mode=='browser':
                pygame.draw.rect(ui.screen,ui.screen.get_at((0,200))[:3],(640,105,355,140))
                ui.text(c.mode,665,120,5,ui.ACCENT)
                self.draw_source_label(ui,650,190,345,3)
            return result
        cls.draw_sample_page=sample
        cls.draw_record_ready_page=lambda ui:self.ready(ui)
        original_bar=cls.draw_bar_items
        def bar(ui,items,*args,**kwargs):
            if main.controls.current_tab=='SAMPLE' and not getattr(ui,'info_mode',False):
                gray=(198,207,204);accent=ui.ACCENT
                if main.record_mode=='browser':
                    items=[('A LOAD',accent),('B BACK',gray),('X REC/LIVE',accent),('Y START '+c.mode,accent),('L2/R2 INPUT',gray),('START PREVIEW',gray)]
                elif main.record_mode=='ready':
                    if c.mode=='LIVE':items=[('D-PAD MIX',gray),('X MODE',accent),('Y FREEZE' if c.active() and c.bus().get('transport.playing')>=.5 else 'Y RESUME' if c.active() else 'Y START',accent),('B STOP/BACK',gray),('L2/R2 INPUT',gray)]
                    else:items=[('X REC/LIVE',accent),('Y START REC',accent),('B BACK',gray),('L2/R2 INPUT',gray)]
                elif main.record_mode=='recording':
                    monitor=c.record_monitor
                    items=[('Y STOP REC',accent),('B STOP',gray),('MONITOR '+(monitor.status if monitor is not None else 'OFF'),gray)]
            return original_bar(ui,items,*args,**kwargs)
        cls.draw_bar_items=bar
    def ready(self,ui):
        c=self.controller
        ui.text(c.mode,55,120,5,ui.ACCENT)
        active=c.active() and self.main.audio_worker and self.main.audio_worker.running
        status='RUNNING' if active else 'READY'
        if active and c.bus().get('transport.playing')<.5:status='PAUSED'
        ui.text(status,715,135,3)
        ui.text('INPUT',55,205,2,(150,160,160))
        self.draw_source_label(ui,55,240,914,4)
        format_text=self.main.current_record_source().get('format','48 KHZ / STEREO USB')
        ui.text(format_text,55,285,2)
        if c.mode=='LIVE':
            from original_adapter import MIX_CONTROLS
            for index,(label,key) in enumerate(MIX_CONTROLS):
                cx=200+index*310;selected=index==c.mix_selection;color=ui.ACCENT if selected else (230,230,230)
                ui.text(label,cx-len(label)*9,345,3,color)
                ui._draw_comp_knob(cx,440,58,c.bus().get(key),selected)
                text=str(round(c.bus().get(key)*100))+'%'
                ui.text(text,cx-len(text)*9,515,3,color)
            ui.text('FREEZE: '+('ON' if c.bus().get('live.freeze')>=.5 else 'OFF'),55,585,2)
            ui.text('HOLD THE LIVE BUFFER',55,625,2)
        else:
            ui.text('READY TO RECORD',55,365,3)
            ui.text('DRY INPUT MONITORING',55,430,2)
            output=next((label for identifier,label,pcm in self.main.ui._audio_outputs if pcm==c.config['playback']),c.config['playback'])
            ui.text('OUTPUT: '+output,55,475,2)
        if not active and c.message and 'LIVE ON' not in c.message:ui.text(c.message[:70].upper(),55,660,2,ui.ACCENT)
