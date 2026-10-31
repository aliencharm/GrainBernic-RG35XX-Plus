#!/usr/bin/env python3
"""Independent V4 experimental controller. Does not import GrainBrick or write V3 files."""
import json
import math
import tempfile
import os
from pathlib import Path
import platform
import subprocess
import time

ROOT = Path(__file__).resolve().parent
PARAMS = [('mix', 'Wet mix', 0., 1., .05), ('gain', 'Output gain', 0., 1., .05),
          ('grain', 'Grain ms', 10., 250., 10.), ('delay', 'History delay ms', 10., 1000., 10.),
          ('pitch', 'Pitch ratio', .5, 2., .05), ('scatter', 'Scatter ms', 0., 100., 5.)]
DEFAULTS = {'mix': 0., 'gain': .5, 'grain': 20., 'delay': 10., 'pitch': 1., 'scatter': 0.}
PERSISTED_KEYS = ('grain', 'delay', 'pitch', 'scatter')


def persistent_values(params):
    return {key:params[key] for key in PERSISTED_KEYS}


def load_settings():
    # Wet mix and gain are deliberately excluded from persisted startup state.
    params=DEFAULTS.copy()
    path=ROOT / 'live-settings.json'
    try:
        if path.stat().st_size > 16384:
            raise ValueError('settings file is too large')
        data=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data,dict) or type(data.get('version')) is not int or data['version']!=1 or not isinstance(data.get('parameters'),dict):
            raise ValueError('unsupported settings format')
        limits={key:(lo,hi) for key,_,lo,hi,_ in PARAMS}
        for key in PERSISTED_KEYS:
            value=data['parameters'].get(key)
            lo,hi=limits[key]
            if type(value) in (int,float) and lo<=value<=hi and math.isfinite(value):
                params[key]=float(value)
            elif value is not None:
                print('V4 SETTINGS IGNORED invalid value for',key,flush=True)
        print('V4 SETTINGS LOADED:',persistent_values(params),flush=True)
    except FileNotFoundError:
        pass
    except (OSError,ValueError) as exc:
        print('V4 SETTINGS LOAD FAILED:',str(exc),flush=True)
    return params


def save_settings(params):
    values=persistent_values(params)
    limits={key:(lo,hi) for key,_,lo,hi,_ in PARAMS}
    for key,value in values.items():
        lo,hi=limits[key]
        if type(value) not in (int,float) or not lo<=value<=hi or not math.isfinite(value):
            raise ValueError('invalid setting: '+key)
    text=json.dumps({'version':1,'parameters':values},indent=2,allow_nan=False)+'\n'
    fd,name=tempfile.mkstemp(prefix='.live-settings-',suffix='.tmp',dir=ROOT)
    temporary=Path(name)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary,ROOT / 'live-settings.json')
    finally:
        temporary.unlink(missing_ok=True)


def start_values(params):
    # Preserve tone controls selected before A, but start dry at half gain.
    return {**params,'mix':DEFAULTS['mix'],'gain':DEFAULTS['gain']}


def send_start_settings(child,params):
    child.stdin.write(''.join(f'{key} {params[key]}\n' for key in PERSISTED_KEYS))
    child.stdin.flush()


def candidates(asound=Path('/proc/asound')):
    """Only Tascam/DR-40 USB cards supporting capture AND playback; no arbitrary USB fallback."""
    import re
    try:
        text = (asound / 'cards').read_text()
    except OSError:
        return []
    result = []
    for m in re.finditer(r'(?m)^\s*(\d+)\s+\[([^\]]+)\]:\s*(.+)$', text):
        card = asound / ('card' + m[1])
        name = m[3].lower()
        if not ('tascam' in name or 'dr-40' in name or 'dr40' in name):
            continue
        if not (card / 'usbid').exists():
            continue
        if not (card / 'pcm0c').exists() or not (card / 'pcm0p').exists():
            continue
        card_id = (card / 'id').read_text().strip()
        if re.fullmatch(r'[A-Za-z0-9_]+', card_id):
            result.append('hw:CARD=' + card_id + ',DEV=0')
    return result


def devices():
    cfg_path = ROOT / 'config.json'
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    if not isinstance(cfg, dict):
        raise ValueError('config.json must contain an object')
    cap, play = cfg.get('capture'), cfg.get('playback')
    if not cap and not play:
        found = candidates()
        if len(found) != 1:
            raise ValueError('Need one Tascam USB card; set config.json if absent/ambiguous')
        cap = play = found[0]
    if not isinstance(cap, str) or not isinstance(play, str) or not cap or not play:
        raise ValueError('Configure BOTH capture and playback PCM names')
    latency = cfg.get('latency_us', 24000)
    if not isinstance(latency, int) or not 10000 <= latency <= 100000:
        raise ValueError('latency_us must be 10000..100000')
    return cap, play, latency


def load_mapping():
    # Read-only reuse of V3 calibration. Never import V3's event monkey-patches.
    for path in [ROOT / 'buttons.json', ROOT.parent / 'grainbrick-beta' / 'gb_buttons.json']:
        try:
            data = json.loads(path.read_text())
            if isinstance(data, dict) and data.get('version') == 1 and isinstance(data.get('buttons'), dict):
                return data
        except (OSError, ValueError):
            pass
    return None


