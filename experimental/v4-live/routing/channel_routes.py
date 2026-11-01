"""Per-app stereo ALSA routes over the interface's existing USB channels."""
from pathlib import Path
import json
import os
import re
from audio_inventory import inventory

FORMATS={'S16_LE','S24_LE','S24_3LE','S32_LE','FLOAT_LE'}

def supports_48k(text):
    rates=[int(n) for n in re.findall(r'\d+',text)]
    return 48000 in rates or ('-' in text and len(rates)>=2 and rates[0]<=48000<=rates[1])

def discover(asound=Path('/proc/asound')):
    routes=[]
    streams=inventory(asound)
    for stream in streams:
        identifier=stream['id']
        if not re.fullmatch(r'[A-Za-z0-9_]+',identifier):continue
        device=int(stream['stream'].removeprefix('stream'))
        for direction in ('capture','playback'):
            modes=[m for m in stream['descriptors'] if m['direction']==direction and m.get('format') in FORMATS and supports_48k(m.get('rates',''))]
            if not modes:continue
            mode=max(modes,key=lambda m:(m['channels'],m['format']=='S32_LE'))
            for first in range(0,mode['channels']-1,2):
                alias=f'v4_{direction}_{identifier}_{device}_{first+1}_{first+2}'
                routes.append(dict(alias=alias,direction=direction,card=identifier,device=device,
                                   channels=mode['channels'],format=mode['format'],first=first,
                                   label=f'{identifier}'+(f' PCM{device}' if sum(s['id']==identifier for s in streams)>1 else '')+f' {first+1}-{first+2}',
                                   hardware=f'hw:CARD={identifier},DEV={device}'))
    return routes

def route_definition(route,hardware=None):
    alias=route['alias'];hardware=hardware or route['hardware']
    if not re.fullmatch(r'[A-Za-z0-9_]+',alias):raise ValueError('Invalid PCM alias')
    if '"' in hardware or '\n' in hardware:raise ValueError('Invalid hardware PCM')
    first=route['first'];count=route['channels'];fmt=route['format']
    if not 0<=first<count-1 or fmt not in FORMATS:raise ValueError('Invalid channel route')
    return f'''pcm.{alias} {{
 type plug
 slave.pcm {{
  type route
  slave {{ pcm "{hardware}" channels {count} format {fmt} }}
  ttable.0.{first} 1
  ttable.1.{first+1} 1
 }}
}}
'''

def configure(app,config,asound=Path('/proc/asound')):
    routes=discover(asound)
    if not routes:return None
    original=os.environ.get('ALSA_CONFIG_PATH','/usr/share/alsa/alsa.conf')
    path=app/'alsa-routing.conf'
    if Path(original)==path:original='/usr/share/alsa/alsa.conf'
    path.write_text('<'+original+'>\n'+''.join(route_definition(r) for r in routes))
    os.environ['ALSA_CONFIG_PATH']=str(path)
    data=json.loads((app/'config.json').read_text())
    inputs=[r for r in routes if r['direction']=='capture'];outputs=[r for r in routes if r['direction']=='playback']
    for direction,items,field in (('input',inputs,'capture'),('output',outputs,'playback')):
        selected=next((r for r in items if r['alias']==data.get(direction+'_route')),None)
        if selected is None:
            selected=next((r for r in items if f'CARD={r["card"]},DEV={r["device"]}' in config[field]),None)
        if selected is not None:config[field]=selected['alias']
    if data.get('output_route')=='default':config['playback']='default'
    print('V4 ROUTES:',[(r['direction'],r['label']) for r in routes],flush=True)
    return Router(app,config,inputs,outputs)

class Router:
    def __init__(self,app,config,inputs,outputs):
        self.app=app;self.config=config;self.inputs=inputs;self.outputs=outputs;self.initialized=False
    def save(self,key,value):
        path=self.app/'config.json';data=json.loads(path.read_text());data[key]=value
        from v4_install import write_json
        write_json(path,data)
    def install(self,main,controller):
        devices=__import__('engine.audio_devices',fromlist=['available_outputs'])
        renderer=__import__('ui.renderer',fromlist=['available_outputs'])
        original=devices.available_outputs
        hardware={f'plughw:CARD={r["card"]},DEV={r["device"]}' for r in self.outputs}
        def outputs():
            base=[entry for entry in original() if entry[2] not in hardware]
            return base+[(r['alias'],r['label'],r['alias']) for r in self.outputs]
        devices.available_outputs=outputs;renderer.available_outputs=outputs
        def resolve(selected):
            return next((pcm for identifier,label,pcm in outputs() if identifier==selected),'default')
        devices.resolve_output=resolve
        if hasattr(main,'resolve_output'):main.resolve_output=resolve
        before=controller.before_input
        def input_poll():
            before()
            if not self.initialized:
                self.initialized=True
                if self.inputs:
                    main.RECORD_SOURCES=[dict(id='usb',label=r['label'],device=r['alias'],channels=2,format='48 KHZ / STEREO USB') for r in self.inputs]
                    main.record_source_index=next((i for i,r in enumerate(self.inputs) if r['alias']==self.config['capture']),0)
                main.ui._audio_outputs_last_scan=-1000000;main.ui.refresh_audio_outputs()
                for identifier,label,pcm in main.ui._audio_outputs:
                    if pcm==self.config['playback']:main.ui.audio_output_id=identifier
                self.last_output=main.ui.audio_output_id
                original_handle=main.handle_record_action
                def handle(action,value):
                    ready=main.controls.current_tab=='SAMPLE' and main.record_mode=='ready'
                    selected=main.record_source_index
                    if ready and action in ('L2','R2'):
                        if value!=0 and len(self.inputs)>1:
                            if controller.active():controller.stop_live()
                            main.select_record_source(-1 if action=='L2' else 1)
                        result=True
                    else:
                        result=original_handle(action,value)
                        if ready and action=='X' and self.inputs:main.record_source_index=selected
                    self.sync_input(main)
                    return result
                main.handle_record_action=handle
            self.sync_input(main)
            if main.ui.audio_output_id!=self.last_output:
                for identifier,label,pcm in main.ui._audio_outputs:
                    if identifier==main.ui.audio_output_id:
                        self.config['playback']=pcm;self.save('output_route',pcm)
                self.last_output=main.ui.audio_output_id
        controller.before_input=input_poll
        ui_cls=type(main.ui) if getattr(main,'ui',None) is not None else renderer.UIEngine
        draw=ui_cls.draw_record_ready_page
        def ready(ui):
            draw(ui)
            if self.inputs:
                r=self.inputs[main.record_source_index%len(self.inputs)]
                ui.text('INPUT: '+r['label'],55,175,2,ui.ACCENT)
                if controller.mode=='LIVE':ui.text('L2 / R2 SELECT INPUT (STOPS LIVE)',55,660,2)
        ui_cls.draw_record_ready_page=ready
    def sync_input(self,main):
        if not self.inputs:return
        index=main.record_source_index%len(self.inputs);pcm=self.inputs[index]['alias']
        if self.config['capture']!=pcm:
            self.config['capture']=pcm
            self.save('input_route',pcm)
            print('V4 INPUT SELECTED:',self.inputs[index]['label'],flush=True)
