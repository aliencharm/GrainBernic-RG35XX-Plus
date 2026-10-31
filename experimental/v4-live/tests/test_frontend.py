import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
import pygame as pg
spec=importlib.util.spec_from_file_location('frontend',Path(__file__).resolve().parents[1]/'package/grainbrick-v4-live/frontend.py')
f=importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
class FrontendTests(unittest.TestCase):
 def test_tascam_requires_duplex_and_usb(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d); (root/'cards').write_text(' 2 [DR40X         ]: USB-Audio - DR-40X\n 3 [Other         ]: USB-Audio - Generic\n')
   card=root/'card2'; card.mkdir(); (card/'id').write_text('DR40X'); (card/'usbid').touch(); (card/'pcm0c').mkdir()
   self.assertEqual(f.candidates(root),[])
   (card/'pcm0p').mkdir(); self.assertEqual(f.candidates(root),['hw:CARD=DR40X,DEV=0'])
 def test_config_requires_both_devices(self):
  old=f.ROOT
  try:
   with tempfile.TemporaryDirectory() as d:
    f.ROOT=Path(d); p=f.ROOT/'config.json'
    p.write_text(json.dumps({'capture':'hw:1'}))
    with self.assertRaises(ValueError): f.devices()
    p.write_text(json.dumps({'capture':'null','playback':'null','latency_us':24000}))
    self.assertEqual(f.devices(),('null','null',24000))
    p.write_text(json.dumps({'capture':'null','playback':'null','latency_us':1}))
    with self.assertRaises(ValueError): f.devices()
  finally: f.ROOT=old
 def test_v3_mapping_and_keyboard(self):
  data={'buttons':{'2':5,'3':4,'9':13},'dpad_buttons':{'7':'LEFT'}}
  for raw,action in [(2,'A'),(3,'B'),(9,'START'),(7,'LEFT')]:
   self.assertEqual(f.translate(pg.event.Event(pg.JOYBUTTONDOWN,button=raw),data,pg),action)
  self.assertEqual(f.translate(pg.event.Event(pg.JOYHATMOTION,value=(0,1)),data,pg),'UP')
  self.assertEqual(f.translate(pg.event.Event(pg.KEYDOWN,key=pg.K_ESCAPE),data,pg),'START')
if __name__=='__main__': unittest.main()
