import unittest
import numpy as np
from stage_mix import StageMix
from live_source import add_live_parameters
from test_live_source import Bus

class Engine:
    def __init__(self,multiplier=2):self.calls=0;self.multiplier=multiplier
    def process(self,audio,parameters):self.calls+=1;audio*=self.multiplier;return audio

class StageMixTests(unittest.TestCase):
    def bus(self):
        p=add_live_parameters(Bus());p.set('live.enabled',1);return p
    def test_default_full_stage_is_identical_to_original(self):
        p=self.bus();engine=Engine();stage=StageMix(engine,'live.fx_mix')
        audio=np.full((512,2),.2,np.float32)
        result=stage.process(audio,p)
        self.assertIs(result,audio);np.testing.assert_array_equal(result,np.full_like(result,.4))
    def test_zero_mix_bypasses_audio_but_keeps_native_state_running(self):
        p=self.bus();p.set('live.fx_mix',0);engine=Engine();stage=StageMix(engine,'live.fx_mix')
        audio=np.full((512,2),.2,np.float32)
        np.testing.assert_array_equal(stage.process(audio,p),np.full_like(audio,.2))
        self.assertEqual(engine.calls,1)
        np.testing.assert_array_equal(audio,np.full_like(audio,.2))
    def test_midpoint_and_independent_stage_controls(self):
        p=self.bus();p.set('live.fx_mix',.5);p.set('live.tape_mix',0)
        fx=StageMix(Engine(2),'live.fx_mix');tape=StageMix(Engine(3),'live.tape_mix')
        result=tape.process(fx.process(np.full((512,2),.2,np.float32),p),p)
        np.testing.assert_allclose(result,.3)
    def test_disabled_native_stage_is_unity_at_every_mix(self):
        p=self.bus();engine=Engine(1);stage=StageMix(engine,'live.fx_mix')
        for mix in (0,.25,.5,1):
            p.set('live.fx_mix',mix)
            np.testing.assert_allclose(stage.process(np.full((512,2),.2,np.float32),p),.2)
    def test_control_change_ramps_across_one_audio_block(self):
        p=self.bus();stage=StageMix(Engine(),'live.fx_mix')
        stage.process(np.ones((512,2),np.float32),p);p.set('live.fx_mix',0)
        transition=stage.process(np.ones((512,2),np.float32),p).copy()
        self.assertEqual(transition[0,0],2);self.assertEqual(transition[-1,0],1)
        self.assertTrue(np.all(np.diff(transition[:,0])<=0))
        np.testing.assert_array_equal(stage.process(np.ones((512,2),np.float32),p),1)
    def test_original_transport_argument_is_forwarded(self):
        class Tape:
            def process(self,audio,parameters,transport_playing):
                self.playing=transport_playing
                return audio
        tape=Tape();p=self.bus()
        StageMix(tape,'live.tape_mix').process(np.zeros((512,2),np.float32),p,transport_playing=True)
        self.assertTrue(tape.playing)
    def test_file_mode_uses_original_stage_regardless_of_live_controls(self):
        p=self.bus();p.set('live.enabled',0);p.set('live.fx_mix',0)
        np.testing.assert_array_equal(StageMix(Engine(),'live.fx_mix').process(np.ones((64,2),np.float32),p),2)

if __name__=='__main__':unittest.main()
