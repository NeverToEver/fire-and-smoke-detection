"""页面: 硬件预估 + 受限环境模拟"""

import os
import io
import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from gui import SCRIPT_DIR
from gui.components import ui_page_header, ui_section, ui_path_chip
from gui.selectors import model_selector, model_config_selector
from gui.utils import estimate_memory, HARDWARE_PROFILES, _get_model_info
from hw_bench import (
    detect_cuda_device, get_cpu_core_count,
    run_benchmark, generate_charts,
    PRESET_PROFILES, get_preset_names, get_preset,
)

def page_hardware():
    ui_page_header(
        "硬件需求预估",
        "根据模型复杂度、输入尺寸、batch 和精度模式，估算推理/训练显存需求。",
        "Hardware Console",
        ["边缘设备", "显存估算", "FP16", "兼容性表"],
    )

    ui_section("模型来源", "可以用 YAML 结构配置，也可以直接读取已训练权重。", "TARGET")
    source_mode = st.radio("选择来源", ["从模型配置预估", "从已训练模型预估"], horizontal=True, key="hw_source")

    if source_mode == "从模型配置预估":
        target = model_config_selector("hw", "选择模型配置")
    else:
        target = model_selector("hw", "已训练模型")

    if not target or not Path(target).exists():
        st.info("请选择模型配置或已训练模型文件")
        return

    ui_path_chip(target, "分析目标")

    # 估算模式切换
    hw_mode = st.radio("估算模式", ["公式估算", "受限环境模拟"], horizontal=True, key="hw_est_mode")

    ui_section("预估参数", "输入尺寸、Batch 和精度模式会直接影响显存峰值。", "PARAMS")
    col1, col2, col3 = st.columns(3)
    imgsz = col1.selectbox("输入尺寸", [320, 416, 512, 640, 800, 1024], index=3, key="hw_imgsz")
    batch = col2.slider("Batch Size", 1, 64, 1, key="hw_batch")
    fp16_mode = col3.checkbox("FP16 模式", value=False, key="hw_fp16",
                               help="开启后半精度，显存需求约减半")

    # ── 受限环境模拟分支 ──
    if hw_mode == "受限环境模拟":
        from hw_bench import render_benchmark_ui, detect_cuda_device

        cuda_info = detect_cuda_device()
        render_benchmark_ui(st, target, imgsz, batch, fp16_mode, cuda_info)
        return

    # 签名跟踪：目标文件 mtime + 参数，检测变化时清除旧结果
    try:
        cur_sig = f"{target}:{os.path.getmtime(target)}:{imgsz}:{batch}:{fp16_mode}"
    except OSError:
        cur_sig = ""
    if st.session_state.get("hw_sig") != cur_sig:
        st.session_state["hw_has_result"] = False
        st.session_state["hw_sig"] = cur_sig

    if st.button("开始预估", type="primary", use_container_width=True):
        with st.spinner("正在分析模型..."):
            import torch
            from ultralytics import YOLO

            try:
                model = YOLO(target)
                total = sum(p.numel() for p in model.model.parameters())
                params_m = total / 1e6

                flops_g = 0.0
                try:
                    from thop import profile
                    dummy = torch.randn(1, 3, imgsz, imgsz)
                    flops, _ = profile(model.model, inputs=(dummy,), verbose=False)
                    flops_g = flops / 1e9
                except Exception:
                    pass

                memory = estimate_memory(params_m, imgsz, batch, fp16_mode)

                st.session_state["hw_params_m"] = params_m
                st.session_state["hw_flops_g"] = flops_g
                st.session_state["hw_memory"] = memory
                st.session_state["hw_saved_imgsz"] = imgsz
                st.session_state["hw_saved_batch"] = batch
                st.session_state["hw_saved_fp16"] = fp16_mode
                st.session_state["hw_target"] = target
                st.session_state["hw_has_result"] = True
                st.session_state["hw_sig"] = cur_sig

            except Exception as e:
                st.error(f"模型分析失败: {e}")
                st.session_state["hw_has_result"] = False

    if st.session_state.get("hw_has_result"):
        params_m = st.session_state["hw_params_m"]
        flops_g = st.session_state["hw_flops_g"]
        memory = st.session_state["hw_memory"]
        imgsz = st.session_state["hw_saved_imgsz"]
        batch = st.session_state.get("hw_saved_batch", 1)
        fp16_mode = st.session_state["hw_saved_fp16"]
        target = st.session_state.get("hw_target", "")

        # 展示预估结果
        ui_section("模型复杂度", "从 Ultralytics 模型信息解析出的参数量和 GFLOPs。", "MODEL")
        c1, c2, c3 = st.columns(3)
        c1.metric("参数量", f"{params_m:.1f} M")
        c2.metric("计算量", f"{flops_g:.1f} GFLOPs")
        c3.metric("模型文件大小 (估)", f"{params_m * 4:.0f} MB" if not fp16_mode else f"{params_m * 2:.0f} MB")

        ui_section("显存 / 内存预估", "粗略估算推理和训练峰值，便于选择部署硬件。", "MEMORY")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("模型占用", f"{memory['model_mb']:.0f} MB")
        c2.metric("激活值", f"{memory['activation_mb']:.0f} MB")
        c3.metric("推理峰值", f"{memory['inference_mb']:.0f} MB ({memory['inference_gb']:.1f} GB)")
        c4.metric("训练峰值", f"{memory['training_mb']:.0f} MB ({memory['training_gb']:.1f} GB)")

        # 硬件兼容性
        ui_section("硬件兼容性", "按 85% 可用显存阈值给出运行建议。", "DEVICE")
        rows = []
        for hw_name, hw in HARDWARE_PROFILES.items():
            mem_ok = memory["inference_gb"] <= hw["gpu_memory_gb"] * 0.85
            status = "可运行" if mem_ok else "显存不足"
            note = ""
            if mem_ok and hw["recommended_imgsz"] < imgsz:
                note = f"建议降 imgsz 至 {hw['recommended_imgsz']}"
            if hw.get("type") == "edge_cpu" and params_m > 20:
                note = "CPU 推理可能较慢"
            rows.append({
                "硬件": hw_name,
                "可用显存": f"{hw['gpu_memory_gb']} GB",
                "推理需求": f"{memory['inference_gb']:.1f} GB",
                "状态": status,
                "建议": note or "—",
            })

        import pandas as pd
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # 导出硬件预估报告
        ui_section("导出报告", "将预估结果导出为 JSON 文件。", "EXPORT")
        import json as _json
        import io as _io
        report = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target": target,
            "params_m": round(params_m, 2),
            "flops_g": round(flops_g, 2),
            "imgsz": imgsz,
            "batch": batch,
            "fp16": fp16_mode,
            "memory": memory,
            "compatibility": rows,
        }
        buf = _io.BytesIO()
        buf.write(_json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8"))
        buf.seek(0)
        st.download_button(
            label="下载硬件预估报告 (JSON)", data=buf,
            file_name=f"hardware_est_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )


# ═══════════════════════════════════════════
# 页面 6：模型优化
# ═══════════════════════════════════════════



def render_benchmark_ui(
    st,
    model_path: str,
    imgsz: int,
    batch: int,
    fp16: bool,
    cuda_info: dict,
) -> None:
    """渲染 Live Benchmark Tab — 预设 + 手动微调 + 运行 + 结果 + 导出"""

    st.markdown("##### 当前设备")
    if cuda_info["available"]:
        st.info(
            f"GPU: {cuda_info['device_name']} | "
            f"总显存: {cuda_info['total_memory_gb']} GB | "
            f"可用: {cuda_info['free_memory_gb']} GB | "
            f"CPU 核心: {get_cpu_core_count()}"
        )
    else:
        st.warning(f"无 CUDA 设备。仅支持 CPU 推理模拟。CPU 核心: {get_cpu_core_count()}")

    has_cuda = cuda_info["available"]
    max_gpu = cuda_info["total_memory_gb"] if has_cuda else 8.0
    max_cores = get_cpu_core_count()

    # ── 预设选择 ──
    st.markdown("##### 快捷预设")
    custom_profiles = get_custom_profiles_from_session(st)
    all_names = get_preset_names() + list(custom_profiles.keys())

    # session_state 追踪预设变更
    if "hw_active_preset" not in st.session_state:
        st.session_state["hw_active_preset"] = "无约束 (当前设备)"

    selected_preset = st.selectbox(
        "选择目标设备（自动填充约束值）",
        all_names,
        key="hw_preset_selector",
    )

    if selected_preset != st.session_state["hw_active_preset"]:
        st.session_state["hw_active_preset"] = selected_preset
        preset = get_preset(selected_preset) or custom_profiles.get(selected_preset, {})
        st.session_state["hw_gpu_limit"] = preset.get("gpu_memory_limit_gb", 0)
        st.session_state["hw_cpu_limit"] = preset.get("cpu_cores", 0)
        st.rerun()

    # 初始化约束值
    if "hw_gpu_limit" not in st.session_state:
        st.session_state["hw_gpu_limit"] = 0.0
    if "hw_cpu_limit" not in st.session_state:
        st.session_state["hw_cpu_limit"] = 0

    st.markdown("##### 约束参数 (可手动微调)")
    col1, col2 = st.columns(2)

    gpu_limit = col1.slider(
        "GPU 显存上限 (GB)",
        min_value=0.0,
        max_value=max_gpu,
        value=float(st.session_state["hw_gpu_limit"]),
        step=0.5,
        help="0 = 不限制。设置后 PyTorch 仅能使用指定显存量",
        key="hw_gpu_slider",
    )
    st.session_state["hw_gpu_limit"] = gpu_limit

    cpu_limit = col2.slider(
        "CPU 核心数",
        min_value=0,
        max_value=max_cores,
        value=int(st.session_state["hw_cpu_limit"]),
        step=1,
        help="0 = 不限制。>0 时自动切 CPU 推理模式",
        key="hw_cpu_slider",
    )
    st.session_state["hw_cpu_limit"] = cpu_limit

    # 约束状态摘要
    constraints = []
    if gpu_limit > 0:
        constraints.append(f"GPU 显存限制至 {gpu_limit} GB")
    if cpu_limit > 0:
        constraints.append(f"CPU 限制 {cpu_limit}/{max_cores} 核")
    if not constraints:
        constraints.append("无约束 (基准测试)")
    st.caption(f"生效约束: {' | '.join(constraints)}")

    # ── 适用于当前约束的设备列表 ──
    st.markdown("##### 适用于当前约束的目标设备")
    matching = []
    for name in all_names:
        p = get_preset(name) or custom_profiles.get(name)
        if p is None:
            continue
        p_gpu = p.get("gpu_memory_limit_gb", 0)
        p_cpu = p.get("cpu_cores", 0)
        matches = True
        issues = []
        if gpu_limit > 0 and p_gpu > 0 and gpu_limit > p_gpu:
            matches = False
            issues.append(f"GPU {gpu_limit}>{p_gpu}GB")
        if cpu_limit > 0 and p_cpu > 0 and cpu_limit != p_cpu:
            issues.append(f"CPU cores mismatch ({cpu_limit}≠{p_cpu})")
        if matches:
            matching.append(f"✓ {name}")
        else:
            matching.append(f"✗ {name} ({'; '.join(issues)})")
    if matching:
        for m in matching:
            st.caption(m)
    else:
        st.caption("无匹配设备")

    # ── 自定义预设 ──
    with st.expander("自定义预设管理"):
        col_name, col_save = st.columns([3, 1])
        custom_name = col_name.text_input("预设名称", key="hw_custom_name")
        if col_save.button("💾 保存为自定义预设", use_container_width=True):
            if custom_name.strip():
                save_custom_preset(st, custom_name.strip(), gpu_limit, cpu_limit, imgsz, fp16)
                st.success(f"已保存 '{custom_name.strip()}'")
                st.rerun()
            else:
                st.error("请输入预设名称")

        if custom_profiles:
            for name in list(custom_profiles.keys()):
                c = st.columns([3, 1])
                p = custom_profiles[name]
                c[0].caption(
                    f"**{name}**: GPU {p['gpu_memory_limit_gb']}GB | "
                    f"CPU {p['cpu_cores']}核 | imgsz {p['recommended_imgsz']}"
                )
                if c[1].button("删除", key=f"del_{name}"):
                    delete_custom_preset(st, name)
                    st.rerun()

    # ── 运行 Benchmark ──
    st.markdown("---")

    # 参数变化时清除旧结果
    cur_bench_sig = f"{model_path}:{imgsz}:{batch}:{fp16}:{gpu_limit}:{cpu_limit}"
    if st.session_state.get("hw_bench_sig") != cur_bench_sig:
        st.session_state["hw_has_bench_result"] = False
        st.session_state["hw_bench_sig"] = cur_bench_sig

    if st.button("🚀 运行模拟 Benchmark", type="primary", use_container_width=True, key="hw_run_bench"):
        with st.spinner("正在受限环境中运行模型..."):
            result = run_benchmark(
                model_path=model_path,
                imgsz=imgsz,
                batch=batch,
                fp16=fp16 and (not cpu_limit > 0),
                gpu_memory_limit_gb=gpu_limit,
                cpu_cores=cpu_limit,
                num_warmup=5,
                num_measure=50,
            )
            st.session_state["hw_bench_result"] = result
            st.session_state["hw_has_bench_result"] = True

    # ── 展示结果 ──
    if st.session_state.get("hw_has_bench_result"):
        r = st.session_state["hw_bench_result"]
        st.markdown("---")
        st.markdown("##### Benchmark 结果")

        # OOM 警告
        if r["oom"]:
            st.error(f"OOM: {r['oom_message'][:300]}")
        else:
            st.success("模型在约束条件下可运行")

        # 指标卡片
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("峰值显存", f"{r['peak_memory_mb']:.0f} MB")
        c2.metric("FPS", f"{r['fps']:.0f}")
        c3.metric("平均延迟", f"{r['latency'].get('mean_ms', 0):.1f} ms")
        c4.metric("P95 延迟", f"{r['latency'].get('p95_ms', 0):.1f} ms")
        c5.metric("推理设备", r["device"].upper())

        # 实测 vs 估算
        estimated_mb = r["estimated"].get("inference_mb", 0)
        measured_mb = r["peak_memory_mb"]
        if estimated_mb > 0 and measured_mb > 0:
            delta = (measured_mb - estimated_mb) / estimated_mb * 100
            st.caption(f"公式估算: {estimated_mb:.0f} MB | 实测: {measured_mb:.0f} MB | 偏差: {delta:+.1f}%")

        # Notes
        if r.get("notes"):
            for note in r["notes"]:
                st.caption(f"ℹ️ {note}")

        # 延迟详情
        with st.expander("延迟详情"):
            lat = r["latency"]
            st.write({
                "min_ms": lat.get("min_ms"), "p50_ms": lat.get("p50_ms"),
                "mean_ms": lat.get("mean_ms"), "p95_ms": lat.get("p95_ms"),
                "p99_ms": lat.get("p99_ms"), "max_ms": lat.get("max_ms"),
                "std_ms": lat.get("std_ms"),
            })

        # ── 导出 ──
        col_dl1, col_dl2 = st.columns(2)

        # JSON 报告
        export_data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model_path": model_path,
            "imgsz": imgsz,
            "batch": batch,
            "fp16": fp16,
            "constraints": {"gpu_memory_limit_gb": gpu_limit, "cpu_cores": cpu_limit},
            **{k: v for k, v in r.items() if k != "estimated"},
        }
        json_buf = io.BytesIO()
        json_buf.write(json.dumps(export_data, indent=2, ensure_ascii=False).encode("utf-8"))
        json_buf.seek(0)
        col_dl1.download_button(
            label="📥 下载报告 JSON",
            data=json_buf,
            file_name=f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )

        # PNG 图表
        try:
            png_data = generate_charts(r, device_total_gb=cuda_info.get("total_memory_gb", 8.0))
            col_dl2.download_button(
                label="📊 导出图表 PNG",
                data=png_data,
                file_name=f"benchmark_charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png",
                use_container_width=True,
            )
        except Exception as e:
            col_dl2.warning(f"图表生成失败: {e}")


def get_custom_profiles_from_session(st) -> dict:
    if "hw_custom_presets" not in st.session_state:
        st.session_state["hw_custom_presets"] = {}
    return st.session_state["hw_custom_presets"]




def save_custom_preset(st, name: str, gpu_mem: float, cpu_cores: int, imgsz: int, fp16: bool):
    custom = get_custom_profiles_from_session(st)
    custom[name] = {
        "gpu_memory_limit_gb": gpu_mem,
        "cpu_cores": cpu_cores,
        "recommended_imgsz": imgsz,
        "supports_fp16": fp16,
    }
    st.session_state["hw_custom_presets"] = custom




def delete_custom_preset(st, name: str):
    custom = get_custom_profiles_from_session(st)
    if name in custom:
        del custom[name]
        st.session_state["hw_custom_presets"] = custom




