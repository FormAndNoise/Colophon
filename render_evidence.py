"""Render verification evidence PNGs for the caption/margin fix."""
import os
import sys
import types

ROOT = os.path.dirname(os.path.abspath(__file__))
stub = types.ModuleType("folder_paths")
stub.get_folder_paths = lambda key: [ROOT]
stub.get_output_directory = lambda: os.path.join(ROOT, "output")
sys.modules["folder_paths"] = stub

import importlib.util
spec = importlib.util.spec_from_file_location(
    "minibook_pack", os.path.join(ROOT, "__init__.py"),
    submodule_search_locations=[ROOT],
)
pack = importlib.util.module_from_spec(spec)
sys.modules["minibook_pack"] = pack
spec.loader.exec_module(pack)

from PIL import Image

EVIDENCE = os.path.join(ROOT, "verification_evidence")
os.makedirs(EVIDENCE, exist_ok=True)

c = pack.NODE_CLASS_MAPPINGS["MiniBookLayoutCompositor"]()
illust = Image.new("RGB", (600, 600), (10, 120, 200))
caption = ("A rather long caption that will certainly need more than two lines "
           "of text when it is wrapped across the width of the page at this "
           "font size — it now stays inside the content area at every margin.")

for margin_percent in (5.0, 12.0):
    page_w, page_h = 1800, 2700
    mh = int(page_w * margin_percent / 100)
    mv = int(page_h * margin_percent / 100)
    margins = {"left": mh, "right": mh, "top": mv, "bottom": mv}
    page, dropped = c._compose_full_illustration(
        caption, illust, page_w, page_h, margins,
        "Z:/missing.ttf", 42,
    )
    path = os.path.join(EVIDENCE, f"caption_fixed_margin_{int(margin_percent)}pct.png")
    page.save(path)
    print(path, "dropped:", dropped)

# section break whitespace-only (formerly a crash)
page = c._compose_section_break("   ", 1800, 2700,
                                {"left": 216, "right": 216, "top": 324, "bottom": 324},
                                "Z:/missing.ttf", 42)
path = os.path.join(EVIDENCE, "section_break_whitespace_fixed.png")
page.save(path)
print(path)
