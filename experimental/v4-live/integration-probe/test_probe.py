import json
import importlib.util
import types
import os
import base64
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
SCRIPT=Path(__file__).with_name('inspect_v3.py')
spec=importlib.util.spec_from_file_location('probe',SCRIPT)
probe=importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
PREFIX='''import sys,types
m=types.ModuleType('engine.parameters')
exec('class ParameterBus:\\n def get(self, key, default=None): pass\\n',m.__dict__)
sys.modules['engine.parameters']=m
'''
class ProbeTests(unittest.TestCase):
 def run_fixture(self,tail):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); app=root/'v3'; app.mkdir(); report=root/'report.json'
   (app/'main.py').write_text(PREFIX+tail)
   r=subprocess.run([sys.executable,'-B',str(SCRIPT),'--test-python-fixture','--v3',str(app),'--output',str(report)],capture_output=True,text=True,timeout=10)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   data=json.loads(report.read_text())
   methods=data['modules']['engine.parameters']['classes']['ParameterBus']['methods']
   self.assertEqual(methods['get']['arguments'],['self','key','default'])
   self.assertEqual(methods['get']['defaults'],[None])
   self.assertFalse((app/'should-not-exist').exists())
   self.assertFalse((app/'__pycache__').exists())
   return data
 def test_import_metadata(self):
  self.assertEqual(self.run_fixture('')['status'],'import_returned_without_startup')
 def test_file_write_is_blocked(self):
  data=self.run_fixture("from pathlib import Path\nPath(__file__).with_name('should-not-exist').write_text('bad')\n")
  self.assertEqual(data['boundary'],'blocked Python file write')
 def test_process_is_blocked(self):
  data=self.run_fixture("import subprocess\nsubprocess.run(['false'])\n")
  self.assertEqual(data['boundary'],'blocked subprocess.Popen')
 def test_directory_write_is_blocked(self):
  data=self.run_fixture("from pathlib import Path\nPath(__file__).with_name('should-not-exist').mkdir()\n")
  self.assertEqual(data['boundary'],'blocked os.mkdir')
 def test_output_cannot_be_inside_v3(self):
  with tempfile.TemporaryDirectory() as d:
   r=subprocess.run([sys.executable,str(SCRIPT),'--test-python-fixture','--v3',d,'--output',str(Path(d)/'report.json')],capture_output=True,text=True)
   self.assertEqual(r.returncode,2)
   self.assertFalse((Path(d)/'report.json').exists())
class CompatibilityTests(unittest.TestCase):
 def modules(self):
  class Parameter:
   def __init__(self,value): self.value=value
   def set(self,value): self.value=value
  class ParameterBus:
   def __init__(self): self.values={}
   def add(self,key,value,lo,hi): self.values[key]=Parameter(value)
   def get(self,key): return self.values[key].value
   def set(self,key,value): self.values[key].set(value)
  class UI:
   def draw(self,*args): return 'original'
  parameter=types.SimpleNamespace(Parameter=Parameter,ParameterBus=ParameterBus)
  return {'engine.parameters':parameter,'ui.renderer':types.SimpleNamespace(UIEngine=UI),'main':types.SimpleNamespace(UIEngine=UI)}
 def test_dispatch_and_restore(self):
  m=self.modules(); ui=m['ui.renderer'].UIEngine; parameter=m['engine.parameters'].Parameter
  draw=ui.draw; setter=parameter.set
  r=probe.compatibility_checks(m)
  self.assertEqual(r['parameter_method_dispatch']['status'],'passed')
  self.assertEqual(r['renderer_class_replacement']['status'],'passed')
  self.assertIs(ui.draw,draw); self.assertIs(parameter.set,setter)
 @unittest.skipUnless(importlib.util.find_spec('pygame'),'Pygame is needed for dummy graphics fixture')
 def test_offscreen_render_fixture(self):
  os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
  import pygame as pg
  pg.display.init(); pg.font.init()
  m=self.modules()
  m['engine.parameters'].create_default_parameters=lambda: object()
  class Controls:
   current_tab='GRAIN'
   def __init__(self,parameters): pass
  m['engine.control']=types.SimpleNamespace(ControlManager=Controls)
  ui=m['ui.renderer'].UIEngine
  def initialize(self,sample=None): self.screen=pg.display.set_mode((640,480))
  ui.__init__=initialize
  ui.refresh_audio_outputs=lambda self: None
  ui.draw_tabs=lambda self,c:self.screen.fill((40,80,120))
  ui.draw_placeholder=lambda self,c:pg.draw.rect(self.screen,(200,150,100),(30,30,80,80))
  original=ui.refresh_audio_outputs
  try:
   r=probe.compatibility_checks(m,pg)['offscreen_original_renderer']
   self.assertEqual(r['status'],'passed')
   self.assertEqual(r['details']['size'],[640,480])
   self.assertTrue(base64.b64decode(r['details']['png_base64']).startswith(b'\x89PNG'))
   self.assertIs(ui.refresh_audio_outputs,original)
  finally: pg.quit()
 def test_missing_main_alias_is_reported(self):
  m=self.modules(); m['main']=None
  r=probe.compatibility_checks(m)
  self.assertEqual(r['renderer_class_replacement']['status'],'failed')
 def test_no_unverified_success_for_empty_modules(self):
  r=probe.compatibility_checks({})
  self.assertTrue(all(v['status']=='failed' for v in r.values()))
if __name__=='__main__': unittest.main()
