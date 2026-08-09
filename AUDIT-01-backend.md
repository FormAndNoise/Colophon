# Backend audit

## Findings fixed

1. `nodes/interleave.py:17` — Unequal image batches silently dropped the unpaired tail, and two empty inputs reached `torch.cat` with an opaque error. The implementation now interleaves the common prefix, preserves both tails, and raises a clear `ValueError` for empty input. Regression coverage: `tests/test_backend_regressions.py::test_interleave_preserves_unpaired_images` and `::test_interleave_rejects_empty_inputs_instead_of_torch_cat_failure`.
2. `nodes/layout_compositor.py:301` — Full-illustration captions started below the bottom margin (`page_h - bottom + 20`) and were therefore clipped or never drawn. Captions now start at the inside edge of the bottom margin and stop at the page boundary. Regression coverage: `test_full_illustration_caption_is_rendered_inside_bottom_margin`.
3. `nodes/layout_compositor.py:324` — Section-break divider selection used the raw `text` truthiness while rendering used `text.strip()`, so whitespace-only input could reference uninitialized `start_y`/`line_height`. A normalized `has_text` guard is now shared. Regression coverage: `test_section_break_accepts_whitespace_only_text`.
4. `nodes/llm_bridge.py:3` — Importing the package outside ComfyUI failed immediately because the optional host-only `folder_paths` module was imported unconditionally. The bridge now treats it as optional for import/test discovery and still reports unavailable toolkit usage from `run_llm`. Regression impact: backend modules can be tested without a ComfyUI process.

## Not fixed

The repository has no existing backend test suite and several ComfyUI-only integrations cannot be exercised without a host runtime and configured LLM toolkit. Those are documented as environment limitations rather than guessed fixes.

## Verification

`pytest -q --import-mode=importlib tests/test_backend_regressions.py` — 6 passed (one existing PyNVML deprecation warning).
`python -m compileall -q nodes` — passed.

Note: tests use `--import-mode=importlib` because pytest's default package collection imports the ComfyUI plugin root as a test package; the plugin itself intentionally depends on host-provided modules.
