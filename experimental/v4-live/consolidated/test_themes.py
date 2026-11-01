import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
from v4_themes import Themes,PALETTES

class UI:pass
class ThemeTests(unittest.TestCase):
    def theme(self,root):
        return Themes(root,types.SimpleNamespace(ui=UI()),None)
    def test_default_amber_and_invalid_saved_theme_fall_back(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'config.json';path.write_text('{"ui_theme":"missing"}')
            theme=self.theme(folder);theme.apply()
            self.assertEqual(theme.name,'AMBER')
            self.assertEqual(theme.color((210,142,78)),(210,142,78))
            path.write_text('{"ui_theme":{}}')
            self.assertEqual(self.theme(folder).name,'AMBER')
    def test_cycle_persists_and_preserves_latest_audio_routes(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'config.json';path.write_text('{"capture":"auto","playback":"auto","input_route":"pair34"}')
            theme=self.theme(folder)
            for name in ('MINT','ICE','VIOLET','PAPER','AMBER'):
                theme.cycle(1);data=json.loads(path.read_text())
                self.assertEqual(data['ui_theme'],name)
                self.assertEqual(data['input_route'],'pair34')
                self.assertEqual(self.theme(folder).name,name)
            theme.cycle(-1);self.assertEqual(theme.name,'PAPER')
    def test_save_failure_retains_visible_theme(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/'config.json').write_text('{}')
            theme=self.theme(folder);theme.apply()
            with patch('v4_themes.write_json',side_effect=OSError('full')):
                with self.assertRaises(OSError):theme.cycle(1)
            self.assertEqual(theme.name,'AMBER')
    def test_legacy_colors_are_mapped_once_and_status_colors_retained(self):
        with tempfile.TemporaryDirectory() as folder:
            theme=self.theme(folder)
            for name in list(PALETTES)[1:]:
                theme.name=name;theme.apply()
                self.assertEqual(theme.color((210,142,78)),theme.roles['ACCENT'])
                self.assertEqual(theme.color((235,238,238)),theme.roles['WHITE'])
                self.assertEqual(theme.color((85,95,100)),theme.roles['DIM'])
                for color in theme.roles.values():self.assertEqual(theme.color(color),color)
                self.assertEqual(theme.color((220,20,40)),(220,20,40))
                self.assertEqual(theme.color((210,142,78,127)),(*theme.roles['ACCENT'],127))
    def test_text_and_selection_contrast(self):
        def luminance(rgb):
            values=[v/255 for v in rgb]
            values=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
            return sum(v*w for v,w in zip(values,(.2126,.7152,.0722)))
        for name,(bg,text,dim,line,accent) in PALETTES.items():
            for color in (text,accent):
                hi,lo=sorted((luminance(bg),luminance(color)),reverse=True)
                self.assertGreaterEqual((hi+.05)/(lo+.05),4.5,name)

if __name__=='__main__':unittest.main()
