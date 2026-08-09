"""conftest.py — stubs ComfyUI's folder_paths before test collection.

Must live under tests/ (not the repo root) to avoid triggering
the package __init__.py during conftest loading.
"""
import os
import sys
import types

# Inject the stub at module scope — this runs before pytest collects tests
if "folder_paths" not in sys.modules:
    _fp = types.ModuleType("folder_paths")
    _fp.get_folder_paths = lambda k: [os.path.abspath(".")]
    _fp.get_output_directory = lambda: os.path.abspath("./output")
    sys.modules["folder_paths"] = _fp
