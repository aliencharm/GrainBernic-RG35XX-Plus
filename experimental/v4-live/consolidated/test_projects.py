import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from v4_projects import ProjectPlayback,relocated_sample,sound_values

class Bus:
    def __init__(self):self.params={'live.enabled':1.,'live.freeze':1.,'grain.size':.1,'transport.playing':1.}
    def set(self,key,value):self.params[key]=value
    def get(self,key):return self.params[key]

class ProjectTests(unittest.TestCase):
    def fixture(self,root):
        bus=Bus()
        class Manager:
            def apply_parameters(self,bus,values):
                for key,value in values.items():bus.set(key,value)
                return {'applied':len(values)}
            def snapshot_parameters(self,bus):return dict(bus.params)
            def resolve_sample_path(self,info):return info
        class State:
            def __init__(self,bus):self.parameters=bus
            def _sound_keys(self):return list(self.parameters.params)
            def load(self):self.parameters.set('live.enabled',1);self.parameters.set('live.freeze',1);return 3
        class Worker:
            running=False
            def start(self):self.running=True
        path=Path(root)/'samples/file.wav';path.parent.mkdir();path.write_bytes(b'fixture')
        entry=types.SimpleNamespace(path=str(path),is_dir=False)
        class Browser:
            current_dir=str(path.parent)
            entries=[types.SimpleNamespace(is_dir=True,path=str(path.parent/'folder')),entry]
            def _inside_root(self,value):return True
            def refresh(self):pass
            def __len__(self):return len(self.entries)
        class Preview:
            def stop(self,restart):self.restart=restart
        class UI:
            def set_sample(self,sample):self.sample=sample
        controls=types.SimpleNamespace(sample_index=0,project_status='',set_sample_count=lambda n:None)
        main=types.SimpleNamespace(params=bus,record_mode='ready',sample=types.SimpleNamespace(path=str(path)),ui=UI(),
            sample_browser=Browser(),controls=controls,sample_preview=Preview(),audio_worker=Worker())
        manager=Manager()
        def load_sample(entry):main.sample=types.SimpleNamespace(path=entry.path);return True
        def open_project(name):
            manager.apply_parameters(bus,{'live.enabled':1,'live.freeze':1,'grain.size':.5,'transport.playing':1})
            controls.project_status='LOADED '+name
        main.load_sample=load_sample;main.open_project=open_project
        class Controller:
            before_input=lambda self:None
            def bus(self):return bus
            def active(self):return bus.get('live.enabled')>=.5
            def stop_live(self):bus.set('live.enabled',0);main.audio_worker.running=False
            def restore_live_output(self):pass
        controller=Controller()
        project_module=types.ModuleType('engine.project_manager');project_module.ProjectManager=Manager
        state_module=types.ModuleType('engine.sound_state');state_module.SoundStateManager=State
        modules={'engine.project_manager':project_module,'engine.sound_state':state_module}
        with patch.dict(sys.modules,modules):playback=ProjectPlayback(root,main,controller).install()
        controller.before_input()
        return main,controller,manager,State

    def test_loaded_project_does_not_rearm_live_and_restarts_same_sample_worker(self):
        with tempfile.TemporaryDirectory() as root:
            main,c,manager,State=self.fixture(root)
            main.open_project('TEST')
            self.assertEqual(main.params.get('live.enabled'),0)
            self.assertEqual(main.params.get('live.freeze'),0)
            self.assertEqual(main.params.get('grain.size'),.5)
            self.assertEqual(main.params.get('transport.playing'),0)
            self.assertEqual(main.record_mode,'browser')
            self.assertEqual(main.ui.record_mode,'browser')
            self.assertEqual(main.controls.sample_index,1)
            self.assertTrue(main.audio_worker.running)
            self.assertFalse(main.sample_preview.restart)

    def test_save_and_startup_filter_session_flags_without_changing_other_parameters(self):
        with tempfile.TemporaryDirectory() as root:
            main,c,manager,State=self.fixture(root)
            state=State(main.params)
            self.assertEqual(state.load(),3)
            self.assertEqual(main.params.get('live.enabled'),0)
            self.assertEqual(main.params.get('live.freeze'),0)
            self.assertNotIn('live.enabled',state._sound_keys())
            main.params.set('live.enabled',1)
            snapshot=manager.snapshot_parameters(main.params)
            self.assertNotIn('live.enabled',snapshot)
            self.assertIn('grain.size',snapshot)
            self.assertEqual(main.params.get('live.enabled'),1)

    def test_old_projects_default_sample_mixes_to_full_and_new_values_are_kept(self):
        with tempfile.TemporaryDirectory() as root:
            main,c,manager,State=self.fixture(root)
            keys=('sample.granular_mix','sample.fx_mix','sample.tape_mix')
            for key in keys:main.params.set(key,.2)
            manager.apply_parameters(main.params,{'grain.size':.3})
            self.assertTrue(all(main.params.get(key)==1. for key in keys))
            manager.apply_parameters(main.params,{'sample.fx_mix':.4})
            self.assertEqual(main.params.get('sample.fx_mix'),.4)
            self.assertEqual(manager.snapshot_parameters(main.params)['sample.fx_mix'],.4)

    def test_moved_media_subpaths_are_relocated_without_basename_guessing(self):
        with tempfile.TemporaryDirectory() as root:
            app=Path(root);(app/'samples/sub').mkdir(parents=True)
            path=app/'samples/sub/record.wav';path.write_bytes(b'audio')
            self.assertEqual(relocated_sample(app,'/old/install/samples/sub/record.wav'),path)
            self.assertEqual(relocated_sample(app,r'C:\old\samples\sub\record.wav'),path)
            self.assertIsNone(relocated_sample(app,'/elsewhere/record.wav'))
            self.assertIsNone(relocated_sample(app,'samples/../../record.wav'))
            self.assertIsNone(relocated_sample(app,'demo-samples/record.wav'))

    def test_ambiguous_recordings_are_not_selected_silently(self):
        with tempfile.TemporaryDirectory() as root:
            app=Path(root)
            for folder in ('recordings','samples/recordings'):
                (app/folder).mkdir(parents=True);(app/folder/'a.wav').write_bytes(b'different')
            self.assertIsNone(relocated_sample(app,'/old/recordings/a.wav'))

if __name__=='__main__':unittest.main()
