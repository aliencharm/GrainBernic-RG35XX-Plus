"""End-to-end renderer contract + real host V4 process using ALSA null."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
import types
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame as pg
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('native_screen',HERE/'native_ui.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
spec=importlib.util.spec_from_file_location('frontend',HERE.parent/'package/grainbrick-v4-live/frontend.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
class Bus:
 def __init__(self):self.values={}
 def add(self,key,value,*args):self.values[key]=value
 def set(self,key,value):self.values[key]=value
 def get(self,key):return self.values[key]
class FixtureUI:
 knobs=0; tabs=0
 def __init__(self,sample=None):
  self.refresh_audio_outputs()  # Must be stubbed, as for the real renderer.
  self.screen=pg.display.set_mode((1024,768));self.font=pg.font.Font(None,22)
 def refresh_audio_outputs(self):raise AssertionError('Device discovery must not run')
 def text(self,text,x,y,scale=2,color=None):
  font=pg.font.Font(None,scale*8)
  self.screen.blit(font.render(text,True,color or (220,220,220)),(x,y))
 def draw_tabs(self,c):
  assert c.TABS==['LIVE'] and c.current_tab=='LIVE'
  type(self).tabs+=1;self.text('LIVE',45,40,3,(224,148,58))
 def _draw_comp_knob(self,x,y,r,value,selected):
  assert 0<=value<=1
  type(self).knobs+=1
  pg.draw.circle(self.screen,(224,148,58) if selected else (90,110,100),(x,y),r,3)
 def close(self):raise AssertionError('Original settings-writing close must not run')
classes={'ui.renderer':types.SimpleNamespace(UIEngine=FixtureUI),'engine.parameters':types.SimpleNamespace(ParameterBus=Bus)}
with tempfile.TemporaryDirectory() as d:
 f.ROOT=Path(d);shutil.copy2(sys.argv[1],f.ROOT/'v4-live')
 (f.ROOT/'config.json').write_text(json.dumps({'capture':'null','playback':'null'}))
 engines=[]
 def factory(root,pg):
  r=native.NativeRenderer(root,pg,classes,install_scaling=False);engines.append(r);return r
 def key(k):pg.event.post(pg.event.Event(pg.KEYDOWN,key=k))
 def interact():
  for _ in range(100):
   if engines:break
   time.sleep(.01)
  time.sleep(.1);key(pg.K_RETURN)
  time.sleep(.2);key(pg.K_RIGHT)
  time.sleep(.1);key(pg.K_UP)
  time.sleep(.1);key(pg.K_RIGHT)
  time.sleep(2.2)
  if len(sys.argv)>2:pg.image.save(engines[0].screen,sys.argv[2])
  key(pg.K_b);time.sleep(.2);key(pg.K_ESCAPE)
 thread=threading.Thread(target=interact,daemon=True);thread.start()
 f.main(renderer_factory=factory);thread.join(timeout=2)
 log=(f.ROOT/'v4-audio.log').read_text()
 assert 'STATS' in log and 'mix=0.05' in log and 'scatter_ms=5' in log and 'EXIT status=0' in log,log
 assert FixtureUI.knobs>=6 and FixtureUI.tabs>0
 print('PASS LIVE tabs/knobs, live wet/scatter commands, real ALSA-null child, stop/exit, original close avoided')
