import multiprocessing as mp
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import wave
import numpy as np
from live_source import SwitchableSource,add_live_parameters
from test_sample_mixer import Bus,Engine
from v4_record_ui import RecordingUI

class Capture:
    def __init__(self):self.offset=0
    def read(self,n):
        values=np.arange(self.offset,self.offset+n,dtype=np.float32)/32768
        self.offset+=n
        return np.column_stack((values,-values))
    def close(self):pass

class FrozenSaveTests(unittest.TestCase):
    def make_source(self,shared=False):
        bus=add_live_parameters(Bus());bus.set('live.enabled',1)
        bus.values.update({'grain.size':.1,'grain.density':10})
        raw=mp.RawArray('f',96*2) if shared else None
        storage=np.frombuffer(raw,dtype=np.float32).reshape(96,2) if shared else None
        source=SwitchableSource(Engine(types.SimpleNamespace(),bus,8),bus,Engine,Capture,rate=8,seconds=12,storage=storage)
        source._test_raw=raw
        self.addCleanup(source.close)
        return bus,source
    def test_partial_and_wrapped_history_are_saved_in_chronological_order(self):
        for blocks in (1,8):
            bus,source=self.make_source()
            for _ in range(blocks):source.render(17)
            bus.set('live.freeze',1);source.render(17)
            audio=source.frozen_snapshot();total=blocks*17;count=min(total,96)
            expected=np.concatenate((np.zeros(96-count,dtype=np.float32),np.arange(total-count,total,dtype=np.float32)/32768))
            np.testing.assert_array_equal(audio[:,0],expected)
            np.testing.assert_array_equal(audio[:,1],-audio[:,0])
            held=audio.copy();source.render(17)
            np.testing.assert_array_equal(source.frozen_snapshot(),held)
    def test_unfrozen_unacknowledged_empty_and_new_session_cannot_save_stale_data(self):
        bus,source=self.make_source()
        with self.assertRaisesRegex(ValueError,'FREEZE'):source.frozen_snapshot()
        bus.set('live.freeze',1)
        with self.assertRaisesRegex(ValueError,'SETTLING'):source.frozen_snapshot()
        source.render(17)
        with self.assertRaisesRegex(ValueError,'NO LIVE'):source.frozen_snapshot()
        bus.set('live.freeze',0);source.render(17);bus.set('live.freeze',1);source.render(17)
        self.assertEqual(len(source.frozen_snapshot()),96)
        source.writer=0;source.written=0
        with self.assertRaisesRegex(ValueError,'SETTLING'):source.frozen_snapshot()
    def test_ui_reads_worker_shared_history_not_parent_private_counters(self):
        bus,source=self.make_source(shared=True)
        ctx=mp.get_context('fork');parent,child=ctx.Pipe()
        def worker():
            for _ in range(8):source.render(17)
            bus.set('live.freeze',1);source.render(17)
            child.send('ready');child.recv()
        process=ctx.Process(target=worker);process.start()
        try:
            self.assertTrue(parent.poll(5));self.assertEqual(parent.recv(),'ready')
            self.assertEqual(source.writer,0);self.assertEqual(source.written,0)
            bus.set('live.freeze',1)
            np.testing.assert_array_equal(source.frozen_snapshot()[:,0],np.arange(40,136,dtype=np.float32)/32768)
        finally:
            if process.is_alive():parent.send('done')
            process.join(5)
            if process.is_alive():process.terminate();process.join()
            parent.close();child.close()
        self.assertEqual(process.exitcode,0)
    def test_wav_round_trip_unique_names_and_live_state_retained(self):
        bus,source=self.make_source();source.render(17);bus.set('live.freeze',1);source.render(17)
        c=types.SimpleNamespace(active=lambda:True,source=lambda:source,message='')
        main=types.SimpleNamespace(audio_worker=types.SimpleNamespace(running=True))
        ui=RecordingUI(main,c)
        with tempfile.TemporaryDirectory() as root,patch('v4_record_ui.__file__',str(Path(root)/'v4_record_ui.py')):
            ui.save_frozen_sample();ui.save_frozen_sample()
            files=list((Path(root)/'samples'/'recordings').glob('*.wav'));self.assertEqual(len(files),2)
            for path in files:
                with wave.open(str(path),'rb') as saved:
                    self.assertEqual((saved.getframerate(),saved.getnchannels(),saved.getsampwidth(),saved.getnframes()),(8,2,2,96))
                    data=np.frombuffer(saved.readframes(96),dtype='<i2').reshape(-1,2)
                    np.testing.assert_array_equal(data[:,0],np.concatenate((np.zeros(79),np.arange(17))))
                    np.testing.assert_array_equal(data[:,1],-np.concatenate((np.zeros(79),np.arange(17))))
            self.assertTrue(c.message.startswith('SAVED '))
        self.assertEqual(bus.get('live.enabled'),1);self.assertEqual(bus.get('live.freeze'),1)
