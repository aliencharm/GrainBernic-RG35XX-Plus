import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import v4_install as install

class MigrationTests(unittest.TestCase):
    def fixture(self,ports,label):
        source=ports/label;source.mkdir()
        (source/install.MAIN).write_bytes(b'original native fixture')
        for name in install.ADAPTERS:(source/name).write_text('# '+name)
        (source/'libgrainbrick_fx.so').write_bytes(b'library fixture')
        for name in ('samples','recordings','projects','resources','_vendor/numpy'):(source/name).mkdir(parents=True,exist_ok=True)
        (source/'_vendor/numpy/__init__.py').write_text('# bundled')
        return source
    def snapshot(self,source):return {str(p.relative_to(source)):p.read_bytes() for p in source.rglob('*') if p.is_file()}
    def test_preserves_both_libraries_settings_projects_and_sources(self):
        with tempfile.TemporaryDirectory() as root:
            ports=Path(root);target=ports/'grainbrick-v4';target.mkdir()
            (target/'v4_entry.py').write_text('# final entry')
            v3=self.fixture(ports,'grainbrick-beta');live=self.fixture(ports,'grainbrick-v4-integrated')
            control=ports/'grainbrick-v4-live';control.mkdir()
            config=dict(capture='plughw:CARD=Series,DEV=0',playback='plughw:CARD=Series,DEV=0',latency_us=24000)
            (control/'config.json').write_text(json.dumps(config))
            for source,value in ((live,b'LIVE audio'),(v3,b'V3 audio')):
                (source/'samples/same.wav').write_bytes(value)
                (source/'recordings/keep.wav').write_bytes(value+b' raw')
                project={'sample':{'path':'samples/same.wav','type':'relative'},'parameters':{'grain.pitch':0}}
                (source/'projects/Preset.json').write_text(json.dumps(project))
                (source/'gb_buttons.json').write_text(json.dumps({'source':source.name}))
            (v3/'projects/Absolute.json').write_text(json.dumps({'sample':{'path':str(v3/'samples/same.wav'),'type':'absolute'}}))
            (live/'sound_state.json').write_text('{"live.fx_mix":0.3,"live.tape_mix":0.7}')
            (v3/'settings.json').write_text(json.dumps({'theme':'original','browser_dir':str(v3/'samples')}))
            before={str(p):self.snapshot(p) for p in (live,v3,control)}
            with patch.object(install,'EXPECTED_MAIN',hashlib.sha256((live/install.MAIN).read_bytes()).hexdigest()):
                report=install.migrate(target)
                self.assertTrue(report['ready_for_cleanup'])
                self.assertEqual((target/'samples/same.wav').read_bytes(),b'LIVE audio')
                self.assertEqual((target/'samples/same [V3].wav').read_bytes(),b'V3 audio')
                self.assertEqual(json.loads((target/'projects/Preset.json').read_text())['sample']['path'],'samples/same.wav')
                self.assertEqual(json.loads((target/'projects/Preset [V3].json').read_text())['sample']['path'],'samples/same [V3].wav')
                self.assertEqual(json.loads((target/'projects/Absolute.json').read_text())['sample']['path'],str(target/'samples/same [V3].wav'))
                self.assertEqual(json.loads((target/'gb_buttons.json').read_text())['source'],live.name)
                self.assertTrue((target/'migration-backups/V3/gb_buttons.json').is_file())
                self.assertEqual(install.device_config(target/'config.json'),config)
                self.assertEqual(json.loads((target/'settings.json').read_text())['browser_dir'],str(target/'samples'))
                self.assertEqual(json.loads((target/'sound_state.json').read_text())['live.fx_mix'],.3)
                self.assertEqual(before,{str(p):self.snapshot(p) for p in (live,v3,control)})
                # The completed app no longer depends on any old folders.
                import shutil
                for source in (live,v3,control):shutil.rmtree(source)
                (target/'samples/new.wav').write_bytes(b'new V4 recording')
                self.assertEqual(install.migrate(target),report)
                self.assertEqual((target/'samples/new.wav').read_bytes(),b'new V4 recording')
    def test_unknown_reference_blocks_cleanup_but_preserves_project(self):
        with tempfile.TemporaryDirectory() as root:
            ports=Path(root);target=ports/'grainbrick-v4';target.mkdir()
            source=self.fixture(ports,'grainbrick-beta')
            (target/'config.json').write_text('{"capture":"in","playback":"out"}')
            missing=str(source/'samples/missing.wav')
            (source/'projects/External.json').write_text(json.dumps({'sample':{'path':missing,'type':'absolute'}}))
            with patch.object(install,'EXPECTED_MAIN',install.digest(source/install.MAIN)):
                report=install.migrate(target)
            self.assertFalse(report['ready_for_cleanup']);self.assertIn(missing,report['external_references'])
            self.assertEqual(json.loads((target/'projects/External.json').read_text())['sample']['path'],missing)
    def test_wrong_engine_and_invalid_config_fail_before_copy(self):
        with tempfile.TemporaryDirectory() as root:
            ports=Path(root);target=ports/'grainbrick-v4';target.mkdir()
            source=self.fixture(ports,'grainbrick-beta')
            with self.assertRaises(RuntimeError):install.migrate(target)
            self.assertFalse((target/install.MAIN).exists())
            with patch.object(install,'EXPECTED_MAIN',install.digest(source/install.MAIN)):
                (target/'config.json').write_text('{"capture":"in"}')
                with self.assertRaises(ValueError):install.migrate(target)
            self.assertFalse((target/install.MAIN).exists())
    def test_restart_after_incomplete_migration_keeps_new_files(self):
        with tempfile.TemporaryDirectory() as root:
            ports=Path(root);target=ports/'grainbrick-v4';target.mkdir()
            source=self.fixture(ports,'grainbrick-beta')
            (target/'config.json').write_text('{"capture":"in","playback":"out"}')
            (source/'samples/a.wav').write_bytes(b'original')
            (target/'samples').mkdir();(target/'samples/a.wav').write_bytes(b'already here')
            with patch.object(install,'EXPECTED_MAIN',install.digest(source/install.MAIN)):
                install.migrate(target)
                (target/install.MARKER).unlink()  # Simulate interrupted final marker write.
                install.migrate(target)
            self.assertEqual((target/'samples/a.wav').read_bytes(),b'already here')
            self.assertEqual((target/'samples/a [V3].wav').read_bytes(),b'original')
            self.assertEqual(len(list((target/'samples').glob('*.wav'))),2)

if __name__=='__main__':unittest.main()
