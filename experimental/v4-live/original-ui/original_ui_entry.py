#!/usr/bin/env python3
"""Separate LIVE-page launcher using V3's actual renderer and V4's audio engine."""
import live_frontend
from native_ui import create_renderer, ensure_v3_closed

if __name__=='__main__':
    print('V4 ORIGINAL UI LIVE 0.2 / audio engine 0.1.1',flush=True)
    ensure_v3_closed()
    live_frontend.main(renderer_factory=create_renderer)
