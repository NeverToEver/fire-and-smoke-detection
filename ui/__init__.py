"""Streamlit UI 包 — 共享常量与路径"""

from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent  # 项目根目录 fireandsomke_detection/
UPLOAD_DIR = SCRIPT_DIR / ".streamlit_uploads"