def translate(ev, mapping, pg):
    if ev.type == pg.KEYDOWN:
        return {pg.K_RETURN:'A', pg.K_SPACE:'A', pg.K_ESCAPE:'START', pg.K_b:'B',
                pg.K_UP:'UP', pg.K_DOWN:'DOWN', pg.K_LEFT:'LEFT', pg.K_RIGHT:'RIGHT'}.get(ev.key)
    if ev.type == pg.JOYHATMOTION:
        x,y = ev.value
        return 'LEFT' if x < 0 else 'RIGHT' if x > 0 else 'UP' if y > 0 else 'DOWN' if y < 0 else None
    if ev.type == pg.JOYBUTTONDOWN and mapping:
        raw = str(ev.button)
        direction = mapping.get('dpad_buttons', {}).get(raw)
        if direction:
            return direction
        brick = mapping.get('buttons', {}).get(raw)
        return {5:'A', 4:'B', 13:'START'}.get(int(brick)) if brick is not None else None
    return None


def diagnostics():
    lines = ['GrainBrick V4 Live experimental 0.1.1', platform.platform(),
             'Python ' + platform.python_version()]
    for path in ['/proc/asound/cards','/proc/asound/pcm','/proc/asound/version']:
        lines.append('=== ' + path)
        try:
            lines.append(Path(path).read_text())
        except OSError as exc:
            lines.append(str(exc))
    for cmd in [['arecord','-l'],['aplay','-l']]:
        lines.append('=== ' + ' '.join(cmd))
        try:
            r = subprocess.run(cmd,capture_output=True,text=True,timeout=3)
            lines.extend([r.stdout,r.stderr,'exit=' + str(r.returncode)])
        except (OSError,subprocess.TimeoutExpired) as exc:
            lines.append(str(exc))
    (ROOT / 'v4-diagnostics.txt').write_text('\n'.join(lines))


