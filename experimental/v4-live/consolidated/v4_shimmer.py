"""Original/Stardust selection inside the existing SHIMMER category."""
import ctypes
import weakref
from pathlib import Path
import numpy as np

STARDUST_PARAMS=('stardust.predelay','stardust.size','stardust.decay','stardust.pitch','stardust.brightness','stardust.frequency','stardust.depth','stardust.input','stardust.send','stardust.return')
SHIMMER_DEFAULTS={'shimmer.type':(0.,0.,1.),**dict(zip(STARDUST_PARAMS,(
    (100.,-1000.,1000.),(.3,0.,1.),(.8,0.,1.),(12.,-12.,12.),(1.,0.,1.),(.5,.05,5.),(.25,0.,1.),(1.,0.,1.),(1.,0.,1.),(.5,0.,1.))))}
LABELS=dict(zip(STARDUST_PARAMS,('PRE DELAY','SIZE','DECAY','PITCH','BRIGHTNESS','FREQUENCY','DEPTH','INPUT','SEND','RETURN')))

class ParameterView:
    def __init__(self,parameters):self.parameters=parameters
    def get(self,key):return 0. if key=='shimmer.mix' else self.parameters.get(key)

class StardustDSP:
    def __init__(self,rate=48000,path=None):
        self.rate=rate;self.library=ctypes.CDLL(str(path or Path(__file__).with_name('libgrainbrick_stardust.so')))
        lib=self.library;ptr=ctypes.POINTER(ctypes.c_float)
        lib.stardust_create.argtypes=[ctypes.c_int];lib.stardust_create.restype=ctypes.c_void_p
        lib.stardust_clear.argtypes=[ctypes.c_void_p];lib.stardust_clear.restype=None
        lib.stardust_destroy.argtypes=[ctypes.c_void_p];lib.stardust_destroy.restype=None
        lib.stardust_process.argtypes=[ctypes.c_void_p,ptr,ptr,ctypes.c_int,ptr];lib.stardust_process.restype=ctypes.c_int
        self.handle=lib.stardust_create(rate)
        if not self.handle:raise RuntimeError('Unable to allocate Stardust')
        self.values=np.zeros(10,np.float32)
    def process(self,feed,audio,parameters):
        if feed.dtype!=np.float32 or audio.dtype!=np.float32 or feed.shape!=audio.shape or feed.ndim!=2 or feed.shape[1]!=2 or not feed.flags.c_contiguous or not audio.flags.c_contiguous:
            raise ValueError('Stardust requires matching contiguous float32 stereo blocks')
        if not len(audio):return audio
        for index,key in enumerate(STARDUST_PARAMS):self.values[index]=parameters.get(key)
        pointer=ctypes.POINTER(ctypes.c_float)
        result=self.library.stardust_process(self.handle,feed.ctypes.data_as(pointer),audio.ctypes.data_as(pointer),len(audio),self.values.ctypes.data_as(pointer))
        if result:raise ValueError('Invalid Stardust parameters')
        return audio
    def clear(self):self.library.stardust_clear(self.handle)
    def close(self):
        if getattr(self,'handle',None):self.library.stardust_destroy(self.handle);self.handle=None
    def __del__(self):self.close()

class ShimmerChoice:
    """Leaves native reverb/FX in place; switches only shimmer contribution."""
    def __init__(self,engine):
        self.engine=weakref.proxy(engine);self.mode=0;self.star=None;self.feed=None;self.last=np.zeros(2,np.float32);self.fade_left=0;self.fade_anchor=None
    def process(self,audio,parameters,original_process):
        mode=int(parameters.get('shimmer.type')>=.5)
        switched=mode!=self.mode
        if switched:
            self.fade_left=max(1,int(self.engine.sample_rate*.02));self.fade_anchor=self.last.copy()
            if self.star is not None:self.star.clear()
            for name in ('shimmer_a','shimmer_b'):
                engine=getattr(self.engine,name,None)
                if engine is not None:engine.clear()
            history=getattr(self.engine,'shimmer_feedback_buffer',None)
            if history is not None:history.fill(0)
            self.mode=mode
        if not mode:
            result=original_process(self.engine,audio,parameters)
        else:
            if self.star is None:self.star=StardustDSP(self.engine.sample_rate)
            if self.feed is None or self.feed.shape!=audio.shape:self.feed=np.empty_like(audio)
            np.copyto(self.feed,audio)
            result=original_process(self.engine,audio,ParameterView(parameters))
            result=self.star.process(self.feed,result,parameters)
        if self.fade_left:
            total=max(1,int(self.engine.sample_rate*.02));count=min(len(result),self.fade_left)
            weights=(np.arange(count,dtype=np.float32)+(total-self.fade_left)+1)/total
            result[:count]=self.fade_anchor[None,:]*(1-weights[:,None])+result[:count]*weights[:,None]
            self.fade_left-=count
        if len(result):self.last[:]=result[-1]
        return result


