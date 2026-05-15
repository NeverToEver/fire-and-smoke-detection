"""资源扫描与缓存工具"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml

from ui import SCRIPT_DIR, UPLOAD_DIR
from engine.logging import get_logger

_log = get_logger(__name__)


@st.cache_data(ttl=10, show_spinner=False)
def scan_datasets(search_dir: str | None = None):
    """扫描目录下所有 data.yaml / dataset.yaml（含上传目录）"""
    bases = [Path(search_dir)] if search_dir else [
        SCRIPT_DIR, UPLOAD_DIR / "datasets", UPLOAD_DIR / "datasets_extracted"
    ]
    datasets = []
    seen = set()
    for base in bases:
        if not base.exists():
            continue
        for yf in sorted(base.rglob("data*.yaml")):
            rp = str(yf.resolve())
            if rp in seen:
                continue
            seen.add(rp)
            try:
                with open(yf) as f:
                    d = yaml.safe_load(f)
                if "train" not in d and "val" not in d:
                    continue
                nc = d.get("nc", "?")
                names = d.get("names", {})
                label = f"{yf.parent.name}/{yf.name}" if yf.parent != base else yf.name
                datasets.append({
                    "label": f"{label} (nc={nc})",
                    "path": rp,
                    "nc": nc,
                    "names": names,
                })
            except Exception as e:
                _log.warning("扫描数据集文件失败: %s — %s", yf, e)
    return datasets


@st.cache_data(ttl=10, show_spinner=False)
def scan_models(search_dir: str | None = None):
    """扫描 runs/detect/ 和上传目录下所有 best.pt / last.pt"""
    bases = [Path(search_dir)] if search_dir else [
        SCRIPT_DIR / "runs" / "detect", UPLOAD_DIR / "models"
    ]
    models = []
    seen = set()
    for base in bases:
        if not base.exists():
            continue
        for ptf in sorted(base.rglob("*.pt"), key=os.path.getmtime, reverse=True):
            rp = str(ptf.resolve())
            if rp in seen:
                continue
            seen.add(rp)
            mtime = datetime.fromtimestamp(os.path.getmtime(ptf)).strftime("%m-%d %H:%M")
            label = f"{ptf.parent.name}/{ptf.name}" if ptf.parent != base else ptf.name
            models.append({
                "label": f"{label} ({mtime})",
                "path": rp,
                "date": mtime,
            })
    return models


@st.cache_data(ttl=10, show_spinner=False)
def scan_model_configs(search_dir: str | None = None):
    """扫描模型 YAML 配置文件"""
    base = Path(search_dir) if search_dir else SCRIPT_DIR
    configs = []
    for yf in sorted(base.glob("*.yaml")):
        try:
            with open(yf) as f:
                d = yaml.safe_load(f)
            if "backbone" not in d and "head" not in d:
                continue
            configs.append({
                "label": yf.name,
                "path": str(yf.resolve()),
            })
        except Exception as e:
            _log.warning("扫描模型配置文件失败: %s — %s", yf, e)
    return configs


def parse_data_yaml(yaml_path: str) -> dict | None:
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        st.error(f"无法读取 {yaml_path}: {e}")
        return None

    if not isinstance(data, dict):
        st.error(f"{yaml_path} 内容格式错误：需要 YAML 字典，实际为 {type(data).__name__}")
        return None

    train_path = data.get("train", "")
    val_path = data.get("val", "")
    test_path = data.get("test", "")
    nc = data.get("nc", 0)
    names = data.get("names", {})

    yaml_dir = Path(yaml_path).parent
    for key in ["train", "val", "test"]:
        p = data.get(key, "")
        if p and not Path(p).is_absolute():
            data[key] = str((yaml_dir / p).resolve())

    return {
        "train": data.get("train", ""),
        "val": data.get("val", ""),
        "test": data.get("test", ""),
        "nc": nc,
        "names": names,
        "yaml_dir": str(yaml_dir),
    }


def save_uploaded_file(uploaded_file, subdir: str) -> str:
    """保存拖拽上传文件（原子写入），并返回可供现有逻辑使用的本地路径。"""
    safe_name = Path(uploaded_file.name).name
    target_dir = UPLOAD_DIR / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / safe_name
    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(target_dir), prefix=f".tmp_{safe_name}_")
    try:
        with os.fdopen(tmp_fd, "wb") as f:
            f.write(uploaded_file.getbuffer())
        os.replace(tmp_path, target_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    return str(target_path.resolve())


@st.cache_resource(show_spinner=False, max_entries=3)
def load_model_cached(model_path: str, _mtime: float = 0.0):
    from ultralytics import YOLO
    return YOLO(model_path)


@st.cache_data(ttl=10, show_spinner=False)
def get_compute_devices() -> dict:
    """检测当前 Python 环境可用的训练设备（CUDA / MPS / CPU）。"""
    info = {
        "torch_available": False,
        "cuda_available": False,
        "mps_available": False,
        "cuda_count": 0,
        "gpus": [],
        "error": "",
    }
    try:
        import torch
        info["torch_available"] = True
        info["cuda_available"] = torch.cuda.is_available()
        info["mps_available"] = torch.backends.mps.is_available()
        if info["cuda_available"]:
            info["cuda_count"] = torch.cuda.device_count()
            for i in range(info["cuda_count"]):
                info["gpus"].append(torch.cuda.get_device_name(i))
        elif info["mps_available"]:
            info["cuda_count"] = 1
            info["gpus"].append("Apple MPS (Metal)")
    except Exception as e:
        info["error"] = str(e)
    return info
