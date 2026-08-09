"""Regression tests for the AUDIT-02 front-end fixes.

Each test reproduces a defect that was verified broken before the fix
(see AUDIT-02-frontend.md). Run with:  python -m pytest tests/ -q
"""
import json
import os

import pytest
import torch
from PIL import Image

from conftest import PACK

MAPPINGS = PACK.NODE_CLASS_MAPPINGS

PAGE_W, PAGE_H = 1800, 2700  # US_Trade_6x9 @ 300 DPI
MARGINS_12 = {"left": 216, "right": 216, "top": 324, "bottom": 324}
MARGINS_5 = {"left": 90, "right": 90, "top": 135, "bottom": 135}
FONT = "Z:/nonexistent/font.ttf"  # forces the bundled-font fallback


# --------------------------------------------------------------------------
# R1 — layout_compositor: section_break whitespace-only text (UnboundLocalError)
# --------------------------------------------------------------------------

def test_section_break_whitespace_only_text_does_not_crash():
    c = MAPPINGS["MiniBookLayoutCompositor"]()
    page = c._compose_section_break("   ", PAGE_W, PAGE_H, MARGINS_12, FONT, 42)
    assert page.size == (PAGE_W, PAGE_H)


def test_section_break_empty_and_normal_text_render():
    c = MAPPINGS["MiniBookLayoutCompositor"]()
    for text in ("", None, "Interlude", "A longer section break epigraph line"):
        page = c._compose_section_break(text, PAGE_W, PAGE_H, MARGINS_12, FONT, 42)
        assert page.size == (PAGE_W, PAGE_H)


# --------------------------------------------------------------------------
# R2 — layout_compositor: compose() crashed on multi-image illustration batch
# --------------------------------------------------------------------------

def test_compose_with_multi_image_illustration_batch():
    c = MAPPINGS["MiniBookLayoutCompositor"]()
    batch = torch.rand(3, 64, 64, 3)  # one IMAGE wire carrying 3 images
    out = c.compose(
        ["one", "two", "three"],
        ["full_illustration", "text_with_illustration", "text_only"],
        ["US_Trade_6x9"], [FONT], [42], [72], [12.0],
        illustrations=[batch],
    )
    (result,) = out
    assert result.shape[0] == 3  # one composed page per input page
    assert result.shape[1:] == (PAGE_H, PAGE_W, 3)


def test_compose_accepts_single_image_tensors_too():
    c = MAPPINGS["MiniBookLayoutCompositor"]()
    single = torch.rand(1, 64, 64, 3)
    out = c.compose(
        ["caption text"], ["full_illustration"],
        ["US_Trade_6x9"], [FONT], [42], [72], [12.0],
        illustrations=[single],
    )
    assert out[0].shape[0] == 1


def test_compose_unwraps_scalar_widgets_and_coerces_types():
    c = MAPPINGS["MiniBookLayoutCompositor"]()
    # scalars arrive wrapped in lists under INPUT_IS_LIST=True; numeric
    # widgets may arrive as floats from the frontend.
    out = c.compose(["hi"], ["text_only"],
                    ["A5"], [FONT], [42.0], [72], [12])
    a5_h = MAPPINGS["MiniBookLayoutCompositor"].SHEET_DIMS["A5"][1]
    assert out[0].shape[1] == a5_h


# --------------------------------------------------------------------------
# R3 — layout_compositor: caption drawn below the bottom margin
# --------------------------------------------------------------------------

@pytest.mark.parametrize("margins", [MARGINS_5, MARGINS_12])
def test_full_illustration_caption_stays_inside_content_area(margins):
    c = MAPPINGS["MiniBookLayoutCompositor"]()
    illust = Image.new("RGB", (400, 400), (10, 120, 200))
    caption = ("A rather long caption that will certainly need more than two "
               "lines of text when it is wrapped across the width of the page "
               "at this font size, no matter what the margin is.")
    page, dropped = c._compose_full_illustration(
        caption, illust, PAGE_W, PAGE_H, margins, FONT, 42
    )
    assert dropped == 0
    px = page.load()
    # No caption-coloured (or any non-paper, non-illustration) ink may appear
    # inside the bottom margin band. Caption fill is grey (100,100,100).
    for y in range(PAGE_H - margins["bottom"], PAGE_H):
        for x in range(0, PAGE_W, 6):
            assert px[x, y] == (252, 250, 245), f"ink at ({x},{y}) in margin band"


