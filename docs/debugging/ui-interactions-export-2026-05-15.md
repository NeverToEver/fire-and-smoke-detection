# Debugging Session: UI interactions and exports

## SYSTEM CONTEXT
Streamlit pages share upload, selection, result-display, and download workflows across dataset, training, inference, evaluation, hardware, benchmark, and optimization screens.

## PROBLEM STATEMENT

**Symptom**: Drag/drop uploads, ZIP extraction, result clearing, and report downloads behave differently across windows. Some exports rebuild with a new timestamp on every rerun, and the inference ZIP upload path was newly implemented directly in the page.

**Hypotheses**:
1. **Upload layer**: Multiple pages implement upload fingerprinting and ZIP extraction independently, causing stale same-name uploads and unsafe extraction behavior.
2. **State layer**: Pages use different signatures and session keys, so old results can remain visible after input changes.
3. **Export layer**: Pages create export names from `datetime.now()` inside render blocks, so download-button reruns can change filenames and saved artifacts.

## VALIDATION TASKS

### Task 1: Locate duplicated upload and export paths

**Status**: VALIDATED

**Findings**:
- `ui/widgets.py` had dataset ZIP upload with fingerprint checks, while `ui/pages/inference.py` had a separate test-image ZIP upload implementation.
- `ui/pages/inference.py` extracted ZIP files with `ZipFile.extractall` and skipped extraction whenever the destination directory already existed.
- Export blocks in inference, evaluation, hardware, benchmark, and optimization built filenames from `datetime.now()` during render.

**Evidence**:
`rg` found upload/download/session logic across `ui/widgets.py`, `ui/pages/inference.py`, `ui/pages/evaluation.py`, `ui/pages/hardware.py`, `ui/pages/hardware_benchmark.py`, and `ui/pages/optimization.py`.

**Conclusion**: The symptoms are consistent with duplicated local implementations instead of shared runtime behavior.

## ROOT CAUSE ANALYSIS SUMMARY

**Primary Root Cause**: Upload processing, stale-result invalidation, and export preparation were implemented page-by-page with inconsistent session-state rules.

**Confidence Level**: High

**Recommended Fix Priority**:
1. Add shared upload ZIP safety, content fingerprints, result signature clearing, and stable export timestamp helpers.
2. Replace direct ZIP extraction and ad hoc export timestamp creation in high-traffic pages.
3. Add focused tests for ZIP traversal and same-name changed uploads.
