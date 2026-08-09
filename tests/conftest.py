"""Shared pytest fixtures for the MiniBook node pack.

The pack is normally loaded in place by ComfyUI. To run the suite standalone
we stub out ComfyUI's ``folder_paths`` module and import the package root
``__init__.py`` directly by path, so the checkout directory name (hyphens
included) never matters.
"""
import importlib.util
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if "folder_paths" not in sys.modules:
    _stub = types.ModuleType("folder_paths")
    _stub.get_folder_paths = lambda key: [ROOT]
    _stub.get_output_directory = lambda: os.path.join(ROOT, "output")
    sys.modules["folder_paths"] = _stub

_spec = importlib.util.spec_from_file_location(
    "minibook_pack", os.path.join(ROOT, "__init__.py"),
    submodule_search_locations=[ROOT],
)
PACK = importlib.util.module_from_spec(_spec)
sys.modules["minibook_pack"] = PACK
_spec.loader.exec_module(PACK)
