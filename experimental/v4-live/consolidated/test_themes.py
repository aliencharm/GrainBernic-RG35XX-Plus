import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
from v4_themes import Themes,PALETTES,TapeFrames
import pygame
import numpy as np

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
            for name in ('MINT','ICE','VIOLET','SAGE','SPRUCE','AMBER'):
                theme.cycle(1);data=json.loads(path.read_text())
                self.assertEqual(data['ui_theme'],name)
                self.assertEqual(data['input_route'],'pair34')
                self.assertEqual(self.theme(folder).name,name)
            theme.cycle(-1);self.assertEqual(theme.name,'SPRUCE')
    def test_old_paper_selection_becomes_dark_sage_without_replacing_config(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'config.json';original='{"ui_theme":"PAPER","input_route":"pair34"}'
            path.write_text(original);theme=self.theme(folder);theme.apply()
            self.assertEqual(theme.name,'SAGE')
            self.assertTrue(all(channel<30 for channel in theme.roles['BG']))
            self.assertEqual(path.read_text(),original)
            theme.cycle(1)
            self.assertEqual(json.loads(path.read_text()),{'ui_theme':'SPRUCE','input_route':'pair34'})

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
        for name,(bg,text,dim,line,accent,wave) in PALETTES.items():
            self.assertLess(luminance(bg),.03,name)
            for color in (text,accent):
                hi,lo=sorted((luminance(bg),luminance(color)),reverse=True)
                self.assertGreaterEqual((hi+.05)/(lo+.05),4.5,name)
            if name!='AMBER':
                for unselected in (text,dim,wave):
                    self.assertGreater(luminance(accent),luminance(unselected),name)
                self.assertLess(max(text),240,name)
        self.assertEqual(PALETTES['SPRUCE'][4],(56,205,208))

    def test_tape_cache_preserves_original_frames_and_amber_restores_them(self):
        with tempfile.TemporaryDirectory() as folder:
            theme=self.theme(folder);frame=pygame.Surface((8,8));frame.fill((240,240,240))
            original=[frame,frame.copy()];theme.main.ui.tape_grain_frames=original
            before=pygame.surfarray.array3d(frame).copy()
            theme.name='SPRUCE';theme.apply()
            frames=theme.main.ui.tape_grain_frames
            self.assertIsInstance(frames,TapeFrames)
            first=frames[0];self.assertIs(frames[0],first)
            self.assertIsNot(frames[1],first)
            np.testing.assert_array_equal(pygame.surfarray.array3d(frame),before)
            self.assertFalse(np.any(np.all(pygame.surfarray.array3d(first)>230,axis=2)))
            theme.name='AMBER';theme.apply()
            self.assertIs(theme.main.ui.tape_grain_frames,original)
            np.testing.assert_array_equal(pygame.surfarray.array3d(original[0]),before)

    def test_visualizer_colors_are_tinted_and_amber_is_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            theme=self.theme(folder)
            for name in list(PALETTES)[1:]:
                theme.name=name;theme.apply();theme._visual_depth=1
                self.assertEqual(theme.color((255,255,255)),theme.roles['WHITE'])
                self.assertEqual(theme.color((255,0,0)),theme.visual_color(255))
                self.assertEqual(tuple(theme._visual_lut[0]),theme.roles['BG'])
                theme._visual_depth=0
                self.assertEqual(theme.color((255,0,0)),(255,0,0))
            theme.name='AMBER';theme.apply();theme._visual_depth=1
            for color in ((255,255,255),(210,142,78),(255,0,0)):
                self.assertEqual(theme.color(color),color)

if __name__=='__main__':unittest.main()