def test_full_illustration_reserves_room_for_caption():
    c = MAPPINGS["MiniBookLayoutCompositor"]()
    illust = Image.new("RGB", (400, 400), (10, 120, 200))
    page, dropped = c._compose_full_illustration(
        "Short caption.", illust, PAGE_W, PAGE_H, MARGINS_12, FONT, 42
    )
    assert dropped == 0
    # The illustration must not cover the caption band: sample a pixel just
    # above the bottom margin; it should be paper (252,250,245) or caption ink.
    sample = page.load()[PAGE_W // 2, PAGE_H - MARGINS_12["bottom"] - 5]
    assert sample == (252, 250, 245) or sample == (100, 100, 100)


# --------------------------------------------------------------------------
# R8 — layout_compositor: silent text truncation now reported
# --------------------------------------------------------------------------

def test_text_only_reports_dropped_lines_on_overflow():
    c = MAPPINGS["MiniBookLayoutCompositor"]()
    page, dropped = c._compose_text_only(
        "word " * 3000, PAGE_W, PAGE_H, MARGINS_12, FONT, 42
    )
    assert dropped > 0
    assert page.size == (PAGE_W, PAGE_H)


def test_text_only_no_drop_for_short_text():
    c = MAPPINGS["MiniBookLayoutCompositor"]()
    _, dropped = c._compose_text_only("A short page.", PAGE_W, PAGE_H, MARGINS_12, FONT, 42)
    assert dropped == 0


# --------------------------------------------------------------------------
# R4 — core_controls: BTRandomTextOverlay crashed on whitespace-only text
# --------------------------------------------------------------------------

def test_random_text_overlay_empty_text_returns_image_unchanged():
    n = MAPPINGS["BTRandomTextOverlay"]()
    img = torch.rand(1, 64, 64, 3)
    (out,) = n.add_random_text_overlay(
        img, "   ", 30, FONT, "#000000", 20, 20, 15, 1.2
    )
    assert out.shape == img.shape
    # The passthrough still round-trips uint8 quantization like the normal
    # path, so compare within one quantization step (1/255).
    assert torch.allclose(out, img, atol=1.0 / 255 + 1e-6)


def test_random_text_overlay_with_missing_font_does_not_crash():
    n = MAPPINGS["BTRandomTextOverlay"]()
    img = torch.rand(1, 128, 128, 3)
    (out,) = n.add_random_text_overlay(
        img, "Hello", 30, FONT, "#000000", 20, 20, 15, 1.2
    )
    assert out.shape == img.shape


def test_image_text_overlay_with_missing_font_does_not_crash():
    n = MAPPINGS["BTImageTextOverlay"]()
    img = torch.rand(1, 128, 128, 3)
    (out,) = n.add_text_overlay(
        img, "Hello", 200, 200, 80, 12, FONT, "center", "#000000",
        0, 0, 20, 1.2,
    )
    assert out.shape == img.shape


def test_text_growth_with_missing_font_does_not_crash():
    n = MAPPINGS["BTTextGrowth"]()
    (growth,) = n.calculate("Hello world", 200, 200, 12, FONT, 50, 1.2)
    assert isinstance(growth, int)


# --------------------------------------------------------------------------
# R5 — core_controls: BTPromptSelector widget contract
# --------------------------------------------------------------------------

def test_prompt_selector_widget_is_string_with_valid_default():
    spec = MAPPINGS["BTPromptSelector"].INPUT_TYPES()["required"]["selected_indexes"]
    assert spec[0] == "STRING"
    assert isinstance(spec[1]["default"], str)


def test_prompt_selector_accepts_comma_list_and_ranges():
    n = MAPPINGS["BTPromptSelector"]()
    d = {"1": "a", "2": "b", "3": "c", "5": "e"}
    assert n.main(d, "1,2,3") == ("a\nb\nc",)
    assert n.main(d, "1-3,5") == ("a\nb\nc\ne",)
    assert n.main(d, 2) == ("b",)  # legacy INT widget value still works
    assert n.main(d, "9") == ("",)  # missing key -> empty string


def test_prompt_selector_rejects_garbage():
    n = MAPPINGS["BTPromptSelector"]()
    with pytest.raises(ValueError):
        n.main({"1": "a"}, "x,y")
    with pytest.raises(ValueError):
        n.main({"1": "a"}, "1-z")


# --------------------------------------------------------------------------
# R6 — core_controls: BTDownloadFont combo default must be selectable
# --------------------------------------------------------------------------

def test_download_font_default_is_a_valid_option():
    spec = MAPPINGS["BTDownloadFont"].INPUT_TYPES()["required"]["font_name"]
    options, cfg = spec[0], spec[1]
    assert cfg["default"] in options


# --------------------------------------------------------------------------
# Registry invariants (node discovery is the ComfyUI "frontend" contract)
# --------------------------------------------------------------------------

def test_registry_maps_are_consistent():
    display = PACK.NODE_DISPLAY_NAME_MAPPINGS
    assert set(MAPPINGS) == set(display), "class/display mapping keys diverge"


def test_workflow_node_types_resolve():
    """Every node type in the shipped workflow must be either one of our
    registered nodes or a known external pack node."""
    wf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "workflows", "minibook_editorial.json")
    external = {
        "CLIPTextEncode", "CLIPVisionLoader", "CheckpointLoaderSimple",
        "EmptyLatentImage", "IPAdapterFaceID", "IPAdapterInsightFaceLoader",
        "IPAdapterUnifiedLoaderFaceID", "KSampler", "LLMToolkitTextGenerator",
        "LoadImage", "VAEDecode", "APIProviderSelectorNode",
        "FL_ImageListToImageBatch", "FL_ImagesToPDF", "FL_PDFSaver",
        "TextInput",  # registered by the external ComfyUI_Text_Processor pack
    }
    with open(wf_path, encoding="utf-8") as f:
        wf = json.load(f)
    unresolvable = [
        (n["id"], n["type"]) for n in wf["nodes"]
        if n["type"] not in MAPPINGS and n["type"] not in external
    ]
    assert unresolvable == []


def test_interleave_rejects_empty_inputs():
    n = MAPPINGS["InterleaveImageLists"]()
    with pytest.raises(ValueError):
        n.interleave([], [])


def test_interleave_alternates_batches():
    n = MAPPINGS["InterleaveImageLists"]()
    a = torch.rand(2, 4, 4, 3)
    b = torch.rand(2, 4, 4, 3)
    (out,) = n.interleave([a], [b])
    assert out.shape[0] == 4
