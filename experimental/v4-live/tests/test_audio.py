"""Run with host executable and optional fault shim directory as positional arguments."""
import os
from pathlib import Path
import subprocess
import sys
import time
exe=str(Path(sys.argv[1]).resolve())
fake=str(Path(sys.argv[2]).resolve()) if len(sys.argv)>2 else None

def run(cap,play,env=None,duration=.12):
 p=subprocess.Popen([exe,cap,play],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
 time.sleep(duration)
 if p.poll() is None:
  try: p.stdin.write('mix 0.7\ngrain 110\npitch 0.8\nquit\n'); p.stdin.flush()
  except BrokenPipeError: pass
 out,err=p.communicate(timeout=5)
 return p.returncode,err
code,log=run('null','null')
assert code==0 and 'READY' in log and 'EXIT status=0' in log,log
code,log=run('hw:CARD=V4_MISSING,DEV=0','null')
assert code==1 and 'FATAL capture open' in log,log
print('PASS ALSA null duplex and missing-device failure')
if fake:
 for fault in ['partial','xrun','write-xrun','disconnect','rate','timeout']:
  env=dict(os.environ,LD_LIBRARY_PATH=fake,V4_TEST_FAULT=fault)
  code,log=run('fake','fake',env,2.2 if fault=='timeout' else .12)
  expected=1 if fault in ('disconnect','rate','timeout') else 0
  assert code==expected,(fault,code,log)
  if 'xrun' in fault: assert 'recovery=1' in log,log
  if fault=='rate': assert 'negotiated format differs' in log,log
  if fault=='timeout': assert 'AUDIO_ERROR' in log,log
  print('PASS injected',fault)
