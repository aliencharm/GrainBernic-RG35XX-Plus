import fcntl
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from import_user_data import import_data

class ImportTests(unittest.TestCase):
    def fixture(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        root=Path(temp.name);old=root/'grainbrick-v4-backup';new=root/'grainbrick-v4'
        old.mkdir();new.mkdir()
        (new/'projects').mkdir();(new/'projects/AMBIENT.json').write_text('{"factory":true}')
        original=hashlib.sha256((new/'projects/AMBIENT.json').read_bytes()).hexdigest()
        (new/'RELEASE.json').write_text(json.dumps(dict(kind='standalone',version='4.2',sha256={'grainbrick-v4/projects/AMBIENT.json':original})))
        for name,content in {'samples/custom.wav':b'sample','samples/recordings/held.wav':b'freeze','recordings/dry.wav':b'rec','projects/AMBIENT.json':b'{"personal":true}', 'projects/mine.json':b'{}','config.json':b'{"ui_theme":"SPRUCE"}','sound_state.json':b'{}','v4.log':b'old log','old_runtime.py':b'old code','GrainBrick_USB_Report.txt':b'old report'}.items():
            path=old/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
        return root,old,new
    def test_imports_personal_media_projects_preferences_without_old_code_or_logs(self):
        root,old,new=self.fixture()
        self.assertIn('IMPORT COMPLETE',import_data(root))
        for name in ('samples/custom.wav','samples/recordings/held.wav','recordings/dry.wav','projects/AMBIENT.json','projects/mine.json','config.json','sound_state.json'):
            self.assertEqual((new/name).read_bytes(),(old/name).read_bytes())
        for name in ('v4.log','old_runtime.py','GrainBrick_USB_Report.txt'):self.assertFalse((new/name).exists())
        (new/'config.json').write_text('{"new_setting":true}')
        self.assertIn('ALREADY IMPORTED',import_data(root))
        self.assertEqual((new/'config.json').read_text(),'{"new_setting":true}')
        self.assertTrue((old/'samples/custom.wav').exists())
    def test_conflicting_new_personal_file_aborts_before_import(self):
        root,old,new=self.fixture();(new/'samples').mkdir();(new/'samples/custom.wav').write_bytes(b'new recording')
        with self.assertRaisesRegex(RuntimeError,'conflicts'):import_data(root)
        self.assertEqual((new/'samples/custom.wav').read_bytes(),b'new recording')
        self.assertFalse((new/'config.json').exists())
    def test_running_app_and_invalid_preferences_block_import(self):
        root,old,new=self.fixture()
        with (old/'.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaisesRegex(RuntimeError,'Close GrainBrick'):import_data(root)
        (old/'config.json').write_text('damaged')
        with self.assertRaises(json.JSONDecodeError):import_data(root)
        self.assertFalse((new/'samples/custom.wav').exists())
    def test_media_symlinks_are_skipped(self):
        root,old,new=self.fixture();outside=root/'private.wav';outside.write_bytes(b'outside')
        (old/'samples/link.wav').symlink_to(outside)
        self.assertIn('IMPORT COMPLETE',import_data(root))
        self.assertFalse((new/'samples/link.wav').exists());self.assertEqual(outside.read_bytes(),b'outside')
