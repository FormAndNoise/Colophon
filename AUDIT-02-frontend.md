# AUDIT-02 — Front-End / UI-Layer Defects

Repo: `ComfyUI-MiniBook_Node` (ComfyUI custom-node pack, "MiniBook Studio")
Branch: `wt/t_fcf1b743` (worktree at `H:\New folder\ComfyUI-MiniBook_Node\.worktrees\t_fcf1b743`)
Base: `6966da1` (committed tree; the ~2,200-line uncommitted delta in the
primary tree is invisible from any worktree and is out of scope here).
Date: 2026-08-08. Scope: the "front end" of a ComfyUI node pack is its widget
contracts (INPUT_TYPES/registration), rendering/layout code, node discovery,
and the shipped workflow JSONs.

Every finding below was **reproduced with a real execution before fixing**
(reproduction harness `scratch_repro_frontend.py`, deleted after use) and
**re-verified after the fix** by a committed regression test, a rendered
screenshot, or the ComfyUI-loader verification script.

---

## 0. TL;DR

- 18 findings in scope; 16 fixed, 2 documented as intentionally left
  (one of which is a false positive in the parent inventory).
- 4 crash defects fixed (section-break UnboundLocalError, multi-image batch
  ValueError, empty-text max() crash, missing-font OSError in 3 nodes).
- 1 rendering defect fixed (caption drawn inside the reserved bottom margin
  and truncated to 2 lines at margin_percent=5).
- 1 silent-data-loss defect fixed (page text overflow now warns instead of
  dropping lines silently).
- 3 widget-contract defects fixed (PromptSelector INT-vs-STRING, DownloadFont
  unselectable default, fragile INPUT_IS_LIST unwrapping).
- New: `tests/` regression suite (22 tests; baseline was 0 tests collected).
- Gates after: `compileall` PASS, `flake8 --select=E9,F` clean (was 9),
  `pytest` 22 passed, package import via ComfyUI-loader replica registers 27
  nodes with 0 widget-contract problems.

---

## 1. Findings — fixed

### F01 `layout_compositor._compose_section_break` — UnboundLocalError on whitespace-only text
- Location: `nodes/layout_compositor.py` (`_compose_section_break`).
- Symptom: a `section_break` page whose text is whitespace-only raised
  `UnboundLocalError: cannot access local variable 'start_y'`.
- Root cause: `divider_y = int(page_h*0.48) if not text else start_y + line_height`
  read `start_y`/`line_height`, which are only bound inside the
  `if text and text.strip():` branch. `"   "` is truthy so the else-arm ran
  with unbound names.
- Fix: track `text_bottom` only when text was actually drawn; place the
  divider below the text block when present, else at 48% height.
- Verified: repro harness R1 (crashed pre-fix, clean post-fix);
  `tests/test_frontend_fixes.py::test_section_break_*`; screenshot
  `verification_evidence/section_break_whitespace_fixed.png`.

### F02 `layout_compositor.compose` — crash when an illustration wire carries a batch
- Location: `nodes/layout_compositor.py` (`compose`, illustration conversion).
- Symptom: `ValueError: cannot select an axis to squeeze out which has size
  not equal to one` whenever an IMAGE input was a batch tensor with N>1 and a
  page needed an illustration.
- Root cause: `np_img.squeeze(0)` on a (3,H,W,C) tensor; squeeze(0) cannot
  remove a non-unit axis.
- Fix: expand (N,H,W,C) batches into individual PIL images (plus clip+RGB
  normalization) so every illustration page gets exactly one image.
- Verified: repro R2; `test_compose_with_multi_image_illustration_batch`,
  `test_compose_accepts_single_image_tensors_too`.

### F03 `layout_compositor._compose_full_illustration` — caption drawn inside the bottom margin
- Location: `nodes/layout_compositor.py` (`_compose_full_illustration`).
- Symptom: caption started at `page_h - margins["bottom"] + 20`, i.e. inside
  the reserved margin band, and clipped at `page_h - 20`; at margin_percent=5
  only 2 caption lines fit (2,493 caption-ink pixels measured inside the
  margin band pre-fix).
- Root cause: caption geometry ignored the margin model entirely.
- Fix: size the caption first, reserve that block inside the content area,
  and shrink the illustration to yield the room; caption is anchored flush
  above the bottom margin and never spills into it.
- Verified: repro R3 (ink-in-margin assertion failed pre-fix, passes post-fix);
  `test_full_illustration_caption_stays_inside_content_area[5% and 12%]`;
  screenshots `verification_evidence/caption_fixed_margin_5pct.png` and
  `..._12pct.png`.

### F04 Silent page-text truncation
- Location: `_compose_text_only`, `_compose_chapter_opener`,
  `_compose_text_with_illustration`, `_compose_full_illustration`.
