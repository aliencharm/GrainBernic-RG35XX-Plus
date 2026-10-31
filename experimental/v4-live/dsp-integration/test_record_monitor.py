import io
from pathlib import Path
import struct
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch
import os
import numpy as np
from record_monitor import RecordingMonitor,wav_layout
from original_adapter import LiveController


def header(channels=2,rate=48000):
    return b'RIFF'+struct.pack('<I',0x7fffffff)+b'WAVEfmt '+struct.pack('<IHHIIHH',16,1,channels,rate,rate*channels*2,channels*2,16)+b'data'+struct.pack('<I',0x7fffffff)

class MonitorTests(unittest.TestCase):
    def test_header_and_incomplete_header(self):
        self.assertIsNone(wav_layout(io.BytesIO(header()[:30])))
        self.assertEqual(wav_layout(io.BytesIO(header())),(44,2,48000))
        self.assertEqual(wav_layout(io.BytesIO(header(1,44100))),(44,1,44100))
        with self.assertRaises(ValueError):wav_layout(io.BytesIO(b'not a wav file'))
    def test_follows_growing_file_without_modifying_recording(self):
        class Output:
            def __init__(self):
                read,write=os.pipe();self.stdin=os.fdopen(write,'wb',buffering=0)
                self.returncode=None;self.audio=bytearray();self.received=threading.Event()
                def drain():
                    with os.fdopen(read,'rb',buffering=0) as source:
                        while data:=source.read(4096):
                            self.audio.extend(data)
                            if len(self.audio)>=2048:self.received.set()
                self.reader=threading.Thread(target=drain);self.reader.start()
            def poll(self):return self.returncode
            def terminate(self):self.returncode=0
            def wait(self,timeout):return self.returncode
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'growing.wav';path.write_bytes(header())
            output=Output();raw=np.full((512,2),10000,dtype='<i2').tobytes()
            with patch('record_monitor.subprocess.Popen',return_value=output) as spawn:
                monitor=RecordingMonitor(path,'test-output');monitor.start()
                with path.open('ab') as recording:recording.write(raw)
                self.assertTrue(output.received.wait(3))
                monitor.stop();output.reader.join(1)
                self.assertIsNone(monitor.error)
                self.assertFalse(monitor.thread.is_alive())
                self.assertEqual(path.read_bytes(),header()+raw)
                self.assertTrue(np.all(np.frombuffer(output.audio,dtype='<i2')==5000))
                self.assertEqual(spawn.call_args.args[0][0],'aplay')
    def test_failure_does_not_modify_recording(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'bad.wav';path.write_bytes(b'not a wav file')
            monitor=RecordingMonitor(path,'unused');monitor.start();monitor.thread.join(1)
            self.assertEqual(monitor.status,'ERROR')
            self.assertEqual(path.read_bytes(),b'not a wav file')
    def test_original_record_lifecycle_and_playback_ownership(self):
        class Worker:
            running=True
            def stop(self):self.running=False
            def start(self):self.running=True
        class Monitor:
            def __init__(self,path,pcm):self.path=path;self.pcm=pcm;self.started=False;self.stopped=False
            def start(self):self.started=True
            def stop(self):self.stopped=True
        main=types.SimpleNamespace(audio_worker=Worker(),record_mode='ready',recorder=types.SimpleNamespace(current_path=Path('record.wav')))
        def start():
            self.assertFalse(main.audio_worker.running)
            main.record_mode='recording'
        def finish():
            self.assertTrue(monitor.stopped)
            main.record_mode='edit'
        main.start_input_recording=start;main.stop_input_recording_to_editor=finish;main.cancel_input_recording=finish
        controller=LiveController(main,{'playback':'USB'})
        controller.install_record_monitor()
        with patch('record_monitor.RecordingMonitor',Monitor):
            main.start_input_recording();monitor=controller.record_monitor
            self.assertTrue(monitor.started);self.assertEqual(monitor.pcm,'USB')
            main.stop_input_recording_to_editor()
            self.assertTrue(main.audio_worker.running);self.assertIsNone(controller.record_monitor)
            main.start_input_recording();monitor=controller.record_monitor
            main.cancel_input_recording();self.assertTrue(monitor.stopped)
            self.assertTrue(main.audio_worker.running)

if __name__=='__main__':unittest.main()
