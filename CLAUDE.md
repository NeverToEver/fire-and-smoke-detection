# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

火焰/烟雾目标检测，基于 YOLOv11 + MobileNetV3 轻量化 backbone + Slim-Neck 特征融合颈，增加 P2 层以提升小目标检测能力。

## 依赖

- `torch`, `torchvision`
- `ultralytics` (YOLOv11)

`train_slimneck.py` 依赖外部 `project_config` 模块提供 `SCRIPTS_DIR` 和 `DATA_YAML` 路径，该模块不在本仓库中，部署时需自行提供。

## 架构

```
输入 → MobileNetV3_Backbone (P2/P3/P4/P5) → YOLOv11_MobileNetV3_Head (Slim-Neck FPN+PAN) → DetectWrapper
```

- **`custom_yolov11_mobilenetv3.py`** — 核心模型定义，包含：
  - `GSConv` / `GSBottleneck` / `VoVGSCSP`：Slim-Neck 轻量化卷积模块，用于替换 YOLO 标准 C3k2 和 Conv
  - `MobileNetV3_Backbone`：基于 torchvision MobileNetV3-Large，输出 4 层特征（通道 [24,40,80,160]）
  - `YOLOv11_MobileNetV3_Head`：FPN+PAN 双向特征融合，Top-down 和 Bottom-up 路径均使用 VoVGSCSP/GSConv
  - `DetectWrapper`：包装 ultralytics 原生 Detect 头
  - 所有自定义模块通过 monkey-patch 注册到 `ultralytics.nn.tasks.__dict__`，使 YAML 配置文件可直接引用

- **`yolo11-mobilenetv3-slimneck-p2.yaml`** — 模型结构配置，`nc: 2`（火焰/烟雾二分类），定义 backbone → head → detect 三层

- **`train_slimneck.py`** — 训练入口，使用 ultralytics YOLO API，关键参数：epochs=150, imgsz=640, batch=8, lr0=0.01, close_mosaic=20, patience=50

- **`custom_models/`** — 子包，`__init__.py` 重导出 `MobileNetV3_Backbone` 和 `YOLOv11_MobileNetV3_Head`，内容与根目录同名文件一致

## 训练

```bash
python train_slimneck.py
```

需确保 `project_config` 模块可用，定义了 `SCRIPTS_DIR`（指向本目录）和 `DATA_YAML`（数据集配置路径）。
