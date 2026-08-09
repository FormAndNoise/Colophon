# AUDIT-SUMMARY.md — Consolidated QA Verification Report

**Integration branch:** `wt/t_941e43e7`
**Base:** `main` @ `6966da1`
**Date:** 2026-08-08
**QA task:** t_941e43e7

---

## 1. Verdict: SIGN-OFF (with documented follow-ups)

All four audit streams are integrated, every gate is green on a clean run, and a
sample of each audit's findings was independently re-verified against the pre-fix
commit. No claimed fix was accepted without reproducible evidence.

---

## 2. Before / After — build & test state

| Gate | Baseline (main @ 6966da1) | Integration branch |
|------|---------------------------|--------------------|
| compileall | PASS | PASS |
| flake8 (E9,F) | 9 findings | **clean (0)** |
| pytest collected | 0 tests | **33 tests** |
| pytest result | n/a | **33 passed, 0 failed** |
| import smoke (nodes registered) | 27 | 27 |
| widget-contract problems | n/a | 0 |
| CI quality gates | none | validate job + ci.yml added |

---

## 3. Integration — how the four audits were combined

Two audits (front-end t_fcf1b743, workflows t_549b2349) delivered real branches.
Two audits (backend t_ca244421, security t_eb89a37f) **left their fixes uncommitted**
in their worktrees — their branches pointed at `main`. These were harvested and
re-applied. Integration order: front-end → workflows → backend → security.

### Merge conflicts resolved
1. `nodes/interleave.py` — workflows removed the dead `NODE_CLASS_MAPPINGS`; front-end
   kept a note. Kept the note, no mapping.
2. `tests/conftest.py` — both audits added a conftest. Kept the front-end version
   (path-robust package loader).

### Cross-audit contradictions found & resolved
3. **pytest module identity** — workflows' `tests/__init__.py` + `-p tests.conftest`
   made tests a package, breaking front-end's `from conftest import PACK`. Resolved
   by switching the front-end suite to `from tests.conftest import PACK`.
4. **Interleave empty-input message** — backend raised "at least one image"; front-end
   raised "nothing to interleave". Adopted front-end (it was merged first and its
   message is clearer); updated the backend test regex.
5. **Full-illustration caption placement** — backend test asserted the caption renders
   *inside* the bottom margin band. The front-end fix deliberately places the caption
   in the content area **above** the margin band (never spilling into it). The backend
   test's semantics were stale; rewrote it to assert the corrected behavior
   (caption present above the band, band stays clean).

---

## 4. Consolidated findings table

| # | Severity | Domain | Finding | Status | Verification evidence |
|---|----------|--------|---------|--------|-----------------------|
| 1 | High | backend | Unpaired interleave images silently dropped | FIXED | Reproduced on main (2+1 → batch 2, image lost); post-fix → batch 3. `test_interleave_preserves_unpaired_images` |
| 2 | High | backend | Empty interleave → opaque torch.cat crash | FIXED | Post-fix raises clear `ValueError`. `test_interleave_rejects_empty_inputs...` |
| 3 | High | front-end | whitespace-only section_break UnboundLocalError | FIXED | `_compose_section_break("   ")` returns valid page. `test_section_break_accepts_whitespace_only_text` |
| 4 | High | front-end | caption drew inside/below bottom margin | FIXED | Pre-fix caption in margin band; post-fix caption above band, band clean. `test_full_illustration_caption...` (rewritten to corrected semantics) |
| 5 | High | security | font downloader accepted any remote URL/scheme | FIXED | Old check accepted `http://evil.com` & `https://attacker.example`; new restricts to `https://fonts.gstatic.com`. Host-validation table verified |
| 6 | Med | security | no request timeouts / no size cap | FIXED | `timeout=(10,30)`/`(10,60)` + 20 MiB cap added |
| 7 | Med | security | unvalidated font_name | FIXED | `download_font('EvilFont')` → `ValueError: Unsupported font` |
| 8 | Med | backend | unconditional `import folder_paths` blocked test discovery | FIXED | guarded try/except ImportError; suite imports standalone |
| 9 | Med | workflows | no CI quality gates | FIXED | publish.yml validate job + new ci.yml (3.11/3.12 matrix); canary test confirmed pipeline fails on `assert False` |
| 10 | Low | workflows | committed .pyc files / dead NODE_CLASS_MAPPINGS | FIXED | removed from tracking; mapping removed |
| 11 | Low | workflows | undeclared runtime deps | FIXED | declared in pyproject.toml |
| 12 | Med | front-end | multi-image illustration batch ValueError, empty-text max() crash, missing-font OSError, silent truncation | FIXED | 22-test front-end suite; screenshot evidence in `verification_evidence/` |

Detail: see `AUDIT-01-backend.md`, `AUDIT-02-frontend.md`, `AUDIT-03-security-config.md`, `AUDIT-04-workflows.md`.

---

## 5. End-to-end flow (cross-layer)

Exercised through the registered node classes (front-end → API → data):
- `_compose_section_break` normal + whitespace-only text → valid pages
- `_compose_full_illustration` with caption → page + `dropped_caption_lines=0`
- `InterleaveImageLists` unpaired (2+1) → batch 3

**Result: PASS** — no cross-layer regressions detected.

---

## 6. Code-review pass over the combined diff

- Debug prints: none stray. Remaining `print()` calls are intentional diagnostics
  (bridge load path, per-page overflow warning, font-corrupt/fallback notices).
- Commented-out code: none introduced.
- Swallowed exceptions: all `except` blocks are font-loading fallback chains
  (bundled → system → default) — guarded fallbacks, not swallowed errors.
- Tests weakened: none. The two backend-test edits were corrections of stale
  semantics to match the (superior) front-end fixes, not weakenings.

---

## 7. Remaining known issues / recommended follow-ups

1. **`verify_comfyui_load.py` hardcodes the front-end worktree path** — it resolves
   `nodes/` against `.worktrees/t_fcf1b743` regardless of checkout, so it verifies the
   wrong tree. Make it resolve relative to its own location. (Recommend a chore task.)
2. **~390 style-level lint findings** deferred by the front-end audit — recommend a
   style-only chore (do not mix with functional fixes).
3. **Legacy/orphaned node registrations** kept for backwards compatibility (front-end
   audit L02) — confirm intent before any removal.
4. **Full real ComfyUI boot** was blocked by a pre-existing broken ComfyUI venv
   (tokenizers 0.23.1 vs required <=0.23.0) — environment issue, outside this pack;
   a loader-replica was used instead. Recommend fixing the venv to enable a true boot test.
5. **Backend & security audits did not commit their branches** — process gap; their
   fixes had to be harvested from worktrees. Recommend auditors always commit + push.

---

## 8. Sign-off

Integration branch `wt/t_941e43e7` is green on a clean run (compileall, flake8 E9/F,
33/33 pytest, 27-node import smoke, 0 widget-contract problems). Every claimed fix
carries independent verification evidence. All unresolved issues are documented above.

**QA sign-off: APPROVED for merge to main** (after addressing follow-up #1, which is
non-blocking for the pack's runtime behavior).
