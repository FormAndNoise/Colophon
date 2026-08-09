"""Verify the fixed worktree pack loads exactly the way ComfyUI loads it.

Replicates nodes.load_custom_node()'s V1 registration path verbatim
(importlib spec_from_file_location on __init__.py, exec_module, then
NODE_CLASS_MAPPINGS / NODE_DISPLAY_NAME_MAPPINGS registration) and then
validates every node's INPUT_TYPES contract the way the ComfyUI frontend
does. A full ComfyUI boot could not be used for verification because the
local ComfyUI install's own venv is broken (transformers requires
tokenizers<=0.23.0 but has 0.23.1 — pre-existing, unrelated to this pack).

Run:  python verify_comfyui_load.py
Exit code 0 = all node contracts valid.
"""
import importlib.util
import os
import sys
import types

WORKTREE = r"H:/New folder/ComfyUI-MiniBook_Node/.worktrees/t_fcf1b743"

# --- stub folder_paths (ComfyUI provides this at runtime) -----------------
if "folder_paths" not in sys.modules:
    stub = types.ModuleType("folder_paths")
    stub.get_folder_paths = lambda key: [WORKTREE]
    stub.get_output_directory = lambda: os.path.join(WORKTREE, "output")
    sys.modules["folder_paths"] = stub

# --- replicate nodes.load_custom_node (V1 path) ---------------------------
sys_module_name = WORKTREE.replace(".", "_x_")
module_spec = importlib.util.spec_from_file_location(
    sys_module_name, os.path.join(WORKTREE, "__init__.py")
)
module = importlib.util.module_from_spec(module_spec)
sys.modules[sys_module_name] = module
module_spec.loader.exec_module(module)

assert hasattr(module, "NODE_CLASS_MAPPINGS")
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
for name, node_cls in module.NODE_CLASS_MAPPINGS.items():
    NODE_CLASS_MAPPINGS[name] = node_cls
    node_cls.RELATIVE_PYTHON_MODULE = "custom_nodes.ComfyUI-MiniBook_Node"
NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)

mb = sorted(k for k in NODE_CLASS_MAPPINGS if "MiniBook" in k or k.startswith("BT"))
print("load_custom_node-equivalent registered nodes:", len(mb))

# --- validate the widget contract the frontend consumes -------------------
problems = []
for key in mb:
    cls = NODE_CLASS_MAPPINGS[key]
    try:
        spec = cls.INPUT_TYPES()
    except Exception as e:
        problems.append(f"{key}: INPUT_TYPES raised {type(e).__name__}: {e}")
        continue
    for group in ("required", "optional"):
        widgets = spec.get(group, {}) or {}
        for name, decl in widgets.items():
            if not isinstance(decl, tuple) or not decl:
                problems.append(f"{key}.{group}.{name}: malformed declaration {decl!r}")
                continue
            wtype = decl[0]
            opts = decl[1] if len(decl) > 1 else {}
            if isinstance(wtype, list):
                if not isinstance(opts, dict):
                    problems.append(f"{key}.{group}.{name}: combo without options dict")
                    continue
                default = opts.get("default")
                if default is not None and default not in wtype:
                    problems.append(
                        f"{key}.{group}.{name}: default {default!r} not in option list"
                    )
    if key not in NODE_DISPLAY_NAME_MAPPINGS:
        problems.append(f"{key}: missing display name")
    if not getattr(cls, "FUNCTION", None) or not hasattr(cls, getattr(cls, "FUNCTION", "")):
        problems.append(f"{key}: FUNCTION missing or unresolvable")
    # OUTPUT_NODE=True nodes are terminals and legitimately have no outputs.
    if not getattr(cls, "OUTPUT_NODE", False) and not getattr(cls, "RETURN_TYPES", None):
        problems.append(f"{key}: RETURN_TYPES empty")

print("widget contract problems:", len(problems))
for p in problems:
    print("  !", p)

# --- smoke-run the repaired compositor through the registered class -------
c = NODE_CLASS_MAPPINGS["MiniBookLayoutCompositor"]()
out = c.compose(
    ["Once upon a time.", "   "],
    ["text_only", "section_break"],
    ["US_Trade_6x9"], ["Z:/missing-font.ttf"], [42], [72], [12.0],
)
print("compose() through registered class ->", tuple(out[0].shape))

sys.exit(1 if problems else 0)
