"""训练日志解析器 — 从 YOLO 训练日志中提取结构化进度数据"""

import re
import time
from pathlib import Path
from typing import Any


def _strip_ansi(text: str) -> str:
    """去除 ANSI 转义序列（颜色码 + 行清除 [K）"""
    return re.sub(r"\x1b\[K", "\n", re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text))


def parse_training_log(
    log_path: str,
    start_time: float | None = None,
    total_epochs_hint: int | None = None,
) -> dict[str, Any]:
    """
    解析训练日志，返回结构化训练状态。

    Returns:
        dict with keys:
        - status: "idle" | "scanning" | "training" | "complete"
        - current_epoch: int
        - total_epochs: int
        - epoch_pct: float (0-100, based on batch progress within epoch)
        - gpu_mem: str
        - box_loss, cls_loss, dfl_loss: float | None
        - map50, map50_95: float | None  (latest validation)
        - precision, recall: float | None (latest validation)
        - eta_str: str | None (human readable)
        - eta_seconds: float | None
        - speed: str | None (it/s)
        - raw_tail: str (last 1500 chars of clean log)
    """
    path = Path(log_path)
    if not path.exists():
        return {"status": "idle", "raw_tail": ""}

    # 只读尾部 256KB，避免长时间训练时日志文件过大撑爆内存
    try:
        fsize = path.stat().st_size
        read_size = min(fsize, 256 * 1024)
        with open(log_path, errors="replace") as f:
            if fsize > read_size:
                f.seek(fsize - read_size)
                raw = f.read()
            else:
                raw = f.read()
    except OSError:
        return {"status": "idle", "raw_tail": ""}
    clean = _strip_ansi(raw)
    lines = clean.split("\n")

    result: dict[str, Any] = {
        "status": "idle",
        "current_epoch": 0,
        "total_epochs": total_epochs_hint or 0,
        "epoch_pct": 0.0,
        "gpu_mem": "",
        "box_loss": None,
        "cls_loss": None,
        "dfl_loss": None,
        "map50": None,
        "map50_95": None,
        "precision": None,
        "recall": None,
        "eta_str": None,
        "eta_seconds": None,
        "speed": None,
        "raw_tail": clean[-1500:] if len(clean) > 1500 else clean,
    }

    # ── 扫描 training progress 行 ──
    train_re = re.compile(
        r"^\s*(\d+)/(\d+)\s+"
        r"(\d+\.\d+G)\s+"
        r"(\d+\.\d+)\s+"
        r"(\d+\.\d+)\s+"
        r"(\d+\.\d+)\s+"
        r"(\d+)\s+"
        r"(\d+):\s+"
        r"\d+%.*?"
        r"(\d+)/(\d+)\s+"
        r"([\d.]+it/s)?\s*"
        r"([\d.]+s)?\s*"
        r"(?:<([\d:]+))?"
    )

    # ── 扫描 validation summary 行 ──
    val_re = re.compile(
        r"^\s*all\s+(\d+)\s+(\d+)\s+"
        r"([\d.]+)\s+"
        r"([\d.]+)\s+"
        r"([\d.]+)\s+"
        r"([\d.]+)"
    )

    for line in lines:
        m = train_re.match(line.strip())
        if m:
            result["status"] = "training"
            result["current_epoch"] = int(m.group(1))
            result["total_epochs"] = int(m.group(2))
            result["gpu_mem"] = m.group(3)
            result["box_loss"] = float(m.group(4))
            result["cls_loss"] = float(m.group(5))
            result["dfl_loss"] = float(m.group(6))
            # instances = m.group(7), imgsz = m.group(8)
            batch_current = int(m.group(9))
            batch_total = int(m.group(10))
            result["epoch_pct"] = (batch_current / batch_total * 100) if batch_total > 0 else 0
            if m.group(11):
                result["speed"] = m.group(11)
            eta_raw = m.group(13)
            if eta_raw:
                result["eta_str"] = eta_raw
                result["eta_seconds"] = _parse_eta(eta_raw)
            continue

        vm = val_re.match(line.strip())
        if vm:
            result["precision"] = float(vm.group(3))
            result["recall"] = float(vm.group(4))
            result["map50"] = float(vm.group(5))
            result["map50_95"] = float(vm.group(6))

    # ── 推断 status ──
    if result["status"] == "idle":
        if "Scanning" in clean or "scanning" in clean.lower():
            result["status"] = "scanning"

    # ── 计算全局 ETA ──
    if result["status"] == "training" and result["total_epochs"] > 0 and start_time:
        elapsed = time.time() - start_time
        cur_ep = result["current_epoch"]
        if cur_ep > 0 and elapsed > 0:
            sec_per_epoch = elapsed / cur_ep
            remaining_epochs = result["total_epochs"] - cur_ep
            if remaining_epochs > 0:
                global_eta = sec_per_epoch * (remaining_epochs - 1)
                batch_eta = result.get("eta_seconds") or 0
                global_eta += batch_eta if batch_eta > 0 else sec_per_epoch
            else:
                # 最后一个 epoch: ETA 仅剩当前 epoch 内批处理余量
                global_eta = result.get("eta_seconds") or 0
            result["eta_seconds"] = max(0, global_eta)
            result["eta_str"] = _format_eta(global_eta)

    return result


def _parse_eta(raw: str) -> float:
    """将 '<6:42' 或 '<56.4s' 转为秒"""
    raw = raw.strip().lstrip("<")
    if ":" in raw:
        parts = raw.split(":")
        return int(parts[0]) * 60 + float(parts[1])
    if raw.endswith("s"):
        return float(raw[:-1])
    try:
        return float(raw)
    except ValueError:
        return 0.0


def _format_eta(seconds: float) -> str:
    """秒转为人类可读格式"""
    if seconds <= 0:
        return "<1s"
    m, s = divmod(int(seconds), 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f"{h}h{m:02d}m"
    if m > 0:
        return f"{m}m{s:02d}s"
    return f"{s}s"
