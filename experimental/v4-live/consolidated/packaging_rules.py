"""Build-time rules for the handheld NumPy runtime, not a development installation."""
from pathlib import PurePosixPath


def include_vendor(relative):
    path=PurePosixPath(relative)
    # Retain legal notices even when their development directory is omitted.
    if path.name.upper().startswith(('LICENSE','COPYING','COPYRIGHT','NOTICE')):return True
    parts=set(path.parts)
    if parts & {'tests','__pycache__','doc','include','f2py','_pyinstaller'}:return False
    if path.suffix in {'.pyc','.pyo','.pyi','.pxd','.h','.hpp','.c','.cpp','.f','.f90'}:return False
    if path.name in {'conftest.py','RECORD','entry_points.txt'}:return False
    return True
