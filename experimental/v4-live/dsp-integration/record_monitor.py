"""Dry software monitoring of the ORIGINAL recorder's growing WAV (one capture)."""
import os
from pathlib import Path
import select
import struct
import subprocess
import threading
import time


def wav_layout(file):
    """Parse a possibly unfinished PCM WAV header; None means wait for more bytes."""
    file.seek(0)
    header=file.read(12)
    if len(header)<12:return None
    if header[:4]!=b'RIFF' or header[8:]!=b'WAVE':raise ValueError('Recording monitor requires RIFF WAV')
    fmt=None;offset=12
    while offset<1024*1024:
        file.seek(offset);chunk=file.read(8)
        if len(chunk)<8:return None
        name,size=struct.unpack('<4sI',chunk)
        if name==b'fmt ':
            if size<16:raise ValueError('Invalid WAV format chunk')
            data=file.read(16)
            if len(data)<16:return None
            encoding,channels,rate,_,_,bits=struct.unpack('<HHIIHH',data)
            if encoding!=1 or bits!=16 or channels not in (1,2) or not 8000<=rate<=192000:
                raise ValueError('Recording monitor requires PCM16 mono/stereo')
            fmt=(channels,rate)
        if name==b'data':
            if fmt is None:raise ValueError('Missing WAV format')
            return offset+8,*fmt
        offset+=8+size+(size%2)
    raise ValueError('Recording WAV header too large')


class RecordingMonitor:
    def __init__(self,path,pcm,gain=.5):
        self.path=Path(path);self.pcm=pcm;self.gain=gain
        self._stop=threading.Event();self.thread=None;self.process=None
        self.status='STARTING';self.error=None;self.frames=0;self.dropped_frames=0
    def start(self):
        self.thread=threading.Thread(target=self._run,name='v4-record-monitor',daemon=True)
        self.thread.start()
    def _run(self):
        try:
            deadline=time.monotonic()+3
            while not self._stop.is_set():
                try:
                    with self.path.open('rb') as file:layout=wav_layout(file)
                except FileNotFoundError:layout=None
                if layout is not None:break
                if time.monotonic()>deadline:raise TimeoutError('Recording WAV header did not appear')
                self._stop.wait(.01)
            if self._stop.is_set():return
            offset,channels,rate=layout;frame_bytes=channels*2
            self.process=subprocess.Popen(['aplay','-q','-D',self.pcm,'-t','raw','-f','S16_LE','-r',str(rate),'-c',str(channels),'--buffer-time=24000','--period-time=6000'],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,bufsize=0)
            os.set_blocking(self.process.stdin.fileno(),False)
            self.status='ON'
            print('REC MONITOR START:',self.pcm,'rate',rate,'channels',channels,'gain',self.gain,flush=True)
            import numpy as np
            with self.path.open('rb',buffering=0) as file:
                file.seek(offset)
                while not self._stop.is_set():
                    if self.process.poll() is not None:raise OSError('Recording monitor output exited: '+str(self.process.returncode))
                    available=max(0,os.fstat(file.fileno()).st_size-file.tell())//frame_bytes
                    # Follow the present, rather than playing accumulated backlog.
                    limit=max(512,int(rate*.05))
                    if available>limit:
                        skip=available-limit;file.seek(skip*frame_bytes,1);self.dropped_frames+=skip
                    data=file.read(512*frame_bytes)
                    if not data:self._stop.wait(.005);continue
                    if len(data)%frame_bytes:
                        extra=len(data)%frame_bytes;file.seek(-extra,1);data=data[:-extra]
                    if not data:self._stop.wait(.005);continue
                    audio=(np.frombuffer(data,dtype='<i2').astype(np.float32)*self.gain).astype('<i2').tobytes()
                    remaining=memoryview(audio);deadline=time.monotonic()+.1
                    while remaining and not self._stop.is_set():
                        if time.monotonic()>deadline:raise TimeoutError('Recording monitor output stalled')
                        _,ready,_=select.select([],[self.process.stdin],[],.01)
                        if ready:
                            try:n=os.write(self.process.stdin.fileno(),remaining)
                            except BlockingIOError:continue
                            remaining=remaining[n:]
                    self.frames+=len(data)//frame_bytes
        except Exception as exc:
            self.error=str(exc);self.status='ERROR'
            print('REC MONITOR FAILED:',self.error,'(original recording continues)',flush=True)
        finally:
            process=self.process
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                    try:process.wait(timeout=1)
                    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=1)
                process.stdin.close()
            if self.status!='ERROR':self.status='OFF'
            print('REC MONITOR END: frames',self.frames,'skipped',self.dropped_frames,flush=True)
    def stop(self):
        self._stop.set()
        if self.thread is not None:self.thread.join(timeout=3)
