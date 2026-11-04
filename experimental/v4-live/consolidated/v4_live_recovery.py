"""App-level opt-in for LIVE capture catch-up, shared with the audio worker."""
import json
from multiprocessing import RawValue
from pathlib import Path
from v4_install import write_json


class RecoverySettings:
    def __init__(self,app,controller):
        self.path=Path(app)/'config.json';self.controller=controller
        try:data=json.loads(self.path.read_text())
        except (OSError,ValueError):data={}
        enabled=isinstance(data,dict) and data.get('live_recovery_enabled') is True
        self.shared_enabled=RawValue('b',int(enabled))
    @property
    def enabled(self):return bool(self.shared_enabled.value)
    def set_enabled(self,enabled):
        data=json.loads(self.path.read_text())
        if not isinstance(data,dict):raise ValueError('Device config must be an object')
        data['live_recovery_enabled']=bool(enabled)
        write_json(self.path,data)
        self.shared_enabled.value=int(bool(enabled))
        print('LIVE INPUT RECOVERY:', 'ON - STALE INPUT MAY BE SKIPPED' if self.enabled else 'OFF - NO RECOVERY SKIPS',flush=True)
    def install(self):
        original=self.controller.capture_factory
        def capture():
            result=original();result.recovery_enabled=self.shared_enabled
            print('LIVE INPUT RECOVERY:', 'ON' if self.enabled else 'OFF',flush=True)
            return result
        self.controller.capture_factory=capture
        self.controller.recovery_settings=self
        return self
