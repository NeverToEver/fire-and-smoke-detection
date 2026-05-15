"""页面: Evaluation"""

import os
from io import BytesIO
from pathlib import Path
from datetime import datetime
import streamlit as st
import matplotlib.pyplot as plt
from gui import SCRIPT_DIR
from gui.components import ui_page_header, ui_section, ui_path_chip
from gui.selectors import model_selector, dataset_selector
from gui.resources import scan_models, load_model_cached
from gui.utils import get_model_info, run_eval

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
            c3.metric("Precision", f"{eval_result['precision']:.4f}" if eval_result['precision'] else "—")
            c4.metric("Recall", f"{eval_result['recall']:.4f}" if eval_result['recall'] else "—")
            c5.metric("F1", f"{2 * eval_result['precision'] * eval_result['recall'] / (eval_result['precision'] + eval_result['recall'] + 1e-6):.4f}")

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

            f1_val = 2 * eval_result['precision'] * eval_result['recall'] / (eval_result['precision'] + eval_result['recall'] + 1e-6)
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.axis("off")

            title = f"Evaluation Report — {Path(model_path).name}"
            ax.text(0.5, 0.92, title, transform=ax.transAxes, fontsize=18, fontweight="bold",
                    ha="center", va="top", fontfamily="monospace")

            info_lines = [
                f"Model: {Path(model_path).name}",
                f"Dataset: {Path(yaml_path).name}",
                f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
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

            fname = f"eval_{Path(model_path).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            st.download_button(label="下载评估报告 (PNG)", data=buf, file_name=fname, mime="image/png")

            eval_dir = (SCRIPT_DIR / "eval_results")
            eval_dir.mkdir(exist_ok=True)
            save_path = eval_dir / fname
            save_path.write_bytes(buf.getvalue())
            st.caption(f"已自动保存至 {save_path.resolve()}")

    # ══════════════ Tab 2: 多模型对比 ══════════════
    with tab2:
        ui_section("对比输入", "选择 2 到 5 个模型，使用同一个数据集评估。", "COMPARE")
        models = scan_models()
        if not models:
            st.info("未发现已训练模型，请先训练模型")
        else:
            model_options = [m["label"] for m in models]
            selected_labels = st.multiselect(
                "选择要对比的模型（2-5 个）",
                model_options,
                max_selections=5,
                key="eval_compare",
            )
            yaml_path = dataset_selector("eval_cmp", "评估数据集")

            compare_ready = len(selected_labels) >= 2 and yaml_path and Path(yaml_path).exists()
            if len(selected_labels) < 2:
                st.info("请至少选择 2 个模型进行对比")
            elif not yaml_path or not Path(yaml_path).exists():
                st.info("请选择评估数据集")

            if compare_ready and st.button("开始对比", type="primary", key="eval_compare_btn"):
                selected_paths = [m["path"] for m in models if m["label"] in selected_labels]
                selected_names = [Path(p).parent.name for p in selected_paths]
                comparison_data = []

                progress = st.progress(0)
                for i, (name, path) in enumerate(zip(selected_names, selected_paths)):
                    with st.spinner(f"评估 {name}..."):
                        try:
                            metrics = run_eval(path, yaml_path)
                            info = get_model_info(path)
                            comparison_data.append({
                                "模型": name,
                                "mAP@50": metrics["map50"],
                                "mAP@50-95": metrics["map50_95"],
                                "Precision": metrics["precision"],
                                "Recall": metrics["recall"],
                                "F1": 2 * metrics["precision"] * metrics["recall"]
                                       / (metrics["precision"] + metrics["recall"] + 1e-6),
                                "参数量 (M)": info["params_m"],
                                "GFLOPs": info["flops_g"],
                            })
                        except Exception as e:
                            st.warning(f"{name} 评估失败: {e}")
                    progress.progress((i + 1) / len(selected_paths))
                progress.empty()

                if len(comparison_data) >= 2:
                    st.session_state["cmp_data"] = comparison_data
                    st.session_state["cmp_names"] = selected_names[:len(comparison_data)]
                    st.session_state["cmp_yaml"] = yaml_path
                    st.session_state["cmp_has_result"] = True
                else:
                    st.error("至少需要 2 个模型评估成功才能对比")
                    st.session_state["cmp_has_result"] = False

            # 持久化展示对比结果
            if st.session_state.get("cmp_has_result"):
                comparison_data = st.session_state["cmp_data"]
                selected_names = st.session_state["cmp_names"]
                import pandas as pd
                df = pd.DataFrame(comparison_data)

                # 对比表格
                ui_section("指标对比表", "同一评估集上的横向指标。", "TABLE")
                st.dataframe(
                    df.style.format({
                        "mAP@50": "{:.4f}", "mAP@50-95": "{:.4f}",
                        "Precision": "{:.4f}", "Recall": "{:.4f}", "F1": "{:.4f}",
                        "参数量 (M)": "{:.1f}", "GFLOPs": "{:.1f}",
                    }),
                    use_container_width=True, hide_index=True,
                )

                # 分组柱形图：mAP
                ui_section("检测精度对比", "mAP@50 与 mAP@50-95 对比。", "CHART")
                chart_data_map = pd.DataFrame({
                    "模型": selected_names[:len(comparison_data)],
                    "mAP@50": [d["mAP@50"] for d in comparison_data],
                    "mAP@50-95": [d["mAP@50-95"] for d in comparison_data],
                }).set_index("模型")
                st.bar_chart(chart_data_map, use_container_width=True)

                # 分组柱形图：P/R/F1
                ui_section("Precision / Recall / F1", "精确率、召回率和综合 F1 对比。", "CHART")
                chart_data_pr = pd.DataFrame({
                    "模型": selected_names[:len(comparison_data)],
                    "Precision": [d["Precision"] for d in comparison_data],
                    "Recall": [d["Recall"] for d in comparison_data],
                    "F1": [d["F1"] for d in comparison_data],
                }).set_index("模型")
                st.bar_chart(chart_data_pr, use_container_width=True)

                # 水平条形图：参数量 / FLOPs
                ui_section("模型复杂度对比", "参数量和计算量越低越适合边缘部署。", "COST")
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, max(3, len(comparison_data) * 0.6)))
                names = selected_names[:len(comparison_data)]
                params_vals = [d["参数量 (M)"] for d in comparison_data]
                flops_vals = [d["GFLOPs"] for d in comparison_data]

                colors_params = ["#4CAF50" if v == min(params_vals) else "#2196F3" for v in params_vals]
                ax1.barh(names, params_vals, color=colors_params)
                ax1.set_xlabel("参数量 (M)")
                ax1.set_title("参数量对比 (越小越好)")

                colors_flops = ["#4CAF50" if v == min(flops_vals) else "#2196F3" for v in flops_vals]
                ax2.barh(names, flops_vals, color=colors_flops)
                ax2.set_xlabel("GFLOPs")
                ax2.set_title("计算量对比 (越小越好)")

                fig.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

                # 导出对比结果
                ui_section("导出对比", "生成包含全部模型对比指标的汇总图片。", "EXPORT")

                n = len(comparison_data)
                fig, axes = plt.subplots(2, 2, figsize=(12, 8))
                fig.suptitle("Model Comparison Report", fontsize=16, fontweight="bold", fontfamily="monospace")
                names_list = [d["模型"] for d in comparison_data]
                colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336"]

                # mAP
                ax = axes[0][0]
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

                # Precision / Recall / F1
                ax = axes[0][1]
                x = range(n)
                w = 0.25
                ax.bar([i - w for i in x], [d["Precision"] for d in comparison_data], w, color=colors[2], label="Precision")
                ax.bar(x, [d["Recall"] for d in comparison_data], w, color=colors[3], label="Recall")
                ax.bar([i + w for i in x], [d["F1"] for d in comparison_data], w, color=colors[4], label="F1")
                ax.set_xticks(x)
                ax.set_xticklabels(names_list, fontsize=8)
                ax.set_ylim(0, 1)
                ax.set_title("Precision / Recall / F1", fontsize=11)
                ax.legend(fontsize=8)

                # 参数量
                ax = axes[1][0]
                params_vals = [d["参数量 (M)"] for d in comparison_data]
                ax.bar(names_list, params_vals, color=[colors[i % len(colors)] for i in range(n)])
                ax.set_title("Parameters (M)", fontsize=11)
                ax.tick_params(axis="x", labelsize=8)
                for i, v in enumerate(params_vals):
                    ax.text(i, v + max(params_vals) * 0.02, f"{v:.1f}", ha="center", fontsize=9, fontweight="bold")

                # GFLOPs
                ax = axes[1][1]
                flops_vals = [d["GFLOPs"] for d in comparison_data]
                ax.bar(names_list, flops_vals, color=[colors[i % len(colors)] for i in range(n)])
                ax.set_title("GFLOPs", fontsize=11)
                ax.tick_params(axis="x", labelsize=8)
                for i, v in enumerate(flops_vals):
                    ax.text(i, v + max(flops_vals) * 0.02, f"{v:.1f}", ha="center", fontsize=9, fontweight="bold")

                fig.tight_layout()

                buf = BytesIO()
                fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
                buf.seek(0)
                plt.close(fig)

                fname = f"compare_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                st.download_button(label="下载对比报告 (PNG)", data=buf, file_name=fname, mime="image/png")

                eval_dir = (SCRIPT_DIR / "eval_results")
                eval_dir.mkdir(exist_ok=True)
                (eval_dir / fname).write_bytes(buf.getvalue())
                st.caption(f"已自动保存至 {eval_dir.resolve() / fname}")


