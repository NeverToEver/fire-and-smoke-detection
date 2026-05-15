"""页面: Inference"""

import os
import io as _io
import json as _json
import zipfile as _zipfile
from pathlib import Path
from datetime import datetime
import streamlit as st
import cv2
import numpy as np
from ui.components import ui_page_header, ui_section, ui_path_chip
from ui.widgets import model_selector
from ui.scanner import load_model_cached, scan_datasets, parse_data_yaml
from ui.image_utils import get_image_files

def page_inference():
    ui_page_header(
        "模型推理",
        "加载已训练权重，对上传图片或测试集目录执行火焰/烟雾检测。",
        "Inference Console",
        ["单图/多图上传", "目录批处理", "置信度阈值"],
    )

    ui_section("模型输入", "选择 best.pt 或 last.pt 权重，也可以手动输入权重路径。", "MODEL")
    model_path = model_selector("inf", "模型权重")

    if not model_path or not Path(model_path).exists():
        if model_path:
            st.warning(f"模型文件不存在: {model_path}")
        else:
            st.info("请选择已训练的 .pt 模型")
        return

    try:
        mtime = os.path.getmtime(model_path)
        model = load_model_cached(model_path, mtime)
    except Exception as e:
        st.error(f"模型加载失败: {e}")
        return

    ui_path_chip(model_path, "当前权重")

    # 推理模式
    ui_section("推理设置", "选择推理来源并设置最低置信度。", "CONTROL")
    mode = st.radio("推理模式", ["单张/多张上传", "测试集目录"], horizontal=True, key="inf_mode")
    conf_threshold = st.slider("置信度阈值", 0.0, 1.0, 0.25, 0.05, key="inf_conf")

    # 输入变化检测：模型路径 + 模式 + 阈值改变时清除旧结果
    inf_sig = f"{model_path}:{mode}:{conf_threshold}"
    if st.session_state.get("inf_sig") != inf_sig:
        st.session_state.pop("inf_has_results", None)
        st.session_state.pop("inf_results", None)
        st.session_state.pop("inf_batch_has", None)
        st.session_state.pop("inf_batch", None)
        st.session_state["inf_sig"] = inf_sig

    if mode == "单张/多张上传":
        uploaded_files = st.file_uploader(
            "上传图片", type=["jpg", "jpeg", "png", "bmp"],
            accept_multiple_files=True, key="inf_upload",
        )
        if not uploaded_files:
            st.info("请上传图片进行推理")
            return

        if st.button("运行推理", type="primary", use_container_width=True):
            results_list = []
            for uploaded in uploaded_files:
                file_bytes = np.frombuffer(uploaded.read(), np.uint8)
                img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                inf_result = model.predict(img, conf=conf_threshold, verbose=False)
                result_img = inf_result[0].plot()
                result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)

                boxes = inf_result[0].boxes
                if boxes is not None and len(boxes) > 0:
                    cls_ids = boxes.cls.cpu().numpy().astype(int)
                    fire_count = int((cls_ids == 0).sum())
                    smoke_count = int((cls_ids == 1).sum())
                    confs = boxes.conf.cpu().numpy()
                    caption = f"火焰 {fire_count} 处 | 烟雾 {smoke_count} 处 | 均置信度 {confs.mean():.2f}"
                else:
                    caption = "未检测到目标"
                results_list.append({"img": result_img, "caption": caption})
                uploaded.seek(0)
            st.session_state["inf_results"] = results_list
            st.session_state["inf_has_results"] = True

        if st.session_state.get("inf_has_results"):
            ui_section("检测结果", "上传图片的检测框和目标数量。", "RESULT")
            results_list = st.session_state["inf_results"]
            cols = st.columns(min(len(results_list), 3))
            for i, r in enumerate(results_list):
                cols[i % 3].image(r["img"], caption=r["caption"], use_container_width=True)

            # 导出推理结果
            ui_section("导出结果", "打包所有检测结果图片。", "EXPORT")
            buf = _io.BytesIO()
            with _zipfile.ZipFile(buf, "w", _zipfile.ZIP_DEFLATED) as zf:
                for i, r in enumerate(results_list):
                    img_bytes = cv2.imencode(".jpg", cv2.cvtColor(r["img"], cv2.COLOR_RGB2BGR))[1].tobytes()
                    zf.writestr(f"result_{i+1:03d}.jpg", img_bytes)
            buf.seek(0)
            st.download_button(
                label="下载检测结果 (ZIP)", data=buf,
                file_name=f"inference_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
            )

    else:
        # 测试集目录模式 — 分块处理以支持中途取消
        ui_section("测试集目录", "从数据集配置自动取 test/val，或手动指定图片目录。", "DATA")

        datasets = scan_datasets()
        dataset_options = [d["label"] for d in datasets]
        selected_ds = st.selectbox(
            "从数据集选择 (自动获取 val/test 路径)",
            ["-- 选择数据集 --"] + dataset_options,
            key="inf_ds",
        )

        test_dir = ""
        if selected_ds != "-- 选择数据集 --":
            for d in datasets:
                if d["label"] == selected_ds:
                    data_info = parse_data_yaml(d["path"])
                    if data_info:
                        test_dir = data_info.get("test") or data_info.get("val", "")
                        ui_path_chip(d["path"], "数据集配置")
                    break

        manual_dir = st.text_input("或手动输入测试图片目录", placeholder="/path/to/test/images", key="inf_dir_manual")
        if manual_dir:
            test_dir = manual_dir

        if not test_dir or not Path(test_dir).exists():
            st.info("请选择数据集或输入测试图片目录路径")
            return

        test_images = get_image_files(test_dir, limit=1000)
        if not test_images:
            st.warning(f"目录下没有找到图片: {test_dir}")
            return

        st.caption(f"共发现 {len(test_images)} 张测试图片")

        max_display = st.slider("最多显示结果图", 4, 24, 8, 4, key="inf_max_display")

        # 分块推理状态
        CHUNK_SIZE = 20
        batch_running = st.session_state.get("_inf_batch_running", False)
        batch_cancelled = st.session_state.get("_inf_batch_cancel", False)

        if batch_running:
            progress_bar = st.progress(0)
            status_text = st.empty()
            stop_col, _ = st.columns([1, 3])
            with stop_col:
                if st.button("停止批量推理", type="primary", key="inf_stop_btn"):
                    st.session_state["_inf_batch_cancel"] = True
                    st.rerun()

            chunk_start = st.session_state.get("_inf_batch_idx", 0)
            if batch_cancelled:
                progress_bar.empty()
                status_text.empty()
                st.session_state["_inf_batch_running"] = False
                st.session_state["_inf_batch_cancel"] = False
                st.warning("批量推理已取消")
                st.rerun()

            total_fire = st.session_state.get("_inf_batch_fire", 0)
            total_smoke = st.session_state.get("_inf_batch_smoke", 0)
            all_confs = st.session_state.get("_inf_batch_confs", [])
            results_display = st.session_state.get("_inf_batch_display", [])

            chunk_end = min(chunk_start + CHUNK_SIZE, len(test_images))
            for idx in range(chunk_start, chunk_end):
                if st.session_state.get("_inf_batch_cancel"):
                    break
                img_path = test_images[idx]
                img = cv2.imread(img_path)
                if img is None:
                    continue
                results = model.predict(img, conf=conf_threshold, verbose=False)
                boxes = results[0].boxes
                cls_ids = None
                confs = None
                if boxes is not None and len(boxes) > 0:
                    cls_ids = boxes.cls.cpu().numpy().astype(int)
                    confs = boxes.conf.cpu().numpy()
                    total_fire += int((cls_ids == 0).sum())
                    total_smoke += int((cls_ids == 1).sum())
                    all_confs.extend(confs.tolist())
                if len(results_display) < max_display:
                    result_img = results[0].plot()
                    result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
                    has_boxes = boxes is not None and len(boxes) > 0
                    results_display.append({
                        "name": Path(img_path).name,
                        "img": result_img,
                        "fire": int((cls_ids == 0).sum()) if has_boxes else 0,
                        "smoke": int((cls_ids == 1).sum()) if has_boxes else 0,
                        "has_boxes": has_boxes,
                    })
                progress_bar.progress((idx + 1) / len(test_images))
                status_text.text(f"处理中: {idx + 1}/{len(test_images)} — {Path(img_path).name}")

            if st.session_state.get("_inf_batch_cancel") or chunk_end >= len(test_images):
                progress_bar.empty()
                status_text.empty()
                st.session_state["_inf_batch_running"] = False
                st.session_state["_inf_batch_cancel"] = False
                st.session_state["inf_batch"] = {
                    "total_images": len(test_images),
                    "total_fire": total_fire,
                    "total_smoke": total_smoke,
                    "avg_conf": np.mean(all_confs) if all_confs else 0,
                    "display": results_display,
                }
                st.session_state["inf_batch_has"] = True
                st.rerun()
            else:
                st.session_state["_inf_batch_idx"] = chunk_end
                st.session_state["_inf_batch_fire"] = total_fire
                st.session_state["_inf_batch_smoke"] = total_smoke
                st.session_state["_inf_batch_confs"] = all_confs
                st.session_state["_inf_batch_display"] = results_display
                import time as _time
                _time.sleep(0.5)
                st.rerun()

        elif st.button("批量推理", type="primary", use_container_width=True):
            st.session_state["_inf_batch_running"] = True
            st.session_state["_inf_batch_cancel"] = False
            st.session_state["_inf_batch_idx"] = 0
            st.session_state["_inf_batch_fire"] = 0
            st.session_state["_inf_batch_smoke"] = 0
            st.session_state["_inf_batch_confs"] = []
            st.session_state["_inf_batch_display"] = []
            st.rerun()

        if st.session_state.get("inf_batch_has"):
            batch = st.session_state["inf_batch"]
            ui_section("推理汇总", "批量目录的目标计数和平均置信度。", "SUMMARY")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("测试图片数", batch["total_images"])
            c2.metric("检测火焰总数", batch["total_fire"])
            c3.metric("检测烟雾总数", batch["total_smoke"])
            c4.metric("平均置信度", f"{batch['avg_conf']:.3f}" if batch["avg_conf"] else "—")

            results_display = batch["display"]
            if results_display:
                ui_section("部分检测结果", f"展示前 {len(results_display)} 张结果图。", "GALLERY")
                cols = st.columns(4)
                for i, r in enumerate(results_display):
                    col = cols[i % 4]
                    cap = f"{r['name']} | 火焰 {r['fire']} | 烟雾 {r['smoke']}" if r["has_boxes"] else f"{r['name']} | 无检测"
                    col.image(r["img"], caption=cap, use_container_width=True)

            # 导出汇总 JSON
            ui_section("导出结果", "下载推理汇总数据和结果图片。", "EXPORT")
            summary = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model": model_path,
                "test_dir": test_dir,
                "total_images": batch["total_images"],
                "total_fire": batch["total_fire"],
                "total_smoke": batch["total_smoke"],
                "avg_confidence": round(float(batch["avg_conf"]), 4),
            }
            json_buf = _io.BytesIO()
            json_buf.write(_json.dumps(summary, indent=2, ensure_ascii=False).encode("utf-8"))
            json_buf.seek(0)
            st.download_button(
                label="下载推理汇总 (JSON)", data=json_buf,
                file_name=f"inference_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )


