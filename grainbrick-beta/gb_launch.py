# Public bootstrap, deliberately contains no proprietary application source.
# + RG40XX H patch: scales the Brick 1024x768 UI to the real screen.
import importlib
import importlib.util
import os
from pathlib import Path
import platform
import sys

APP = Path(__file__).resolve().parent
if sys.version_info[:2] != (3, 12):
    raise SystemExit('GrainBrick: KNULLI Python 3.12 required')
if platform.machine().lower() not in ('aarch64', 'arm64'):
    raise SystemExit('GrainBrick: ARM64 required')

# Import official KNULLI pygame/numpy before adding this app directory, so
# an old standalone release's leftover folders cannot shadow system packages.
sys.path[:] = [p for p in sys.path if Path(p or os.getcwd()).resolve() != APP]
import pygame
try:
    import numpy
except ModuleNotFoundError:
    # KNULLI Scarab 20260511 provides pygame but not necessarily numpy.
    # GrainBrick's official release bundles its tested NumPy 1.26.4 under
    # _vendor, so use that copy when system NumPy is unavailable.
    vendor = APP / '_vendor'
    if vendor.is_dir():
        sys.path.insert(0, str(vendor))
        import numpy
    else:
        raise
pygame_location = Path(pygame.__file__).resolve()
numpy_location = Path(numpy.__file__).resolve()
if APP == pygame_location or APP in pygame_location.parents:
    raise SystemExit('GrainBrick: embedded pygame detected: ' + str(pygame_location))
print('PYGAME:', pygame_location, 'NUMPY:', numpy_location, flush=True)
# Preload surfarray while the bundled NumPy path is definitely available.
# GrainBrick's native startup can alter import paths before the renderer first
# accesses pygame.surfarray; eager loading avoids that late lazy-import failure.
try:
    import pygame.surfarray as _pygame_surfarray
    print('PYGAME SURFARRAY:', Path(_pygame_surfarray.__file__).resolve(), flush=True)
except Exception as exc:
    raise SystemExit('GrainBrick: pygame.surfarray preload failed: ' + repr(exc))

# GrainBernik adapters for RG40XX H: button layout first (may show the
# one-time calibration screen), then screen scaling 1024x768 -> 640x480.
def _load_adapter(name):
    path = APP / (name + '.py')
    if not path.is_file():
        return
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.install()
    except Exception as exc:
        print('GRAINBERNIK ADAPTER FAILED:', name, repr(exc), flush=True)

_load_adapter('gb_audio')
_load_adapter('gb_buttons')
_load_adapter('gb_display_fit')

os.environ['GRAINBRICK_ROOT'] = str(APP)
sys.path.insert(0,str(APP))
importlib.import_module('main')
