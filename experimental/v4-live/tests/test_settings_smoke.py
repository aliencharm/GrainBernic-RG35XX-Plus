"""Real host engine test: edits before A, dry startup, stop/save, relaunch/restore."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame as pg
spec=importlib.util.spec_from_file_location('frontend_persistence_smoke',Path(__file__).resolve().parents[1]/'package/grainbrick-v4-live/frontend.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
expected={'grain':60.,'delay':40.,'pitch':.75,'scatter':15.}
with tempfile.TemporaryDirectory() as d:
 f.ROOT=Path(d);shutil.copy2(sys.argv[1],f.ROOT/'v4-live')
 (f.ROOT/'config.json').write_text(json.dumps({'capture':'null','playback':'null'}))
 errors=[];snapshots=[]
 class View:
  def __init__(self,root,pg):self.screen=pg.display.set_mode((640,480))
  def draw_header(self,playing):pass
  def draw_text(self,*args):pass
  def draw_footer(self,*args):pass
  def draw_parameters(self,params,selected):snapshots.append(params.copy())
  def close(self):pass
 def key(k,n=1):
  for _ in range(n):pg.event.post(pg.event.Event(pg.KEYDOWN,key=k))
 def run(interaction):
  snapshots.clear()
  def inject():
   try:
    for _ in range(200):
     if snapshots:break
     time.sleep(.01)
    assert snapshots,'UI never initialized'
    interaction()
   except BaseException as exc:
    errors.append(exc)
    if pg.display.get_init():key(pg.K_ESCAPE)
  t=threading.Thread(target=inject,daemon=True);t.start()
  f.main(renderer_factory=View);t.join(timeout=3)
  assert not errors,errors
 def first():
  key(pg.K_RIGHT) # Wet mix before A must be discarded for startup.
  key(pg.K_DOWN,2);key(pg.K_RIGHT,4) # Grain 60.
  key(pg.K_DOWN);key(pg.K_RIGHT,3) # Delay 40.
  key(pg.K_DOWN);key(pg.K_LEFT,5) # Pitch .75.
  key(pg.K_DOWN);key(pg.K_RIGHT,3) # Scatter 15.
  key(pg.K_RETURN)
  time.sleep(2.3)
  assert f.persistent_values(snapshots[-1])==expected,snapshots[-1]
  assert snapshots[-1]['mix']==0 and snapshots[-1]['gain']==.5
  assert not (f.ROOT/'live-settings.json').exists(),'Settings were written during streaming'
  key(pg.K_UP,5);key(pg.K_RIGHT,6) # Wet .30 while playing.
  time.sleep(2.1);key(pg.K_b)
  for _ in range(100):
   if (f.ROOT/'live-settings.json').exists():break
   time.sleep(.01)
  assert (f.ROOT/'live-settings.json').exists(),'B did not persist settings'
  key(pg.K_ESCAPE)
 run(first)
 data=json.loads((f.ROOT/'live-settings.json').read_text())
 assert data=={'version':1,'parameters':expected},data
 def second():
  assert f.persistent_values(snapshots[0])==expected,snapshots[0]
  key(pg.K_RIGHT,4) # Wet .20 before A.
  key(pg.K_DOWN);key(pg.K_RIGHT,6) # Gain .80 before A.
  key(pg.K_RETURN);time.sleep(2.3)
  assert f.persistent_values(snapshots[-1])==expected,snapshots[-1]
  assert snapshots[-1]['mix']==0 and snapshots[-1]['gain']==.5,snapshots[-1]
  key(pg.K_ESCAPE) # Exit directly while audio is active.
 run(second)
 sessions=(f.ROOT/'v4-audio.log').read_text().split('\nSTART ')[1:]
 assert len(sessions)==2
 assert all('EXIT status=0' in s for s in sessions)
 assert all('grain_ms=60 delay_ms=40 pitch=0.75 scatter_ms=15' in s for s in sessions),sessions
 assert 'mix=0.30' in sessions[0] and 'mix=0.00' in sessions[1],sessions
 assert json.loads((f.ROOT/'live-settings.json').read_text())['parameters']==expected
 print('PASS pre-start edits reach real engine, no save during audio, B saves, relaunch restores, A resets wet/gain, active exit clean')