- Symptom: overflowing text was dropped with no warning, return value, or log.
- Root cause: draw loops `break` on overflow and return only the page.
- Fix: the composers now return `(page, dropped_lines)`; `compose()` prints a
  per-page warning naming the page and the dropped line count.
- Verified: repro R8; `test_text_only_reports_dropped_lines_on_overflow`,
  `test_text_only_no_drop_for_short_text`.

### F05 Fragile INPUT_IS_LIST scalar unwrapping
- Location: `layout_compositor.compose`.
- Symptom: five hand-written `if isinstance(x, list): x = x[0]` blocks; any new
  scalar widget silently stays wrapped; numeric widgets may arrive as floats.
- Fix: single `_unwrap_scalar` helper (raises on empty list) plus explicit
  `int()`/`float()` coercion for the numeric widgets.
- Verified: `test_compose_unwraps_scalar_widgets_and_coerces_types`.

### F06 `BookToolsRandomTextOverlay` — crash on whitespace-only text
- Location: `nodes/core_controls.py` (`add_random_text_overlay`).
- Symptom: `ValueError: max() arg is an empty sequence` when the text wraps to
  no lines.
- Fix: return the input image unchanged when there is nothing to overlay.
- Verified: repro R4; `test_random_text_overlay_empty_text_returns_image_unchanged`.

### F07 Missing-font crash in three BookTools nodes
- Location: `nodes/core_controls.py` (`BTRandomTextOverlay`,
  `BookToolsCalculateTextGrowth`, `BookToolsImageTextOverlay`).
- Symptom: `OSError: cannot open resource` when the configured font path does
  not exist (the default `C:/Windows/Fonts/arial.ttf` need not exist on
  non-Windows hosts).
- Fix: shared `_safe_truetype()` — requested path → bundled `fonts/` →
  Windows arial → Pillow embedded default; never raises.
- Verified: repro R7a/R7b; `test_*_with_missing_font_does_not_crash`.

### F08 `BookToolsPromptSelector` — widget contract self-contradiction
- Location: `nodes/core_controls.py`.
- Symptom: `selected_indexes` declared `("INT", {"multiline": False, "default": "1,2,3"})`
  (string default on an INT widget) while the docstring promised comma lists
  and ranges, and the body raised unless it received a plain int and could
  select exactly one key.
- Root cause: inherited verbatim from the upstream Book-Tools pack
  (verified in the installed `ComfyUI-Book-Tools/__init__.py`).
- Fix: widget is now `STRING` (matching default and docs); parser accepts
  comma lists and inclusive ranges (`1-3,5`); a legacy plain int still works.
- Verified: repro R5; `test_prompt_selector_*` (contract, ranges, legacy int,
  garbage rejection).

### F09 `BookToolsDownloadFont` — unselectable combo default
- Location: `nodes/core_controls.py`.
- Symptom: `{"default": "Open Sans"}` is not a member of `SUPPORTED_FONTS`;
  the widget default can never be selected and `download_font` would KeyError.
- Fix: default changed to `"Delius"` (first supported font).
- Verified: repro R6; `test_download_font_default_is_a_valid_option`.

### F10 Bare `except:` in text-width helpers
- Location: `nodes/core_controls.py:~502`, `nodes/text_to_image.py:~103`.
- Symptom: bare except would swallow KeyboardInterrupt/SystemExit.
- Fix: narrowed to `except Exception`.
- Verified: `compileall` + full import + BTTextToImage smoke run (gradient,
  background, justification paths).

### F11 Dead `NODE_CLASS_MAPPINGS` in `nodes/interleave.py`
- Location: `nodes/interleave.py` (module bottom).
- Symptom: ComfyUI only discovers the mapping in the package root; the local
  copy was dead code and a trap.
- Fix: removed, with a comment so it is not re-added.
- Verified: import harness still registers 27 nodes.

### F12 `InterleaveImageLists` — opaque crash on empty inputs
- Location: `nodes/interleave.py`.
- Symptom: two empty lists produced a raw `torch.cat` error.
- Fix: raise a clear `ValueError` naming the node.
- Verified: `test_interleave_rejects_empty_inputs`, `test_interleave_alternates_batches`.

### F13–F15 Dead code / unused names (F824/F841/F401)
- F13: `global reset_global` declared but never assigned in
  `BookToolsLoopStart.run/IS_CHANGED` (2× F824) — declarations removed.
- F14: dead locals removed — `usable_width` (front_matter `_compose_toc_page`),
  `effective_height`/redundant textbox math (core_controls `calculate`),
  `text_width`+redundant `text_height` (text_to_image `draw_text_with_border`).
- F15: unused imports removed — `re` (front_matter), `json/re/math`
  (layout_compositor).
