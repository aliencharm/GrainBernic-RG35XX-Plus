"""Headless full frontend -> native process -> control -> stop -> exit test."""
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
spec=importlib.util.spec_from_file_location('frontend',Path(__file__).resolve().parents[1]/'package/grainbrick-v4-live/frontend.py')
f=importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
with tempfile.TemporaryDirectory() as d:
 f.ROOT=Path(d)
 shutil.copy2(sys.argv[1],f.ROOT/'v4-live')
 (f.ROOT/'config.json').write_text(json.dumps({'capture':'null','playback':'null'}))
 def key(k): pg.event.post(pg.event.Event(pg.KEYDOWN,key=k))
 def interact():
  for _ in range(100):
   if pg.display.get_init(): break
   time.sleep(.01)
  time.sleep(.1); key(pg.K_RETURN)
  time.sleep(.2); key(pg.K_RIGHT)
  time.sleep(.1); key(pg.K_UP)
  time.sleep(.1); key(pg.K_RIGHT)
  time.sleep(2.2); key(pg.K_b)
  time.sleep(.2); key(pg.K_ESCAPE)
 thread=threading.Thread(target=interact,daemon=True); thread.start()
 f.main(); thread.join(timeout=2)
 log=(f.ROOT/'v4-audio.log').read_text()
 assert 'STATS' in log and 'mix=0.05' in log and 'scatter_ms=5' in log and 'grain_ms=20 delay_ms=10' in log and 'EXIT status=0' in log,log
 print('PASS full headless UI start, live wet/scatter controls, default settings, stats, stop and exit')
