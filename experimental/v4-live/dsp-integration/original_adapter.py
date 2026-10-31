"""Runtime REC/LIVE extension of the ORIGINAL app; original DSPChain.render stays intact."""
import sys
import types
import weakref
import numpy as np
from live_source import SwitchableSource,ArecordCapture,add_live_parameters
from stage_mix import StageMix

MIX_CONTROLS=(('GRANULAR MIX','live.mix'),('FX MIX','live.fx_mix'),('TAPE MIX','live.tape_mix'))

class LiveController:
    def __init__(self,main,config,capture_factory=None):
        self.main=main;self.config=config;self.mode='REC';self.message=''
        self.capture_factory=capture_factory or (lambda:ArecordCapture(self.config['capture'],latency_us=self.config.get('latency_us',24000)))
        self.initialized=False;self.sources=weakref.WeakSet()
        self.record_monitor=None;self.record_worker=None
        self.live_output_restore=None
        self.mix_selection=0
    def configure_live_output(self,audio):
        self.restore_live_output()
        names=('low_latency_buffer_frames','low_latency_period_frames','low_latency_pipe_bytes')
        self.live_output_restore=(audio,{name:getattr(audio,name) for name in names})
        audio.low_latency_buffer_frames=2048
        audio.low_latency_period_frames=512
        audio.low_latency_pipe_bytes=4096
        audio._v4_live_output=True
        print('ORIGINAL LIVE OUTPUT REQUEST: buffer_frames=2048 period_frames=512 pipe_bytes=4096',flush=True)
    def restore_live_output(self):
        if self.live_output_restore is None:return
        audio,values=self.live_output_restore;self.live_output_restore=None
        for name,value in values.items():setattr(audio,name,value)
        audio._v4_live_output=False
    def bus(self):return self.main.params
    def active(self):return self.bus().get('live.enabled')>=.5
    def source(self):
        chain=getattr(self.main,'dsp',None)
        return getattr(chain,'_v4_live_source',None)
    def choose_output(self):
        ui=self.main.ui
        ui._audio_outputs_last_scan=-1000000
        ui.refresh_audio_outputs()
        for identifier,label,pcm in ui._audio_outputs:
            if pcm==self.config['playback']:
                ui.audio_output_id=identifier
                return pcm
        raise RuntimeError('Select the configured USB output in SETTINGS before starting LIVE')
    def ensure_worker(self,pcm):
        main=self.main
        if getattr(main,'audio_worker',None) is not None:return
        # A silent in-memory placeholder lets LIVE start without loading a file.
        sample=types.SimpleNamespace(data=np.zeros((48000,2),np.float32),frames=48000,sample_rate=48000,channels=2)
        main.granular=main.GranularEngine(sample,main.params,output_rate=main.RATE)
        main.audio=main.AudioOutput(rate=main.RATE,channels=2,device=pcm)
        main.dsp=main.DSPChain(main.granular,main.params,output_rate=main.RATE)
        main.audio_worker=main.AudioWorker(main.dsp,main.audio,block_size=main.BLOCK)
    def start_live(self):
        main=self.main;pcm=self.choose_output();self.ensure_worker(pcm)
        worker=main.audio_worker
        worker.stop()
        self.configure_live_output(main.audio)
        source=self.source()
        if source is None:raise RuntimeError('The original DSP chain has no live-source adapter')
        source.close();source.data.fill(0);source.writer=0;source.written=0;source.processed=0;source._last_report=0;source.live_engine=None
        main.params.set('live.mix',0);main.params.set('live.freeze',0)
        main.params.set('live.enabled',1);main.params.set('transport.playing',1)
        main.audio.device=pcm
        worker.request_audio_device(pcm)
        worker.start();main.record_mode='ready'
        self.message='LIVE ON - UP/DOWN SELECT MIX'
        print('ORIGINAL LIVE START:',self.config,flush=True)
    def stop_live(self):
        worker=getattr(self.main,'audio_worker',None)
        if worker is not None and worker.running:worker.stop()
        self.restore_live_output()
        self.bus().set('live.enabled',0);self.bus().set('live.freeze',0)
        self.bus().set('transport.playing',0)
        if getattr(self.main,'ui',None) is not None:self.main.ui.set_sample(getattr(self.main,'sample',None))
        self.message='LIVE STOPPED'
        print('ORIGINAL LIVE STOP',flush=True)
    def prepare_runtime(self):
        if self.initialized:return
        self.initialized=True
        self.install_record_monitor()
        # Original state restoration may include our keys, but never auto-arm LIVE.
        for key in ('live.enabled','live.freeze','live.mix'):self.bus().set(key,0)
        original=self.main.handle_record_action
        def handle(action,value):
            controls=self.main.controls
            ready=controls.current_tab=='SAMPLE' and self.main.record_mode=='ready'
            if ready and action=='X':
                if value==0:return True
                if self.active():self.stop_live()
                self.mode='LIVE' if self.mode=='REC' else 'REC'
                if self.mode=='LIVE':self.main.record_source_index=0
                self.message='';return True
            if self.active() and action in ('TAB_PREV','TAB_NEXT'):
                # Let original navigation continue, without its REC cancellation.
                self.main.record_mode='browser'
                return False
            if ready and self.mode=='LIVE':
                if action in ('UP','DOWN'):
                    if value!=0:self.mix_selection=(self.mix_selection+(1 if action=='DOWN' else -1))%len(MIX_CONTROLS)
                    return True
                if action=='A':
                    if value!=0 and (not self.active() or not self.main.audio_worker or not self.main.audio_worker.running):
                        try:self.start_live()
                        except Exception as exc:
                            self.stop_live();self.message=str(exc)
                            print('ORIGINAL LIVE START FAILED:',str(exc),flush=True)
                    elif value!=0:
                        self.bus().set('transport.playing',1)
                    return True
                if action=='B' and self.active():
                    if value!=0:self.stop_live()
                    return True
                if action=='Y':
                    if value!=0 and self.active():self.bus().set('live.freeze',1-self.bus().get('live.freeze'))
                    return True
                if action in ('LEFT','RIGHT'):
                    if value!=0:
                        step=.05*(1 if action=='RIGHT' else -1)
                        key=MIX_CONTROLS[self.mix_selection][1]
                        self.bus().set(key,self.bus().get(key)+step)
                    return True
            return original(action,value)
        self.main.handle_record_action=handle
    def stop_record_monitor(self):
        if self.record_monitor is not None:
            self.record_monitor.stop();self.record_monitor=None
    def restore_record_worker(self):
        worker=self.record_worker;self.record_worker=None
        if worker is not None and worker is getattr(self.main,'audio_worker',None) and not worker.running:
            worker.start()
    def install_record_monitor(self):
        original_start=self.main.start_input_recording
        def start():
            self.stop_record_monitor()
            worker=getattr(self.main,'audio_worker',None)
            self.record_worker=worker if worker is not None and worker.running else None
            if self.record_worker is not None:self.record_worker.stop()
            try:
                # Keep the original arecord WAV writer; only reduce ALSA period size.
                import subprocess
                original_popen=subprocess.Popen
                import threading
                recording_thread=threading.get_ident()
                def record_popen(args,*a,**kw):
                    if threading.get_ident()==recording_thread:
                        from record_monitor import recording_command
                        args=recording_command(args)
                    return original_popen(args,*a,**kw)
                subprocess.Popen=record_popen
                try:result=original_start()
                finally:subprocess.Popen=original_popen
                if self.main.record_mode=='recording':
                    try:
                        from record_monitor import RecordingMonitor
                        path=self.main.recorder.current_path
                        if callable(path):path=path()
                        self.record_monitor=RecordingMonitor(path,self.config['playback'])
                        self.record_monitor.start()
                    except Exception as exc:
                        print('REC MONITOR SETUP FAILED:',str(exc),'(original recording continues)',flush=True)
                else:self.restore_record_worker()
                return result
            except Exception:
                self.stop_record_monitor();self.restore_record_worker();raise
        self.main.start_input_recording=start
        def ending(original):
            def finish(*args,**kwargs):
                self.stop_record_monitor()
                try:return original(*args,**kwargs)
                finally:self.restore_record_worker()
            return finish
        for name in ('stop_input_recording_to_editor','cancel_input_recording'):
            setattr(self.main,name,ending(getattr(self.main,name)))
    def before_input(self):
        self.prepare_runtime()
        if self.active() and self.main.controls.current_tab=='SAMPLE':self.main.record_mode='ready'
    def filter_record_actions(self,actions):
        if self.main.controls.current_tab!='SAMPLE' or self.main.record_mode!='edit':return actions
        remaining=[]
        for action,value in actions:
            if action not in ('L2','R2'):
                remaining.append((action,value));continue
            if value==0:continue
            if not self.main.record_denoise_available():
                self.message='DENOISE UNAVAILABLE: BUILT-IN MIC ONLY'
                print('REC DENOISE UNAVAILABLE',flush=True)
                continue
            self.main.change_record_denoise(-5 if action=='L2' else 5)
            self.message='DENOISE '+str(self.main.record_denoise_percent)+'%'
            print('REC DENOISE:',self.main.record_denoise_percent,flush=True)
        return remaining
    def draw_ready(self,ui,original):
        original(ui)
        ui.text('X  REC / LIVE',650,120,2,ui.ACCENT)
        ui.text('MODE: '+self.mode,650,156,2,ui.ACCENT)
        if self.mode!='LIVE':return
        import pygame
        pygame.draw.rect(ui.screen,ui.screen.get_at((0,200))[:3],(42,210,930,370))
        ui.text('LIVE USB INPUT',55,235,3,ui.ACCENT)
        status='RUNNING' if self.active() and self.main.audio_worker and self.main.audio_worker.running else 'STOPPED'
        if status=='RUNNING' and self.bus().get('transport.playing')<.5:status='PAUSED'
        ui.text(status,55,292,3)
        for index,(label,key) in enumerate(MIX_CONTROLS):
            selected=index==self.mix_selection
            value=self.bus().get(key);cx=200+index*310
            color=ui.ACCENT if selected else (230,230,230)
            ui.text(label,cx-len(label)*9,335,3,color)
            ui._draw_comp_knob(cx,430,62,value,selected)
            text=str(round(value*100))+'%'
            ui.text(text,cx-len(text)*9,510,3,color)
        ui.text('FREEZE  '+('ON' if self.bus().get('live.freeze')>=.5 else 'OFF'),55,580,2)
    def draw_live_footer(self,ui):
        import pygame
        pygame.draw.rect(ui.screen,ui.screen.get_at((0,200))[:3],(36,704,955,64))
        ui.text('UP/DOWN SELECT   L/R MIX',38,704,2)
        ui.text('Y FREEZE',38,738,2)
        ui.text('A START LIVE',480,738,2,ui.ACCENT)
        ui.text('B STOP/BACK',820,738,2)


