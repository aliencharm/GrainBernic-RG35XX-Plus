"""SAMPLE browser/mixer and LIVE ready/mixer around original recording actions."""
from pathlib import Path
import pygame

SAMPLE_MIX_CONTROLS=(('GRANULAR MIX','sample.granular_mix'),('FX MIX','sample.fx_mix'),('TAPE MIX','sample.tape_mix'))


def fit_label(value,width,scale):
    limit=max(3,int(width)//(6*scale))
    if len(value)<=limit:return value
    left=max(1,(limit-3)//2)
    return value[:left]+'...'+value[-(limit-3-left):]

class RecordingUI:
    def __init__(self,main,controller,router=None):
        self.main=main;self.controller=controller;self.router=router;self.initialized=False
        self.sample_mixer=False;self.sample_selection=0;self._drawing_browser=False
    def usb_available(self):
        return bool(self.router is not None and self.router.inputs)
    def preview_sample(self):
        main=self.main
        entry=main.sample_browser.get(main.controls.sample_index)
        path=getattr(entry,'path',None)
        if not path:return
        try:
            device=main.resolve_output(main.ui.audio_output_id)
            main.sample_preview.toggle(path,getattr(main,'audio_worker',None),device)
        except Exception as exc:self.controller.message=str(exc)
    def mode_label(self):return 'LIVE' if self.controller.mode=='LIVE' else 'SAMPLE'
    def source_label(self):
        try:return self.main.current_record_source()['label']
        except (AttributeError,KeyError,IndexError):return 'USB INPUT'
    def draw_source_label(self,ui,x,y,width,scale):
        label=self.source_label()
        while scale>1 and len(label)*6*scale>width:scale-=1
        ui.text(fit_label(label,width,scale),x,y,scale,ui.ACCENT)
    def set_page(self,mode):
        self.main.record_mode=mode
        if getattr(self.main,'ui',None) is not None:self.main.ui.record_mode=mode
    def stop_preview(self,restart=True):
        preview=getattr(self.main,'sample_preview',None)
        if preview is not None:preview.stop(restart=restart)
    def sample_page(self):
        c=self.controller
        if c.active():c.stop_live()
        c.restore_live_output();c.mode='REC';c.message=''
        c.bus().set('live.enabled',0);c.bus().set('live.freeze',0)
        self.sample_mixer=False;self.set_page('browser')
        ui=getattr(self.main,'ui',None)
        if ui is not None:ui.set_sample(getattr(self.main,'sample',None));ui._v4_display_source=None
        worker=getattr(self.main,'audio_worker',None)
        if getattr(self.main,'sample',None) is not None and worker is not None and not worker.running:
            try:worker.start()
            except Exception as exc:c.message=str(exc)
    def live_page(self):
        c=self.controller
        self.stop_preview(restart=False);c.bus().set('transport.playing',0)
        selected=self.main.record_source_index
        self.main.open_input_recording_page();self.main.record_source_index=selected
        if self.router:self.router.sync_input(self.main)
        c.mode='LIVE';c.message='';self.sample_mixer=False;self.set_page('ready')
    def toggle_mixer(self):
        if self.sample_mixer:
            self.sample_mixer=False;self.set_page('browser')
        else:
            self.stop_preview(restart=True);self.sample_mixer=True;self.set_page('ready')
    def start_recording(self):
        if not self.usb_available():
            self.controller.message='NO USB INPUT - CONNECT AN AUDIO INTERFACE';return
        was_mixer=self.sample_mixer;self.sample_mixer=False
        if self.main.record_mode=='browser':
            selected=self.main.record_source_index
            self.main.open_input_recording_page();self.main.record_source_index=selected
            if self.router:self.router.sync_input(self.main)
        self.main.start_input_recording()
        if self.main.record_mode=='ready':
            self.sample_mixer=was_mixer
            self.set_page('ready' if was_mixer else 'browser')
            self.controller.message=getattr(self.main.controls,'sample_error','')
    def play_sample(self):
        if getattr(self.main,'sample',None) is None:
            self.controller.message='LOAD OR RECORD A SAMPLE FIRST';return
        worker=getattr(self.main,'audio_worker',None)
        if worker is None:self.controller.message='LOAD THE SAMPLE AGAIN TO START AUDIO';return
        if not worker.running:
            try:worker.start()
            except Exception as exc:self.controller.message=str(exc);return
        bus=self.controller.bus();bus.set('transport.playing',1-bus.get('transport.playing'))
    def install(self):
        main=self.main;c=self.controller
        # LIVE can use Internal output, but always requires a real USB input.
        def choose_output():
            if not self.usb_available():raise RuntimeError('NO USB INPUT - CONNECT AN AUDIO INTERFACE')
            main.ui.refresh_audio_outputs()
            return main.resolve_output(main.ui.audio_output_id)
        c.choose_output=choose_output
        previous_filter=c.filter_record_actions
        def filter_actions(actions):
            actions=previous_filter(actions)
            if main.controls.current_tab=='SAMPLE' and c.mode!='LIVE' and main.record_mode in ('browser','ready'):
                return [('SAMPLE_MIXER' if action=='SELECT' else action,value) for action,value in actions]
            return actions
        c.filter_record_actions=filter_actions
        before=c.before_input
        def before_input():
            before()
            if main.record_mode=='browser':
                self.sample_mixer=False
                if c.mode=='LIVE' and main.controls.current_tab=='SAMPLE':self.set_page('ready')
            if self.initialized:return
            if not self.usb_available():
                main.RECORD_SOURCES=[dict(id='usb',label='NO USB INPUT',device='V4_USB_NOT_CONNECTED',channels=2,format='CONNECT A USB AUDIO INTERFACE')]
                main.record_source_index=0
            self.initialized=True
            original=main.handle_record_action
            def handle(action,value):
                if main.controls.current_tab!='SAMPLE':return original(action,value)
                mode=main.record_mode
                if mode in ('recording','edit'):
                    if mode=='recording' and action=='Y':
                        if value!=0:main.stop_input_recording_to_editor()
                        return True
                    return original(action,value)
                if action=='X' and mode in ('browser','ready'):
                    if value!=0:
                        if c.mode=='LIVE':self.sample_page()
                        else:self.live_page()
                    return True
                if action=='SAMPLE_MIXER' and c.mode!='LIVE' and mode in ('browser','ready'):
                    if value!=0:self.toggle_mixer()
                    return True
                if self.sample_mixer and mode=='ready':
                    if action in ('UP','DOWN'):
                        if value!=0:self.sample_selection=(self.sample_selection+(1 if action=='DOWN' else -1))%3
                        return True
                    if action in ('LEFT','RIGHT'):
                        if value!=0:
                            key=SAMPLE_MIX_CONTROLS[self.sample_selection][1]
                            c.bus().set(key,c.bus().get(key)+(.05 if action=='RIGHT' else -.05))
                        return True
                    if action in ('A','START'):
                        if value!=0:self.play_sample()
                        return True
                    if action=='B':
                        if value!=0:self.toggle_mixer()
                        return True
                if mode=='browser' and action=='START':
                    if value!=0:self.preview_sample()
                    return True
                if mode=='browser' and action in ('L2','R2'):
                    if value!=0:
                        main.select_record_source(-1 if action=='L2' else 1)
                        if self.router:self.router.sync_input(main)
                    return True
                if mode=='ready' and c.mode=='LIVE' and action=='A':
                    if value!=0:
                        if c.active():c.bus().set('live.freeze',1-c.bus().get('live.freeze'))
                        else:c.message='START LIVE WITH Y BEFORE FREEZING'
                    return True
                if action=='Y' and mode in ('browser','ready'):
                    if value==0:return True
                    if c.mode!='LIVE':self.start_recording();return True
                    if c.active() and c.bus().get('transport.playing')>=.5:return original('Y',value)
                    return original('A',value)
                if action=='B' and mode=='ready' and c.mode=='LIVE':
                    if value!=0:
                        if c.active():c.stop_live()
                        else:self.sample_page()
                    return True
                return original(action,value)
            main.handle_record_action=handle
        c.before_input=before_input
        cls=__import__('ui.renderer',fromlist=['UIEngine']).UIEngine
        original_sample=cls.draw_sample_page
        def sample(ui,*args,**kwargs):
            self._drawing_browser=main.record_mode=='browser'
            try:result=original_sample(ui,*args,**kwargs)
            finally:self._drawing_browser=False
            if main.record_mode=='browser':
                pygame.draw.rect(ui.screen,ui.BG,(770,105,225,140))
                ui.text('SAMPLE',782,120,4,ui.ACCENT)
                ui.text('INPUT',782,175,2,ui.DIM)
                self.draw_source_label(ui,782,205,210,2)
                pygame.draw.rect(ui.screen,ui.BG,(750,226,245,5))
                ui.text('PRESS SELECT TO SHOW MIXER',55,680,2,ui.DIM)
                if c.message:ui.text(fit_label(c.message.upper(),914,2),55,660,2,ui.ACCENT)
            return result
        cls.draw_sample_page=sample
        original_text=cls.text
        def text(ui,value,*args,**kwargs):
            if self._drawing_browser and isinstance(value,str):
                if value=='Y RECORD':return
                if len(args)>=3:
                    x,y,scale=args[:3]
                    if x<770 and 105<=y<245:value=fit_label(value,750-x,scale)
            return original_text(ui,value,*args,**kwargs)
        cls.text=text
        cls.draw_record_ready_page=lambda ui:self.ready(ui)
        original_bar=cls.draw_bar_items
        def bar(ui,items,*args,**kwargs):
            if main.controls.current_tab=='SAMPLE' and not getattr(ui,'info_mode',False):
                gray=ui.WHITE;accent=ui.ACCENT
                if main.record_mode=='browser':
                    items=[('A LOAD',accent),('B BACK',gray),('X LIVE',accent),('Y RECORD',accent),('SELECT MIX',gray),('L2/R2 INPUT',gray),('START PREVIEW',gray)]
                elif main.record_mode=='ready':
                    if c.mode=='LIVE':
                        action='Y FREEZE' if c.active() and c.bus().get('transport.playing')>=.5 else 'Y RESUME' if c.active() else 'Y START'
                        items=[('D-PAD MIX',gray),('X SAMPLE',accent),(action,accent),('A FREEZE',gray),('B STOP/BACK',gray),('L2/R2 INPUT',gray)]
                    else:
                        action='A/START PAUSE' if c.bus().get('transport.playing')>=.5 else 'A/START PLAY'
                        items=[('D-PAD MIX',gray),('X LIVE',accent),('Y RECORD',accent),('SELECT/B BACK',gray),(action,accent)]
                elif main.record_mode=='recording':
                    monitor=c.record_monitor
                    items=[('Y STOP REC',accent),('B STOP',gray),('MONITOR '+(monitor.status if monitor is not None else 'OFF'),gray)]
            return original_bar(ui,items,*args,**kwargs)
        cls.draw_bar_items=bar
    def ready(self,ui):
        c=self.controller;live=c.mode=='LIVE'
        ui.text('LIVE' if live else 'SAMPLE',782,120,4,ui.ACCENT)
        worker=getattr(self.main,'audio_worker',None)
        if live:
            active=c.active() and worker is not None and worker.running
            status='RUNNING' if active else 'READY'
            if active and c.bus().get('transport.playing')<.5:status='PAUSED'
        else:
            status='NO SAMPLE' if getattr(self.main,'sample',None) is None else 'PLAYING' if c.bus().get('transport.playing')>=.5 else 'PAUSED'
        ui.text(status,782,175,2)
        if live:
            ui.text('INPUT / USB AUDIO',55,120,2,ui.DIM)
            self.draw_source_label(ui,55,165,695,4)
            ui.text(self.main.current_record_source().get('format','48 KHZ / STEREO USB'),55,220,2)
            from original_adapter import MIX_CONTROLS
            controls=MIX_CONTROLS;selected_index=c.mix_selection
        else:
            ui.text('INPUT / USB AUDIO',55,120,2,ui.DIM)
            self.draw_source_label(ui,55,165,695,4)
            ui.text(self.main.current_record_source().get('format','48 KHZ / STEREO USB'),55,220,2)
            controls=SAMPLE_MIX_CONTROLS;selected_index=self.sample_selection
        for index,(label,key) in enumerate(controls):
            cx=200+index*310;selected=index==selected_index;color=ui.ACCENT if selected else ui.WHITE
            ui.text(label,cx-len(label)*9,295,3,color)
            ui._draw_comp_knob(cx,390,58,c.bus().get(key),selected)
            value=str(round(c.bus().get(key)*100))+'%'
            ui.text(value,cx-len(value)*9,465,3,color)
        if live:
            frozen=c.bus().get('live.freeze')>=.5
            ui.text('A: FREEZE',55,545,3,ui.WHITE)
            pygame.draw.rect(ui.screen,ui.ACCENT if frozen else ui.DIM,(250,540,96,32),2,border_radius=7)
            ui.text('ON' if frozen else 'OFF',286 if frozen else 280,548,2,ui.ACCENT if frozen else ui.WHITE)
            ui.text('HOLD THE LIVE BUFFER',55,600,2,ui.DIM)
        else:
            ui.text('Y: RECORD SAMPLE',55,545,3,ui.WHITE)
            ui.text('LOADED SAMPLE',55,600,2,ui.DIM)
            sample=getattr(self.main,'sample',None)
            label=Path(sample.path).name if sample is not None else 'LOAD OR RECORD A SAMPLE FIRST'
            ui.text(fit_label(label,914,2),55,630,2,ui.ACCENT)
        if c.message and 'LIVE ON' not in c.message:ui.text(fit_label(c.message.upper(),914,2),55,660,2,ui.ACCENT)
