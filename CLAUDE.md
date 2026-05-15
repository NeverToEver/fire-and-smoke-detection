# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

火焰/烟雾目标检测，基于 YOLOv11 + MobileNetV3 轻量化 backbone + Slim-Neck 特征融合颈，增加 P2 层以提升小目标检测能力。提供 Streamlit 可视化界面用于数据集浏览、训练、推理、评估、硬件预估和模型导出。

## 常用命令

```bash
# 启动 Streamlit 界面（主要入口）
.venv/bin/python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true

# 命令行训练
python train.py --data /path/to/data.yaml [--model configs/yolo11-mobilenetv3-slimneck-p2.yaml]

# 安装依赖
.venv/bin/pip install -r requirements.txt
```

虚拟环境位于项目根目录的 `.venv/`。

## 架构

```
输入 → MobileNetV3_Backbone (P2/P3/P4/P5) → YOLOv11_MobileNetV3_Head (Slim-Neck FPN+PAN) → DetectWrapper
```

### 模型定义

- **`models/yolo_mobilenet.py`** — 核心模型定义，包含：
  - `GSConv` / `GSBottleneck` / `VoVGSCSP`：Slim-Neck 轻量化卷积模块，用于替换 YOLO 标准 C3k2 和 Conv
  - `MobileNetV3_Backbone`：基于 torchvision MobileNetV3-Large，输出 4 层特征（通道 [24,40,80,160]）
  - `YOLOv11_MobileNetV3_Head`：FPN+PAN 双向特征融合，Top-down 和 Bottom-up 路径均使用 VoVGSCSP/GSConv
  - `DetectWrapper`：包装 ultralytics 原生 Detect 头
  - 所有自定义模块通过 monkey-patch 注册到 `ultralytics.nn.tasks.__dict__`，使 YAML 配置文件可直接引用
- **`models/__init__.py`** — 重导出 `MobileNetV3_Backbone` 和 `YOLOv11_MobileNetV3_Head`
- **`yolo_mobilenet.py`**（根目录）— 仅一行 `from models.yolo_mobilenet import *`，供 `train.py` 的 `import models.yolo_mobilenet` 触发注册
- **`configs/yolo11-mobilenetv3-slimneck-p2.yaml`** — 模型结构配置，`nc: 2`（火焰/烟雾二分类），定义 backbone → head → detect 三层

### Streamlit 应用 (`app.py`, ~2800 行)

单体应用，无模块拆分。结构：

- **常量/路径**：`SCRIPT_DIR`（项目根目录）、`UPLOAD_DIR`（`.streamlit_uploads/`）、`RUNS_DIR`（`runs/detect/`）
- **资源扫描**：`scan_datasets()` / `scan_models()` / `scan_model_configs()` — 带 `@st.cache_data` 缓存
- **通用组件**：`dataset_selector()` / `model_selector()` / `model_config_selector()` — 支持拖拽上传和本地路径输入
- **6 个页面函数**：`page_dataset()` → `page_training()` → `page_inference()` → `page_evaluation()` → `page_hardware()` → `page_optimization()`
- **主入口**：`main()` 渲染侧边栏导航、主题切换、资源统计，按选择路由到对应页面
- **自动清理**：`_cleanup_old_files()` 首次运行时清理 `eval_results/`（保留最近 10 个）和上传目录中 7 天前的文件

### 训练脚本

- **`train.py`** — 命令行训练入口，使用 argparse 接收 `--data` 和 `--model` 参数。关键参数：epochs=150, imgsz=640, batch=8, lr0=0.01, close_mosaic=20, patience=50。通过 `import models.yolo_mobilenet` 触发模块注册后调用 `YOLO(model_yaml).train()`。

## 数据流

- 数据集为 Ultralytics YOLO 格式，需 `data.yaml` 指定 `train`/`val`/`test` 路径和 `names`
- 训练输出到 `runs/detect/<name>/`，包含 `weights/best.pt`、`weights/last.pt`
- 评估结果输出到 `eval_results/`（JSON 格式）
- 上传文件保存到 `.streamlit_uploads/<models|datasets|model_configs|datasets_extracted>/`
- `.gitignore` 已排除 `runs/`、`eval_results/`、`.streamlit_uploads/`、`.venv/`
