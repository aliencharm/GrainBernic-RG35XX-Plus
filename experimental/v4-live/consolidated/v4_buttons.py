"""Use KNULLI's existing RG35XX Plus SDL mapping before original V3 calibration."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from v4_install import write_json

CONFIG_PATHS=(Path('/userdata/system/configs/emulationstation/es_input.cfg'),
              Path('/userdata/system/.emulationstation/es_input.cfg'),
              Path('/usr/share/emulationstation/es_input.cfg'),
              Path('/etc/emulationstation/es_input.cfg'))
BINDINGS=(('A',('a',),5),('B',('b',),4),('X',('x',),7),('Y',('y',),6),
          ('L1',('pageup','l1','leftshoulder'),8),('R1',('pagedown','r1','rightshoulder'),9),
          ('L2',('l2','lefttrigger'),10),('R2',('r2','righttrigger'),11),
          ('SELECT',('select','back'),12),('START',('start',),13))


def mapping_from_config(path,joy):
    root=ET.parse(path).getroot()
    name=joy.get_name()
    try:guid=joy.get_guid().lower()
    except (AttributeError,RuntimeError):guid=''
    candidates=[p for p in root.iter('inputConfig') if p.get('type')=='joystick']
    matches=[p for p in candidates if guid and p.get('deviceGUID','').lower()==guid]
    if not matches:matches=[p for p in candidates if p.get('deviceName','').casefold()==name.casefold()]
    if len(matches)!=1:raise ValueError('No unique system mapping for this controller')
    bindings={p.get('name','').lower():p.attrib for p in matches[0].findall('input')}
    buttons={};axes={};dpad={};used=set()
    def binding(aliases):
        return next((bindings[a] for a in aliases if a in bindings),None)
    for label,aliases,brick in BINDINGS:
        item=binding(aliases)
        if item is None:raise ValueError('System mapping missing '+label)
        index=int(item['id']);kind=item.get('type')
        if kind=='button' and 0<=index<joy.get_numbuttons():
            if index in used:raise ValueError('Conflicting system button bindings')
            used.add(index);buttons[str(index)]=brick
        elif kind=='axis' and label in ('L2','R2') and 0<=index<joy.get_numaxes():
            axes[str(brick)]=index
        else:raise ValueError('Unsupported system binding for '+label)
    for name,hat_value in (('up',1),('down',4),('left',8),('right',2)):
        item=bindings.get(name)
        if item is None:raise ValueError('System mapping missing D-pad '+name)
        index=int(item['id']);kind=item.get('type')
        if kind=='hat' and index==0 and joy.get_numhats()>0 and int(item.get('value','0'))==hat_value:continue
        if kind=='button' and 0<=index<joy.get_numbuttons() and index not in used:
            used.add(index);dpad[str(index)]=name.upper();continue
        raise ValueError('Unsupported system D-pad binding')
    menu=binding(('hotkey','menu'))
    if menu is not None and menu.get('type')=='button':
        index=int(menu['id'])
        if 0<=index<joy.get_numbuttons() and index not in used:buttons[str(index)]=14
    return {'version':1,'device':joy.get_name(),'buttons':buttons,'dpad_buttons':dpad,
            'trigger_axes':axes,'axis_rest':[joy.get_axis(i) for i in range(joy.get_numaxes())],
            'source':'KNULLI '+str(path)}


def prepare_buttons(app,pg=None,paths=CONFIG_PATHS):
    destination=Path(app)/'gb_buttons.json'
    if destination.is_file():return True  # Keep existing user calibration.
    try:
        if pg is None:import pygame as pg
        pg.joystick.init()
        if not pg.joystick.get_count():raise ValueError('No controller detected')
        joy=pg.joystick.Joystick(0);joy.init()
        if not re.search(r'rg35xx[\s_-]*(plus|\+)',joy.get_name(),re.I):
            raise ValueError('Controller is not the target RG35XX Plus')
        for path in paths:
            if not path.is_file():continue
            try:data=mapping_from_config(path,joy)
            except (OSError,ValueError,ET.ParseError,KeyError):continue
            write_json(destination,data)
            print('V4 BUTTONS: automatic RG35XX Plus mapping from',str(path),flush=True)
            return True
        raise ValueError('No compatible KNULLI controller profile found')
    except Exception as exc:
        print('V4 BUTTONS: original calibration fallback:',str(exc),flush=True)
        return False
