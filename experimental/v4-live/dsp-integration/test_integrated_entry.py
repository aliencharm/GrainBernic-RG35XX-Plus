import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import integrated_entry as entry

class PreparationTests(unittest.TestCase):
    def test_isolated_copy_and_relaunch_preserve_user_files(self):
        with tempfile.TemporaryDirectory() as root:
            source=Path(root)/'grainbrick-beta';source.mkdir()
            target=Path(root)/'grainbrick-v4-integrated'
            library=source/'main.cpython-312-aarch64-linux-gnu.so';library.write_bytes(b'test fixture')
            (source/'gb_launch.py').write_text('# fixture')
            (source/'settings.json').write_text('{}')
            (source/'sound_state.json').write_text('{"user":true}')
            for name in ('samples','recordings','projects','demo-samples'):(source/name).mkdir()
            (source/'samples/private.wav').write_bytes(b'private audio')
            (source/'demo-samples/demo.wav').write_bytes(b'demo')
            before={str(p.relative_to(source)):p.read_bytes() for p in source.rglob('*') if p.is_file()}
            with patch.object(entry,'EXPECTED_MAIN',hashlib.sha256(library.read_bytes()).hexdigest()):
                entry.prepare_original(source,target)
                self.assertFalse((target/'samples/private.wav').exists())
                self.assertFalse((target/'sound_state.json').exists())
                self.assertEqual((target/'samples/demo.wav').read_bytes(),b'demo')
                (target/'recordings/new.wav').write_bytes(b'new recording')
                entry.prepare_original(source,target)
                self.assertEqual((target/'recordings/new.wav').read_bytes(),b'new recording')
                other=Path(root)/'unknown';other.mkdir()
                with self.assertRaises(RuntimeError):entry.prepare_original(source,other)
            after={str(p.relative_to(source)):p.read_bytes() for p in source.rglob('*') if p.is_file()}
            self.assertEqual(before,after)
            with self.assertRaises(RuntimeError):entry.prepare_original(source,Path(root)/'wrong')
    def test_device_config_rejects_invalid_values(self):
        with tempfile.TemporaryDirectory() as root:
            control=Path(root)
            for invalid in ([],{},dict(capture='x',playback='y',latency_us=True),dict(capture='x',playback='y',latency_us=1)):
                (control/'config.json').write_text(json.dumps(invalid))
                with self.assertRaises(ValueError):entry.load_device_config(control)
            (control/'config.json').write_text(json.dumps(dict(capture='capture',playback='playback')))
            self.assertEqual(entry.load_device_config(control)['latency_us'],24000)

if __name__=='__main__':unittest.main()