def install_at_boot(main,config,capture_factory=None,shared_storage=True):
    controller=LiveController(main,config,capture_factory)
    audio_cls=main.AudioOutput
    original_audio_start=audio_cls.start
    def audio_start(self):
        result=original_audio_start(self)
        if getattr(self,'_v4_live_output',False):
            print('ORIGINAL LIVE OUTPUT ACTIVE: low_latency='+str(self.low_latency_active)+' buffer_frames='+str(self.low_latency_buffer_frames)+' period_frames='+str(self.low_latency_period_frames)+' pipe_bytes='+str(self.low_latency_pipe_bytes),flush=True)
        return result
    audio_cls.start=audio_start
    parameter_module=sys.modules['engine.parameters']
    original_create=parameter_module.create_default_parameters
    def create():return add_live_parameters(original_create())
    parameter_module.create_default_parameters=create;main.create_default_parameters=create
    chain_cls=sys.modules['engine.dsp_chain'].DSPChain
    original_chain_init=chain_cls.__init__
    def chain_init(self,granular,parameters,output_rate=48000):
        add_live_parameters(parameters)
        storage=None;raw=None
        if shared_storage:
            from multiprocessing import RawArray
            raw=RawArray('f',16*output_rate*2)
            storage=np.frombuffer(raw,dtype=np.float32).reshape(16*output_rate,2)
        source=SwitchableSource(granular,parameters,main.GranularEngine,controller.capture_factory,rate=output_rate,storage=storage)
        source._shared_storage=raw
        original_chain_init(self,source,parameters,output_rate)
        self.fx=StageMix(self.fx,'live.fx_mix')
        self.tape=StageMix(self.tape,'live.tape_mix')
        source.chain=weakref.proxy(self);self._v4_live_source=source;controller.sources.add(source)
    chain_cls.__init__=chain_init
    original_chain_render=chain_cls.render
    def render(self,frames):
        source=getattr(self,'_v4_live_source',None)
        if source is not None and (not source.enabled() or self.parameters.get('transport.playing')<.5):
            source.close()
        return original_chain_render(self,frames)
    chain_cls.render=render
    input_cls=sys.modules['engine.input'].InputManager
    original_poll=input_cls.poll
    def poll(self,*args,**kwargs):
        controller.before_input()
        return controller.filter_record_actions(original_poll(self,*args,**kwargs))
    input_cls.poll=poll
    ui_cls=sys.modules['ui.renderer'].UIEngine
    original_text=ui_cls.text
    def text(self,value,*args,**kwargs):
        if getattr(self,'_v4_drawing_tabs',False) and value=='SAMPLE' and len(args)>=3:
            # Keep the original tab positions and internal SAMPLE identifier.
            # The longer visible label fits its slot using the native small font.
            args=list(args);args[1]+=4;args[2]=2;value='SAMPLE/LIVE'
        return original_text(self,value,*args,**kwargs)
    ui_cls.text=text
    original_tabs=ui_cls.draw_tabs
    def draw_tabs(self,controls):
        self._v4_drawing_tabs=True
        try:return original_tabs(self,controls)
        finally:self._v4_drawing_tabs=False
    ui_cls.draw_tabs=draw_tabs
    original_ready=ui_cls.draw_record_ready_page
    ui_cls.draw_record_ready_page=lambda self:controller.draw_ready(self,original_ready)
    original_draw=ui_cls.draw
    def draw(self,*args,**kwargs):
        if controller.active():
            source=controller.source()
            if source is not None:
                args=list(args)
                args[2]=source;args[3]=source.sample
                if getattr(self,'_v4_display_source',None) is not source:
                    self.set_sample(source.sample);self._v4_display_source=source
                import pygame
                now=pygame.time.get_ticks()
                if now-getattr(self,'_v4_wave_refresh',-2000)>=2000:
                    self.waveform.points=self.waveform.build_peaks(source.sample,800)
                    self._v4_wave_refresh=now
                if args[0].current_tab=='SAMPLE':self.record_mode='ready'
        elif getattr(self,'_v4_display_source',None) is not None:
            self.set_sample(getattr(main,'sample',None));self._v4_display_source=None
        result=original_draw(self,*args,**kwargs)
        if args[0].current_tab=='SAMPLE' and getattr(main,'record_mode',None)=='recording':
            monitor=controller.record_monitor
            status=monitor.status if monitor is not None else 'OFF'
            self.text('REC MONITOR '+status+' / DRY 100%',42,662,2,self.ACCENT)
        if args[0].current_tab=='SAMPLE' and getattr(main,'record_mode',None)=='edit' and not getattr(self,'info_mode',False):
            import pygame
            pygame.draw.rect(self.screen,self.screen.get_at((0,200))[:3],(36,695,955,24))
            hint='L2 / R2 DENOISE - / +' if main.record_denoise_available() else 'DENOISE: BUILT-IN MIC ONLY / USB UNAVAILABLE'
            self.text(hint,38,695,2,self.ACCENT)
        if controller.mode=='LIVE' and args[0].current_tab=='SAMPLE' and self.record_mode=='ready' and not getattr(self,'info_mode',False):
            controller.draw_live_footer(self)
        return result
    ui_cls.draw=draw
    print('INSTALLED original DSP source / REC-LIVE adapter',flush=True)
    return controller
