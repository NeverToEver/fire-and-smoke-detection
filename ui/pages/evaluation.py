"""页面: Evaluation"""

from io import BytesIO
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from ui import SCRIPT_DIR
from ui.components import ui_page_header, ui_section, ui_path_chip
from ui.widgets import model_selector, dataset_selector
from ui.scanner import scan_models, save_uploaded_file
from ui.image_utils import get_model_info, run_eval
from ui.runtime import clear_export_timestamp, export_timestamp, file_fingerprint, reset_state_on_change

def page_evaluation():
    ui_page_header(
        "模型评估",
        "运行验证集评估，查看检测精度、模型复杂度，并对多个训练结果做横向比较。",
        "Evaluation Console",
        ["mAP", "Precision / Recall", "参数量", "FLOPs"],
    )

    tab1, tab2 = st.tabs(["单模型评估", "多模型对比"])

    # ══════════════ Tab 1: 单模型评估 ══════════════
    with tab1:
        ui_section("评估输入", "选择一个模型权重和一个 data.yaml 作为评估对象。", "SINGLE")
        model_path = model_selector("eval", "模型权重")
        yaml_path = dataset_selector("eval", "评估数据集")
        reset_state_on_change(
            "eval_single_sig",
            f"{model_path}|{yaml_path}",
            [
                "eval_has_result",
                "eval_result",
                "eval_model_info",
                "eval_model_path",
                "eval_yaml_path",
                "eval_single_export_ts",
            ],
        )

        if not model_path or not Path(model_path).exists():
            st.info("请选择已训练的 .pt 模型")
        elif not yaml_path or not Path(yaml_path).exists():
            st.info("请选择评估数据集 data.yaml")
        elif st.button("开始评估", type="primary", key="eval_single"):
            with st.spinner("正在评估模型..."):
                try:
                    st.session_state["eval_result"] = run_eval(model_path, yaml_path)
                    st.session_state["eval_model_info"] = get_model_info(model_path)
                    st.session_state["eval_model_path"] = model_path
                    st.session_state["eval_yaml_path"] = yaml_path
                    st.session_state["eval_has_result"] = True
                    clear_export_timestamp("eval_single_export_ts")
                except Exception as e:
                    st.error(f"评估失败: {e}")
                    st.session_state["eval_has_result"] = False

        # 持久化展示结果（不因下载按钮点击而消失）
        if st.session_state.get("eval_has_result"):
            eval_result = st.session_state["eval_result"]
            model_info = st.session_state["eval_model_info"]
            model_path = st.session_state["eval_model_path"]
            yaml_path = st.session_state["eval_yaml_path"]

            # 第一行：检测指标
            ui_section("检测指标", "验证集上的目标检测核心指标。", "METRICS")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("mAP@50", f"{eval_result['map50']:.4f}")
            c2.metric("mAP@50-95", f"{eval_result['map50_95']:.4f}")
            p_val = eval_result['precision']
            r_val = eval_result['recall']
            c3.metric("Precision", f"{p_val:.4f}" if p_val is not None else "—")
            c4.metric("Recall", f"{r_val:.4f}" if r_val is not None else "—")
            f1 = 2 * p_val * r_val / (p_val + r_val) if (p_val is not None and r_val is not None and (p_val + r_val) > 0) else 0
            c5.metric("F1", f"{f1:.4f}")

            # 第二行：模型复杂度
            ui_section("模型复杂度", "参数量和估算计算量。", "COST")
            c1, c2 = st.columns(2)
            c1.metric("参数量", f"{model_info['params_m']:.1f} M")
            c2.metric("计算量", f"{model_info['flops_g']:.1f} GFLOPs")

            # 评估图表 — 使用本次评估的 save_dir
            save_dir_str = eval_result.get("save_dir", "")
            val_dir = Path(save_dir_str) if save_dir_str and Path(save_dir_str).exists() else None
            if val_dir:
                ui_section("评估图表", "Ultralytics 验证流程输出的可视化结果。", "PLOTS")
                plot_files = sorted(val_dir.glob("*.png"))
                if plot_files:
                    cols = st.columns(2)
                    for i, pf in enumerate(plot_files):
                        cols[i % 2].image(str(pf), caption=pf.name, use_container_width=True)
                else:
                    st.info("未找到评估图表文件")
            else:
                st.info("评估图表将在运行后自动生成")

            # 导出评估结果
            ui_section("导出结果", "生成含全部评估指标和曲线的汇总图片。", "EXPORT")
            ts_eval = export_timestamp("eval_single_export_ts")
            report_time = datetime.strptime(ts_eval, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")

            f1_val = 2 * eval_result['precision'] * eval_result['recall'] / (eval_result['precision'] + eval_result['recall'] + 1e-6)
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.axis("off")

            title = f"Evaluation Report — {Path(model_path).name}"
            ax.text(0.5, 0.92, title, transform=ax.transAxes, fontsize=18, fontweight="bold",
                    ha="center", va="top", fontfamily="monospace")

            info_lines = [
                f"Model: {Path(model_path).name}",
                f"Dataset: {Path(yaml_path).name}",
                f"Date: {report_time}",
            ]
            for i, line in enumerate(info_lines):
                ax.text(0.05, 0.80 - i * 0.05, line, transform=ax.transAxes,
                        fontsize=9, fontfamily="monospace", color="#555555")

            bar_labels, bar_vals, bar_colors = [], [], []
            for name, val in [
                ("mAP@50", eval_result["map50"]),
                ("mAP@50-95", eval_result["map50_95"]),
                ("Precision", eval_result["precision"]),
                ("Recall", eval_result["recall"]),
                ("F1 Score", f1_val),
            ]:
                bar_labels.append(name)
                bar_vals.append(val)
                bar_colors.append("#4CAF50" if val >= 0.7 else "#FF9800" if val >= 0.4 else "#F44336")

            ax_bar = fig.add_axes([0.08, 0.38, 0.5, 0.32])
            bars = ax_bar.barh(bar_labels, bar_vals, color=bar_colors, height=0.5)
            ax_bar.set_xlim(0, 1)
            ax_bar.set_xlabel("Score", fontsize=9)
            for bar, val in zip(bars, bar_vals):
                ax_bar.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                            f"{val:.4f}", va="center", fontsize=10, fontweight="bold", fontfamily="monospace")
            ax_bar.invert_yaxis()

            ax_table = fig.add_axes([0.62, 0.38, 0.34, 0.32])
            ax_table.axis("off")
            table_data = [["Params", f"{model_info['params_m']:.1f} M"],
                          ["GFLOPs", f"{model_info['flops_g']:.1f}"]]
            tbl = ax_table.table(cellText=table_data, colLabels=["Metric", "Value"],
                                 cellLoc="center", loc="center", colWidths=[0.18, 0.14])
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(10)
            for key, cell in tbl.get_celld().items():
                if key[0] == 0:
                    cell.set_facecolor("#333333")
                    cell.set_text_props(color="white", fontweight="bold")

            footer = "Flame & Smoke Detection · YOLOv11 + MobileNetV3 + Slim-Neck"
            ax.text(0.5, 0.02, footer, transform=ax.transAxes, fontsize=8,
                    ha="center", va="bottom", fontfamily="monospace", color="#aaaaaa")

            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
            buf.seek(0)
            plt.close(fig)

            fname = f"eval_{Path(model_path).stem}_{ts_eval}.png"
            st.download_button(label="下载评估报告 (PNG)", data=buf, file_name=fname, mime="image/png")

            eval_dir = (SCRIPT_DIR / "eval_results")
            eval_dir.mkdir(exist_ok=True)
            save_path = eval_dir / fname
            save_path.write_bytes(buf.getvalue())
            st.caption(f"已自动保存至 {save_path.resolve()}")

    # ══════════════ Tab 2: 多模型对比 ══════════════
    with tab2:
        ui_section("对比输入", "选择 2 到 5 个模型，使用同一个数据集评估。支持拖拽上传、自动发现和手动输入路径。", "COMPARE")
        models = scan_models()

        # 收集所有可选模型路径: {label: path}
        available_models = {}  # label → path
        if models:
            for m in models:
                available_models[m["label"]] = m["path"]

        # ── 拖拽上传 ──
        uploaded_files = st.file_uploader(
            "拖拽上传模型权重（可多选）",
            type=["pt"],
            accept_multiple_files=True,
            key="eval_cmp_upload",
            help="支持拖入 best.pt / last.pt。上传后自动加入对比列表。",
        )
        if uploaded_files:
            for uf in uploaded_files:
                fp = file_fingerprint(uf)
                upload_key = f"eval_cmp_uploaded_{fp[:12]}"
                if upload_key not in st.session_state:
                    saved_path = save_uploaded_file(uf, "models")
                    label = f"[上传] {Path(saved_path).name}"
                    st.session_state[upload_key] = {"label": label, "path": saved_path}
                    available_models[label] = saved_path
                    scan_models.clear()
                else:
                    cached = st.session_state[upload_key]
                    available_models[cached["label"]] = cached["path"]

        # ── 自动发现 + 手动输入 ──
        col1, col2 = st.columns([2, 1])
        with col1:
            if available_models:
                default_selection = []
                # 自动选中最新的上传模型
                for label in available_models:
                    if label.startswith("[上传]"):
                        default_selection.append(label)
                selected_labels = st.multiselect(
                    "选择要对比的模型（2-5 个）",
                    options=list(available_models.keys()),
                    default=default_selection[:5],
                    max_selections=5,
                    key="eval_compare",
                )
            else:
                selected_labels = []
                st.info("未发现已训练模型，请上传或手动输入路径")

        with col2:
            manual_input = st.text_area(
                "手动输入路径",
                placeholder="每行一个 .pt 路径",
                key="eval_cmp_manual",
                height=100,
            )
            if manual_input:
                for line in manual_input.strip().split("\n"):
                    p = line.strip()
                    if p and Path(p).exists() and p not in available_models.values():
                        label = f"[手动] {Path(p).name}"
                        available_models[label] = p

        # 同步手动输入到选中列表
        if manual_input:
            for line in manual_input.strip().split("\n"):
                p = line.strip()
                if p and Path(p).exists():
                    matching_label = None
                    for label, path in available_models.items():
                        if path == p:
                            matching_label = label
                            break
                    if matching_label and matching_label not in selected_labels:
                        selected_labels.append(matching_label)

        yaml_path = dataset_selector("eval_cmp", "评估数据集")

        compare_ready = len(selected_labels) >= 2 and yaml_path and Path(yaml_path).exists()
        if len(selected_labels) < 2:
            st.info("请至少选择 2 个模型进行对比")
        elif not yaml_path or not Path(yaml_path).exists():
            st.info("请选择评估数据集")

        # 签名跟踪：输入变化时自动清除旧结果
        selected_sig_paths = [available_models.get(label, label) for label in selected_labels]
        cmp_sig = f"{yaml_path}|{','.join(sorted(selected_sig_paths))}"
        reset_state_on_change(
            "cmp_sig",
            cmp_sig,
            ["cmp_has_result", "cmp_data", "cmp_names", "cmp_yaml", "cmp_export_ts"],
        )

        if compare_ready and st.button("开始对比", type="primary", key="eval_compare_btn"):
            selected_paths = [available_models[l] for l in selected_labels if l in available_models]
            selected_names = [l for l in selected_labels if l in available_models]
            comparison_data = []

            progress = st.progress(0)
            for i, (name, path) in enumerate(zip(selected_names, selected_paths)):
                with st.spinner(f"Evaluating {name}..."):
                    try:
                        metrics = run_eval(path, yaml_path)
                        info = get_model_info(path)
                        comparison_data.append({
                            "Model": name,
                            "mAP@50": metrics["map50"],
                            "mAP@50-95": metrics["map50_95"],
                            "Precision": metrics["precision"],
                            "Recall": metrics["recall"],
                            "F1": 2 * metrics["precision"] * metrics["recall"]
                                   / (metrics["precision"] + metrics["recall"] + 1e-6),
                            "Params (M)": info["params_m"],
                            "GFLOPs": info["flops_g"],
                        })
                    except Exception as e:
                        st.warning(f"{name} evaluation failed: {e}")
                progress.progress((i + 1) / len(selected_paths))
            progress.empty()

            if len(comparison_data) >= 2:
                st.session_state["cmp_data"] = comparison_data
                st.session_state["cmp_names"] = selected_names[:len(comparison_data)]
                st.session_state["cmp_yaml"] = yaml_path
                st.session_state["cmp_has_result"] = True
                clear_export_timestamp("cmp_export_ts")
                st.rerun()
            else:
                st.error("At least 2 models must succeed for comparison")
                st.session_state["cmp_has_result"] = False

    # ── 持久化展示对比结果（在 button 外部，确保下载不清空）──
    if st.session_state.get("cmp_has_result"):
        comparison_data = st.session_state["cmp_data"]
        selected_names = st.session_state["cmp_names"]
    else:
        return

    ts = export_timestamp("cmp_export_ts")
    report_time = datetime.strptime(ts, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")

    col_title, col_clear = st.columns([4, 1])
    with col_title:
        ui_section("对比结果", "多模型在同一验证集上的横向对比。", "RESULT")
    with col_clear:
        if st.button("清除结果", key="eval_cmp_clear"):
            st.session_state["cmp_has_result"] = False
            clear_export_timestamp("cmp_export_ts")
            st.rerun()

    df = pd.DataFrame(comparison_data)

    ui_section("指标对比", "关键检测指标并行展示。", "TABLE")
    st.dataframe(
            df.style.format({
                "mAP@50": "{:.4f}", "mAP@50-95": "{:.4f}",
                "Precision": "{:.4f}", "Recall": "{:.4f}", "F1": "{:.4f}",
                "Params (M)": "{:.1f}", "GFLOPs": "{:.1f}",
            }),
            use_container_width=True, hide_index=True,
    )
    # 表格单独下载 CSV
    csv_buf = df.to_csv(index=False).encode("utf-8")
    st.download_button("下载 CSV", csv_buf, f"metrics_{ts}.csv", "text/csv",
                        key="dl_csv", use_container_width=True)

    ui_section("检测精度", "mAP@50 与 mAP@50-95 模型间对比。", "CHART")
    chart_data_map = pd.DataFrame({
            "Model": selected_names[:len(comparison_data)],
            "mAP@50": [d["mAP@50"] for d in comparison_data],
            "mAP@50-95": [d["mAP@50-95"] for d in comparison_data],
    }).set_index("Model")
    st.bar_chart(chart_data_map, use_container_width=True)
    # 单独下载 mAP 图
    fig_map, ax_map = plt.subplots(figsize=(8, 4))
    x_map = range(len(chart_data_map))
    ax_map.bar([i - 0.15 for i in x_map], chart_data_map["mAP@50"], 0.28, color="#2196F3", label="mAP@50")
    ax_map.bar([i + 0.15 for i in x_map], chart_data_map["mAP@50-95"], 0.28, color="#4CAF50", label="mAP@50-95")
    ax_map.set_xticks(x_map)
    ax_map.set_xticklabels(chart_data_map.index, fontsize=8)
    ax_map.set_ylim(0, 1)
    ax_map.set_title("Detection Accuracy", fontweight="bold")
    ax_map.legend(fontsize=8)
    ax_map.grid(axis="y", alpha=0.3)
    fig_map.tight_layout()
    buf_map = BytesIO()
    fig_map.savefig(buf_map, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    buf_map.seek(0)
    plt.close(fig_map)
    st.download_button("下载图表 (PNG)", buf_map, f"mAP_{ts}.png", "image/png",
                        key="dl_map", use_container_width=True)

    ui_section("精确率 / 召回率 / F1", "三指标在各模型上的对比。", "CHART")
    chart_data_pr = pd.DataFrame({
            "Model": selected_names[:len(comparison_data)],
            "Precision": [d["Precision"] for d in comparison_data],
            "Recall": [d["Recall"] for d in comparison_data],
            "F1": [d["F1"] for d in comparison_data],
    }).set_index("Model")
    st.bar_chart(chart_data_pr, use_container_width=True)
    # 单独下载 PRF 图
    fig_prf, ax_prf = plt.subplots(figsize=(8, 4))
    x_prf = range(len(chart_data_pr))
    w = 0.25
    ax_prf.bar([i - w for i in x_prf], chart_data_pr["Precision"], w, color="#FF9800", label="Precision")
    ax_prf.bar(x_prf, chart_data_pr["Recall"], w, color="#9C27B0", label="Recall")
    ax_prf.bar([i + w for i in x_prf], chart_data_pr["F1"], w, color="#F44336", label="F1")
    ax_prf.set_xticks(x_prf)
    ax_prf.set_xticklabels(chart_data_pr.index, fontsize=8)
    ax_prf.set_ylim(0, 1)
    ax_prf.set_title("Precision / Recall / F1", fontweight="bold")
    ax_prf.legend(fontsize=8)
    ax_prf.grid(axis="y", alpha=0.3)
    fig_prf.tight_layout()
    buf_prf = BytesIO()
    fig_prf.savefig(buf_prf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    buf_prf.seek(0)
    plt.close(fig_prf)
    st.download_button("下载图表 (PNG)", buf_prf, f"PRF_{ts}.png", "image/png",
                        key="dl_prf", use_container_width=True)

    ui_section("模型复杂度", "参数量与计算量对比，越低越适合边缘部署。", "COST")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, max(3, len(comparison_data) * 0.6)))
    names = selected_names[:len(comparison_data)]
    params_vals = [d["Params (M)"] for d in comparison_data]
    flops_vals = [d["GFLOPs"] for d in comparison_data]

    colors_params = ["#4CAF50" if v == min(params_vals) else "#2196F3" for v in params_vals]
    ax1.barh(names, params_vals, color=colors_params)
    ax1.set_xlabel("Parameters (M)")
    ax1.set_title("Parameters (lower is better)")

    colors_flops = ["#4CAF50" if v == min(flops_vals) else "#2196F3" for v in flops_vals]
    ax2.barh(names, flops_vals, color=colors_flops)
    ax2.set_xlabel("GFLOPs")
    ax2.set_title("Compute (lower is better)")

    fig.tight_layout()
    st.pyplot(fig)
    buf_cost = BytesIO()
    fig.savefig(buf_cost, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    buf_cost.seek(0)
    plt.close(fig)
    st.download_button("下载图表 (PNG)", buf_cost, f"complexity_{ts}.png", "image/png",
                        key="dl_complexity", use_container_width=True)

    # ── 导出（PNG + PDF）──
    ui_section("导出报告", "下载对比图表与表格，支持 PNG 和 PDF 格式。", "EXPORT")

    n = len(comparison_data)
    names_list = [d["Model"] for d in comparison_data]
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336"]

    # ── PNG 导出 ──
    fig_png, axes_png = plt.subplots(2, 2, figsize=(12, 8))
    fig_png.suptitle("Model Comparison Report", fontsize=16, fontweight="bold")

    ax = axes_png[0][0]
    x = range(n)
    ax.bar([i - 0.15 for i in x], [d["mAP@50"] for d in comparison_data], 0.28,
               color=colors[0], label="mAP@50")
    ax.bar([i + 0.15 for i in x], [d["mAP@50-95"] for d in comparison_data], 0.28,
               color=colors[1], label="mAP@50-95")
    ax.set_xticks(x)
    ax.set_xticklabels(names_list, fontsize=8)
    ax.set_ylim(0, 1)
    ax.set_title("Detection Accuracy", fontsize=11)
    ax.legend(fontsize=8)

    ax = axes_png[0][1]
    w = 0.25
    ax.bar([i - w for i in x], [d["Precision"] for d in comparison_data], w, color=colors[2], label="Precision")
    ax.bar(x, [d["Recall"] for d in comparison_data], w, color=colors[3], label="Recall")
    ax.bar([i + w for i in x], [d["F1"] for d in comparison_data], w, color=colors[4], label="F1")
    ax.set_xticks(x)
    ax.set_xticklabels(names_list, fontsize=8)
    ax.set_ylim(0, 1)
    ax.set_title("Precision / Recall / F1", fontsize=11)
    ax.legend(fontsize=8)

    ax = axes_png[1][0]
    params_vals_png = [d["Params (M)"] for d in comparison_data]
    ax.bar(names_list, params_vals_png, color=[colors[i % len(colors)] for i in range(n)])
    ax.set_title("Parameters (M)", fontsize=11)
    ax.tick_params(axis="x", labelsize=8)
    for i, v in enumerate(params_vals_png):
            ax.text(i, v + max(params_vals_png) * 0.02, f"{v:.1f}", ha="center", fontsize=9, fontweight="bold")

    ax = axes_png[1][1]
    flops_vals_png = [d["GFLOPs"] for d in comparison_data]
    ax.bar(names_list, flops_vals_png, color=[colors[i % len(colors)] for i in range(n)])
    ax.set_title("GFLOPs", fontsize=11)
    ax.tick_params(axis="x", labelsize=8)
    for i, v in enumerate(flops_vals_png):
            ax.text(i, v + max(flops_vals_png) * 0.02, f"{v:.1f}", ha="center", fontsize=9, fontweight="bold")

    fig_png.tight_layout()

    # PNG 下载
    buf_png = BytesIO()
    fig_png.savefig(buf_png, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    buf_png.seek(0)
    plt.close(fig_png)

    col_png, col_pdf = st.columns(2)
    with col_png:
            fname_png = f"compare_{ts}.png"
            st.download_button(
                label="下载报告 PNG",
                data=buf_png,
                file_name=fname_png,
                mime="image/png",
                use_container_width=True,
            )

    # ── PDF 导出 ──
    buf_pdf = BytesIO()
    with PdfPages(buf_pdf) as pdf:
            # Page 1: Title + table
            fig_p1, ax_p1 = plt.subplots(figsize=(10, 8))
            ax_p1.axis("off")
            ax_p1.text(0.5, 0.95, "Model Comparison Report", transform=ax_p1.transAxes,
                      fontsize=20, fontweight="bold", ha="center", va="top")
            ax_p1.text(0.5, 0.88, f"Date: {report_time}",
                      transform=ax_p1.transAxes, fontsize=10, ha="center", va="top",
                      fontfamily="monospace", color="#555555")

            col_labels = ["Model", "mAP@50", "mAP@50-95", "Precision", "Recall", "F1", "Params(M)", "GFLOPs"]
            cell_text = []
            for d in comparison_data:
                cell_text.append([
                    d["Model"][:30],
                    f"{d['mAP@50']:.4f}",
                    f"{d['mAP@50-95']:.4f}",
                    f"{d['Precision']:.4f}",
                    f"{d['Recall']:.4f}",
                    f"{d['F1']:.4f}",
                    f"{d['Params (M)']:.1f}",
                    f"{d['GFLOPs']:.1f}",
                ])
            tbl = ax_p1.table(cellText=cell_text, colLabels=col_labels, cellLoc="center",
                             loc="center", colWidths=[0.18, 0.1, 0.12, 0.1, 0.1, 0.1, 0.1, 0.1])
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(8)
            tbl.scale(1.2, 1.4)
            for key, cell in tbl.get_celld().items():
                if key[0] == 0:
                    cell.set_facecolor("#333333")
                    cell.set_text_props(color="white", fontweight="bold")
                cell.set_edgecolor("#CCCCCC")
            pdf.savefig(fig_p1)
            plt.close(fig_p1)

            # Page 2: mAP chart
            fig_p2, ax_p2 = plt.subplots(figsize=(10, 6))
            x = range(n)
            ax_p2.bar([i - 0.15 for i in x], [d["mAP@50"] for d in comparison_data], 0.28,
                     color=colors[0], label="mAP@50")
            ax_p2.bar([i + 0.15 for i in x], [d["mAP@50-95"] for d in comparison_data], 0.28,
                     color=colors[1], label="mAP@50-95")
            ax_p2.set_xticks(x)
            ax_p2.set_xticklabels(names_list, fontsize=9)
            ax_p2.set_ylim(0, 1)
            ax_p2.set_title("Detection Accuracy", fontsize=14, fontweight="bold")
            ax_p2.set_ylabel("Score")
            ax_p2.legend(fontsize=10)
            ax_p2.grid(axis="y", alpha=0.3)
            pdf.savefig(fig_p2)
            plt.close(fig_p2)

            # Page 3: Precision/Recall/F1
            fig_p3, ax_p3 = plt.subplots(figsize=(10, 6))
            w = 0.25
            ax_p3.bar([i - w for i in x], [d["Precision"] for d in comparison_data], w, color=colors[2], label="Precision")
            ax_p3.bar(x, [d["Recall"] for d in comparison_data], w, color=colors[3], label="Recall")
            ax_p3.bar([i + w for i in x], [d["F1"] for d in comparison_data], w, color=colors[4], label="F1")
            ax_p3.set_xticks(x)
            ax_p3.set_xticklabels(names_list, fontsize=9)
            ax_p3.set_ylim(0, 1)
            ax_p3.set_title("Precision / Recall / F1", fontsize=14, fontweight="bold")
            ax_p3.set_ylabel("Score")
            ax_p3.legend(fontsize=10)
            ax_p3.grid(axis="y", alpha=0.3)
            pdf.savefig(fig_p3)
            plt.close(fig_p3)

            # Page 4: Parameters + GFLOPs
            fig_p4, (ax_p4a, ax_p4b) = plt.subplots(1, 2, figsize=(10, 5))
            ax_p4a.bar(names_list, params_vals_png, color=[colors[i % len(colors)] for i in range(n)])
            ax_p4a.set_title("Parameters (M)", fontsize=13, fontweight="bold")
            ax_p4a.set_ylabel("M")
            ax_p4a.tick_params(axis="x", labelsize=8)
            for i, v in enumerate(params_vals_png):
                ax_p4a.text(i, v + max(params_vals_png) * 0.02, f"{v:.1f}", ha="center", fontsize=9, fontweight="bold")

            ax_p4b.bar(names_list, flops_vals_png, color=[colors[i % len(colors)] for i in range(n)])
            ax_p4b.set_title("GFLOPs", fontsize=13, fontweight="bold")
            ax_p4b.tick_params(axis="x", labelsize=8)
            for i, v in enumerate(flops_vals_png):
                ax_p4b.text(i, v + max(flops_vals_png) * 0.02, f"{v:.1f}", ha="center", fontsize=9, fontweight="bold")
            fig_p4.tight_layout()
            pdf.savefig(fig_p4)
            plt.close(fig_p4)

            # Metadata
            d = pdf.infodict()
            d["Title"] = "Model Comparison Report"
            d["Author"] = "Fire & Smoke Detection Platform"
            d["CreationDate"] = datetime.strptime(ts, "%Y%m%d_%H%M%S")

    buf_pdf.seek(0)

    with col_pdf:
            fname_pdf = f"compare_{ts}.pdf"
            st.download_button(
                label="下载报告 PDF",
                data=buf_pdf,
                file_name=fname_pdf,
                mime="application/pdf",
                use_container_width=True,
            )

    # 自动保存到 eval_results
    eval_dir = (SCRIPT_DIR / "eval_results")
    eval_dir.mkdir(exist_ok=True)
    (eval_dir / fname_png).write_bytes(buf_png.getvalue())
    buf_pdf.seek(0)
    (eval_dir / fname_pdf).write_bytes(buf_pdf.getvalue())
    st.caption(f"Auto-saved to {eval_dir.resolve()}")
