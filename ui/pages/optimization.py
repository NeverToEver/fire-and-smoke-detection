"""页面: Optimization"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
import streamlit as st
from ui import SCRIPT_DIR
from ui.components import ui_page_header, ui_section, ui_path_chip
from ui.widgets import model_selector
from ui.scanner import load_model_cached
from ui.image_utils import HARDWARE_PROFILES

def page_optimization():
    ui_page_header(
        "模型优化",
        "把训练好的 YOLO 权重导出为更适合目标硬件的部署格式。",
        "Optimization Console",
        ["ONNX", "FP16", "INT8", "输入尺寸缩减"],
    )

    ui_section("待优化模型", "选择训练好的 .pt 权重，后续导出流程会基于它执行。", "MODEL")
    target_model = model_selector("opt", "待优化模型")

    if not target_model or not Path(target_model).exists():
        st.info("请选择已训练的 .pt 模型")
        return

    # 读取模型基本信息
    model_size_mb = round(os.path.getsize(target_model) / 1024 / 1024, 1)
    ui_path_chip(target_model, "待优化权重")
    st.metric("当前模型大小", f"{model_size_mb} MB")

    # 目标硬件
    ui_section("目标硬件", "不同硬件支持的导出格式和推荐输入尺寸不同。", "DEVICE")
    hw_options = list(HARDWARE_PROFILES.keys())
    target_hw = st.selectbox("目标硬件", hw_options, key="opt_hw")
    hw = HARDWARE_PROFILES[target_hw]

    # 显示硬件信息
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("可用显存", f"{hw['gpu_memory_gb']} GB")
    col_b.metric("类型", hw["type"])
    col_c.metric("推荐 imgsz", hw["recommended_imgsz"])

    ui_section("优化方案", "按硬件能力选择导出格式，可同时勾选多个方案。", "PLAN")

    opt_col1, opt_col2 = st.columns(2)

    with opt_col1:
        st.markdown("**方案 A: FP16 半精度**")
        st.caption("模型大小减半，精度几乎无损")
        if hw["supports_fp16"]:
            st.success("该硬件支持 FP16")
        else:
            st.warning("该硬件不支持 FP16，请选 INT8")
        export_fp16 = st.checkbox("导出 FP16 ONNX", value=hw["supports_fp16"], key="opt_fp16")

        st.markdown("**方案 C: INT8 量化**")
        st.caption("模型大小减少 ~75%，轻微精度损失")
        if hw["supports_int8"]:
            st.success("该硬件支持 INT8")
        else:
            st.warning("该硬件不支持 INT8 量化")
        export_int8 = st.checkbox("导出 INT8 TFLite", value=hw["supports_int8"] and not hw["supports_fp16"], key="opt_int8")

    with opt_col2:
        st.markdown("**方案 B: ONNX 导出**")
        st.caption("通用跨平台格式，保持 FP32")
        export_onnx = st.checkbox("导出 FP32 ONNX", value=False, key="opt_onnx")

        st.markdown("**方案 D: 缩减输入尺寸**")
        st.caption("降低 imgsz 直接减少计算量")
        reduced_imgsz = st.selectbox(
            "目标 imgsz",
            [160, 224, 320, 416, 512],
            index=[160, 224, 320, 416, 512].index(
                min([160, 224, 320, 416, 512], key=lambda x: abs(x - hw["recommended_imgsz"]))
            ),
            key="opt_imgsz",
        )
        st.caption(f"原 640 → {reduced_imgsz}，计算量约降至 {(reduced_imgsz/640)**2:.0%}")

    ui_section("执行", "导出产物会写入 Ultralytics 返回的模型路径。", "EXPORT")

    if st.button("执行优化", type="primary", use_container_width=True):
        import shutil as _shutil
        results = []
        export_dir = SCRIPT_DIR / "runs" / "optimize"
        export_dir.mkdir(parents=True, exist_ok=True)
        model_name = Path(target_model).stem

        mtime = os.path.getmtime(target_model)
        model = load_model_cached(target_model, mtime)

        if export_fp16:
            with st.spinner("导出 FP16 ONNX..."):
                try:
                    out = model.export(format="onnx", half=True, imgsz=reduced_imgsz)
                    dest = export_dir / f"{model_name}_fp16_{reduced_imgsz}.onnx"
                    _shutil.copy2(out, dest)
                    out_size = round(os.path.getsize(dest) / 1024 / 1024, 1)
                    results.append(("FP16 ONNX", str(dest), out_size, "通用硬件，半精度"))
                except Exception as e:
                    st.error(f"FP16 导出失败: {e}")

        if export_onnx:
            with st.spinner("导出 FP32 ONNX..."):
                try:
                    out = model.export(format="onnx", half=False, imgsz=reduced_imgsz)
                    dest = export_dir / f"{model_name}_fp32_{reduced_imgsz}.onnx"
                    _shutil.copy2(out, dest)
                    out_size = round(os.path.getsize(dest) / 1024 / 1024, 1)
                    results.append(("FP32 ONNX", str(dest), out_size, "通用跨平台部署"))
                except Exception as e:
                    st.error(f"ONNX 导出失败: {e}")

        if export_int8:
            with st.spinner("导出 INT8 TFLite（需较长时间）..."):
                try:
                    out = model.export(format="tflite", int8=True, imgsz=reduced_imgsz)
                    dest = export_dir / f"{model_name}_int8_{reduced_imgsz}.tflite"
                    _shutil.copy2(out, dest)
                    out_size = round(os.path.getsize(dest) / 1024 / 1024, 1)
                    results.append(("INT8 TFLite", str(dest), out_size, "边缘设备，极致压缩"))
                except Exception as e:
                    st.error(f"INT8 导出失败: {e}。可能需要代表性数据集校准，尝试无量化导出...")
                    try:
                        out = model.export(format="tflite", imgsz=reduced_imgsz)
                        dest = export_dir / f"{model_name}_fp32_{reduced_imgsz}.tflite"
                        _shutil.copy2(out, dest)
                        out_size = round(os.path.getsize(dest) / 1024 / 1024, 1)
                        results.append(("FP32 TFLite", str(dest), out_size, "边缘设备备用"))
                    except Exception as e2:
                        st.error(f"TFLite 导出也失败: {e2}")

        st.session_state["opt_results"] = results
        st.session_state["opt_model_size"] = model_size_mb
        st.session_state["opt_has_result"] = bool(results)

    if st.session_state.get("opt_has_result"):
        results = st.session_state["opt_results"]
        model_size_mb = st.session_state["opt_model_size"]
        st.success(f"优化完成！共生成 {len(results)} 个模型文件")
        ui_section("优化结果", "导出文件路径、大小和压缩比例。", "OUTPUT")
        for name, path, size, desc in results:
            c1, c2, c3 = st.columns([2, 1, 2])
            c1.code(f"{name}: {path}")
            c2.metric("大小", f"{size} MB", f"{(1 - size/model_size_mb)*100:.0f}%" if model_size_mb else "")
            c3.caption(desc)

        # 导出优化汇总
        ui_section("导出优化报告", "将优化结果导出为 JSON 汇总。", "EXPORT")
        import json as _json
        import io as _io
        report = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_model": target_model,
            "original_size_mb": model_size_mb,
            "target_hardware": target_hw,
            "results": [{"format": r[0], "path": r[1], "size_mb": r[2]} for r in results],
        }
        buf = _io.BytesIO()
        buf.write(_json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8"))
        buf.seek(0)
        st.download_button(
            label="下载优化报告 (JSON)", data=buf,
            file_name=f"optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )


