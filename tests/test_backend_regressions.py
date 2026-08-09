import importlib.util
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image


def load_node_module(name):
    path = Path(__file__).resolve().parents[1] / "nodes" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


InterleaveImageLists = load_node_module("interleave").InterleaveImageLists
MiniBookLayoutCompositor = load_node_module("layout_compositor").MiniBookLayoutCompositor


def test_interleave_rejects_empty_inputs_instead_of_torch_cat_failure():
    with pytest.raises(ValueError, match="at least one image"):
        InterleaveImageLists().interleave([], [])


def test_interleave_preserves_unpaired_images():
    first = [torch.full((1, 2, 2, 3), 0.1), torch.full((1, 2, 2, 3), 0.2)]
    second = [torch.full((1, 2, 2, 3), 0.3)]
    result = InterleaveImageLists().interleave(first, second)[0]
    assert result.shape[0] == 3
    assert torch.equal(result[2], first[1][0])


def test_full_illustration_caption_is_rendered_inside_bottom_margin():
    page = MiniBookLayoutCompositor()._compose_full_illustration(
        "A short caption.", Image.new("RGB", (20, 20), (10, 10, 10)), 200, 200,
        {"left": 10, "right": 10, "top": 10, "bottom": 40}, "missing-font.ttf", 20)
    pixels = np.asarray(page)
    assert np.any(np.any(pixels[160:200] != (10, 10, 10), axis=2))
    assert np.any(np.any(pixels[160:200] != (252, 250, 245), axis=2))


@pytest.mark.parametrize("text", ["", "   ", "\n\n"])
def test_section_break_accepts_whitespace_only_text(text):
    page = MiniBookLayoutCompositor()._compose_section_break(
        text, 200, 200, {"left": 10, "right": 10, "top": 10, "bottom": 10},
        "missing-font.ttf", 20)
    assert page.size == (200, 200)
