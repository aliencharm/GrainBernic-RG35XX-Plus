from pathlib import Path
import tempfile
import unittest
from channel_routes import discover,route_definition,supports_48k,Router

class RouteTests(unittest.TestCase):
    def test_audio4c_exposes_four_pairs_in_each_direction(self):
        with tempfile.TemporaryDirectory() as root:
            card=Path(root)/'card3';card.mkdir();(card/'id').write_text('AUDIO4c');(card/'usbid').write_text('2321:0021')
            (card/'stream0').write_text('iConnectivity AUDIO4c at usb-host\nPlayback:\n Interface 2\n Altset 1\n Format: S32_LE\n Channels: 8\n Rates: 48000\nCapture:\n Interface 1\n Altset 1\n Format: S32_LE\n Channels: 8\n Rates: 48000\n')
            routes=discover(Path(root))
            self.assertEqual(len(routes),8)
            for direction in ('capture','playback'):
                selected=[r for r in routes if r['direction']==direction]
                self.assertEqual([r['first'] for r in selected],[0,2,4,6])
                self.assertEqual(selected[-1]['label'],'AUDIO4c 7-8')
                self.assertIn('ttable.0.6 1',route_definition(selected[-1]))
                self.assertIn('channels 8 format S32_LE',route_definition(selected[-1]))
                self.assertFalse(any('9-10' in r['label'] for r in selected))
    def test_short_names_are_shared_by_input_and_output_without_changing_routes(self):
        for identifier,description,expected in (
            ('Series','TASCAM DR-40X at usb-host','TASCAM'),
            ('Series','Series at usb-host','TASCAM'),
            ('AUDIO4c','iConnectivity AUDIO4c at usb-host','AUDIO4c'),
            ('USB','Other interface at usb-host','USB'),
        ):
            with self.subTest(identifier=identifier),tempfile.TemporaryDirectory() as root:
                card=Path(root)/'card3';card.mkdir()
                (card/'id').write_text(identifier);(card/'usbid').write_text('1234:5678')
                modes=''.join(direction+':\n Interface 1\n Altset 1\n Format: S32_LE\n Channels: 4\n Rates: 48000\n' for direction in ('Playback','Capture'))
                (card/'stream0').write_text(description+'\n'+modes)
                routes=discover(Path(root))
                for direction in ('capture','playback'):
                    selected=[r for r in routes if r['direction']==direction]
                    self.assertEqual([r['label'] for r in selected],[expected+' 1-2',expected+' 3-4'])
                    self.assertEqual(selected[0]['alias'],f'v4_{direction}_{identifier}_0_1_2')
                    self.assertEqual(selected[0]['hardware'],f'hw:CARD={identifier},DEV=0')

    def test_original_output_resolver_can_resolve_pair_aliases(self):
        import types,sys
        from unittest.mock import patch
        class UI:
            def draw_record_ready_page(self):pass
        devices=types.ModuleType('engine.audio_devices')
        devices.available_outputs=lambda:[('internal','INTERNAL','default'),('usb','USB','plughw:CARD=AUDIO4c,DEV=0')]
        renderer=types.ModuleType('ui.renderer');renderer.UIEngine=UI
        main=types.SimpleNamespace(ui=UI(),resolve_output=lambda selected:'old')
        controller=types.SimpleNamespace(before_input=lambda:None)
        outputs=[dict(card='AUDIO4c',device=0,alias='pair78',label='AUDIO4c 7-8')]
        with patch.dict(sys.modules,{'engine.audio_devices':devices,'ui.renderer':renderer}):
            Router(Path('/unused'),{},[],outputs).install(main,controller)
            self.assertEqual(main.resolve_output('pair78'),'pair78')
            self.assertEqual(main.resolve_output('internal'),'default')
            self.assertEqual(devices.available_outputs(),[('internal','INTERNAL','default'),('pair78','AUDIO4c 7-8','pair78')])
    def test_rates_and_pair_bounds(self):
        self.assertTrue(supports_48k('44100 - 192000 (continuous)'))
        self.assertFalse(supports_48k('44100, 96000'))
        with self.assertRaises(ValueError):route_definition(dict(alias='test',first=7,channels=8,format='S32_LE',hardware='null'))

if __name__=='__main__':unittest.main()
