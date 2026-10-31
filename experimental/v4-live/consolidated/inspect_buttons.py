"""ARM offline check: system profile -> V3 event translator -> original input handler."""
from pathlib import Path
import importlib.util
import os
import sys
import tempfile
import types
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'original-ui'))
import native_ui,pygame as pg
native_ui.TARGETS=(*native_ui.TARGETS,'engine.input','engine.button_mapping')
modules,_=native_ui.load_classes(Path(sys.argv[1]),root/'package/grainbrick-v4-live/v4-live',pg)
from test_buttons import Joy,config
from v4_buttons import mapping_from_config
spec=importlib.util.spec_from_file_location('original_buttons',root.parents[1]/'grainbrick-beta/gb_buttons.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
with tempfile.TemporaryDirectory() as temp:
    path=Path(temp)/'es_input.cfg';config(path)
    mapping=mapping_from_config(path,Joy())
translator=adapter._Translator(mapping)
pg.display.init();pg.display.set_mode((640,480))
cls=modules['engine.input'].InputManager
manager=cls.__new__(cls)
manager.joy=types.SimpleNamespace(get_hat=lambda index:(0,0),get_axis=lambda index:0.)
manager.mapping=modules['engine.button_mapping'].ButtonMapping()
manager.capture_mode=False;manager.buttons_down=set();manager.hat_x=0;manager.hat_y=0
manager.horizontal_hold_start=0;manager.horizontal_last_repeat=0;manager.horizontal_repeat_enabled=False
manager._ab_context=None;manager._ab_since={'A':None,'B':None};manager._ab_last={'A':0,'B':0}
for raw,expected in ((0,'A'),(1,'B'),(2,'X'),(3,'Y'),(4,'L'),(5,'R'),(6,'L2'),(7,'R2'),(8,'SELECT'),(9,'START')):
    event=pg.event.Event(pg.JOYBUTTONDOWN,button=raw,joy=0,instance_id=0)
    for translated in translator.translate([event]):pg.event.post(translated)
    actions=manager.poll()
    assert any(action==expected for action,value in actions),(raw,expected,actions)
    for translated in translator.translate([pg.event.Event(pg.JOYBUTTONUP,button=raw,joy=0,instance_id=0)]):pg.event.post(translated)
    manager.poll()
for value,expected in (((0,1),'UP'),((0,-1),'DOWN'),((-1,0),'LEFT'),((1,0),'RIGHT')):
    pg.event.post(pg.event.Event(pg.JOYHATMOTION,hat=0,value=value,joy=0))
    actions=manager.poll();assert any(action==expected for action,amount in actions),(expected,actions)
    pg.event.post(pg.event.Event(pg.JOYHATMOTION,hat=0,value=(0,0),joy=0));manager.poll()
for raw in (8,9):
    for event in translator.translate([pg.event.Event(pg.JOYBUTTONDOWN,button=raw,joy=0,instance_id=0)]):pg.event.post(event)
assert any(action=='EXIT' for action,value in manager.poll())
print('PASS automatic KNULLI profile -> actual V3 translator -> actual original InputManager: A/B/X/Y, L/R, L2/R2, SELECT/START, D-pad and exit combo; joystick/profile mocked',flush=True)
