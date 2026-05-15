"""受限环境 Benchmark UI 组件 — 预设选择、约束配置、运行、结果展示、导出"""

import io
import json
from datetime import datetime

from hw_bench import (
    get_cpu_core_count,
    get_preset_names,
    get_preset,
    run_benchmark,
    generate_charts,
)


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


def render_benchmark_ui(
    st,
    model_path: str,
    imgsz: int,
    batch: int,
    fp16: bool,
    device_info_local: dict,
) -> None:
    """渲染 Live Benchmark Tab — 预设 + 手动微调 + 运行 + 结果 + 导出"""

    st.markdown("##### 当前设备")
    has_gpu = device_info_local["available"]
    device_type = device_info_local.get("device_type", "cpu")

    if has_gpu:
        backend_label = "CUDA" if device_type == "cuda" else "MPS (Metal)"
        st.info(
            f"GPU ({backend_label}): {device_info_local['device_name']} | "
            f"总显存: {device_info_local['total_memory_gb']} GB | "
            f"可用: {device_info_local['free_memory_gb']} GB | "
            f"CPU 核心: {get_cpu_core_count()}"
        )
    else:
        st.warning(f"无 GPU 设备（CUDA/MPS 均不可用）。仅支持 CPU 推理模拟。CPU 核心: {get_cpu_core_count()}")

    max_gpu = device_info_local["total_memory_gb"] if has_gpu else 8.0
    max_cores = get_cpu_core_count()

    # ── 预设选择 ──
    st.markdown("##### 快捷预设")
    custom_profiles = get_custom_profiles_from_session(st)
    all_names = get_preset_names() + list(custom_profiles.keys())

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

        if r["oom"]:
            st.error(f"OOM: {r['oom_message'][:300]}")
        else:
            st.success("模型在约束条件下可运行")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("峰值显存", f"{r['peak_memory_mb']:.0f} MB")
        c2.metric("FPS", f"{r['fps']:.0f}")
        c3.metric("平均延迟", f"{r['latency'].get('mean_ms', 0):.1f} ms")
        c4.metric("P95 延迟", f"{r['latency'].get('p95_ms', 0):.1f} ms")
        c5.metric("推理设备", r["device"].upper())

        estimated_mb = r["estimated"].get("inference_mb", 0)
        measured_mb = r["peak_memory_mb"]
        if estimated_mb > 0 and measured_mb > 0:
            delta = (measured_mb - estimated_mb) / estimated_mb * 100
            st.caption(f"公式估算: {estimated_mb:.0f} MB | 实测: {measured_mb:.0f} MB | 偏差: {delta:+.1f}%")

        if r.get("notes"):
            for note in r["notes"]:
                st.caption(f"ℹ️ {note}")

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

        try:
            png_data = generate_charts(r, device_total_gb=device_info_local.get("total_memory_gb", 8.0))
            col_dl2.download_button(
                label="📊 导出图表 PNG",
                data=png_data,
                file_name=f"benchmark_charts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png",
                use_container_width=True,
            )
        except Exception as e:
            col_dl2.warning(f"图表生成失败: {e}")
