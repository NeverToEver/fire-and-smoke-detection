"""
受限环境硬件 Benchmark 模块

支持 CUDA / Apple MPS / CPU 三种设备。
- CUDA: 通过 set_per_process_memory_fraction 限制 GPU 显存
- MPS: 通过 PYTORCH_MPS_HIGH_WATERMARK_RATIO 限制 GPU 显存
- CPU: 通过 set_num_threads 限制核心数

在受限条件下实测推理显存、延迟、FPS，验证目标设备可用性。
"""

import os
import time
import io
import json
from datetime import datetime

import torch
import numpy as np


# ═══════════════════════════════════════════
# 设备检测
# ═══════════════════════════════════════════

def _get_device_type() -> str:
    """返回当前首选加速设备类型: 'cuda' | 'mps' | 'cpu'"""
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _get_device() -> torch.device:
    """返回最佳可用加速设备"""
    return torch.device(_get_device_type())


def detect_device() -> dict:
    """检测 CUDA / MPS 设备信息，均不可用时回退 CPU"""
    device_type = _get_device_type()
    result = {
        "available": device_type != "cpu",
        "device_type": device_type,
        "device_name": "",
        "total_memory_gb": 0.0,
        "free_memory_gb": 0.0,
    }

    try:
        if device_type == "cuda":
            result["device_name"] = torch.cuda.get_device_name(0)
            free, total = torch.cuda.mem_get_info()
            result["total_memory_gb"] = round(total / 1e9, 2)
            result["free_memory_gb"] = round(free / 1e9, 2)
        elif device_type == "mps":
            result["device_name"] = "Apple MPS (Metal)"
            try:
                import psutil
                vm = psutil.virtual_memory()
                result["total_memory_gb"] = round(vm.total / 1e9, 2)
                result["free_memory_gb"] = round(vm.available / 1e9, 2)
            except ImportError:
                result["total_memory_gb"] = 0.0
                result["free_memory_gb"] = 0.0
    except Exception:
        pass

    return result


def detect_cuda_device() -> dict:
    """向后兼容别名 — 检测 CUDA 设备（优先），并回退 MPS/CPU"""
    result = detect_device()
    # 保持旧接口兼容：always has cuda-specific top-level keys
    if result["device_type"] == "cuda":
        return {
            "available": True,
            "device_name": result["device_name"],
            "total_memory_gb": result["total_memory_gb"],
            "free_memory_gb": result["free_memory_gb"],
        }
    # 非 CUDA 时返回 MPS 信息或空
    return {
        "available": result["available"],
        "device_name": result["device_name"] if result["available"] else "",
        "total_memory_gb": result["total_memory_gb"],
        "free_memory_gb": result["free_memory_gb"],
    }


def get_cpu_core_count() -> int:
    return os.cpu_count() or 1


# ═══════════════════════════════════════════
# 设备无关同步与内存工具
# ═══════════════════════════════════════════

def _synchronize():
    """根据当前设备执行同步"""
    dt = _get_device_type()
    if dt == "cuda":
        torch.cuda.synchronize()
    elif dt == "mps":
        torch.mps.synchronize()


def _reset_peak_stats():
    """重置峰值显存统计（MPS 不支持，静默跳过）"""
    dt = _get_device_type()
    if dt == "cuda":
        torch.cuda.reset_peak_memory_stats()


def _empty_cache():
    """清空 GPU 缓存"""
    dt = _get_device_type()
    if dt == "cuda":
        torch.cuda.empty_cache()
    elif dt == "mps":
        torch.mps.empty_cache()


def _get_memory_snapshot() -> dict:
    """获取当前设备显存快照"""
    dt = _get_device_type()
    if dt == "cuda":
        return {
            "allocated_mb": round(torch.cuda.memory_allocated() / 1e6, 1),
            "peak_allocated_mb": round(torch.cuda.max_memory_allocated() / 1e6, 1),
        }
    elif dt == "mps":
        current = torch.mps.current_allocated_memory() / 1e6
        try:
            driver = torch.mps.driver_allocated_memory() / 1e6
        except Exception:
            driver = current
        return {
            "allocated_mb": round(current, 1),
            "peak_allocated_mb": round(driver, 1),
        }
    return {"allocated_mb": 0, "peak_allocated_mb": 0}


