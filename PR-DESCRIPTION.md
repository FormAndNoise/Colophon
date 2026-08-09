# PR: Audit consolidation — backend + front-end + security + workflows, QA-verified

**Base:** main  **Head:** wt/t_941e43e7
**Create at:** https://github.com/FormAndNoise/ComfyUI-MiniBook_Node/pull/new/wt/t_941e43e7

## Summary
Integration of all four audit streams (backend, front-end, security/config, workflows)
into a single QA-verified branch. Full details in **AUDIT-SUMMARY.md**.

## Gates (clean run)
- compileall: PASS
- flake8 E9/F: 0 findings (was 9)
- pytest: 33 passed (baseline: 0 collected)
- import smoke: 27 nodes registered, 0 widget-contract problems

## Highlights
- Backend: unpaired interleave images no longer dropped; clear error on empty input;
  guarded ComfyUI import.
- Front-end: 4 crash fixes, caption/overflow rendering fixes, widget-contract repairs,
  22-test suite.
- Security: font downloader restricted to https://fonts.gstatic.com, timeouts, 20 MiB
  cap, font-name validation.
- Workflows: CI quality gates (validate job + ci.yml), deps declared, .pyc/dead-mapping
  cleanup.

## QA verification
Every claimed fix independently re-verified against the pre-fix commit. Cross-audit
conflicts resolved (pytest module identity, interleave message, caption-placement
semantics). End-to-end flows pass.

## Known follow-ups (documented, non-blocking)
- verify_comfyui_load.py resolves nodes against a hardcoded (wrong) worktree path.
- ~390 style-level lint findings deferred to a style-only chore.
- Full real ComfyUI boot blocked by a pre-existing broken venv (tokenizers pin).

See AUDIT-SUMMARY.md for the consolidated findings table and sign-off.
