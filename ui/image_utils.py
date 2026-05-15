"""图像处理与硬件预估工具函数"""

import os
from pathlib import Path

from engine.logging import get_logger

_log = get_logger(__name__)


def find_label_path(image_path: str) -> str | None:
    p = Path(image_path)
    parts = list(p.parts)
    for i, part in enumerate(parts):
        if part == "images":
            parts[i] = "labels"
            break
    label_path = Path(*parts).with_suffix(".txt")
    return str(label_path) if label_path.exists() else None


def draw_boxes_cv2(image, labels_path: str, class_names: dict, conf_threshold=0.0):
    import cv2
    if image is None:
        return image
    h, w = image.shape[:2]
    try:
        with open(labels_path) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                cls_id = int(parts[0])
                cx, cy, bw, bh = map(float, parts[1:5])
                conf = float(parts[5]) if len(parts) >= 6 else 1.0
                if conf < conf_threshold:
                    continue
                x1 = int((cx - bw / 2) * w)
                y1 = int((cy - bh / 2) * h)
                x2 = int((cx + bw / 2) * w)
                y2 = int((cy + bh / 2) * h)
                name = class_names.get(cls_id, str(cls_id))
                color = (0, 0, 255) if cls_id == 0 else (0, 255, 255)
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                label = f"{name} {conf:.2f}"
                cv2.putText(image, label, (x1, max(y1 - 5, 15)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    except Exception:
        pass
    return image


def get_image_files(dir_path: str, limit=500) -> list[str]:
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    files = []
    if not dir_path or not Path(dir_path).exists():
        return files
    for root, _, filenames in os.walk(dir_path):
        for f in filenames:
            if Path(f).suffix.lower() in exts:
                files.append(os.path.join(root, f))
                if len(files) >= limit:
                    return files
    return files


def get_model_info(model_path: str) -> dict:
    """获取模型的参数量和 FLOPs"""
    import torch
    from ultralytics import YOLO

    model = YOLO(model_path)
    total = sum(p.numel() for p in model.model.parameters())
    params_m = total / 1e6

    flops_g = 0.0
    try:
        from thop import profile
        dummy = torch.randn(1, 3, 640, 640)
        flops, _ = profile(model.model, inputs=(dummy,), verbose=False)
        flops_g = flops / 1e9
    except Exception as e:
        _log.warning("FLOPs 计算失败 (model=%s): %s", model_path, e)

    return {"params_m": params_m, "flops_g": flops_g}


def run_eval(model_path: str, data_yaml: str):
    """运行评估，返回指标字典"""
    from ui.scanner import load_model_cached

    try:
        mtime = os.path.getmtime(model_path)
        model = load_model_cached(model_path, mtime)
        metrics = model.val(data=data_yaml, verbose=False)
    except Exception:
        _log.exception("模型评估失败: model=%s data=%s", model_path, data_yaml)
        raise

    save_dir = getattr(metrics, "save_dir", None)
    return {
        "map50": metrics.box.map50,
        "map50_95": metrics.box.map,
        "precision": metrics.box.mp if hasattr(metrics.box, "mp") else 0.0,
        "recall": metrics.box.mr if hasattr(metrics.box, "mr") else 0.0,
        "save_dir": str(save_dir) if save_dir else "",
    }


# 向后兼容别名
_get_model_info = get_model_info
_run_eval = run_eval


# estimate_memory 已统一由 engine/benchmark 导出，此处仅保留别名以免破坏导入
from engine.benchmark import estimate_memory  # noqa: E402, F811


HARDWARE_PROFILES = {
    "Jetson Nano 2GB": {
        "gpu_memory_gb": 2.0,
        "compute_tflops": 0.472,
        "type": "edge",
        "supports_fp16": True,
        "supports_int8": False,
        "recommended_imgsz": 320,
    },
    "Jetson Orin Nano 8GB": {
        "gpu_memory_gb": 8.0,
        "compute_tflops": 40.0,
        "type": "edge",
        "supports_fp16": True,
        "supports_int8": True,
        "recommended_imgsz": 640,
    },
    "Raspberry Pi 5 8GB": {
        "gpu_memory_gb": 3.0,
        "compute_tflops": 0.1,
        "type": "edge_cpu",
        "supports_fp16": False,
        "supports_int8": True,
        "recommended_imgsz": 320,
    },
    "RTX 3060 12GB": {
        "gpu_memory_gb": 12.0,
        "compute_tflops": 12.7,
        "type": "desktop",
        "supports_fp16": True,
        "supports_int8": True,
        "recommended_imgsz": 640,
    },
    "RTX 4090 24GB": {
        "gpu_memory_gb": 24.0,
        "compute_tflops": 82.6,
        "type": "desktop",
        "supports_fp16": True,
        "supports_int8": True,
        "recommended_imgsz": 640,
    },
    "AWS T4 16GB": {
        "gpu_memory_gb": 16.0,
        "compute_tflops": 8.1,
        "type": "cloud",
        "supports_fp16": True,
        "supports_int8": True,
        "recommended_imgsz": 640,
    },
}
