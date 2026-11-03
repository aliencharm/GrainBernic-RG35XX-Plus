import types
import tempfile
from pathlib import Path
import unittest
import numpy as np
from live_source import SwitchableSource,add_live_parameters
from stage_mix import StageMix
from v4_record_ui import RecordingUI,fit_label

class Bus:
    def __init__(self):
        self.params={};self.values={'transport.playing':1.,'grain.enabled':1.,'grain.position':.5,
            'grain.pitch':0.,'roam.enabled':0.,'motion.enabled':0.}
    def add(self,key,value,lo,hi):self.params[key]=True;self.values[key]=value
    def get(self,key):return self.values[key]
    def set(self,key,value):self.values[key]=max(0.,min(1.,value))
class Engine:
    def __init__(self,sample,parameters,rate):self.sample=sample;self.parameters=parameters
    def render(self,frames):return np.full((frames,2),.6 if self.parameters.get('grain.enabled') else .2,np.float32)
    def active_grains(self):return 1
    def roam_position(self):return .5
class Effect:
    def process(self,audio,parameters):audio*=2;return audio

class SampleMixerTests(unittest.TestCase):
    def source(self):
        bus=add_live_parameters(Bus());sample=types.SimpleNamespace(data=np.full((48000,2),.2,np.float32))
        engine=Engine(sample,bus,48000)
        source=SwitchableSource(engine,bus,Engine,lambda:(_ for _ in ()).throw(AssertionError('Sample mode opened capture')))
        self.addCleanup(source.close);return bus,engine,source
    def test_full_sample_mix_is_original_output_and_opens_no_capture_or_dry_engine(self):
        bus,engine,source=self.source()
        np.testing.assert_array_equal(source.render(512),engine.render(512))
        self.assertIsNone(source.capture);self.assertIsNone(source.sample_dry)
    def test_sample_granular_dry_half_and_full_blends_use_original_file_engine(self):
        for mix,expected in ((0.,.2),(.5,.4),(1.,.6)):
            bus,engine,source=self.source();bus.set('sample.granular_mix',mix)
            np.testing.assert_allclose(source.render(512),expected,atol=1e-7)
            if mix<1:self.assertIs(source.sample_dry.sample,engine.sample)
            self.assertEqual(bus.get('grain.enabled'),1.)
    def test_sample_mix_changes_are_ramped_and_live_values_are_independent(self):
        bus,engine,source=self.source();bus.set('sample.granular_mix',0)
        source.render(512);bus.set('sample.granular_mix',1)
        result=source.render(512)
        self.assertAlmostEqual(float(result[0,0]),.2,places=6)
        self.assertAlmostEqual(float(result[-1,0]),.6,places=6)
        self.assertEqual(bus.get('live.mix'),0)
    def test_granular_mix_sweep_with_grain_on_off_and_roam_motion_states(self):
        for enabled in (0.,1.):
            for roam,motion in ((0.,0.),(1.,0.),(0.,1.),(1.,1.)):
                bus,engine,source=self.source()
                bus.set('grain.enabled',enabled);bus.set('roam.enabled',roam);bus.set('motion.enabled',motion)
                for mix in (0.,.01,.25,.5,.75,.99,1.,.75,.5,.25,0.):
                    bus.set('sample.granular_mix',mix)
                    source.render(512) # First block ramps from the previous setting.
                    expected=.2+(.6-.2)*mix if enabled else .2
                    np.testing.assert_allclose(source.render(512),expected,atol=1e-7)
    def test_granular_mix_ramps_in_both_directions(self):
        bus,engine,source=self.source()
        bus.set('sample.granular_mix',1);source.render(512)
        bus.set('sample.granular_mix',0)
        result=source.render(512)
        np.testing.assert_allclose(result[:,0],np.linspace(.6,.2,512),atol=1e-7)
        self.assertTrue(np.all(np.diff(result[:,0])<=1e-7))
    def test_straight_file_dry_loops_and_pauses_without_roam(self):
        bus,engine,source=self.source();engine.sample.data=np.repeat(np.array([.1,.2,.3,.4],np.float32)[:,None],2,axis=1)
        bus.set('sample.granular_mix',0);bus.set('roam.enabled',0)
        np.testing.assert_allclose(source.render(6)[:,0],[.1,.2,.3,.4,.1,.2])
        bus.set('transport.playing',0);np.testing.assert_array_equal(source.render(5),np.zeros((5,2)))
        bus.set('transport.playing',1)
        np.testing.assert_allclose(source.render(2)[:,0],[.3,.4])
    def test_straight_file_dry_resamples_at_original_sample_rate(self):
        bus,engine,source=self.source();engine.sample.sample_rate=24000
        engine.sample.data=np.repeat(np.array([0,.2,.4,.6],np.float32)[:,None],2,axis=1)
        bus.set('sample.granular_mix',0)
        np.testing.assert_allclose(source.render(8)[:,0],[0,.1,.2,.3,.4,.5,.6,.3],atol=1e-7)
    def test_disabled_granular_plays_original_even_with_full_mix(self):
        bus,engine,source=self.source();engine.sample.data=np.full((100,2),.7,np.float32)
        bus.set('grain.enabled',0);bus.set('sample.granular_mix',1)
        np.testing.assert_allclose(source.render(512),.7)
    def test_sample_fx_and_tape_mixes_default_to_original_and_bypass_only_the_stage(self):
        for key in ('live.fx_mix','live.tape_mix'):
            for mix,expected in ((0.,1.),(.5,1.5),(1.,2.)):
                bus=add_live_parameters(Bus());bus.set(key.replace('live.','sample.'),mix)
                result=StageMix(Effect(),key).process(np.ones((512,2),np.float32),bus)
                np.testing.assert_allclose(result,expected)
                self.assertEqual(bus.get(key),1.)
    def test_preview_dispatches_loaded_and_unloaded_entries_to_same_player(self):
        calls=[]
        main=types.SimpleNamespace(controls=types.SimpleNamespace(sample_index=0),
            ui=types.SimpleNamespace(audio_output_id='internal'),audio_worker=object(),
            sample=types.SimpleNamespace(path='loaded.wav'),
            sample_preview=types.SimpleNamespace(toggle=lambda *args:calls.append(args)),
            resolve_output=lambda value:'default')
        main.sample_browser=types.SimpleNamespace(get=lambda index:types.SimpleNamespace(path=('loaded.wav','other.wav')[index]))
        ui=RecordingUI(main,types.SimpleNamespace(message=''))
        ui.preview_sample();main.controls.sample_index=1;ui.preview_sample()
        self.assertEqual([args[0] for args in calls],['loaded.wav','other.wav'])
        self.assertTrue(all(args[1] is main.audio_worker and args[2]=='default' for args in calls))
    def test_missing_usb_blocks_record_before_touching_original_recorder(self):
        c=types.SimpleNamespace(message='')
        ui=RecordingUI(types.SimpleNamespace(),c)
        ui.start_recording()
        self.assertIn('NO USB INPUT',c.message)
        self.assertFalse(ui.usb_available())
        ui.router=types.SimpleNamespace(inputs=[dict(alias='usb')])
        self.assertTrue(ui.usb_available())
    def deletion_fixture(self,loaded=False):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        root=Path(folder.name);path=root/'test.wav';path.write_bytes(b'test')
        class Browser:
            entries=[types.SimpleNamespace(path=str(path),is_dir=False)]
            def get(self,index):return self.entries[index] if self.entries else None
            def _inside_root(self,value):return Path(value).is_relative_to(root)
            def refresh(self):self.entries=[e for e in self.entries if Path(e.path).exists()]
            def __len__(self):return len(self.entries)
        bus=add_live_parameters(Bus());worker=types.SimpleNamespace(stops=0)
        def stop():worker.stops+=1
        worker.stop=stop
        main=types.SimpleNamespace(sample_browser=Browser(),controls=types.SimpleNamespace(sample_index=0,set_sample_count=lambda n:None,sample_loaded_path=str(path)),
            sample=types.SimpleNamespace(path=str(path)) if loaded else None,audio_worker=worker,
            ui=types.SimpleNamespace(set_sample=lambda sample:None),sample_preview=types.SimpleNamespace(stop=lambda restart:None))
        ui=RecordingUI(main,types.SimpleNamespace(bus=lambda:bus,message=''))
        return ui,path,main,bus,worker
    def test_parent_navigation_cancels_delete_and_stays_inside_sample_root(self):
        ui,path,main,bus,worker=self.deletion_fixture(loaded=True)
        nested=path.parent/'nested';nested.mkdir()
        main.sample_browser.current_dir=str(nested)
        ui.pending_delete=path
        ui.parent_folder()
        self.assertEqual(main.sample_browser.current_dir,str(path.parent))
        self.assertIsNone(ui.pending_delete);self.assertTrue(path.exists())
        self.assertEqual(worker.stops,0)
        ui.parent_folder()
        self.assertEqual(main.sample_browser.current_dir,str(path.parent))
    def test_delete_requires_same_file_confirmation_and_refreshes_browser(self):
        ui,path,main,bus,worker=self.deletion_fixture()
        self.assertTrue(ui.delete_sample());self.assertTrue(path.exists())
        self.assertEqual(ui.pending_delete,path)
        self.assertTrue(ui.delete_sample());self.assertFalse(path.exists())
        self.assertEqual(len(main.sample_browser),0);self.assertEqual(main.controls.sample_index,0)
        self.assertEqual(worker.stops,0)
    def test_delete_loaded_sample_stops_playback_and_clears_loaded_state(self):
        ui,path,main,bus,worker=self.deletion_fixture(loaded=True)
        ui.delete_sample();ui.delete_sample()
        self.assertEqual(worker.stops,1);self.assertIsNone(main.sample)
        self.assertIsNone(main.audio_worker);self.assertIsNone(main.dsp)
        self.assertEqual(bus.get('transport.playing'),0)
    def test_delete_other_file_keeps_loaded_sample_and_worker(self):
        ui,path,main,bus,worker=self.deletion_fixture()
        loaded=types.SimpleNamespace(path=str(path.parent/'other.wav'));main.sample=loaded
        ui.delete_sample();ui.delete_sample()
        self.assertIs(main.sample,loaded);self.assertIs(main.audio_worker,worker)
        self.assertEqual(worker.stops,0)
    def test_changing_target_requires_a_new_confirmation(self):
        ui,path,main,bus,worker=self.deletion_fixture()
        ui.delete_sample()
        other=path.parent/'other.wav';other.write_bytes(b'other')
        main.sample_browser.entries[0].path=str(other)
        ui.delete_sample()
        self.assertTrue(path.exists());self.assertTrue(other.exists())
        self.assertEqual(ui.pending_delete,other)
    def test_delete_cannot_remove_directories_or_outside_browser_root(self):
        ui,path,main,bus,worker=self.deletion_fixture()
        main.sample_browser.entries[0].is_dir=True
        self.assertFalse(ui.delete_sample());self.assertTrue(path.exists())
        main.sample_browser.entries[0].is_dir=False
        main.sample_browser._inside_root=lambda path:False
        self.assertFalse(ui.delete_sample());self.assertTrue(path.exists())
    def test_source_labels_fit_reserved_header_width(self):
        label='LOADED: '+('a very long sample filename/'*5)+'audio.wav'
        fitted=fit_label(label,695,2)
        self.assertLessEqual(len(fitted)*12,695)
        self.assertTrue(fitted.endswith('audio.wav'));self.assertIn('...',fitted)
    def test_switching_live_is_ready_without_starting_capture_and_returns_sample(self):
        bus=add_live_parameters(Bus())
        main=types.SimpleNamespace(params=bus,record_mode='browser',record_source_index=2,
            ui=types.SimpleNamespace(record_mode='browser',set_sample=lambda sample:None),
            sample=types.SimpleNamespace(path='sample.wav'),sample_preview=types.SimpleNamespace(stop=lambda restart:None),
            audio_worker=types.SimpleNamespace(running=True))
        def open_ready():main.record_mode='ready';main.record_source_index=0
        main.open_input_recording_page=open_ready
        c=types.SimpleNamespace(mode='REC',message='',bus=lambda:bus,active=lambda:bus.get('live.enabled')>=.5,
            restore_live_output=lambda:None)
        ui=RecordingUI(main,c);ui.live_page()
        self.assertEqual(c.mode,'LIVE');self.assertEqual(main.record_mode,'ready')
        self.assertEqual(main.record_source_index,2);self.assertEqual(bus.get('live.enabled'),0)
        ui.sample_page();self.assertEqual(c.mode,'REC');self.assertEqual(main.record_mode,'browser')
    def test_sample_mixer_is_a_second_page_without_changing_transport(self):
        bus=add_live_parameters(Bus())
        main=types.SimpleNamespace(record_mode='browser',ui=types.SimpleNamespace(record_mode='browser'),
            sample_preview=types.SimpleNamespace(stop=lambda restart:None))
        c=types.SimpleNamespace(mode='REC',bus=lambda:bus)
        ui=RecordingUI(main,c);ui.toggle_mixer()
        self.assertTrue(ui.sample_mixer);self.assertEqual(main.record_mode,'ready')
        self.assertEqual(bus.get('transport.playing'),1)
        ui.toggle_mixer();self.assertEqual(main.record_mode,'browser')

if __name__=='__main__':unittest.main()
