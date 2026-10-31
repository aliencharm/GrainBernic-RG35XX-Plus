import io
import os
from pathlib import Path
import sys
import threading
import types
import unittest
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from live_source import SwitchableSource,ArecordCapture,add_live_parameters
class Bus:
    def __init__(self):self.params={};self.values={'transport.playing':1.,'grain.position':.5,'grain.size':.18,'grain.pitch':0.,'grain.spray':.1,'grain.density':8.}
    def add(self,key,value,lo,hi):self.params[key]=True;self.values[key]=value
    def get(self,key):return self.values[key]
    def set(self,key,value):self.values[key]=value
class Engine:
    def __init__(self,sample,p,rate):self.sample=sample;self.parameters=p
    def render(self,n):return np.full((n,2),.2,np.float32)
    def active_grains(self):return 2
    def roam_position(self):return .5
    def roam_range_start(self):return 0.
    def roam_range_end(self):return 1.
class Capture:
    def __init__(self):self.value=.3;self.closed=0
    def read(self,n):return np.full((n,2),self.value,np.float32)
    def close(self):self.closed+=1
class SourceTests(unittest.TestCase):
    def source(self):
        p=add_live_parameters(Bus());capture=Capture();file=Engine(None,p,48000)
        source=SwitchableSource(file,p,Engine,lambda:capture)
        self.addCleanup(source.close)
        return p,capture,file,source
    def test_file_passthrough_does_not_capture(self):
        p,c,f,s=self.source()
        np.testing.assert_allclose(s.render(512),.2)
        self.assertIsNone(s.capture);self.assertEqual(len(s.grains),2)
    def test_live_dry_wet_native_params_and_file_return(self):
        p,c,f,s=self.source();p.set('live.enabled',1)
        np.testing.assert_allclose(s.render(512),.3)
        p.set('live.mix',1);np.testing.assert_allclose(s.render(512),.2)
        self.assertEqual(s.view.get('grain.density'),8)
        self.assertEqual(s.view.get('grain.size'),.18)
        self.assertEqual(s.view.get('grain.pitch'),0)
        self.assertTrue(0<=s.view.get('grain.position')<=1)
        self.assertEqual(p.get('grain.position'),.5)
        p.set('live.enabled',0);np.testing.assert_allclose(s.render(512),.2)
        self.assertEqual(c.closed,1)
    def test_freeze_holds_history_but_not_dry_capture(self):
        p,c,f,s=self.source();p.set('live.enabled',1);s.render(512)
        data=s.data.copy();position=s.writer;p.set('live.freeze',1);c.value=.4
        np.testing.assert_allclose(s.render(512),.4)
        self.assertEqual(position,s.writer);np.testing.assert_array_equal(data,s.data)
        p.set('live.freeze',0);s.render(512);self.assertNotEqual(position,s.writer)
    def test_pause_releases_capture_without_reopening_during_fade(self):
        p,c,f,s=self.source();p.set('live.enabled',1);s.render(512)
        position=s.writer;p.set('transport.playing',0)
        for _ in range(4):np.testing.assert_allclose(s.render(512),0)
        self.assertIsNone(s.capture);self.assertEqual(c.closed,1);self.assertEqual(s.writer,position)
    def test_ring_wraps_and_stays_bounded(self):
        p,c,f,s=self.source();p.set('live.enabled',1)
        for _ in range(s.capacity//512+2):s.render(512)
        self.assertTrue(0<=s.writer<s.capacity)
        self.assertGreater(s.written,s.capacity)
        np.testing.assert_allclose(s.data,.3)
class Process:
    def __init__(self,fd):self.stdout=os.fdopen(fd,'rb',buffering=0);self.returncode=None
    def poll(self):return self.returncode
    def terminate(self):self.returncode=0
    def wait(self,timeout=None):return self.returncode
    def kill(self):self.returncode=-9
class CaptureTests(unittest.TestCase):
    def test_partial_reads_keep_stereo_frame_alignment(self):
        r,w=os.pipe();process=Process(r)
        values=np.arange(-32,32,dtype='<i2').reshape(32,2);raw=values.tobytes()
        with patch('live_source.subprocess.Popen',return_value=process) as start:
            c=ArecordCapture('plughw:CARD=Series,DEV=0')
        def write():os.write(w,raw[:7]);os.write(w,raw[7:]);os.close(w)
        t=threading.Thread(target=write);t.start()
        try:np.testing.assert_array_equal(c.read(32),values.astype(np.float32)/32768.)
        finally:t.join();c.close()
        self.assertIn('--buffer-time=24000',start.call_args.args[0])
        self.assertTrue(process.stdout.closed)
    def test_timeout_is_bounded(self):
        r,w=os.pipe();process=Process(r)
        with patch('live_source.subprocess.Popen',return_value=process):c=ArecordCapture('test')
        try:
            with patch('live_source.time.monotonic',side_effect=[0,3]):
                with self.assertRaises(TimeoutError):c.read(32)
        finally:os.close(w);c.close()
    def test_ended_stream_raises(self):
        r,w=os.pipe();os.close(w);process=Process(r)
        with patch('live_source.subprocess.Popen',return_value=process):c=ArecordCapture('test')
        try:
            with self.assertRaisesRegex(OSError,'stream ended'):c.read(32)
        finally:c.close()
if __name__=='__main__':unittest.main()
