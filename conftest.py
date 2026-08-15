"""Shared pytest fixtures for the MiniBook node pack."""
import importlib.util
import os
import sys
import types

ROOT = os.path.dirname(os.path.abspath(__file__))

if "folder_paths" not in sys.modules:
    _stub = types.ModuleType("folder_paths")
    _stub.get_folder_paths = lambda key: [ROOT]
    _stub.get_output_directory = lambda: os.path.join(ROOT, "output")
    sys.modules["folder_paths"] = _stub

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

_spec = importlib.util.spec_from_file_location(
    "minibook_pack", os.path.join(ROOT, "__init__.py"),
    submodule_search_locations=[ROOT],
)
PACK = importlib.util.module_from_spec(_spec)
PACK.__package__ = "minibook_pack"
sys.modules["minibook_pack"] = PACK
_spec.loader.exec_module(PACK)
