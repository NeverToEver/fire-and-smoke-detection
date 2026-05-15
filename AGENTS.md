# Repository Guidelines

## Project Structure & Module Organization

This repository is a Python Streamlit application for fire/smoke detection with Ultralytics YOLO and custom MobileNetV3 model components.

- `app.py` starts the Streamlit UI.
- `train.py` provides CLI training entry points.
- `ui/` contains shared UI helpers, scanners, themes, widgets, and page modules under `ui/pages/`.
- `engine/` contains training, logging, benchmark, and monitor utilities.
- `models/` registers custom YOLO modules used by YAML model definitions.
- `configs/` stores model architecture YAML files.
- `docs/audits/` contains review notes and audit reports.
- Runtime outputs such as `runs/`, `eval_results/`, `.streamlit_uploads/`, `.runtime_cache/`, `*.log`, and model weights should stay out of source changes unless explicitly needed.

## Build, Test, and Development Commands

Create and populate a local environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the app locally:

```bash
.venv/bin/python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
```

Run CLI training:

```bash
python train.py --data /path/to/data.yaml --model configs/yolo11-mobilenetv3-p2.yaml
```

Use `python -m py_compile app.py train.py ui/*.py ui/pages/*.py engine/*.py models/*.py` for a quick syntax check when no tests cover a change.

## Coding Style & Naming Conventions

Use Python 3 style with 4-space indentation, type hints where they clarify interfaces, and small functions around Streamlit page actions. Keep filenames and modules lowercase with underscores, e.g. `training_monitor.py`. Use `snake_case` for functions and variables, `PascalCase` for classes, and constants in `UPPER_SNAKE_CASE`. Keep user-facing UI text consistent with the existing Chinese interface.

## Testing Guidelines

No formal test suite is currently committed. For non-trivial logic, add focused `pytest` tests under `tests/` using `test_*.py` names. Prioritize scanner/path handling, model config discovery, cleanup behavior, and error handling around training and inference. Avoid tests that require GPU hardware unless clearly marked and optional.

## Commit & Pull Request Guidelines

History uses Conventional Commit-style prefixes, including `feat:`, `fix:`, `refactor:`, and `docs:`. Keep subjects concise and specific; Chinese or English is acceptable if consistent with the surrounding work.

Pull requests should include a short summary, validation commands run, affected UI pages or training paths, linked issues when available, and screenshots for visible Streamlit changes. Note any new dependency, dataset assumption, model weight, or hardware requirement.

## Security & Configuration Tips

Do not commit private datasets, local absolute paths, API keys, uploaded files, or large generated weights. Prefer documenting required paths in examples and keep environment-specific files local.