def install(main):
    fx_module=__import__('engine.fx_c',fromlist=['FXEngine']);cls=fx_module.FXEngine
    original_process=cls.process
    def process(engine,audio,parameters):
        choice=getattr(engine,'_v4_shimmer_choice',None)
        if choice is None and parameters.get('shimmer.type')<.5:
            result=original_process(engine,audio,parameters)
            if len(result):engine._v4_last_shimmer_output=(float(result[-1,0]),float(result[-1,1]))
            return result
        if choice is None:
            choice=engine._v4_shimmer_choice=ShimmerChoice(engine)
            choice.last[:]=getattr(engine,'_v4_last_shimmer_output',(0.,0.))
        return choice.process(audio,parameters,original_process)
    cls._stardust_original_process=original_process
    cls.process=process
    original_reset=cls.reset
    def reset(engine):
        result=original_reset(engine)
        choice=getattr(engine,'_v4_shimmer_choice',None)
        if choice is not None:
            if choice.star is not None:choice.star.clear()
            choice.last.fill(0);choice.fade_left=0
        return result
    cls.reset=reset
    controls=__import__('engine.control',fromlist=['ControlManager']).ControlManager
    index=next(i for i,(name,_) in enumerate(controls.FX_PAGES) if name=='SHIMMER')
    name,original=controls.FX_PAGES[index]
    controls.FX_PAGES=list(controls.FX_PAGES);controls.FX_PAGES[index]=(name,['shimmer.type']+list(original))
    old_params=controls.current_fx_params
    def params(self):
        if self.current_fx_name=='SHIMMER' and self.parameters.get('shimmer.type')>=.5:return ['shimmer.type']+list(STARDUST_PARAMS)
        items=old_params.fget(self)
        if self.current_fx_name=='SHIMMER':self.fx_param_indices[self.fx_page_index]=min(self.fx_param_indices[self.fx_page_index],len(items)-1)
        return items
    controls.current_fx_params=property(params)
    old_page=controls.params_for_page
    def page(control):
        if control.current_tab=='FX' and control.current_fx_name=='SHIMMER':return control.current_fx_params
        return old_page(control)
    controls.params_for_page=page
    old_current=controls.current_param
    def current(control):
        if control.current_tab=='FX' and control.current_fx_name=='SHIMMER':
            items=control.current_fx_params
            index=min(control.fx_param_indices[control.fx_page_index],len(items)-1)
            return items[index]
        return old_current.fget(control)
    controls.current_param=property(current)
    original_change=controls.change_param
    def change(control,amount):
        if control.current_tab=='FX' and control.current_fx_name=='SHIMMER' and control.current_param=='shimmer.type':
            if amount:control.parameters.set('shimmer.type',1. if amount>0 else 0.)
            return
        return original_change(control,amount)
    controls.change_param=change
    controls.STEPS=dict(controls.STEPS);controls.DEFAULTS=dict(controls.DEFAULTS)
    for key,(value,lo,hi) in SHIMMER_DEFAULTS.items():
        controls.DEFAULTS[key]=value
        controls.STEPS[key]=1. if key in ('shimmer.type','stardust.pitch') else 5. if key=='stardust.predelay' else .05 if key=='stardust.frequency' else .02
    renderer=__import__('ui.renderer',fromlist=['UIEngine']).UIEngine
    original_format=renderer.format_value
    def format_value(ui,key,value):
        if key=='shimmer.type':return 'STARDUST' if value>=.5 else 'ORIGINAL'
        if key.startswith('stardust.'):
            if key=='stardust.predelay':return f'{value:+.0f} MS'
            if key=='stardust.pitch':return f'{value:+.0f} ST'
            if key=='stardust.frequency':return f'{value:.2f} HZ'
            return str(round(value*100))+'%'
        return original_format(ui,key,value)
    renderer.format_value=format_value
    original_text=renderer.text
    def text(ui,value,*args,**kwargs):
        if getattr(main,'controls',None) is not None and main.controls.current_tab=='FX' and isinstance(value,str):
            value=value.replace('X NEXT FX','L2/R2 FX').replace('X: NEXT FX','L2/R2: FX')
        if value=='SHIMMER.TYPE':value='TYPE'
        elif value=='NO DESCRIPTION AVAILABLE.' and getattr(main,'controls',None) is not None and main.controls.current_tab=='FX' and main.controls.current_param=='shimmer.type':
            value='SELECT ORIGINAL OR STARDUST SHIMMER.'
        return original_text(ui,value,*args,**kwargs)
    renderer.text=text
    original_draw=renderer.draw_fx_page
    descriptions={
        'shimmer.type':'Choose Original or Stardust shimmer.',
        'stardust.predelay':'Positive delays the effect send; negative delays the dry signal.',
        'stardust.size':'Adjusts the size of the Stardust feedback network.',
        'stardust.decay':'Controls how long the shimmer tail lingers.',
        'stardust.pitch':'Pitch movement recirculated inside Stardust.',
        'stardust.brightness':'Darkens or brightens the circulating tail.',
        'stardust.frequency':'Speed of the gentle shimmer pitch drift.',
        'stardust.depth':'Gentle pitch drift; the lower half gives finer control.',
        'stardust.input':'Level of the dry signal.',
        'stardust.send':'Level feeding the Stardust network.',
        'stardust.return':'Level of the Stardust tail.'}
    original_labels={'shimmer.mix':'MIX','shimmer.feedback':'FEEDBACK','shimmer.tone':'TONE','shimmer.smooth':'SMOOTH','shimmer.dual':'DUAL','shimmer.shift':'SHIFT','shimmer.spread':'SPREAD','shimmer.voice2_level':'VOICE 2'}
    descriptions.update({'shimmer.mix':'Blend in the original shimmer.','shimmer.feedback':'How much shimmer returns to its input.','shimmer.tone':'Brightness of the original shimmer tail.','shimmer.smooth':'Smooth the original shimmer texture.','shimmer.dual':'Enable the original second shimmer voice.','shimmer.shift':'Pitch shift of the original shimmer voice.','shimmer.spread':'Stereo spread of the original shimmer voices.','shimmer.voice2_level':'Level of the original second shimmer voice.'})
    def draw(ui,control,parameters,audio_worker=None):
        if control.current_fx_name!='SHIMMER':return original_draw(ui,control,parameters,audio_worker)
        import pygame
        items=control.current_fx_params
        index=min(control.fx_param_indices[control.fx_page_index],len(items)-1)
        selected=items[index];color=ui.ACCENT if index==0 else ui.WHITE
        ui.text('SHIMMER',55,120,4,ui.ACCENT)
        pygame.draw.rect(ui.screen,color,(625,112,345,58),1)
        if index==0:ui.text('>',605,132,2,ui.ACCENT)
        ui.text('TYPE',640,135,2,color)
        ui.text('STARDUST' if parameters.get('shimmer.type')>=.5 else 'ORIGINAL',720,128,3,color)
        ui.text('MENU / A/B WHEN SELECTED',640,190,2,ui.DIM)
        ui.text(descriptions.get(selected,''),55,230,2,ui.WHITE)
        pygame.draw.line(ui.screen,ui.DIM,(55,270),(970,270),1)
        for i,key in enumerate(items[1:]):
            x=55+(i%4)*235;y=310+(i//4)*120;color=ui.ACCENT if i+1==index else ui.WHITE
            if i+1==index:ui.text('>',x-22,y,2,ui.ACCENT)
            ui.text(LABELS.get(key,original_labels.get(key,key)),x,y,2,color)
            ui.text(ui.format_value(key,parameters.get(key)),x,y+36,3,color)
    renderer.draw_fx_page=draw
    original_nav=controls.navigate_param
    def navigate(control,action):
        if control.current_tab!='FX' or control.current_fx_name!='SHIMMER':return original_nav(control,action)
        items=control.current_fx_params;index=control.fx_param_indices[control.fx_page_index]
        if action=='LEFT':index=max(0,index-1)
        elif action=='RIGHT':index=min(len(items)-1,index+1)
        elif action=='UP':index=0 if index<=4 else index-4
        elif action=='DOWN':index=1 if index==0 else min(len(items)-1,index+4)
        else:return original_nav(control,action)
        control.fx_param_indices[control.fx_page_index]=index
    controls.navigate_param=navigate
    import pygame
    original_events=pygame.event.get
    captured=set()
    def events(*args,**kwargs):
        out=[]
        for event in original_events(*args,**kwargs):
            control=getattr(main,'controls',None)
            in_fx=control is not None and control.current_tab=='FX'
            here=in_fx and control.current_fx_name=='SHIMMER'
            if event.type==pygame.JOYBUTTONUP and getattr(event,'button',None) in captured:
                captured.discard(event.button)
            elif in_fx and event.type==pygame.JOYBUTTONDOWN and event.button in (7,10,11):
                captured.add(event.button)
                if event.button in (10,11):
                    control.fx_page_index=(control.fx_page_index+(-1 if event.button==10 else 1))%len(control.FX_PAGES)
            elif here and event.type==pygame.JOYBUTTONDOWN and event.button==14:
                captured.add(event.button)
                value=control.parameters.get('shimmer.type')
                control.parameters.set('shimmer.type',0. if value>=.5 else 1.)
                control.fx_param_indices[control.fx_page_index]=0
            else:out.append(event)
        return out
    pygame.event.get=events
    original_bar=renderer.draw_bar_items
    def bar(ui,items,*args,**kwargs):
        control=getattr(main,'controls',None)
        if control is not None and control.current_tab=='FX' and control.current_fx_name=='SHIMMER' and not getattr(ui,'info_mode',False):
            items=[('D-PAD',ui.WHITE),('B - / A +',ui.WHITE),('Y FINE',ui.WHITE),('MENU TYPE',ui.ACCENT),('L2/R2 FX',ui.WHITE)]
        elif control is not None and control.current_tab=='FX':
            items=[('L2/R2 FX' if 'X' in label and ('FX' in label or 'EFFECT' in label) else label,color) for label,color in items]
        return original_bar(ui,items,*args,**kwargs)
    renderer.draw_bar_items=bar
