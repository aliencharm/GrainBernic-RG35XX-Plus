import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
from v4_live_recovery import RecoverySettings


class RecoverySettingsTests(unittest.TestCase):
    def setting(self,root):
        controller=types.SimpleNamespace(capture_factory=lambda:types.SimpleNamespace())
        return RecoverySettings(root,controller).install()
    def test_default_is_off_and_invalid_saved_values_do_not_enable_it(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'config.json'
            for data in ({},{'live_recovery_enabled':'ON'},{'live_recovery_enabled':1}):
                path.write_text(json.dumps(data));self.assertFalse(self.setting(root).enabled)
            path.write_text('{"live_recovery_enabled":true}');self.assertTrue(self.setting(root).enabled)
    def test_save_preserves_latest_routes_and_updates_an_existing_capture(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'config.json';path.write_text('{"capture":"auto","ui_theme":"SAGE"}')
            setting=self.setting(root);capture=setting.controller.capture_factory()
            self.assertFalse(capture.recovery_enabled.value)
            path.write_text('{"capture":"auto","ui_theme":"SPRUCE","input_route":"pair34"}')
            setting.set_enabled(True);self.assertTrue(capture.recovery_enabled.value)
            self.assertEqual(json.loads(path.read_text()),{'capture':'auto','ui_theme':'SPRUCE','input_route':'pair34','live_recovery_enabled':True})
            self.assertTrue(self.setting(root).enabled)
            setting.set_enabled(False);self.assertFalse(capture.recovery_enabled.value)
    def test_failed_save_leaves_current_setting_and_file_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'config.json';path.write_text('{}');setting=self.setting(root)
            with patch('v4_live_recovery.write_json',side_effect=OSError('full')):
                with self.assertRaises(OSError):setting.set_enabled(True)
            self.assertFalse(setting.enabled);self.assertEqual(path.read_text(),'{}')
