"""Execute the ORIGINAL app loop in an isolated runtime, with audio output mocked."""
import os
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',OPENBLAS_NUM_THREADS='1',PYGAME_HIDE_SUPPORT_PROMPT='1')
from pathlib import Path
import importlib
import json
import signal
import sys
import types
import numpy as np
import pygame as pg

app=Path(sys.argv[1]).resolve()
os.environ['GRAINBRICK_ROOT']=str(app)
sys.path.insert(0,str(app))
integrated='--integrated' in sys.argv
controller=None
state={'installed':False,'frames':0,'worker_constructed':0,'worker_started':0,'worker_stopped':0,'record_overlay_calls':0,'record_start_delegated':0}
report={}

def install():
    main=sys.modules.get('main')
    renderer=sys.modules.get('ui.renderer')
    workers=sys.modules.get('engine.audio_worker')
    if not all((main,renderer,workers)):return
    state['installed']=True
    cls=workers.AudioWorker
    def initialize(self,granular,audio,block_size=512):
        state['worker_constructed']+=1
        self.granular=granular;self.audio=audio;self.block_size=block_size
        self.error=None;self._mock_running=False;self._mock_device=getattr(audio,'device','default')
        self._mock_waveform=np.zeros(512,dtype=np.float32)
        self._mock_spectrum=np.zeros(128,dtype=np.float32)
        self._mock_orbix=np.zeros(256,dtype=np.float32)
    def start(self):state['worker_started']+=1;self._mock_running=True
    def stop(self):state['worker_stopped']+=1;self._mock_running=False
    def request(self,pcm):self._mock_device=pcm
    cls.__init__=initialize;cls.start=start;cls.stop=stop;cls.request_audio_device=request
    cls.running=property(lambda self:self._mock_running)
    cls.active_audio_device=property(lambda self:self._mock_device)
    for name in ('dsp_load','write_load','total_load','render_ms','write_ms','total_ms','overruns','active_grains','rms_l','rms_r','peak','roam_position','roam_range_start','roam_range_end','comp_gain_reduction_db'):
        setattr(cls,name,property(lambda self:0))
    cls.waveform=property(lambda self:self._mock_waveform)
    cls.spectrum=property(lambda self:self._mock_spectrum)
    cls.orbix_visual_state=property(lambda self:self._mock_orbix)
    input_cls=sys.modules['engine.input'].InputManager
    class Joy:
        def get_hat(self,index):return (0,0)
        def get_axis(self,index):return 0.
    def init_input(self):
        self.joy=Joy()
        self.button_mapping=sys.modules['engine.button_mapping'].ButtonMapping()
        self.mapping=self.button_mapping
        self.capture_mode=False
    def poll_input(self,*args,**kwargs):
        if integrated:
            actions={1:'X',2:'A',3:'TAB_NEXT',4:'TAB_NEXT',5:'TAB_PREV',6:'TAB_PREV',7:'Y',8:'RIGHT',9:'B',10:'X',11:'A',12:'B',13:'EXIT'}
            action=actions.get(state['frames'])
            return [(action,None)] if action else []
        return [('EXIT',None) for ev in pg.event.get() if ev.type==pg.QUIT]
    input_cls.__init__=init_input;input_cls.poll=poll_input
    input_cls.close=lambda self:None
    input_cls.is_action_held=lambda self,action:False
    if integrated:
        global controller
        from original_adapter import install_at_boot
        import multiprocessing.heap
        multiprocessing.heap.Arena._dir_candidates=[]  # Keep lab IPC in /tmp, not /dev/shm.
        class Capture:
            def read(self,n):return np.zeros((n,2),np.float32)
            def close(self):pass
        controller=install_at_boot(main,{'capture':'synthetic','playback':'default'},Capture,shared_storage=True)
    ui_cls=renderer.UIEngine
    original_draw=ui_cls.draw
    original_ready=ui_cls.draw_record_ready_page
    def ready(self):
        state['record_overlay_calls']+=1
        original_ready(self)
        if not integrated:self.text('REC / LIVE SWITCH TEST',570,120,2,(220,150,60))
    ui_cls.draw_record_ready_page=ready
    def draw(self,*args,**kwargs):
        state['frames']+=1
        main=sys.modules['main']
        if state['frames']==1:
            report['original_main_functions']=[k for k,v in vars(main).items() if callable(v) and getattr(v,'__module__',None)=='main']
            report['record_globals']={k:v if isinstance(v,(str,int,float,bool,type(None))) else type(v).__name__ for k,v in vars(main).items() if 'record' in k}
            action=main.handle_record_action
            report['handle_record_action_arguments']=list(action.__code__.co_varnames[:action.__code__.co_argcount])
            browser=getattr(main,'sample_browser',None)
            if browser is not None:
                entries=getattr(browser,'entries',[])
                for entry in entries:
                    if not getattr(entry,'is_dir',True):
                        main.load_sample(entry)
                        break
            # Ask the REAL original main to enter its real recording page.
            main.controls.tab_index=main.controls.TABS.index('SAMPLE')
            main.handle_record_action('Y',None)
            if integrated:
                def no_record_file():state['record_start_delegated']+=1
                main.start_input_recording=no_record_file
        if integrated:
            report.setdefault('frames',[]).append({'frame':state['frames'],'tab':main.controls.current_tab,'record_mode':main.record_mode,'mode':controller.mode,'active':controller.active(),'freeze':main.params.get('live.freeze'),'mix':main.params.get('live.mix'),'worker':bool(main.audio_worker and main.audio_worker.running)})
        original_draw(self,*args,**kwargs)
        if integrated and state['frames'] in (3,4,5):
            pg.image.save(self.screen,str(app/('integrated-frame-'+str(state['frames'])+'.png')))
            report['live_waveform_fields']=list(vars(self.waveform))
        if state['frames']>=(14 if integrated else 3):
            pg.image.save(self.screen,str(app/'original-record-page.png'))
            pg.event.post(pg.event.Event(pg.QUIT))
    ui_cls.draw=draw
    print('INSTALLED original app runtime hooks',flush=True)

def audit(event,args):
    if event in ('subprocess.Popen','os.fork','os.forkpty','os.posix_spawn','os.system','os.exec'):
        raise PermissionError('Offline original-app test blocks external processes and audio')
    if event=='os.mkdir' and not state['installed']:
        install()
sys.addaudithook(audit)
signal.alarm(35)
try:
    importlib.import_module('main')
finally:
    signal.alarm(0)
    report['state']=state
    (app/'original-main-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('ORIGINAL MAIN TEST RESULT',json.dumps(state),flush=True)
assert state['frames']>=3 and state['worker_constructed']>0 and state['worker_stopped']>0
assert state['record_overlay_calls']>0,'Original record page hook was not dispatched'
if integrated:
    frames=report['frames']
    assert any(f['tab']=='FX' and f['active'] and f['worker'] for f in frames),frames
    assert any(f['tab']=='GRAIN' and f['active'] and f['worker'] for f in frames),frames
    assert any(f['freeze']==1 for f in frames),frames
    assert state['record_start_delegated']==1,state
    assert any(f['mode']=='REC' and not f['active'] for f in frames[3:]),frames
    print('PASS original recording-page REC/LIVE routing, LIVE across original GRAIN/FX tabs, freeze, stop and original REC action delegation',flush=True)
print('PASS original main event loop, original record page, runtime drawing hooks and clean shutdown; audio mocked',flush=True)
