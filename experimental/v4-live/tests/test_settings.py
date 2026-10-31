import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('settings_frontend',Path(__file__).resolve().parents[1]/'package/grainbrick-v4-live/frontend.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
class SettingsTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=f.ROOT;f.ROOT=Path(self.tmp.name)
 def tearDown(self):f.ROOT=self.old;self.tmp.cleanup()
 def write(self,data): (f.ROOT/'live-settings.json').write_text(json.dumps(data))
 def test_missing_file_defaults_and_no_write(self):
  self.assertEqual(f.load_settings(),f.DEFAULTS)
  self.assertFalse((f.ROOT/'live-settings.json').exists())
 def test_roundtrip_excludes_mix_gain_and_other_configuration(self):
  params={**f.DEFAULTS,'grain':130.,'delay':220.,'pitch':.55,'scatter':90.,'mix':1.,'gain':.9}
  (f.ROOT/'config.json').write_text('device config');(f.ROOT/'buttons.json').write_text('calibration')
  f.save_settings(params)
  data=json.loads((f.ROOT/'live-settings.json').read_text())
  self.assertEqual(set(data['parameters']),set(f.PERSISTED_KEYS))
  loaded=f.load_settings()
  self.assertEqual(f.persistent_values(loaded),f.persistent_values(params))
  self.assertEqual(loaded['mix'],0.);self.assertEqual(loaded['gain'],.5)
  self.assertEqual((f.ROOT/'config.json').read_text(),'device config')
  self.assertEqual((f.ROOT/'buttons.json').read_text(),'calibration')
 def test_invalid_values_default_individually(self):
  for bad in [True,'80',[],{},float('nan'),float('inf'),-1,100000,10**400]:
   self.write({'version':1,'parameters':{'grain':bad,'delay':40,'pitch':.75,'scatter':15,'mix':1,'gain':1}})
   loaded=f.load_settings();self.assertEqual(loaded['grain'],20.)
   self.assertEqual(loaded['pitch'],.75);self.assertEqual(loaded['delay'],40.)
   self.assertEqual(loaded['mix'],0.);self.assertEqual(loaded['gain'],.5)
 def test_broken_or_unknown_schema_is_not_rewritten_on_read(self):
  for text in ['{broken','[]','{"version":2,"parameters":{}}','{"version":true,"parameters":{}}','{"version":1,"parameters":[]}']:
   path=f.ROOT/'live-settings.json';path.write_text(text)
   self.assertEqual(f.load_settings(),f.DEFAULTS)
   self.assertEqual(path.read_text(),text)
 def test_replace_failure_preserves_old_file_and_cleans_temporary(self):
  f.save_settings(f.DEFAULTS);path=f.ROOT/'live-settings.json';old=path.read_bytes()
  with patch.object(f.os,'replace',side_effect=OSError('fixture disk failure')):
   with self.assertRaises(OSError):f.save_settings({**f.DEFAULTS,'pitch':.75})
  self.assertEqual(path.read_bytes(),old)
  self.assertEqual(list(f.ROOT.glob('.live-settings-*.tmp')),[])
 def test_save_rejects_nonfinite_or_out_of_range(self):
  for bad in [True,float('nan'),float('inf'),3.,10**400]:
   with self.assertRaises(ValueError):f.save_settings({**f.DEFAULTS,'pitch':bad})
  self.assertFalse((f.ROOT/'live-settings.json').exists())
 def test_start_preserves_tone_controls_resets_mix_gain(self):
  p={**f.DEFAULTS,'grain':60.,'delay':40.,'pitch':.75,'scatter':15.,'mix':1.,'gain':.9}
  started=f.start_values(p)
  self.assertEqual(f.persistent_values(started),f.persistent_values(p))
  self.assertEqual(started['mix'],0.);self.assertEqual(started['gain'],.5)
  child=type('Child',(),{'stdin':io.StringIO()})()
  f.send_start_settings(child,started)
  self.assertEqual(child.stdin.getvalue(),'grain 60.0\ndelay 40.0\npitch 0.75\nscatter 15.0\n')
if __name__=='__main__':unittest.main()
