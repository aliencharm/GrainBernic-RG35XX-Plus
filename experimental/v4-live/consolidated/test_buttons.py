from pathlib import Path
import tempfile
import types
import unittest
from v4_buttons import mapping_from_config,prepare_buttons

NAME='Anbernic RG35XX-Plus Controller'
class Joy:
    def init(self):pass
    def get_name(self):return NAME
    def get_guid(self):return 'target-guid'
    def get_numbuttons(self):return 11
    def get_numaxes(self):return 0
    def get_numhats(self):return 1


def config(path,omit=None):
    rows=[]
    for i,name in enumerate(('a','b','x','y','pageup','pagedown','l2','r2','select','start','hotkey')):
        if name!=omit:rows.append('<input name="'+name+'" type="button" id="'+str(i)+'" value="1"/>')
    for name,value in (('up',1),('down',4),('left',8),('right',2)):
        rows.append('<input name="'+name+'" type="hat" id="0" value="'+str(value)+'"/>')
    path.write_text('<inputList><inputConfig type="joystick" deviceName="'+NAME+'" deviceGUID="target-guid">'+''.join(rows)+'</inputConfig></inputList>')

class ButtonsTests(unittest.TestCase):
    def pygame(self):
        return types.SimpleNamespace(joystick=types.SimpleNamespace(init=lambda:None,get_count=lambda:1,Joystick=lambda i:Joy()))
    def test_system_face_shoulders_triggers_exit_and_menu_bindings(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'es_input.cfg';config(path)
            result=mapping_from_config(path,Joy())
            self.assertEqual(result['buttons'],{'0':5,'1':4,'2':7,'3':6,'4':8,'5':9,'6':10,'7':11,'8':12,'9':13,'10':14})
            self.assertEqual(result['dpad_buttons'],{})
    def test_first_launch_writes_original_adapter_format(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);path=root/'es_input.cfg';config(path)
            self.assertTrue(prepare_buttons(root,self.pygame(),(path,)))
            import json
            saved=json.loads((root/'gb_buttons.json').read_text())
            self.assertEqual(saved['version'],1);self.assertEqual(saved['buttons']['0'],5)
    def test_existing_calibration_is_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);path=root/'gb_buttons.json';path.write_text('existing calibration')
            self.assertTrue(prepare_buttons(root,pg=None,paths=()))
            self.assertEqual(path.read_text(),'existing calibration')
    def test_missing_binding_uses_calibration_fallback(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);path=root/'es_input.cfg';config(path,omit='l2')
            self.assertFalse(prepare_buttons(root,self.pygame(),(path,)))
            self.assertFalse((root/'gb_buttons.json').exists())
    def test_hotkey_shared_with_select_does_not_break_exit_combo(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'es_input.cfg';config(path)
            path.write_text(path.read_text().replace('name="hotkey" type="button" id="10"','name="hotkey" type="button" id="8"'))
            result=mapping_from_config(path,Joy())
            self.assertEqual(result['buttons']['8'],12)
    def test_unknown_controller_does_not_get_guessed_mapping(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);path=root/'es_input.cfg';config(path)
            pg=self.pygame();joy=Joy();joy.get_name=lambda:'Different Controller';pg.joystick.Joystick=lambda i:joy
            self.assertFalse(prepare_buttons(root,pg,(path,)))
            self.assertFalse((root/'gb_buttons.json').exists())

if __name__=='__main__':unittest.main()
