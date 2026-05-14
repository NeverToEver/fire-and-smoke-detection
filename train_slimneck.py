import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def train(data_yaml: str, model_yaml: str | None = None):
    from ultralytics import YOLO
    import custom_models.custom_yolov11_mobilenetv3  # noqa: F401 — 注册自定义模块
    if model_yaml is None:
        model_yaml = str(SCRIPT_DIR / "yolo11-mobilenetv3-slimneck-p2.yaml")

    model = YOLO(model_yaml)
    model.train(
        data=data_yaml,
        epochs=150,
        imgsz=640,
        batch=8,
        device=0,
        project="runs/detect",
        name="fire_mobilenet_slimneck",
        optimizer="auto",
        lr0=0.01,
        close_mosaic=20,
        patience=50,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="训练火焰烟雾检测模型")
    parser.add_argument("--data", required=True, help="数据集 YAML 配置文件路径")
    parser.add_argument("--model", default=None, help="模型 YAML 配置文件路径（默认使用同目录下的 yolo11-mobilenetv3-slimneck-p2.yaml）")
    args = parser.parse_args()
    train(args.data, args.model)
