import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import v4_install as install

class CleanSetupTests(unittest.TestCase):
    def fixture(self,root):
        ports=Path(root);target=ports/'grainbrick-v4';target.mkdir()
        source=ports/'grainbrick-beta';source.mkdir()
        (source/install.MAIN).write_bytes(b'original fixture')
        for name in install.ADAPTERS:(source/name).write_text('# adapter')
        for name in ('_vendor/numpy','resources','demo-samples','samples','recordings','projects'):(source/name).mkdir(parents=True)
        (source/'_vendor/numpy/__init__.py').write_text('# numpy')
        demo=source/'demo-samples/demo.wav';demo.write_bytes(b'original demo')
        (source/'demo-samples/personal.wav').write_bytes(b'not factory')
        for name in ('samples/private.wav','recordings/private.wav','projects/private.json'):(source/name).write_bytes(b'private')
        (target/'factory-content.json').write_text(json.dumps({'demo-samples/demo.wav':install.digest(demo)}))
        (target/'factory-preset.json').write_text('{"sample":{"path":"samples/demo.wav","type":"relative"}}')
        (target/'config.json').write_text('{"capture":"in","playback":"out"}')
        (source/'gb_buttons.json').write_text('{"version":1}')
        return ports,target,source
    def test_only_original_demos_and_preset_are_added(self):
        with tempfile.TemporaryDirectory() as root:
            ports,target,source=self.fixture(root)
            before={str(p.relative_to(source)):p.read_bytes() for p in source.rglob('*') if p.is_file()}
            with patch.object(install,'EXPECTED_MAIN',install.digest(source/install.MAIN)):
                result=install.prepare(target)
                self.assertFalse(result['user_media_imported'])
                self.assertEqual([p.name for p in (target/'samples').iterdir()],['demo.wav'])
                self.assertEqual(list((target/'recordings').iterdir()),[])
                self.assertEqual([p.name for p in (target/'projects').iterdir()],['AMBIENT.json'])
                self.assertFalse((target/'demo-samples/personal.wav').exists())
                self.assertTrue((target/'gb_buttons.json').is_file())
                self.assertEqual(before,{str(p.relative_to(source)):p.read_bytes() for p in source.rglob('*') if p.is_file()})
                shutil.rmtree(source)
                (target/'recordings/new.wav').write_bytes(b'new V4 recording')
                self.assertEqual(install.prepare(target),result)
                self.assertEqual((target/'recordings/new.wav').read_bytes(),b'new V4 recording')
    def test_old_import_install_requires_backup_without_deleting_data(self):
        with tempfile.TemporaryDirectory() as root:
            _,target,_=self.fixture(root)
            (target/install.MARKER).write_text('{"version":"1.0"}')
            (target/'recordings').mkdir();private=target/'recordings/keep.wav';private.write_bytes(b'keep')
            with self.assertRaisesRegex(RuntimeError,'Back up'):install.prepare(target)
            self.assertEqual(private.read_bytes(),b'keep')
    def test_modified_factory_demo_is_not_imported(self):
        with tempfile.TemporaryDirectory() as root:
            _,target,source=self.fixture(root)
            (source/'demo-samples/demo.wav').write_bytes(b'modified')
            with patch.object(install,'EXPECTED_MAIN',install.digest(source/install.MAIN)):
                with self.assertRaisesRegex(RuntimeError,'demo file missing or changed'):install.prepare(target)
            self.assertFalse((target/install.MAIN).exists())
    def test_interrupted_setup_can_retry_without_importing_media(self):
        with tempfile.TemporaryDirectory() as root:
            _,target,source=self.fixture(root)
            original=install.write_json
            def interrupted(path,data):
                if path.name==install.MARKER:raise OSError('simulated interruption')
                original(path,data)
            with patch.object(install,'EXPECTED_MAIN',install.digest(source/install.MAIN)):
                with patch.object(install,'write_json',interrupted):
                    with self.assertRaises(OSError):install.prepare(target)
                self.assertTrue((target/'.v4-clean-setup-pending').exists())
                install.prepare(target)
                self.assertEqual([p.name for p in (target/'samples').iterdir()],['demo.wav'])
                self.assertFalse((target/'.v4-clean-setup-pending').exists())
    def test_previous_final_folder_can_supply_engine_and_device_config(self):
        with tempfile.TemporaryDirectory() as root:
            ports,target,source=self.fixture(root)
            source.rename(ports/'grainbrick-v4-previous');source=ports/'grainbrick-v4-previous'
            (target/'config.json').replace(source/'config.json')
            with patch.object(install,'EXPECTED_MAIN',install.digest(source/install.MAIN)):
                install.prepare(target)
            self.assertEqual(install.device_config(target/'config.json')['capture'],'in')
            self.assertEqual([p.name for p in (target/'samples').iterdir()],['demo.wav'])
    def test_invalid_configuration_is_rejected_before_copy(self):
        with tempfile.TemporaryDirectory() as root:
            _,target,source=self.fixture(root)
            (target/'config.json').write_text('{}')
            with patch.object(install,'EXPECTED_MAIN',install.digest(source/install.MAIN)):
                with self.assertRaises(ValueError):install.prepare(target)
            self.assertFalse((target/install.MAIN).exists())

if __name__=='__main__':unittest.main()
