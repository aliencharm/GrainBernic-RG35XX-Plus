import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
MODULE=Path(__file__).resolve().with_name('native_ui.py')
spec=importlib.util.spec_from_file_location('native_ui_under_test',MODULE)
n=importlib.util.module_from_spec(spec); spec.loader.exec_module(n)
ENGINE=Path(os.environ.get('V4_TEST_ENGINE',str(MODULE.parent.parent/'build/v4-live'))).resolve()
class PolicyTests(unittest.TestCase):
 def test_read_allowed_write_blocked_after_bootstrap(self):
  p=n.BootstrapPolicy(Path('/tmp/v3'),Path('/tmp/v4/v4-live')); p.loading=False
  p.audit('open',('/tmp/v3/settings.json','r',0))
  p.audit('open',('/tmp/v4/log.txt','a',0))
  with self.assertRaises(PermissionError):p.audit('open',('/tmp/v3/settings.json','w',0))
  with self.assertRaises(PermissionError):p.audit('os.rename',('/tmp/v4/file','/tmp/v3/file',-1,-1))
 def test_bootstrap_blocks_writes_and_processes(self):
  p=n.BootstrapPolicy(Path('/tmp/v3'),Path('/tmp/v4/v4-live'))
  with self.assertRaises(n.BootstrapStop):p.audit('open',('/tmp/new','w',0))
  with self.assertRaises(n.BootstrapStop):p.audit('subprocess.Popen',('/bin/true',['true'],None,None))
 def test_only_v4_child_is_allowed(self):
  p=n.BootstrapPolicy(Path('/tmp/v3'),Path('/tmp/v4/v4-live')); p.loading=False
  p.audit('subprocess.Popen',('/tmp/v4/v4-live',[],None,None))
  with self.assertRaises(PermissionError):p.audit('subprocess.Popen',('/usr/bin/aplay',[],None,None))
  with self.assertRaises(PermissionError):p.audit('ctypes.dlopen',('libasound.so.2',))
 def test_guarded_loader_captures_classes_without_finishing_main(self):
  with tempfile.TemporaryDirectory() as d:
   v3=Path(d)/'v3';v3.mkdir()
   (v3/'main.py').write_text("import sys,types,os\nsys.modules['ui.renderer']=types.ModuleType('ui.renderer')\nsys.modules['engine.parameters']=types.ModuleType('engine.parameters')\nos.mkdir('must-not-be-created')\nraise RuntimeError('main resumed')\n")
   code="""import sys,types,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import native_ui
fn=lambda *a,**k:None
pg=types.SimpleNamespace(init=fn,display=types.SimpleNamespace(init=fn,set_mode=fn),mixer=types.SimpleNamespace(init=fn),joystick=types.SimpleNamespace(init=fn))
v3=Path(sys.argv[2]); engine=Path(sys.argv[3])
classes,policy=native_ui.load_classes(v3,engine,pg,allow_fixture=True)
assert classes['ui.renderer'] is not None and not policy.loading
try:
 (v3/'settings.json').write_text('bad')
 raise AssertionError('V3 write was allowed')
except PermissionError: pass
try:
 pg.mixer.init()
 raise AssertionError('mixer was allowed')
except RuntimeError: pass
import subprocess
r=subprocess.run([str(engine),'--version'],capture_output=True,text=True)
assert r.returncode==0
print('PASS loaded modules, V3 protected, mixer blocked, only own audio child started')
"""
   r=subprocess.run([sys.executable,'-B','-c',code,str(MODULE.parent),str(v3),str(ENGINE)],capture_output=True,text=True,cwd=d,timeout=10)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertFalse((Path(d)/'must-not-be-created').exists())
   self.assertFalse((v3/'settings.json').exists())
class FrontendFailureTests(unittest.TestCase):
 def frontend(self):
  file=MODULE.parent.parent/'package/grainbrick-v4-live/frontend.py'
  spec=importlib.util.spec_from_file_location('frontend_failure_test',file)
  f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f);return f
 def test_shared_lock_refuses_a_second_frontend(self):
  import fcntl
  with tempfile.TemporaryDirectory() as d:
   f=self.frontend();f.ROOT=Path(d)
   with (f.ROOT/'.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with self.assertRaisesRegex(SystemExit,'already running'):f.main()
 @unittest.skipUnless(importlib.util.find_spec('pygame'),'Pygame needed for startup failure cleanup')
 def test_renderer_startup_failure_closes_display_and_starts_no_audio(self):
  os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
  import pygame as pg
  with tempfile.TemporaryDirectory() as d:
   f=self.frontend();f.ROOT=Path(d)
   def bad_renderer(root,pg):raise RuntimeError('fixture renderer unavailable')
   with self.assertRaisesRegex(RuntimeError,'fixture renderer unavailable'):f.main(renderer_factory=bad_renderer)
   self.assertFalse(pg.display.get_init())
   self.assertFalse((f.ROOT/'v4-audio.log').exists())
if __name__=='__main__':unittest.main()
