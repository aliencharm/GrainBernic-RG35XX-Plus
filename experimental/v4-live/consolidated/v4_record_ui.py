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
        self.sample_mixer=False;self.sample_selection=0;self._drawing_browser=False;self.pending_delete=None;self._menu_back=False;self._live_actions=[];self._captured_buttons=set()
    def save_frozen_sample(self):
        c=self.controller;worker=getattr(self.main,'audio_worker',None)
        if not c.active() or worker is None or not worker.running:
            c.message='START AND FREEZE LIVE BEFORE SAVING';return
        try:
            source=c.source()
            if source is None:raise ValueError('NO LIVE AUDIO TO SAVE')
            audio=source.frozen_snapshot()
            import os,wave
            import numpy as np
            from datetime import datetime
            app=Path(__file__).resolve().parent
            folder=Path(getattr(self.main,'RECORDINGS_SAMPLE_DIR',app/'samples'/'recordings'))
            folder.mkdir(parents=True,exist_ok=True)
            stem='LIVE_FREEZE_'+datetime.now().strftime('%Y%m%d_%H%M%S')
            pcm=np.rint(np.clip(audio,-1.,32767./32768.)*32768.).astype('<i2')
            for index in range(1000):
                path=folder/(stem+('' if index==0 else '_'+str(index))+'.wav')
                try:handle=path.open('xb')
                except FileExistsError:continue
                try:
                    with handle:
                        with wave.open(handle,'wb') as output:
                            output.setnchannels(2);output.setsampwidth(2);output.setframerate(source.rate)
                            output.writeframes(pcm.tobytes())
                except Exception:
                    path.unlink(missing_ok=True);raise
                break
            else:raise OSError('Unable to choose a free recording name')
            # Match the diagnostic's network-readable media permissions.
            os.chmod(path,0o666)
            browser=getattr(self.main,'sample_browser',None)
            if browser is not None:
                browser.refresh();self.main.controls.set_sample_count(len(browser))
                self.main.controls.sample_index=max(0,min(self.main.controls.sample_index,len(browser)-1))
            c.message='SAVED '+path.name
            print('LIVE FREEZE SAVED:',path,'frames',len(audio),flush=True)
        except Exception as exc:
            c.message=str(exc).upper()
            print('LIVE FREEZE SAVE FAILED:',str(exc),flush=True)
    def parent_folder(self):
        self.pending_delete=None;self.controller.message=''
        browser=self.main.sample_browser
        parent=Path(browser.current_dir).resolve().parent
        if not browser._inside_root(str(parent)):return
        self.stop_preview(restart=True)
        browser.current_dir=str(parent);browser.refresh()
        self.main.controls.set_sample_count(len(browser));self.main.controls.sample_index=0
    def selected_sample_file(self):
        main=self.main
        entry=main.sample_browser.get(main.controls.sample_index)
        if entry is None or getattr(entry,'is_dir',True):return None
        path=Path(entry.path)
        if path.is_symlink() or not path.is_file() or not main.sample_browser._inside_root(str(path.resolve())):return None
        return path.resolve()
    def delete_sample(self):
        path=self.selected_sample_file()
        if path is None:self.pending_delete=None;return False
        if self.pending_delete!=path:
            self.pending_delete=path;self.controller.message='';return True
        self.pending_delete=None
        main=self.main
        try:
            self.stop_preview(restart=True)
            path.unlink()
        except OSError as exc:
            self.controller.message='DELETE FAILED: '+str(exc);return True
        loaded=getattr(getattr(main,'sample',None),'path',None)
        if loaded and Path(loaded).resolve()==path:
            self.controller.bus().set('transport.playing',0)
            worker=getattr(main,'audio_worker',None)
            if worker is not None:worker.stop()
            main.sample=None;main.granular=None;main.dsp=None;main.audio_worker=None
            main.controls.sample_loaded_path=''
            main.ui.set_sample(None)
        main.sample_browser.refresh()
        count=len(main.sample_browser);main.controls.set_sample_count(count)
        main.controls.sample_index=max(0,min(main.controls.sample_index,count-1))
        self.controller.message='DELETED '+path.name
        return True
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
        original_events=pygame.event.get
        def events(*args,**kwargs):
            result=[]
            for event in original_events(*args,**kwargs):
                browser=main.controls.current_tab=='SAMPLE' and main.record_mode=='browser'
                live=main.controls.current_tab=='SAMPLE' and main.record_mode=='ready' and c.mode=='LIVE'
                live_buttons={4:'LIVE_BACK',5:'LIVE_FREEZE',6:'LIVE_TOGGLE',7:'LIVE_SAMPLE',14:'SAVE_FROZEN'}
                if event.type==pygame.JOYBUTTONUP and event.button in self._captured_buttons:
                    self._captured_buttons.discard(event.button)
                elif live and event.type==pygame.JOYBUTTONDOWN and event.button in live_buttons:
                    self._captured_buttons.add(event.button)
                    self._live_actions.append((live_buttons[event.button],None))
                elif browser and event.type==pygame.JOYBUTTONDOWN and event.button==14:
                    self._captured_buttons.add(event.button);self._menu_back=True
                else:result.append(event)
            return result
        pygame.event.get=events
        previous_filter=c.filter_record_actions
        def filter_actions(actions):
            actions=previous_filter(actions)
            if self._menu_back:
                self._menu_back=False;actions=list(actions)+[('SAMPLE_BACK',None)]
            if self._live_actions:
                actions=list(actions)+self._live_actions;self._live_actions=[]
            if main.controls.current_tab=='SAMPLE' and c.mode!='LIVE' and main.record_mode in ('browser','ready'):
                return [('SAMPLE_MIXER' if action=='SELECT' else action,value) for action,value in actions]
            return actions
        c.filter_record_actions=filter_actions
        before=c.before_input
        def before_input():
            before()
            if self.pending_delete is not None:
                if main.controls.current_tab!='SAMPLE' or main.record_mode!='browser' or self.selected_sample_file()!=self.pending_delete:self.pending_delete=None
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
                if c.mode=='LIVE':
                    action={'LIVE_BACK':'B','LIVE_FREEZE':'A','LIVE_TOGGLE':'Y','LIVE_SAMPLE':'X'}.get(action,action)
                mode=main.record_mode
                if mode=='browser' and action in ('SAMPLE_BACK','MENU','LEFT'):
                    if value!=0:
                        self.parent_folder()
                    return True
                if mode=='browser' and self.pending_delete is not None and action!='B' and value!=0:
                    self.pending_delete=None
                    if action=='A':return True
                if mode=='browser' and c.mode!='LIVE' and action=='B':
                    if value==0:return True
                    if self.delete_sample():return True
                if mode=='ready' and c.mode=='LIVE' and action in ('SAVE_FROZEN','MENU'):
                    if value!=0:self.save_frozen_sample()
                    return True
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
                    if action=='A':return True
                    if action=='START':
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
                    if c.active():c.stop_live()
                    else:
                        try:c.start_live()
                        except Exception as exc:
                            c.stop_live();c.message=str(exc)
                    self.set_page('ready')
                    return True
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
                ui.text('Y RECORD  /  SELECT TO SHOW MIXER',55,680,2,ui.DIM)
                if c.message:ui.text(fit_label(c.message.upper(),914,2),55,660,2,ui.ACCENT)
                if self.pending_delete is not None:
                    pygame.draw.rect(ui.screen,ui.BG,(95,280,834,190))
                    pygame.draw.rect(ui.screen,ui.ACCENT,(95,280,834,190),2)
                    ui.text('DELETE SAMPLE?',125,310,3,ui.ACCENT)
                    ui.text(fit_label(self.pending_delete.name,774,2),125,360,2,ui.WHITE)
                    ui.text('B: DELETE  /  A: CANCEL',125,420,2,ui.WHITE)
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
                    items=[('B DELETE',accent),('A CANCEL',gray)] if self.pending_delete else [('A LOAD',accent),('B DELETE' if self.selected_sample_file() else 'B BACK',gray),('X LIVE',accent),('MENU BACK',gray),('SELECT MIX',gray),('L2/R2 INPUT',gray),('START PREVIEW',gray)]
                elif main.record_mode=='ready':
                    if c.mode=='LIVE':
                        action='Y STOP' if c.active() else 'Y START'
                        items=[('D-PAD MIX',gray),('X SAMPLE',accent),(action,accent),('A FREEZE',gray),('B STOP' if c.active() else 'B BACK',gray),('MENU SAVE',accent)] if c.active() and c.bus().get('live.freeze')>=.5 else [('D-PAD MIX',gray),('X SAMPLE',accent),(action,accent),('A FREEZE',gray),('B STOP' if c.active() else 'B BACK',gray),('L2/R2 INPUT',gray)]
                    else:
                        action='START PAUSE' if c.bus().get('transport.playing')>=.5 else 'START PLAY'
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
            if frozen and c.active():ui.text('MENU: SAVE SAMPLE',55,630,2,ui.WHITE)
        else:
            ui.text('Y: RECORD SAMPLE',55,545,3,ui.WHITE)
            ui.text('LOADED SAMPLE',55,600,2,ui.DIM)
            sample=getattr(self.main,'sample',None)
            label=Path(sample.path).name if sample is not None else 'LOAD OR RECORD A SAMPLE FIRST'
            ui.text(fit_label(label,914,2),55,630,2,ui.ACCENT)
        if c.message and 'LIVE ON' not in c.message:ui.text(fit_label(c.message.upper(),914,2),55,660,2,ui.ACCENT)
