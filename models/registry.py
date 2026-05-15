"""Custom Ultralytics module registry for project-owned architectures."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ArchitectureSpec:
    """Metadata for one trusted architecture implementation."""

    id: str
    label: str
    module: str
    default_config: str
    description: str
    components: tuple[str, ...]


ARCHITECTURES: tuple[ArchitectureSpec, ...] = (
    ArchitectureSpec(
        id="mobilenetv3_p2",
        label="MobileNetV3 + YOLOv11 Head",
        module="models.yolo_mobilenet",
        default_config="configs/yolo11-mobilenetv3-p2.yaml",
        description="标准 Conv + C3k2 颈部，作为稳定基线。",
        components=("MobileNetV3_Backbone", "YOLOv11_MobileNetV3_Head", "DetectWrapper"),
    ),
    ArchitectureSpec(
        id="mobilenetv3_slimneck_p2",
        label="MobileNetV3 + Slim-Neck",
        module="models.yolo_mobilenet_slimneck",
        default_config="configs/yolo11-mobilenetv3-slimneck-p2.yaml",
        description="GSConv + VoVGSCSP 轻量化颈部，偏向边缘部署。",
        components=("MobileNetV3_Backbone", "YOLOv11_MobileNetV3_SlimNeck_Head", "DetectWrapper"),
    ),
)


def register_custom_modules() -> tuple[str, ...]:
    """Import all trusted custom modules so Ultralytics can resolve YAML classes."""
    loaded: list[str] = []
    for spec in ARCHITECTURES:
        importlib.import_module(spec.module)
        loaded.append(spec.module)
    return tuple(loaded)


def get_architectures() -> tuple[ArchitectureSpec, ...]:
    return ARCHITECTURES


def architecture_for_config(config_path: str | Path) -> ArchitectureSpec | None:
    """Return the registered architecture whose default YAML matches config_path."""
    path = Path(config_path)
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path

    for spec in ARCHITECTURES:
        spec_path = PROJECT_ROOT / spec.default_config
        try:
            if resolved == spec_path.resolve():
                return spec
        except OSError:
            if path.as_posix() == spec.default_config:
                return spec
    return None
