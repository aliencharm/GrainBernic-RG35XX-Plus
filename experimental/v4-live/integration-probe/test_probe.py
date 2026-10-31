import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
SCRIPT=Path(__file__).with_name('inspect_v3.py')
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
if __name__=='__main__': unittest.main()
