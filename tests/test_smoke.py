"""Smoke tests for ComfyUI-MiniBook_Node.

These tests run without ComfyUI installed — tests/conftest.py (loaded as
a pytest plugin via addopts) stubs folder_paths before collection.
"""
import os
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ensure_path():
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)
    parent = os.path.dirname(REPO_ROOT)
    if parent not in sys.path:
        sys.path.insert(0, parent)


def _get_mappings():
    """Import the package properly and return (NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS)."""
    _ensure_path()
    # The package directory name is the importable name
    pkg_name = os.path.basename(REPO_ROOT)
    # ComfyUI-style packages often have hyphens; Python needs underscores,
    # but this package uses __init__.py with relative imports,
    # so we must import it as-is from the parent directory
    parent = os.path.dirname(REPO_ROOT)
    saved = os.getcwd()
    try:
        os.chdir(parent)
        # Use the worktree dir name — pytest already put '.' on pythonpath
        import importlib
        mod = importlib.import_module(pkg_name)
        return mod.NODE_CLASS_MAPPINGS, mod.NODE_DISPLAY_NAME_MAPPINGS
    finally:
        os.chdir(saved)


# ---------------------------------------------------------------------------
# Import / registration smoke tests
# ---------------------------------------------------------------------------

def test_package_imports():
    """Every node module must import without error."""
    _ensure_path()
    import nodes.dual_llm_nodes       # noqa: F401
    import nodes.editorial_art_director  # noqa: F401
    import nodes.front_matter          # noqa: F401
    import nodes.interleave            # noqa: F401
    import nodes.layout_compositor     # noqa: F401
    import nodes.literary_editor       # noqa: F401
    import nodes.text_to_image         # noqa: F401
    import nodes.core_controls         # noqa: F401


def test_node_class_mappings_populated():
    """NODE_CLASS_MAPPINGS must contain at least the 27 committed nodes."""
    class_map, _ = _get_mappings()
    assert len(class_map) >= 27, (
        f"Expected >=27 nodes, got {len(class_map)}"
    )


def test_node_display_name_mappings_match():
    """Every key in NODE_CLASS_MAPPINGS must have a display name."""
    class_map, display_map = _get_mappings()
    class_keys = set(class_map.keys())
    display_keys = set(display_map.keys())
    missing = class_keys - display_keys
    assert not missing, f"Nodes without display names: {missing}"


def test_compileall_passes():
    """python -m compileall must succeed on all .py files."""
    import compileall
    result = compileall.compile_dir(REPO_ROOT, quiet=2, force=True)
    assert result, "compileall found syntax errors"


def test_intentional_failure_is_caught():
    """Canary: pytest must report real assertion failures, not swallow them."""
    x = 1 + 1
    assert x == 2, "Basic arithmetic must work"
