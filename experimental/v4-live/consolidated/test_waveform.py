import sys
import types
import unittest
from unittest.mock import patch
from v4_waveform import install

class WaveformTests(unittest.TestCase):
    def install_view(self):
        class View:
            def __init__(self):self.points=[.8]*800;self.seen=[];self.fail=False
            def draw(self,surface,rect,*args,**kwargs):
                self.seen.append((self.points,args,kwargs))
                if self.fail:raise RuntimeError('native draw failed')
                return {int(i/(len(self.points)-1)*rect[2]) for i in range(len(self.points))}
        module=types.ModuleType('ui.waveform');module.WaveformView=View
        with patch.dict(sys.modules,{'ui.waveform':module}):install();install()
        return View()

    def test_every_display_column_is_filled_and_markers_are_forwarded(self):
        view=self.install_view();source=view.points
        args=(.2,.4,0.,1.,True,False,.3)
        columns=view.draw(None,(30,145,964,205),*args,color=(85,95,100))
        self.assertEqual(columns,set(range(965)))
        self.assertIs(view.points,source)
        self.assertEqual(view.seen[0][1],args)
        self.assertEqual(view.seen[0][2],{'color':(85,95,100)})
        self.assertTrue(all(value==.8 for value in view.seen[0][0]))

    def test_cache_refreshes_when_source_or_width_changes(self):
        view=self.install_view();rect=(0,0,964,205)
        view.draw(None,rect);first=view.seen[-1][0]
        view.draw(None,rect);self.assertIs(view.seen[-1][0],first)
        view.points=[.2]*800;view.draw(None,rect)
        self.assertIsNot(view.seen[-1][0],first)
        self.assertTrue(all(value==.2 for value in view.seen[-1][0]))
        view.draw(None,(0,0,1000,205));self.assertEqual(len(view.seen[-1][0]),1002)

    def test_native_failure_restores_original_peaks(self):
        view=self.install_view();source=view.points;view.fail=True
        with self.assertRaises(RuntimeError):view.draw(None,(0,0,964,205))
        self.assertIs(view.points,source)

if __name__=='__main__':unittest.main()
