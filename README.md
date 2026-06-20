# 🔥 火焰烟雾检测平台

基于 **YOLOv11 + MobileNetV3 + Slim-Neck** 的火焰/烟雾目标检测项目，提供 Streamlit 可视化界面，支持数据集浏览、模型训练、推理、评估、硬件预估和模型导出。

## ✨ 功能特性

- 📊 **数据集浏览** — 可视化 YOLO 标注框，统计训练/验证/测试集分布
- 🚀 **模型训练** — 支持自定义模型结构、训练参数、设备选择
- 🔍 **模型推理** — 单张/批量图片检测，可调置信度阈值
- 📈 **模型评估** — 单模型指标 + 多模型横向对比（mAP、Precision、Recall、F1）
- ⚡ **硬件预估** — 估算参数量、GFLOPs、推理/训练显存峰值
- 📦 **模型导出** — 支持 ONNX、FP16、INT8/TFLite 等部署格式

## 🚀 快速开始

```bash
# 克隆仓库
git clone https://github.com/NeverToEver/fire-and-smoke-detection.git
cd fire-and-smoke-detection

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动界面
streamlit run app.py
```

访问 `http://localhost:8501` 即可使用。

## 📁 项目结构

```
.
├── app.py                  # Streamlit 主入口
├── train.py                # 命令行训练脚本
├── requirements.txt        # 依赖列表
├── configs/                # 模型结构配置 (YAML)
│   ├── yolo11-mobilenetv3-p2.yaml
│   └── yolo11-mobilenetv3-slimneck-p2.yaml
├── models/                 # 自定义模型定义
│   ├── registry.py         # 模块注册
│   ├── yolo_mobilenet.py   # MobileNetV3 Backbone
│   └── yolo_mobilenet_slimneck.py
├── ui/                     # Streamlit UI 组件
│   ├── pages/              # 各功能页面
│   ├── components.py       # 通用组件
│   └── theme.py            # 主题样式
├── engine/                 # 训练/评估引擎
└── tests/                  # 测试文件
```

## 📖 使用说明

### 数据集格式

使用 Ultralytics YOLO 格式，需提供 `data.yaml`：

```yaml
train: /path/to/train/images
val: /path/to/val/images
test: /path/to/test/images
nc: 2
names: ['fire', 'smoke']
```

### 训练模型

```bash
# 命令行训练
python train.py --data /path/to/data.yaml --model configs/yolo11-mobilenetv3-slimneck-p2.yaml

# 或使用 Streamlit 界面
streamlit run app.py  # 进入"训练管理"页面
```

### 模型配置

当前内置两种架构：

- `configs/yolo11-mobilenetv3-p2.yaml` — 标准 MobileNetV3 + YOLOv11 Head
- `configs/yolo11-mobilenetv3-slimneck-p2.yaml` — MobileNetV3 + Slim-Neck（推荐）

## 🛠️ 技术栈

- Python 3.10+
- PyTorch / torchvision
- Ultralytics YOLO
- Streamlit
- OpenCV / matplotlib / pandas

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 👥 致谢

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) — 目标检测框架
- [MobileNetV3](https://arxiv.org/abs/1905.02244) — 轻量化骨干网络
- [Streamlit](https://streamlit.io/) — Web UI 框架
