"""Keep persisted sound parameters separate from LIVE/REC session ownership."""
from pathlib import Path,PurePosixPath
import hashlib

SAMPLE_MIX_KEYS=('sample.granular_mix','sample.fx_mix','sample.tape_mix')
SESSION_KEYS=frozenset(('live.enabled','live.freeze'))
FACTORY_DEMO='sample grainbrick 1.wav'
FACTORY_SHA256='a3dad730ac8c64296be3d225803fc6cd2b037c4eb86ea178012bfc2051354d8c'


def sound_values(values):
    return {key:value for key,value in values.items() if key not in SESSION_KEYS}


def clear_session(bus):
    for key in SESSION_KEYS:
        if key in bus.params:bus.set(key,0)


def relocated_sample(app,missing):
    """Retain media subpaths when an installation moved; never guess by basename."""
    app=Path(app).resolve();parts=PurePosixPath(str(missing).replace('\\','/')).parts
    candidates=[]
    for index,part in enumerate(parts):
        if part not in ('samples','recordings','demo-samples'):continue
        tail=parts[index+1:]
        if not tail:continue
        folders=('samples',) if part in ('samples','demo-samples') else ('recordings','samples/recordings')
        for folder in folders:
            root=(app/folder).resolve();candidate=root.joinpath(*tail).resolve()
            if not candidate.is_relative_to(root) or not candidate.is_file():continue
            if part=='demo-samples':
                if tail!=(FACTORY_DEMO,) or hashlib.sha256(candidate.read_bytes()).hexdigest()!=FACTORY_SHA256:continue
            candidates.append(candidate)
    unique=set(candidates)
    return next(iter(unique)) if len(unique)==1 else None


class ProjectPlayback:
    def __init__(self,app,main,controller):
        self.app=Path(app);self.main=main;self.controller=controller;self.initialized=False
    def file_mode(self):
        c=self.controller
        if c.active():c.stop_live()
        else:c.restore_live_output()
        clear_session(c.bus());c.mode='REC'
        self.main.record_mode='browser'
        ui=getattr(self.main,'ui',None)
        if ui is not None:
            ui.record_mode='browser';ui._v4_display_source=None
            ui.set_sample(getattr(self.main,'sample',None))
    def select_loaded_sample(self):
        main=self.main;sample=getattr(main,'sample',None)
        path=getattr(sample,'path',None)
        if not path or not Path(path).is_file():return
        browser=main.sample_browser;parent=str(Path(path).resolve().parent)
        if browser._inside_root(parent):
            browser.current_dir=parent;browser.refresh()
            main.controls.set_sample_count(len(browser))
            for index,entry in enumerate(browser.entries):
                if not entry.is_dir and Path(entry.path).resolve()==Path(path).resolve():
                    main.controls.sample_index=index;break
        main.controls.sample_loaded_path=str(path)
    def install(self):
        # Install before original startup restores last-sound state or starts a worker.
        project_cls=__import__('engine.project_manager',fromlist=['ProjectManager']).ProjectManager
        original_apply=project_cls.apply_parameters
        def apply(manager,bus,values):
            if isinstance(values,dict):
                values=sound_values(values)
                values.pop('transport.playing',None)
                from v4_shimmer import SHIMMER_DEFAULTS
                for key,(default,_,__) in SHIMMER_DEFAULTS.items():
                    if key in bus.params:values.setdefault(key,default)
                for key in SAMPLE_MIX_KEYS:
                    if key in bus.params:values.setdefault(key,1.)
            bus.set('transport.playing',0)
            return original_apply(manager,bus,values)
        project_cls.apply_parameters=apply
        original_snapshot=project_cls.snapshot_parameters
        project_cls.snapshot_parameters=lambda manager,bus:sound_values(original_snapshot(manager,bus))
        original_resolve=project_cls.resolve_sample_path
        def resolve(manager,info):
            path=original_resolve(manager,info)
            if not path or Path(path).is_file():return path
            candidate=relocated_sample(self.app,path)
            if candidate is None:return path
            print('V4 PROJECT SAMPLE RELOCATED:',path,'->',str(candidate),flush=True)
            return candidate if isinstance(path,Path) else str(candidate)
        project_cls.resolve_sample_path=resolve
        state_cls=__import__('engine.sound_state',fromlist=['SoundStateManager']).SoundStateManager
        original_keys=state_cls._sound_keys
        state_cls._sound_keys=lambda state:[key for key in original_keys(state) if key not in SESSION_KEYS]
        original_load=state_cls.load
        def load(state,*args,**kwargs):
            result=original_load(state,*args,**kwargs)
            clear_session(state.parameters)
            return result
        state_cls.load=load
        before=self.controller.before_input
        def before_input():
            before()
            if self.initialized:return
            self.initialized=True;main=self.main;c=self.controller
            original_load_sample=main.load_sample
            def load_sample(entry):
                if getattr(main,'sample_preview',None) is not None:main.sample_preview.stop(restart=False)
                self.file_mode()
                result=original_load_sample(entry)
                self.file_mode();self.select_loaded_sample()
                return result
            main.load_sample=load_sample
            original_open=main.open_project
            def open_project(name):
                c.bus().set('transport.playing',0)
                if getattr(main,'sample_preview',None) is not None:main.sample_preview.stop(restart=False)
                self.file_mode()
                result=original_open(name)
                c.bus().set('transport.playing',0)
                self.file_mode();self.select_loaded_sample()
                # Same-sample project loads may skip native load_sample. Restart the
                # original file worker if LIVE/preview previously owned the device.
                worker=getattr(main,'audio_worker',None)
                loaded=str(getattr(main.controls,'project_status','')).startswith('LOADED')
                if loaded and getattr(main,'sample',None) is not None and worker is not None and not worker.running:
                    try:worker.start()
                    except Exception as exc:
                        main.controls.project_status='AUDIO START ERROR'
                        main.controls.sample_error=str(exc)
                        print('V4 PROJECT AUDIO START ERROR:',str(exc),flush=True)
                return result
            main.open_project=open_project
            # Original startup can restore a file before these hooks are installed.
            self.file_mode();self.select_loaded_sample()
        self.controller.before_input=before_input
        return self
