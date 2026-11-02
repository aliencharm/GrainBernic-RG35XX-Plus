import types
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
        bus=add_live_parameters(Bus());sample=types.SimpleNamespace(data=np.zeros((48000,2),np.float32))
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
    def test_sample_fx_and_tape_mixes_default_to_original_and_bypass_only_the_stage(self):
        for key in ('live.fx_mix','live.tape_mix'):
            for mix,expected in ((0.,1.),(.5,1.5),(1.,2.)):
                bus=add_live_parameters(Bus());bus.set(key.replace('live.','sample.'),mix)
                result=StageMix(Effect(),key).process(np.ones((512,2),np.float32),bus)
                np.testing.assert_allclose(result,expected)
                self.assertEqual(bus.get(key),1.)
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
