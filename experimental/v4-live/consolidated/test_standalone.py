import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import v4_install as install

class StandaloneTests(unittest.TestCase):
    def fixture(self,root):
        app=Path(root)/'grainbrick-v4';app.mkdir()
        paths=[install.MAIN,*install.ADAPTERS,'_vendor/numpy/__init__.py','config.example.json']
        for name in paths:
            path=app/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'fixture '+name.encode())
        (app/'config.example.json').write_text('{"capture":"auto","playback":"auto","latency_us":24000}')
        hashes={'grainbrick-v4/'+p:install.digest(app/p) for p in paths}
        (app/'RELEASE.json').write_text(json.dumps({'kind':'standalone','sha256':hashes,'immutable_paths':list(hashes)}))
        return app
    def test_first_launch_needs_no_old_folders_or_downloads(self):
        with tempfile.TemporaryDirectory() as root:
            app=self.fixture(root)
            with patch.object(install,'EXPECTED_MAIN',install.digest(app/install.MAIN)):
                install.prepare(app)
                self.assertEqual(json.loads((app/'config.json').read_text())['capture'],'auto')
                self.assertTrue((app/'recordings').is_dir())
                self.assertEqual([p.name for p in Path(root).iterdir()],['grainbrick-v4'])
                (app/'recordings/new.wav').write_bytes(b'new audio')
                (app/'config.json').write_text('{"capture":"manual-in","playback":"manual-out","latency_us":24000}')
                install.prepare(app)
                self.assertEqual((app/'recordings/new.wav').read_bytes(),b'new audio')
                self.assertEqual(install.device_config(app/'config.json')['capture'],'manual-in')
    def test_integrity_failure_is_detected(self):
        with tempfile.TemporaryDirectory() as root:
            app=self.fixture(root);(app/'gb_audio.py').write_text('changed')
            with patch.object(install,'EXPECTED_MAIN',install.digest(app/install.MAIN)):
                with self.assertRaisesRegex(RuntimeError,'gb_audio.py'):install.prepare(app)
    def test_non_standalone_package_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            app=self.fixture(root);(app/'RELEASE.json').write_text('{"version":"1.1"}')
            with self.assertRaisesRegex(RuntimeError,'complete standalone'):install.prepare(app)
    def card(self,asound,identifier='Series'):
        asound.mkdir();(asound/'cards').write_text(' 1 [HDMI           ]: H3 Audio - Internal HDMI\n 3 [Series         ]: USB-Audio - TASCAM DR Series\n')
        card=asound/'card3';card.mkdir();(card/'usbid').write_text('0644:8047');(card/'id').write_text(identifier)
        for name in ('pcm0c','pcm0p'):(card/name).mkdir()
    def test_auto_selects_usb_duplex_card_and_keeps_config_portable(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);asound=root/'asound';self.card(asound)
            path=root/'config.json';path.write_text('{"capture":"auto","playback":"auto"}')
            result=install.device_config(path,asound)
            self.assertEqual(result,dict(capture='plughw:CARD=Series,DEV=0',playback='plughw:CARD=Series,DEV=0',latency_us=24000))
            self.assertEqual(json.loads(path.read_text())['capture'],'auto')
    def test_no_usb_does_not_prevent_sample_or_orbix_startup(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);path=root/'config.json';path.write_text('{"capture":"auto","playback":"auto"}')
            result=install.device_config(path,root/'no-asound')
            self.assertEqual(result['capture'],install.NO_USB)
            self.assertEqual(result['playback'],install.NO_USB)
    def test_unsafe_card_identifier_uses_numeric_alsa_device(self):
        with tempfile.TemporaryDirectory() as root:
            asound=Path(root)/'asound';self.card(asound,'Device With Spaces')
            self.assertEqual(install.usb_devices(asound),('plughw:3,0','plughw:3,0'))
    def test_invalid_configuration_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'config.json'
            for data in ([],{},dict(capture='in',playback='out',latency_us=True)):
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):install.device_config(path)

if __name__=='__main__':unittest.main()
