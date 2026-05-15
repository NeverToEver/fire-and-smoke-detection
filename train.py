import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def train(
    data_yaml: str,
    model_yaml: str | None = None,
    epochs: int = 150,
    imgsz: int = 640,
    batch: int = 8,
    lr0: float = 0.01,
    close_mosaic: int = 20,
    patience: int = 50,
    device: str = "auto",
    project_name: str = "fire_mobilenet",
):
    import torch
    from ultralytics import YOLO
    from models.registry import register_custom_modules

    register_custom_modules()
    if model_yaml is None:
        model_yaml = str(SCRIPT_DIR / "configs/yolo11-mobilenetv3-p2.yaml")

    if not Path(data_yaml).exists():
        raise FileNotFoundError(f"数据集配置文件不存在: {data_yaml}")
    if not Path(model_yaml).exists():
        raise FileNotFoundError(f"模型配置文件不存在: {model_yaml}")

    try:
        model = YOLO(model_yaml)
    except Exception as e:
        raise RuntimeError(f"模型加载失败，请检查模型配置文件 {model_yaml}: {e}") from e

    try:
        model.train(
            data=data_yaml,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
            project="runs/detect",
            name=project_name,
            optimizer="auto",
            lr0=lr0,
            close_mosaic=close_mosaic,
            patience=patience,
        )
    except torch.cuda.OutOfMemoryError as e:
        raise RuntimeError(f"CUDA 显存不足 (OOM)，请减小 batch size 或 imgsz。当前 batch={batch}, imgsz={imgsz}") from e
    except RuntimeError as e:
        msg = str(e).lower()
        if "out of memory" in msg:
            raise RuntimeError(f"显存不足 (OOM)，请减小 batch size 或 imgsz。当前 batch={batch}, imgsz={imgsz}") from e
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="训练火焰烟雾检测模型")
    parser.add_argument("--data", required=True, help="数据集 YAML 配置文件路径")
    parser.add_argument("--model", default=None, help="模型 YAML 配置文件路径")
    parser.add_argument("--epochs", type=int, default=150, help="训练轮数 (default: 150)")
    parser.add_argument("--imgsz", type=int, default=640, help="输入尺寸 (default: 640)")
    parser.add_argument("--batch", type=int, default=8, help="Batch size (default: 8)")
    parser.add_argument("--lr0", type=float, default=0.01, help="初始学习率 (default: 0.01)")
    parser.add_argument("--close-mosaic", type=int, default=20, help="关闭 mosaic 的 epoch (default: 20)")
    parser.add_argument("--patience", type=int, default=50, help="早停 patience (default: 50)")
    parser.add_argument("--device", default="auto", help="训练设备 (default: auto)")
    parser.add_argument("--name", default="fire_mobilenet", help="输出目录名")
    args = parser.parse_args()
    train(
        args.data, args.model,
        epochs=args.epochs, imgsz=args.imgsz, batch=args.batch,
        lr0=args.lr0, close_mosaic=args.close_mosaic, patience=args.patience,
        device=args.device, project_name=args.name,
    )