def main(renderer_factory=None):
    import fcntl
    with (ROOT / '.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('V4 is already running')
        return _run(renderer_factory)


def _run(renderer_factory):
    import signal
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    diagnostics()
    import pygame as pg
    os.environ.setdefault('SDL_AUDIODRIVER','dummy')  # UI never opens the USB audio PCM.
    pg.display.init()
    pg.font.init()
    pg.joystick.init()
    joys = [pg.joystick.Joystick(i) for i in range(pg.joystick.get_count())]
    for j in joys:
        j.init()
    renderer = None
    try:
        renderer = renderer_factory(ROOT,pg) if renderer_factory else None
        screen = renderer.screen if renderer else pg.display.set_mode((640,480), pg.FULLSCREEN)
    except BaseException:
        pg.quit()
        raise
    pg.mouse.set_visible(False)
    font = pg.font.Font(None,27)
    small = pg.font.Font(None,23)
    clock = pg.time.Clock()
    mapping = load_mapping()
    calibration = ['A','B','START','UP','DOWN','LEFT','RIGHT'] if mapping is None and joys else []
    new_map = {'version':1,'buttons':{},'dpad_buttons':{}}
    params = load_settings()
    saved_params = persistent_values(params)
    selected = 0
    child = None
    log = None
    status = 'Stopped. A starts dry monitoring.'
    device_label = 'Tascam detection on start'
    latest = ''
    running = True
    cap_step = 0
    calibrated_buttons = set()
    log_read = None
    log_offset = 0

    def stop_audio():
        nonlocal child, log, log_read, status, latest, saved_params
        if child:
            if child.poll() is None:
                try:
                    child.stdin.write('quit\n'); child.stdin.flush()
                    child.wait(timeout=3)
                except (OSError, subprocess.TimeoutExpired):
                    child.terminate()
                    try:
                        child.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        child.kill(); child.wait()
            try:
                child.stdin.close()
            except OSError:
                pass
            child = None
        if log:
            log.close(); log = None
        if log_read:
            log_read.close(); log_read = None
        status = 'Stopped. A starts dry monitoring.'
        latest = ''
        current = persistent_values(params)
        if current != saved_params:
            try:
                save_settings(params)
                saved_params = current
                status = 'Settings saved. A starts dry monitoring.'
                print('V4 SETTINGS SAVED:',current,flush=True)
            except (OSError,ValueError) as exc:
                status = 'Stopped; settings could not be saved'
                print('V4 SETTINGS SAVE FAILED:',str(exc),flush=True)

    try:
        while running:
            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    running = False
                if calibration:
                    if ev.type == pg.KEYDOWN and ev.key == pg.K_ESCAPE:
                        running = False
                    target = calibration[cap_step]
                    accepted = False
                    if ev.type == pg.JOYBUTTONDOWN and ev.button not in calibrated_buttons:
                        raw = str(ev.button)
                        if target in ('A','B','START'):
                            new_map['buttons'][raw] = {'A':5,'B':4,'START':13}[target]
                        else:
                            new_map['dpad_buttons'][raw] = target
                        calibrated_buttons.add(ev.button)
                        accepted = True
                    elif ev.type == pg.JOYHATMOTION and target in ('UP','DOWN','LEFT','RIGHT'):
                        expected = {'UP':(0,1),'DOWN':(0,-1),'LEFT':(-1,0),'RIGHT':(1,0)}[target]
                        accepted = ev.value == expected
                    if accepted:
                        cap_step += 1
                        if cap_step == len(calibration):
                            (ROOT / 'buttons.json').write_text(json.dumps(new_map,indent=2))
                            mapping = new_map
                            calibration = []
                    continue
                action = translate(ev,mapping,pg)
                if action == 'START':
                    running = False
                elif action == 'B':
                    stop_audio()
                elif action in ('UP','DOWN'):
                    selected = (selected + (1 if action == 'DOWN' else -1)) % len(PARAMS)
                elif action in ('LEFT','RIGHT'):
                    key,_,lo,hi,step = PARAMS[selected]
                    params[key] = round(max(lo,min(hi,params[key]+step*(1 if action=='RIGHT' else -1))),4)
                    if child and child.poll() is None:
                        try:
                            child.stdin.write(f'{key} {params[key]}\n'); child.stdin.flush()
                        except OSError:
                            status = 'Audio stopped; check v4-audio.log'
                elif action == 'A' and child is None:
                    try:
                        for proc in Path('/proc').iterdir():
                            if proc.name.isdigit():
                                try:
                                    args = (proc / 'cmdline').read_bytes().split(b'\0')
                                    if any(arg.endswith(b'/gb_launch.py') or arg == b'gb_launch.py' for arg in args):
                                        raise ValueError('Close GrainBrick V3 before starting V4')
                                except (OSError, PermissionError):
                                    pass
                        cap,play,latency = devices()
                        device_label = cap + ' -> ' + play
                        log_path = ROOT / 'v4-audio.log'
                        if log_path.exists() and log_path.stat().st_size > 2_000_000:
                            log_path.replace(ROOT / 'v4-audio.previous.log')
                        log = log_path.open('a',buffering=1)
                        log.write(f'\nSTART {time.strftime("%Y-%m-%d %H:%M:%S")} {platform.platform()}\n')
                        log.flush()
                        log_read = log_path.open()
                        log_read.seek(0,2)
                        log_offset = log_read.tell()
                        child = subprocess.Popen([str(ROOT/'v4-live'),cap,play,str(latency)],
                                                 stdin=subprocess.PIPE,stdout=log,stderr=log,text=True)
                        params = start_values(params)
                        send_start_settings(child,params)
                        status = 'Starting audio...'
                        latest = ''
                    except (OSError,ValueError) as exc:
                        stop_audio()
                        status = str(exc)
                        print("V4 START FAILED:", status, flush=True)
            if child:
                if log_read:
                    log_read.seek(log_offset)
                    text = log_read.read(8192)
                    log_offset = log_read.tell()
                    for line in text.splitlines():
                        if line.startswith('STATS'):
                            latest = line
                            status = 'Monitoring (verify sound on hardware)'
                        if line.startswith(('FATAL','AUDIO_ERROR')):
                            status = line
                if child.poll() is not None:
                    code = child.returncode
                    stop_audio()
                    status = f'Audio exited ({code}); see v4-audio.log'
            screen.fill((0,0,0) if renderer else (14,19,25))
            def draw(text,y,color=(218,226,231),small_font=False):
                if renderer:
                    renderer.draw_text(text,y,color,small_font)
                    return
                # Wrap long device names/errors so useful diagnostics remain visible.
                f = small if small_font else font
                for start in range(0,len(text),66 if small_font else 55):
                    screen.blit(f.render(text[start:start+(66 if small_font else 55)],True,color),(20,y))
                    y += 22
            if renderer:
                renderer.draw_header(child is not None and child.poll() is None)
            else:
                draw('GrainBrick V4 LIVE - experimental 0.1.1',18,(100,220,190))
                draw('Independent engine / V3 stays unchanged',48,small_font=True)
            if calibration:
                draw('V4 controller setup (saved separately)',110)
                draw('Press '+calibration[cap_step],160,(255,213,100))
                draw('For D-pad, press the indicated direction.',210,small_font=True)
            else:
                if renderer:
                    renderer.draw_parameters(params,selected)
                    renderer.draw_footer(status,device_label,latest)
                else:
                    for i,(key,label,_,_,_) in enumerate(PARAMS):
                        text = f'{">" if selected==i else " "} {label}: {params[key]:.2f}'
                        draw(text,85+i*31,(255,213,100) if selected==i else (218,226,231))
                    draw(status,288,(100,220,190),True)
                    draw(device_label,338,small_font=True)
                    draw('D-pad: select/change | A: start | B: stop',402,small_font=True)
                    draw('START: exit | Disable Tascam direct monitoring',428,small_font=True)
                    draw('Start at low headphone volume. No audio files saved.',452,small_font=True)
            pg.display.flip()
            clock.tick(30)
    except KeyboardInterrupt:
        pass
    finally:
        stop_audio()
        if renderer:
            renderer.close()
        pg.quit()

if __name__ == '__main__':
    main()