def _get_total_memory_mb() -> float:
    """获取设备总内存（MB），用于计算 headroom"""
    dt = _get_device_type()
    if dt == "cuda":
        return torch.cuda.mem_get_info()[1] / 1e6
    elif dt == "mps":
        try:
            import psutil
            return psutil.virtual_memory().total / 1e6
        except ImportError:
            return 8192  # fallback: 8GB
    return 8192


# ═══════════════════════════════════════════
# 环境约束
# ═══════════════════════════════════════════

def constrain_gpu_memory(target_gb: float) -> float:
    """
    限制 GPU 显存为 target_gb GB，返回实际设置的参数。
    CUDA: 使用 set_per_process_memory_fraction
    MPS: 使用 PYTORCH_MPS_HIGH_WATERMARK_RATIO（0.0~1.0）
    """
    dt = _get_device_type()
    if dt == "cuda":
        _, total = torch.cuda.mem_get_info()
        total_gb = total / 1e9
        fraction = min(target_gb / total_gb, 1.0)
        torch.cuda.set_per_process_memory_fraction(fraction)
        torch.cuda.empty_cache()
        return fraction
    elif dt == "mps":
        # MPS 通过环境变量控制显存上限，但需在导入 torch 前设置
        # 运行时只能通过 empty_cache 释放，无法精确限制
        try:
            import psutil
            total = psutil.virtual_memory().total
            ratio = min(target_gb / (total / 1e9), 1.0)
            os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = str(ratio)
            torch.mps.empty_cache()
            return ratio
        except ImportError:
            pass
    return 1.0


def release_gpu_constraint():
    """释放 GPU 显存限制"""
    dt = _get_device_type()
    if dt == "cuda":
        torch.cuda.set_per_process_memory_fraction(1.0)
        torch.cuda.empty_cache()
    elif dt == "mps":
        os.environ.pop("PYTORCH_MPS_HIGH_WATERMARK_RATIO", None)
        torch.mps.empty_cache()


def constrain_cpu_cores(n_cores: int) -> bool:
    """限制 PyTorch 线程数模拟低核心环境"""
    max_cores = os.cpu_count() or 1
    n = max(1, min(n_cores, max_cores))
    torch.set_num_threads(n)
    torch.set_num_interop_threads(n)
    return True


# ═══════════════════════════════════════════
# CUDA 内存工具（向后兼容别名）
# ═══════════════════════════════════════════

def _reset_cuda_stats():
    _reset_peak_stats()
    _empty_cache()


# 向后兼容别名
_reset_cuda_and_cache = _reset_cuda_stats


def _get_cuda_memory_snapshot() -> dict:
    return _get_memory_snapshot()


# ═══════════════════════════════════════════
# 公式估算
# ═══════════════════════════════════════════

def estimate_memory(params_m: float, imgsz: int, batch: int, fp16: bool = False) -> dict:
    bytes_per_param = 2 if fp16 else 4
    scale = (imgsz / 640) ** 2
    model_mb = params_m * bytes_per_param * 1.3
    base_activation_mb = 250 if fp16 else 500
    activation_mb = batch * scale * base_activation_mb
    cuda_overhead_mb = 250
    inference_mb = model_mb + activation_mb + cuda_overhead_mb

    grad_opt_mb = params_m * 4 * 3 * 1.1
    extra_activation_mb = activation_mb * 1.5
    train_workspace_mb = 200
    training_mb = inference_mb + grad_opt_mb + extra_activation_mb + train_workspace_mb

    return {
        "model_mb": round(model_mb, 1),
        "activation_mb": round(activation_mb, 1),
        "inference_mb": round(inference_mb, 1),
        "training_mb": round(training_mb, 1),
        "inference_gb": round(inference_mb / 1024, 2),
        "training_gb": round(training_mb / 1024, 2),
    }


# ═══════════════════════════════════════════
# 核心 Benchmark
# ═══════════════════════════════════════════

