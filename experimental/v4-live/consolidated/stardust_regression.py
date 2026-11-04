"""Original app SHIMMER selector and independent ARM Stardust render checks."""
from pathlib import Path
import json
import numpy as np

class StardustChecks:
    actions={1:'A',2:'DOWN',3:'A',4:'UP',5:'B',6:'A',8:'EXIT'}
    def __init__(self,app):self.app=Path(app)
    def prepare(self):assert 'work' in self.app.parts or self.app.is_relative_to(Path('/tmp'))
    def first(self,main,c,state):
        from v4_shimmer import STARDUST_PARAMS,ShimmerChoice
        main.load_sample(main._ProjectSampleEntry(str(self.app/'samples/sample grainbrick 1.wav')))
        self.index=next(i for i,(name,_) in enumerate(main.controls.FX_PAGES) if name=='SHIMMER')
        main.controls.tab_index=main.controls.TABS.index('FX');main.controls.fx_page_index=self.index;main.controls.fx_param_indices[self.index]=0
        main.params.set('shimmer.type',0)
        assert main.controls.current_fx_params[0]=='shimmer.type'
        assert main.controls.current_fx_params[1]=='shimmer.mix'
        main.params.set('shimmer.type',1)
        assert main.controls.current_fx_params==['shimmer.type']+list(STARDUST_PARAMS)
        for i,key in enumerate(main.controls.current_fx_params):
            main.controls.fx_param_indices[self.index]=i
            assert main.controls.current_param==key,(i,main.controls.current_param,key)
            before=main.params.get(key)
            main.controls.change_param(-1)
            assert main.params.get(key)<before,(key,before,main.params.get(key))
            main.params.set(key,before)
        main.controls.fx_param_indices[self.index]=0
        main.controls.navigate_param('DOWN')
        assert main.controls.current_param=='stardust.predelay'
        main.controls.navigate_param('UP')
        assert main.controls.current_param=='shimmer.type'
        main.project_manager.save_project('TEST_STARDUST',main.params,str(main.sample.path))
        saved=json.loads((self.app/'projects/TEST_STARDUST.json').read_text())
        assert saved['parameters']['shimmer.type']==1
        main.project_manager.apply_parameters(main.params,{'grain.enabled':1})
        assert main.params.get('shimmer.type')==0
        main.open_project('TEST_STARDUST')
        assert main.params.get('shimmer.type')==1
        main.controls.tab_index=main.controls.TABS.index('FX');main.controls.fx_page_index=self.index;main.controls.fx_param_indices[self.index]=0
        fx=main.dsp.fx.engine
        handle=fx.handle
        before={k:main.params.get(k) for k in main.params.params if k.startswith('reverb.')}
        main.params.set('stardust.input',0);main.params.set('stardust.return',1);main.params.set('stardust.send',1)
        main.params.set('shimmer.type',1);main.params.set('shimmer.mix',.8)
        audio=np.zeros((512,2),np.float32);audio[0]=.7
        energy=0.
        for i in range(300):
            out=fx.process(audio.copy() if i==0 else np.zeros_like(audio),main.params)
            assert np.isfinite(out).all()
            if i>10:energy+=float(np.sum(out*out))
        assert energy>1e-5,energy
        assert fx.handle==handle
        assert {k:main.params.get(k) for k in before}==before
        assert main.params.get('shimmer.mix')==.8
        assert fx._v4_shimmer_choice.star is not None
        main.params.set('shimmer.type',0)
        for _ in range(3):fx.process(np.zeros_like(audio),main.params)
        assert fx._v4_shimmer_choice.mode==0
        main.params.set('stardust.input',1);main.params.set('stardust.return',.35)
        import sys
        from multiprocessing import RawArray
        keys=list(main.params.params)
        shared=RawArray('d',[main.params.get(key) for key in keys])
        reader_cls=sys.modules['engine.audio_worker']._SharedParameterReader
        reader=reader_cls(keys,shared)
        shared[keys.index('shimmer.type')]=1;reader.refresh()
        fx.process(np.zeros_like(audio),reader)
        assert fx._v4_shimmer_choice.mode==1
        shared[keys.index('shimmer.type')]=0;reader.refresh()
        fx.process(np.zeros_like(audio),reader)
        assert fx._v4_shimmer_choice.mode==0
        print('PASS actual AudioWorker shared parameter reader selects Stardust/Original',flush=True)
        saved={k:main.params.get(k) for k in main.params.params}
        source=main.dsp._v4_live_source
        class Capture:
            def __init__(self):self.frame=0
            def read(self,n):
                time=(np.arange(n)+self.frame)/48000.;self.frame+=n
                return np.repeat((.1*np.sin(time*2*np.pi*220)).astype(np.float32)[:,None],2,axis=1)
            def close(self):pass
        try:
            for key,value in {'transport.playing':1,'live.enabled':1,'live.mix':0,'live.fx_mix':1,'live.tape_mix':1,'shimmer.type':1,'stardust.predelay':0,'stardust.send':1,'stardust.depth':0,'stardust.pitch':12,'tape.enabled':0,'orbix.enabled':0,'delay.mix':0,'reverb.mix':0,'shimmer.mix':0}.items():
                if key in main.params.params:main.params.set(key,value)
            levels={}
            for input_level,return_level in ((1,0),(0,0),(0,1)):
                main.params.set('stardust.input',input_level);main.params.set('stardust.return',return_level)
                main.dsp.fx.engine.reset();source.close();source.capture=Capture()
                rendered=[main.dsp.render(512).copy() for _ in range(200)]
                levels[input_level,return_level]=float(np.sqrt(np.mean(np.stack(rendered[-64:])**2)))
            print('FULL LIVE SHIMMER INPUT/RETURN RMS',levels,flush=True)
            assert levels[1,0]>.01,levels
            assert levels[0,0]<1e-7,levels
            assert levels[0,1]>.01,levels
        finally:
            source.close()
            for key,value in saved.items():main.params.set(key,value)
            main.dsp.fx.engine.reset()
        print('PASS full original LIVE chain: INPUT/RETURN zero silences, dry-only and wet-only routing work at FX MIX 100%',flush=True)
        import pygame
        mapping=json.loads((self.app/'gb_buttons.json').read_text())['buttons']
        menu=next(int(k) for k,v in mapping.items() if v==14)
        for expected in (1.,0.):
            pygame.event.post(pygame.event.Event(pygame.JOYBUTTONDOWN,button=menu,joy=0))
            pygame.event.post(pygame.event.Event(pygame.JOYBUTTONUP,button=menu,joy=0))
            events=pygame.event.get()
            assert not any(e.type in (pygame.JOYBUTTONDOWN,pygame.JOYBUTTONUP) and e.button==14 for e in events)
            assert main.params.get('shimmer.type')==expected
        def press(logical):
            physical=next(int(k) for k,v in mapping.items() if v==logical)
            pygame.event.post(pygame.event.Event(pygame.JOYBUTTONDOWN,button=physical,joy=0))
            pygame.event.post(pygame.event.Event(pygame.JOYBUTTONUP,button=physical,joy=0))
            return pygame.event.get()
        for index in range(len(main.controls.FX_PAGES)):
            main.controls.fx_page_index=index
            for logical,direction in ((11,1),(10,-1)):
                before=main.controls.fx_page_index
                assert not any(e.type in (pygame.JOYBUTTONDOWN,pygame.JOYBUTTONUP) and e.button==logical for e in press(logical))
                assert main.controls.fx_page_index==(before+direction)%len(main.controls.FX_PAGES)
            before=main.controls.fx_page_index
            assert not any(e.type in (pygame.JOYBUTTONDOWN,pygame.JOYBUTTONUP) and e.button==7 for e in press(7))
            assert main.controls.fx_page_index==before
            assert any(e.type==pygame.JOYBUTTONDOWN and e.button==6 for e in press(6))
        main.controls.tab_index=main.controls.TABS.index('GRAIN')
        for logical in (7,10,11):
            assert any(e.type==pygame.JOYBUTTONDOWN and e.button==logical for e in press(logical))
        main.controls.tab_index=main.controls.TABS.index('FX');main.controls.fx_page_index=self.index
        print('PASS MENU type, mapped L2/R2 previous/next with wrap, X inactive in FX, Y unchanged and other tabs untouched',flush=True)
        print('PASS Original/Stardust SHIMMER selector, parameters, project round trip and old-project default, ARM shimmer tail and unchanged native reverb instance/parameters',flush=True)
    def frame(self,main,state):
        if state['frames']==2:assert main.params.get('shimmer.type')==1
        if state['frames']==6:assert main.params.get('shimmer.type')==0
        if state['frames']==7:
            assert main.params.get('shimmer.type')==1
            main.controls.fx_param_indices[self.index]=10
            assert main.controls.current_param=='stardust.return'
    def after_draw(self,main,state):
        if state['frames'] in (1,2,6,7,8):
            import pygame
            pygame.image.save(main.ui.screen,str(self.app/f'stardust-ui-{state["frames"]}.png'))
    def finish(self,main,state):pass
