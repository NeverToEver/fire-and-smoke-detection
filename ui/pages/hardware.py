"""页面: 硬件预估 + 受限环境模拟"""

import os
import io
import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from ui import SCRIPT_DIR
from ui.components import ui_page_header, ui_section, ui_path_chip
from ui.widgets import model_selector, model_config_selector
from ui.image_utils import estimate_memory, HARDWARE_PROFILES, get_model_info
from ui.pages.hardware_benchmark import render_benchmark_ui

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
        from engine.benchmark import detect_device

        device_info_local = detect_device()
        render_benchmark_ui(st, target, imgsz, batch, fp16_mode, device_info_local)
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
            finally:
                try:
                    del model
                except Exception:
                    pass
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

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
        csv_hw = df.to_csv(index=False).encode("utf-8")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button("下载兼容性表格 (CSV)", csv_hw, f"hardware_compat_{ts}.csv",
                           "text/csv", key="dl_hw_csv", use_container_width=True)

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