def run_benchmark(
    model_path: str,
    imgsz: int,
    batch: int,
    fp16: bool,
    gpu_memory_limit_gb: float = 0,
    cpu_cores: int = 0,
    num_warmup: int = 5,
    num_measure: int = 50,
) -> dict:
    """
    在约束条件下实测模型性能。

    gpu_memory_limit_gb > 0 → 限制 GPU 显存上限
    cpu_cores > 0 → 限制 CPU 核心数（同时自动切 CPU 推理）
    均为 0 → 无约束基准测试
    """
    result = {
        "constraint": {"gpu_memory_limit_gb": gpu_memory_limit_gb, "cpu_cores": cpu_cores},
        "oom": False,
        "oom_message": "",
        "peak_memory_mb": 0.0,
        "memory_headroom_mb": 0.0,
        "fps": 0.0,
        "latency": {},
        "model_info": {"params_m": 0.0, "weights_mb": 0.0},
        "estimated": {},
        "warmup_runs": num_warmup,
        "benchmark_runs": num_measure,
        "device": "cpu",
        "notes": [],
    }

    from ultralytics import YOLO

    device_type = _get_device_type()
    gpu_available = device_type != "cpu"

    # 推理设备决策
    use_gpu = gpu_available and cpu_cores <= 0

    try:
        model = YOLO(model_path)
    except Exception as e:
        result["load_error"] = True
        result["oom_message"] = f"模型加载失败: {e}"
        return result

    # 计算参数量
    total_params = sum(p.numel() for p in model.model.parameters())
    params_m = total_params / 1e6
    bytes_per_param = 2 if (fp16 and use_gpu) else 4
    weights_mb = total_params * bytes_per_param / 1e6
    result["model_info"] = {"params_m": round(params_m, 2), "weights_mb": round(weights_mb, 1)}

    # 公式估算对比
    result["estimated"] = estimate_memory(params_m, imgsz, batch, fp16 and use_gpu)

    # ── 施加约束 ──
    if gpu_memory_limit_gb > 0 and gpu_available:
        fraction = constrain_gpu_memory(gpu_memory_limit_gb)
        result["constraint"]["gpu_fraction_set"] = round(fraction, 4)
        result["constraint"]["gpu_applied"] = True
        result["constraint"]["device_type"] = device_type
        use_gpu = True
    else:
        result["constraint"]["gpu_applied"] = False

    if cpu_cores > 0:
        constrain_cpu_cores(cpu_cores)
        result["constraint"]["cpu_affinity_ok"] = True
        use_gpu = False  # CPU 核心限制 → 切 CPU 推理模式
        if device_type == "mps":
            result["notes"].append("MPS 设备使用 CPU 推理模式，性能不代表 GPU 加速效果")
    else:
        result["constraint"]["cpu_affinity_ok"] = True

    # ── 准备推理 ──
    device_str = device_type if use_gpu else "cpu"
    result["device"] = device_str
    device = torch.device(device_str)

    try:
        model.model.to(device)
        model.model.eval()

        dummy = torch.randn(batch, 3, imgsz, imgsz, device=device)
        if fp16 and use_gpu and device_type == "cuda":
            model.model.half()
            dummy = dummy.half()

        # ── 显存测量 ──
        if use_gpu:
            _reset_peak_stats()
            _empty_cache()
            _synchronize()
            model_allocated_mb = round(_get_memory_snapshot()["allocated_mb"], 1)

            # Warmup
            with torch.no_grad():
                for _ in range(num_warmup):
                    _ = model.model(dummy)
            _synchronize()
            _reset_peak_stats()

            # 测量
            with torch.no_grad():
                for _ in range(min(num_measure, 10)):
                    _ = model.model(dummy)
            _synchronize()
            snapshot = _get_memory_snapshot()
            result["peak_memory_mb"] = round(model_allocated_mb + snapshot["peak_allocated_mb"], 1)
            if gpu_memory_limit_gb > 0:
                limit_mb = gpu_memory_limit_gb * 1024
            else:
                limit_mb = _get_total_memory_mb()
            result["memory_headroom_mb"] = round(limit_mb - result["peak_memory_mb"], 1)
        else:
            result["peak_memory_mb"] = result["estimated"]["inference_mb"]
            result["memory_headroom_mb"] = gpu_memory_limit_gb * 1024 - result["peak_memory_mb"] if gpu_memory_limit_gb > 0 else 0

        # ── FPS / 延迟测量 ──
        latencies = []
        with torch.no_grad():
            for i in range(num_measure):
                _synchronize()
                t0 = time.perf_counter()
                _ = model.model(dummy)
                _synchronize()
                latencies.append((time.perf_counter() - t0) * 1000)

        arr = np.array(latencies)
        result["latency"] = {
            "mean_ms": round(float(np.mean(arr)), 2),
            "median_ms": round(float(np.median(arr)), 2),
            "p50_ms": round(float(np.percentile(arr, 50)), 2),
            "p95_ms": round(float(np.percentile(arr, 95)), 2),
            "p99_ms": round(float(np.percentile(arr, 99)), 2),
            "min_ms": round(float(np.min(arr)), 2),
            "max_ms": round(float(np.max(arr)), 2),
            "std_ms": round(float(np.std(arr)), 2),
        }
        result["fps"] = round(1000.0 / result["latency"]["mean_ms"], 1)

        if cpu_cores > 0:
            result["notes"].append("CPU 推理基准在 x86/M-series 环境下测得，不等同 ARM NEON 性能")

    except torch.cuda.OutOfMemoryError as e:
        result["oom"] = True
        result["oom_message"] = f"CUDA OOM: {e}"
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            result["oom"] = True
            result["oom_message"] = str(e)
        elif "MPS" in str(e) and "out of memory" in str(e).lower():
            result["oom"] = True
            result["oom_message"] = f"MPS OOM: {e}"
        else:
            raise
    finally:
        release_gpu_constraint()

        try:
            del model
        except (NameError, AttributeError):
            pass
        try:
            del dummy
        except (NameError, AttributeError):
            pass
        _empty_cache()
        try:
            torch.set_num_threads(get_cpu_core_count())
        except RuntimeError:
            pass

    return result