- Verified: `flake8 --select=E9,F` exit 0 across the package (was 9 findings).

### F16 Duplicated resize block in `MiniBookAssembler`
- Location: `nodes/editorial_art_director.py`.
- Symptom: near-identical 8-line NHWC→NCHW→interpolate→NHWC blocks for front
  and back pages, each with its own in-branch import.
- Fix: extracted to `_fit_to_body` staticmethod; behaviour unchanged.
- Verified: assembler smoke run with mismatched front/body sizes
  (output shape (5, H, W, C)).

### F17 Windows-only font fallback chain
- Location: `_load_font` in `layout_compositor.py` and `front_matter.py`.
- Symptom: fallback went straight to `C:/Windows/Fonts/arial.ttf`; on a host
  without that path, pages rendered with Pillow's bitmap default.
- Fix: bundled `fonts/` tried before the Windows path.
- Verified: all render tests run with a deliberately missing font path
  (`Z:/nonexistent/font.ttf`) and produce real TTF output.

---

## 2. Findings — intentionally left unfixed

### L01 Parent-inventory false positive: `TextInput` in the shipped workflow is NOT a bug
- The inventory (§5.6) flagged `workflows/minibook_editorial.json` for using
  `TextInput` instead of `MiniBookTextInput`. Investigation shows the five
  `TextInput` nodes carry `properties.cnr_id: "text_processor"` and the
  `separator`+`text1..text7` widget schema of the **external
  ComfyUI_Text_Processor pack**, which registers `"TextInput"`
  (verified in `custom_nodes/ComfyUI_Text_Processor/text_input.py`). This
  pack's `MiniBookTextInput` (single `text` input) is a different node.
- Action taken: an initial "fix" renaming them to `MiniBookTextInput` was
  applied and then **reverted** after the evidence — it would have broken a
  working workflow. The workflow is untouched.
- A regression test pins the correct expectation
  (`test_workflow_node_types_resolve` lists `TextInput` under external packs).

### L02 Legacy/orphaned nodes kept registered
- ~20 of 27 registered nodes are unused by the shipped workflow (three
  paginator generations, BookTools suite, dual text-to-image IDs). Deleting
  them is a product/backwards-compat decision, not a defect fix; the
  registration IDs are deliberately preserved for old workflows
  (`__init__.py` documents this). Left as-is; noted for a future deprecation
  pass.

### L03 Style-level lint debt (W291/W293/E501/…)
- `flake8 --max-line-length=120` still reports ~390 style findings
  (mostly whitespace in `text_to_image.py`). These are cosmetic, not defects;
  the defect gate (`--select=E9,F`) is clean. A style-only cleanup belongs in
  a separate chore commit to keep this branch reviewable.

### L04 ComfyUI full-boot verification not possible on this host
- The local ComfyUI install's own venv is broken (its `transformers`
  requires `tokenizers<=0.23.0` but has 0.23.1) — a pre-existing environment
  issue unrelated to this pack. Verification therefore used a faithful
  replica of `nodes.load_custom_node()`'s V1 registration path
  (`verify_comfyui_load.py`), which registered all 27 nodes with 0 widget
  contract problems.

### L05 Out-of-scope items owned by sibling audits
- Module-scope `import folder_paths` in `llm_bridge.py`, module-global loop
  state, API-key-as-widget, committed `.pyc` files, CI gates — these belong
  to the backend (t_ca244421), security (t_eb89a37f), and devops
  (t_549b2349) audits respectively and were deliberately not touched here.

---

## 3. Verification summary (post-fix)

| Gate | Command | Result |
|---|---|---|
| Bytecode | `python -m compileall -q nodes/ __init__.py tests/` | PASS (exit 0) |
| Defect lint | `python -m flake8 --select=E9,F --exclude=__pycache__ .` | clean (was 9 findings) |
| Tests | `python -m pytest tests/ -q` | **22 passed** (baseline: 0 collected) |
| Import | ComfyUI-stubbed import harness | 27 nodes registered |
| Loader replica | `python verify_comfyui_load.py` | 27 nodes, 0 widget-contract problems |
| Screenshots | `verification_evidence/*.png` | caption inside content area at 5%/12%; section break renders |

Commits on `wt/t_fcf1b743` (base `6966da1`):
1. `762c5ad` fix(layout): compositor crashes + caption/overflow rendering
2. `af2a350` fix(widgets): widget contracts + crash paths in BookTools controls
3. `d806033` fix(front_matter): bundled-font fallback + dead-code cleanup
4. `c85bdd5` fix(interleave): dead mapping + empty-input guard
5. `2ae1bb3` refactor(assembler): dedupe resize helper
6. `636163b` fix(text): narrow bare excepts + dead local
7. `b21d1be` test: regression suite for the fixes
8. (this report + verification tooling)
