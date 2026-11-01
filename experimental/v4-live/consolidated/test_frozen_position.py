"""Regress the frozen LIVE size-dependent read-head shift without changing file DSP."""
import types
import unittest
from live_source import LiveParameterView

class FrozenPositionTests(unittest.TestCase):
    def setUp(self):
        self.values={'grain.position':.5,'grain.size':.18,'grain.pitch':0.,'live.freeze':0.,'grain.spray':.1}
        self.source=types.SimpleNamespace(parameters=types.SimpleNamespace(get=self.values.__getitem__),
                                          writer=300000,capacity=768000,rate=48000,block=512,written=768000)
        # SimpleNamespace does not support weakrefs.
        class Source:pass
        source=Source();source.__dict__.update(vars(self.source));self.source=source
        self.view=LiveParameterView(source)

    def test_freeze_retains_anchor_across_size_pitch_changes_and_roam_modes(self):
        initial=self.view.get('grain.position');self.values['live.freeze']=1
        for roam in (0,1):
            self.values['roam.enabled']=roam
            for size,pitch in ((.02,0),(.5,12),(.08,-12)):
                self.values.update({'grain.size':size,'grain.pitch':pitch})
                self.assertEqual(self.view.get('grain.position'),initial)
                self.assertEqual(self.view.get('grain.size'),size)
                self.assertEqual(self.view.get('grain.pitch'),pitch)
        self.assertEqual(self.values['grain.position'],.5)

    def test_position_still_scans_and_unfreeze_resumes_tracking(self):
        initial=self.view.get('grain.position');self.values['live.freeze']=1
        self.values['grain.position']=.6
        self.assertAlmostEqual(self.view.get('grain.position')-initial,.1*768000/767999)
        self.values.update({'grain.position':.5,'grain.size':.5,'live.freeze':0})
        self.source.writer+=512
        current=self.view.get('grain.position')
        expected=(self.source.writer-int(.5*48000)-512-960)/767999
        self.assertEqual(current,expected)
        self.values['live.freeze']=1;self.values['grain.size']=.02
        self.assertEqual(self.view.get('grain.position'),current)

    def test_first_read_already_frozen_and_ring_boundary_are_bounded(self):
        self.source.writer=100;self.values['live.freeze']=1
        initial=self.view.get('grain.position')
        self.assertTrue(0<=initial<=1)
        self.values['grain.size']=1
        self.assertEqual(self.view.get('grain.position'),initial)

if __name__=='__main__':unittest.main()