# ═══════════════════════════════════════════
# 预设设备档案
# ═══════════════════════════════════════════

PRESET_PROFILES = {
    "Jetson Nano 2GB": {
        "gpu_memory_limit_gb": 2.0,
        "cpu_cores": 0,
        "recommended_imgsz": 320,
        "supports_fp16": True,
    },
    "Jetson Orin Nano 8GB": {
        "gpu_memory_limit_gb": 8.0,
        "cpu_cores": 0,
        "recommended_imgsz": 640,
        "supports_fp16": True,
    },
    "树莓派 5 8GB (CPU)": {
        "gpu_memory_limit_gb": 0,
        "cpu_cores": 4,
        "recommended_imgsz": 320,
        "supports_fp16": False,
        "note": "x86 CPU 近似，ARM NEON 指令集差异无法模拟",
    },
    "RTX 3060 12GB": {
        "gpu_memory_limit_gb": 12.0,
        "cpu_cores": 0,
        "recommended_imgsz": 640,
        "supports_fp16": True,
    },
    "RTX 4090 24GB": {
        "gpu_memory_limit_gb": 24.0,
        "cpu_cores": 0,
        "recommended_imgsz": 640,
        "supports_fp16": True,
    },
    "AWS T4 16GB": {
        "gpu_memory_limit_gb": 16.0,
        "cpu_cores": 0,
        "recommended_imgsz": 640,
        "supports_fp16": True,
    },
    "无约束 (当前设备)": {
        "gpu_memory_limit_gb": 0,
        "cpu_cores": 0,
        "recommended_imgsz": 640,
        "supports_fp16": True,
    },
}


def get_preset_names() -> list:
    return list(PRESET_PROFILES.keys())


def get_preset(name: str) -> dict | None:
    return PRESET_PROFILES.get(name)


# ═══════════════════════════════════════════
# 图表生成
# ═══════════════════════════════════════════

