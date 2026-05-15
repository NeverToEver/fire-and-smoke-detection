# 火焰烟雾检测平台

基于 YOLOv11、MobileNetV3 Backbone 和 Slim-Neck 的火焰/烟雾目标检测项目，提供 Streamlit 可视化界面，用于数据集浏览、模型训练、推理、评估、硬件预估和模型导出优化。

## 功能概览

- 数据集浏览：扫描 `data.yaml`，统计训练/验证/测试图片数量，预览图片和 YOLO 标注框。
- 训练管理：选择数据集和模型结构 YAML，配置 epoch、batch、imgsz、学习率等参数并启动训练。
- 训练设备：自动检测 Torch/CUDA/GPU 数量，支持手动选择 CPU 或具体 GPU，并显示训练状态。
- 模型推理：加载 `.pt` 权重，对上传图片或测试集目录执行检测。
- 模型评估：支持单模型指标评估和 2-5 个模型横向对比。
- 硬件预估：估算参数量、GFLOPs、推理/训练显存峰值，并给出常见硬件兼容性建议。
- 模型优化：导出 ONNX、FP16、INT8/TFLite 等部署格式。
- UI 辅助：支持拖拽上传 YAML/权重/图片，支持白天模式、夜间模式和跟随系统主题。

## 技术栈

- Python
- Streamlit
- PyTorch / torchvision
- Ultralytics YOLO
- OpenCV
- pandas
- matplotlib
- YAML

模型结构配置位于 [configs/yolo11-mobilenetv3-slimneck-p2.yaml](configs/yolo11-mobilenetv3-slimneck-p2.yaml)，自定义模块注册逻辑位于 [models/yolo_mobilenet.py](models/yolo_mobilenet.py)。

## 环境准备

建议使用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

依赖文件包含：

```txt
torch
torchvision
ultralytics
streamlit
opencv-python
matplotlib
pandas
thop
```

注意：`ultralytics` 是训练、推理、评估和硬件预估的必要依赖。如果运行时出现 `No module named 'ultralytics'`，说明当前启动 Streamlit 的 Python 环境没有安装完整依赖，请重新执行 `python -m pip install -r requirements.txt`。

## 启动界面

```bash
streamlit run app.py
```

启动后访问终端输出的本地地址，通常是：

```text
http://127.0.0.1:8501
```

## 数据集格式

数据集需要使用 Ultralytics YOLO 格式，并提供 `data.yaml`，例如：

```yaml
train: /absolute/path/to/train/images
val: /absolute/path/to/val/images
test: /absolute/path/to/test/images
nc: 2
names:
  0: fire
  1: smoke
```

界面支持拖拽上传 `data.yaml` / `dataset.yaml`。如果 YAML 中使用相对路径，上传后可能因为保存目录变化导致图片路径失效；更稳妥的做法是使用绝对路径，或在界面中手动输入原始 `data.yaml` 路径。

## 模型配置

默认模型配置为：

```text
configs/yolo11-mobilenetv3-slimneck-p2.yaml
```

该配置定义：

- `MobileNetV3_Backbone`
- `YOLOv11_MobileNetV3_Head`
- `DetectWrapper`
- P2/P3/P4/P5 多尺度检测特征
- `nc: 2` 火焰/烟雾二分类

训练时界面会自动扫描项目根目录下包含 `backbone` 或 `head` 字段的 `.yaml` 文件，也支持拖拽上传模型结构 YAML。

## 训练

在界面中进入“训练管理”：

1. 选择或拖拽上传训练数据集 `data.yaml`。
2. 选择或拖拽上传模型配置 YAML。
3. 设置 `Epochs`、`Batch Size`、`Image Size`、`Learning Rate`、`Device` 等参数。
4. 在“训练设备”区域查看 Torch/CUDA/GPU 状态，并选择 CPU 或具体 GPU。
5. 在“执行”区域确认训练状态、设备参数、输出目录和日志窗口。
6. 点击“开始训练”。

训练结果默认输出到：

```text
runs/detect/<输出目录名>/
```

训练设备选择会传递给 Ultralytics 的 `device` 参数：

- `CPU` -> `device="cpu"`
- `GPU 0: ...` -> `device="0"`
- `GPU 1: ...` -> `device="1"`

如果界面显示 CUDA 不可用，请检查当前 Python 环境中的 PyTorch 是否支持 CUDA。

也可以使用命令行训练：

```bash
python train.py --data /path/to/data.yaml --model configs/yolo11-mobilenetv3-slimneck-p2.yaml
```

## 推理

进入“模型推理”：

- 选择或拖拽上传 `.pt` 权重文件。
- 选择“单张/多张上传”可以直接拖入图片推理。
- 选择“测试集目录”可以从数据集配置中获取 `test` / `val` 路径，或手动输入图片目录。
- 调整置信度阈值后点击运行。

## 评估和对比

进入“模型评估”：

- 单模型评估：选择一个 `.pt` 权重和一个数据集 YAML，输出 mAP、Precision、Recall、F1、参数量和 GFLOPs。
- 多模型对比：选择 2-5 个已训练模型，使用同一数据集评估并生成对比表和图表。

如果“多模型对比”没有模型可选，请先完成训练，或将 `.pt` 权重放到 `runs/detect/` 下，或使用拖拽上传权重的入口。

## 硬件预估

进入“硬件预估”后可以：

- 从模型配置 YAML 预估。
- 从已训练 `.pt` 权重预估。
- 设置输入尺寸、Batch Size 和 FP16 模式。
- 查看推理/训练内存估算和常见硬件兼容性表。

## 模型优化

进入“模型优化”后可以选择目标硬件，并导出：

- FP16 ONNX
- FP32 ONNX
- INT8 TFLite
- FP32 TFLite 备用格式

导出能力依赖 Ultralytics 和对应导出后端环境。

## UI 使用说明

- 侧边栏提供“跟随系统 / 白天模式 / 夜间模式”主题切换。
- 数据集 YAML、模型配置 YAML、模型权重和推理图片均支持拖拽上传。
- Streamlit 默认顶部工具栏已在样式中隐藏，界面更接近独立应用。

## 常见问题

### No module named 'ultralytics'

当前启动 Streamlit 的 Python 环境缺少 Ultralytics。请确认是在同一个环境中安装依赖：

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### 拖拽上传 data.yaml 后找不到图片

浏览器上传文件不会保留原始本地目录。上传后的 YAML 会保存到 `.streamlit_uploads/`，如果其中的 `train` / `val` / `test` 是相对路径，可能无法解析到原始图片。建议使用绝对路径或手动输入原始 YAML 路径。

### 模型配置下拉为空

界面只会自动识别项目根目录下包含 `backbone` 或 `head` 字段的 `.yaml` 文件。也可以直接拖拽上传模型配置 YAML。

## 项目结构

```text
.
├── app.py
├── train.py
├── requirements.txt
├── configs/yolo11-mobilenetv3-slimneck-p2.yaml
├── models/
│   ├── __init__.py
│   └── yolo_mobilenet.py
└── README.md
```
