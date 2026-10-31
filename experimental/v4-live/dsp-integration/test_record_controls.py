import types
import unittest
from original_adapter import LiveController

class RecordingControls(unittest.TestCase):
    def controller(self,available=True):
        main=types.SimpleNamespace(controls=types.SimpleNamespace(current_tab='SAMPLE'),record_mode='edit',record_denoise_percent=50)
        main.record_denoise_available=lambda:available
        main.changes=[]
        def change(delta):
            main.changes.append(delta)
            main.record_denoise_percent=max(0,min(100,main.record_denoise_percent+delta))
        main.change_record_denoise=change
        return LiveController(main,{})
    def test_back_buttons_delegate_and_preserve_other_actions(self):
        c=self.controller()
        self.assertEqual(c.filter_record_actions([('L2',None),('R2',None),('A',None)]),[('A',None)])
        self.assertEqual(c.main.changes,[-5,5])
        self.assertEqual(c.main.record_denoise_percent,50)
    def test_unavailable_denoise_is_not_changed(self):
        c=self.controller(False)
        self.assertEqual(c.filter_record_actions([('R2',None)]),[])
        self.assertEqual(c.main.changes,[])
        self.assertIn('UNAVAILABLE',c.message)
    def test_buttons_untouched_in_live_or_other_tabs(self):
        c=self.controller();actions=[('L2',None),('R2',None)]
        c.main.record_mode='ready'
        self.assertEqual(c.filter_record_actions(actions),actions)
        c.main.record_mode='edit';c.main.controls.current_tab='GRAIN'
        self.assertEqual(c.filter_record_actions(actions),actions)
        self.assertEqual(c.main.changes,[])
    def test_release_is_ignored(self):
        c=self.controller();self.assertEqual(c.filter_record_actions([('L2',0)]),[])
        self.assertEqual(c.main.changes,[])

if __name__=='__main__':unittest.main()