def generate_charts(benchmark_result: dict, device_total_gb: float = 8.0) -> bytes:
    """生成 PNG 图表（显存饼图 + 延迟直方图 + 摘要卡片 + 实测vs公式对比），返回 PNG 二进制"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(12, 10))
    fig.suptitle("Hardware Benchmark Report", fontsize=16, fontweight="bold", y=0.98)

    # ── 1. 显存分布饼图 ──
    ax1 = fig.add_subplot(2, 2, 1)
    peak_mb = benchmark_result.get("peak_memory_mb", 0)
    model_info = benchmark_result.get("model_info", {})
    weights_mb = model_info.get("weights_mb", 0)
    overhead_mb = max(peak_mb - weights_mb, 10) if peak_mb > 0 else 250
    limit_gb = benchmark_result["constraint"].get("gpu_memory_limit_gb", 0)
    if limit_gb > 0:
        limit_mb = limit_gb * 1024
        free_mb = max(limit_mb - peak_mb, 0)
        label = "Free (within limit)"
    else:
        limit_mb = device_total_gb * 1024
        free_mb = max(limit_mb - peak_mb, 0)
        label = "Free"

    sizes = [weights_mb, max(overhead_mb, 10), max(free_mb, 10)]
    labels_pie = [
        f"Weights\n({weights_mb:.0f} MB)",
        f"Activations+Overhead\n({overhead_mb:.0f} MB)",
        f"{label}\n({free_mb:.0f} MB)",
    ]
    colors_pie = ["#4CAF50", "#FF9800", "#2196F3"]
    ax1.pie(sizes, labels=labels_pie, colors=colors_pie, autopct="%1.1f%%",
            startangle=90, textprops={"fontsize": 9})
    ax1.set_title("Memory Distribution", fontsize=13, fontweight="bold")

    # ── 2. 延迟分布柱状图 ──
    ax2 = fig.add_subplot(2, 2, 2)
    lat = benchmark_result.get("latency", {})
    values = [
        lat.get("min_ms", 0), lat.get("p50_ms", 0), lat.get("mean_ms", 0),
        lat.get("p95_ms", 0), lat.get("p99_ms", 0), lat.get("max_ms", 0),
    ]
    names = ["Min", "P50", "Mean", "P95", "P99", "Max"]
    bar_colors = ["#4CAF50", "#8BC34A", "#FFC107", "#FF9800", "#F44336", "#B71C1C"]
    bars = ax2.bar(names, values, color=bar_colors)
    ax2.set_ylabel("Latency (ms)")
    ax2.set_title("Inference Latency Distribution", fontsize=13, fontweight="bold")
    for bar, v in zip(bars, values):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02,
                 f"{v:.1f}", ha="center", fontsize=8, fontweight="bold")

    # ── 3. 摘要卡片 ──
    ax3 = fig.add_subplot(2, 2, 3)
    ax3.axis("off")
    constraint = benchmark_result["constraint"]
    gpu_limit = constraint.get("gpu_memory_limit_gb", 0)
    cpu_limit = constraint.get("cpu_cores", 0)
    constraint_desc = []
    if gpu_limit > 0:
        constraint_desc.append(f"GPU Memory: {gpu_limit} GB")
    if cpu_limit > 0:
        constraint_desc.append(f"CPU Cores: {cpu_limit}")
    if not constraint_desc:
        constraint_desc.append("None (Baseline)")

    lines = [
        f"Device: {benchmark_result.get('device', 'cpu').upper()}",
        f"Constraints: {', '.join(constraint_desc)}",
        f"Model Params: {model_info.get('params_m', 0)}M",
        f"Peak Memory: {benchmark_result['peak_memory_mb']:.0f} MB",
        f"FPS: {benchmark_result['fps']:.1f}",
        f"Mean Latency: {benchmark_result['latency'].get('mean_ms', 0):.1f} ms",
        f"P95 Latency: {benchmark_result['latency'].get('p95_ms', 0):.1f} ms",
        f"OOM: {'YES' if benchmark_result['oom'] else 'No'}",
    ]
    for i, line in enumerate(lines):
        ax3.text(0.05, 0.9 - i * 0.11, line, transform=ax3.transAxes, fontsize=11,
                 fontfamily="monospace", verticalalignment="top")
    if benchmark_result.get("notes"):
        ax3.text(0.05, 0.02, "Notes: " + "; ".join(benchmark_result["notes"]),
                 transform=ax3.transAxes, fontsize=8, fontstyle="italic", color="gray")

    # ── 4. 实测 vs 公式估算对比 ──
    ax4 = fig.add_subplot(2, 2, 4)
    est = benchmark_result.get("estimated", {})
    measured = benchmark_result.get("peak_memory_mb", 0)
    estimated = est.get("inference_mb", 0)
    compare_labels = ["Measured", "Formula\nEstimate"]
    compare_vals = [measured, estimated]
    comp_colors = ["#4CAF50" if measured <= estimated else "#F44336", "#9E9E9E"]
    ax4.bar(compare_labels, compare_vals, color=comp_colors)
    ax4.set_ylabel("Memory (MB)")
    ax4.set_title("Measured vs Estimated Memory", fontsize=13, fontweight="bold")
    for i, v in enumerate(compare_vals):
        ax4.text(i, v + max(compare_vals) * 0.02, f"{v:.1f}", ha="center", fontweight="bold")
    if measured > 0 and estimated > 0:
        delta = (measured - estimated) / estimated * 100
        ax4.text(0.5, 0.95, f"Delta: {delta:+.1f}%", transform=ax4.transAxes, ha="center",
                 fontsize=10, fontweight="bold",
                 color="red" if measured > estimated else "green")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
