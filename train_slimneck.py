from pathlib import Path
from ultralytics import YOLO
from project_config import SCRIPTS_DIR, DATA_YAML
import custom_models.custom_yolov11_mobilenetv3


def train():
    model = YOLO(str(SCRIPTS_DIR / "yolo11-mobilenetv3-slimneck-p2.yaml"))

    model.train(
        data=str(DATA_YAML),
        epochs=150,
        imgsz=640,
        batch=8,
        device=0,
        project="runs/detect",
        name="fire_mobilenet_slimneck",
        optimizer='auto',
        lr0=0.01,
        close_mosaic=20,
        patience=50
    )


if __name__ == '__main__':
    train()