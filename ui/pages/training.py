"""页面: Training"""

import os
import sys
import time
import shutil
import hashlib
import tempfile
import importlib.util
import subprocess
from pathlib import Path
from datetime import datetime
import streamlit as st
from ui import SCRIPT_DIR
from ui.components import ui_page_header, ui_section, ui_path_chip
from ui.widgets import dataset_selector, model_config_selector
from ui.scanner import scan_models, get_compute_devices
from engine.training_monitor import parse_training_log


@st.fragment(run_every=3)
def _training_dashboard():
    """每 3 秒局部刷新训练进度区，进程结束后自行展示完成状态。"""
    import signal as _signal

    log_path = st.session_state.get("_train_log_path", "")
    train_pid = st.session_state.get("_train_pid", 0)
    train_project = st.session_state.get("_train_project_name", "")

    # ── 训练已结束（由本 fragment 或外部设置）—— 展示完成/错误 ──
    if not st.session_state.get("_train_running", True):
        _render_completion(log_path, train_pid, train_project)
        return

    process_alive = False
    if train_pid:
        try:
            os.kill(train_pid, 0)
            process_alive = True
        except (OSError, ProcessLookupError):
            process_alive = False
            if "_train_exit_code" not in st.session_state:
                try:
                    _, status = os.waitpid(train_pid, os.WNOHANG)
                    st.session_state["_train_exit_code"] = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -status
                except OSError:
                    st.session_state["_train_exit_code"] = -1

    if not process_alive:
        st.session_state["_train_running"] = False
        if "_train_exit_code" not in st.session_state:
            st.session_state["_train_exit_code"] = 0
        if "_train_was_stopped" not in st.session_state:
            st.session_state.setdefault("_train_was_stopped", False)
        st.rerun()  # fragment scope: immediately re-render to show completion
        return

    st.session_state["training_status"] = "训练中"

    start_ts = st.session_state.get("_train_start_time", time.time())
    hint_epochs = st.session_state.get("_train_total_epochs", 0)
    prog = parse_training_log(log_path, start_time=start_ts, total_epochs_hint=hint_epochs)

    # ── 整体 Epoch 进度条 ──
    total_ep = prog["total_epochs"] or hint_epochs or 1
    overall_pct = (prog["current_epoch"] - 1 + prog["epoch_pct"] / 100) / total_ep
    overall_pct = max(0.0, min(1.0, overall_pct))
    status_label = "正在扫描数据集..." if prog["status"] == "scanning" else "训练中"
    st.progress(
        overall_pct,
        text=f"{status_label} — Epoch {prog['current_epoch']}/{total_ep} ({overall_pct * 100:.1f}%)",
    )

    # ── 顶部指标卡 ──
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("预计剩余时间", prog["eta_str"] or "计算中...")
    c2.metric("GPU 显存", prog["gpu_mem"] or "-")
    c3.metric("训练速度", prog["speed"] or "-")
    c4.metric("当前 Epoch 进度", f"{prog['epoch_pct']:.0f}%")

    # ── 训练损失 ──
    if prog["box_loss"] is not None:
        st.caption("训练损失")
        l1, l2, l3 = st.columns(3)
        l1.metric("Box Loss", f"{prog['box_loss']:.4f}")
        l2.metric("Cls Loss", f"{prog['cls_loss']:.4f}")
        l3.metric("DFL Loss", f"{prog['dfl_loss']:.4f}")

    # ── 验证指标 ──
    if prog["map50"] is not None:
        st.caption("最新验证指标")
        v1, v2, v3, v4 = st.columns(4)
        v1.metric("mAP50", f"{prog['map50']:.3f}")
        v2.metric("mAP50-95", f"{prog['map50_95']:.3f}")
        v3.metric("Precision", f"{prog['precision']:.3f}")
        v4.metric("Recall", f"{prog['recall']:.3f}")

    # ── 停止按钮 + 原始日志 ──
    col_stop, col_info = st.columns([1, 3])
    with col_stop:
        if st.button("停止训练", type="primary", key="tr_stop_btn"):
            try:
                os.killpg(train_pid, _signal.SIGTERM)
            except OSError:
                pass
            time.sleep(2)
            try:
                os.killpg(train_pid, _signal.SIGKILL)
            except OSError:
                pass
            st.session_state["_train_running"] = False
            st.session_state["_train_was_stopped"] = True
            st.rerun()
    with col_info:
        st.caption(f"PID: {train_pid} | 输出目录: {train_project}")

    with st.expander("原始日志", expanded=False):
        st.code(prog.get("raw_tail", "") or "(等待训练输出...)")


def _render_completion(log_path: str, train_pid: int, train_project: str):
    """在 fragment 内渲染训练完成/错误/停止结果。"""
    result_dir = SCRIPT_DIR / "runs" / "detect" / train_project
    st.session_state.pop("_train_pid", None)  # 防 PID 重用误判
    st.session_state.pop("_train_start_time", None)
    args_file_path = st.session_state.pop("_train_args_file", "")
    if args_file_path and Path(args_file_path).exists():
        try:
            Path(args_file_path).unlink()
        except OSError:
            pass

    exit_code = st.session_state.pop("_train_exit_code", None)
    was_stopped = st.session_state.pop("_train_was_stopped", False)

    if was_stopped:
        st.session_state["training_status"] = "已手动停止"
        st.warning("训练已被用户手动停止")
    elif exit_code is not None and exit_code != 0:
        st.session_state["training_status"] = f"训练异常退出 (code={exit_code})"
        st.error(
            f"训练进程异常退出，退出码: {exit_code}。"
            "请检查日志排查是否为 OOM / 数据集路径错误 / 模型配置不兼容。"
        )
        if log_path and Path(log_path).exists():
            with open(log_path) as f:
                tail = "".join(f.readlines()[-20:])
            st.text_area("日志末尾", tail, height=200)
    else:
        st.session_state["training_status"] = "训练完成"
        st.session_state["last_train_dir"] = str(result_dir)
        st.session_state["_training_just_finished"] = True
        st.success(f"训练完成！结果保存在 {result_dir}")
        scan_models.clear()
        results_img = result_dir / "results.png"
        if results_img.exists():
            ui_section("训练曲线", "本次训练生成的结果图。", "RESULT")
            st.image(str(results_img), caption="训练曲线", use_container_width=True)
            ts_img = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(results_img, "rb") as f:
                st.download_button(
                    "下载训练曲线 (PNG)", f.read(),
                    f"results_{ts_img}.png", "image/png",
                    key="dl_train_results", use_container_width=True,
                )

    st.caption("点击任意位置刷新页面返回配置模式。")


def page_training():
    ui_page_header(
        "训练管理",
        "配置数据集、模型结构和关键超参数，并直接启动 YOLO 训练任务。",
        "Training Console",
        ["YOLOv11", "MobileNetV3", "Slim-Neck", "P2 小目标"],
    )

    # ── 训练运行中：交由 fragment 全权处理（含完成/停止展示）──
    if st.session_state.get("_train_running"):
        _training_dashboard()
        return

    # ── 正常配置表单 ──
    # 数据集选择
    ui_section("训练输入", "先确定数据集和模型结构，下面的训练命令会沿用这些路径。", "SETUP")
    yaml_path = dataset_selector("tr", "训练数据集")
    # 防御性缓存：选择器返回有效路径时持久化到 session state
    if yaml_path and Path(yaml_path).exists():
        st.session_state["_tr_yaml_path"] = yaml_path
    elif not yaml_path:
        yaml_path = st.session_state.get("_tr_yaml_path", "")

    model_yaml = model_config_selector("tr", "模型配置")
    if model_yaml and Path(model_yaml).exists():
        st.session_state["_tr_model_yaml"] = model_yaml
    elif not model_yaml:
        model_yaml = st.session_state.get("_tr_model_yaml", "")

    if not model_yaml:
        st.info("请选择模型配置文件")
        return

    ui_path_chip(model_yaml, "模型配置")

    # ── 模型架构文件（高级）──
    MODEL_PY = SCRIPT_DIR / "models" / "yolo_mobilenet.py"
    with st.expander("模型架构文件（高级）", expanded=False):
        st.caption(f"当前架构: `{MODEL_PY}`")
        arch_upload = st.file_uploader(
            "拖拽上传替换模型架构 .py 文件",
            type=["py"],
            key="tr_arch_upload",
            help="上传自定义 backbone/neck/head 定义文件。原文件将备份为 .bak。",
        )
        if arch_upload is not None:
            fp_key = "tr_arch_processed"
            new_fp = hashlib.sha256(arch_upload.getbuffer()).hexdigest()
            if st.session_state.get(fp_key) != new_fp:
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir=str(SCRIPT_DIR), prefix="_arch_test_") as tf:
                        tf.write(arch_upload.getvalue().decode("utf-8"))
                        tmp_path = tf.name
                    spec = importlib.util.spec_from_file_location("_arch_test", tmp_path)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    required = ["MobileNetV3_Backbone", "YOLOv11_MobileNetV3_Head", "DetectWrapper"]
                    missing = [n for n in required if not hasattr(mod, n)]
                    if missing:
                        st.error(f"缺少必要类: {', '.join(missing)}。文件必须导出: {', '.join(required)}。")
                    else:
                        bak = Path(str(MODEL_PY) + ".bak")
                        if not bak.exists():
                            shutil.copy2(MODEL_PY, bak)
                        shutil.copy2(tmp_path, MODEL_PY)
                        st.session_state[fp_key] = new_fp
                        st.success("模型架构已替换，原文件备份为 .bak。请手动刷新页面以重新加载模块。")
                        if st.button("刷新页面", key="tr_reload_arch"):
                            st.rerun()
                except SyntaxError as e:
                    st.error(f"Python 语法错误: {e}")
                except Exception as e:
                    st.error(f"导入验证失败: {e}")
                finally:
                    if tmp_path:
                        try:
                            Path(tmp_path).unlink()
                        except OSError:
                            pass
            else:
                st.info("此文件已处理过。")

    ui_section("超参数", "调整滑块快速配置训练策略，也可手动微调每个参数。", "PARAMS")

    # ── 训练策略预设 ──
    _PRESETS = {
        "速度优先": {"auto_epochs": False, "epochs": 50,  "imgsz": 320, "batch": 16, "lr0": 0.01,  "close_mosaic": 10, "patience": 20},
        "偏速度":   {"auto_epochs": True,  "epochs": 200, "imgsz": 480, "batch": 12, "lr0": 0.01,  "close_mosaic": 15, "patience": 35},
        "均衡":     {"auto_epochs": True,  "epochs": 300, "imgsz": 640, "batch": 8,  "lr0": 0.01,  "close_mosaic": 20, "patience": 50},
        "偏质量":   {"auto_epochs": True,  "epochs": 300, "imgsz": 800, "batch": 6,  "lr0": 0.007, "close_mosaic": 25, "patience": 65},
        "质量优先": {"auto_epochs": True,  "epochs": 300, "imgsz": 960, "batch": 4,  "lr0": 0.005, "close_mosaic": 30, "patience": 80},
    }

    def _apply_preset():
        p = _PRESETS.get(st.session_state.get("_tr_preset_label", "均衡"), _PRESETS["均衡"])
        for k, v in p.items():
            st.session_state[f"_tr_{k}"] = v

    preset_label = st.select_slider(
        "训练策略",
        options=list(_PRESETS.keys()),
        value="均衡",
        key="_tr_preset_label",
        on_change=_apply_preset,
    )

    # 首次加载时初始化 session_state 默认值
    for k, v in _PRESETS["均衡"].items():
        st.session_state.setdefault(f"_tr_{k}", v)

    auto_epochs = st.checkbox(
        "自动确定最佳 Epoch（根据 Patience 早停）",
        value=st.session_state.get("_tr_auto_epochs", True),
        key="_tr_auto_epochs",
        help="开启后自动设置较高 epoch 上限，靠 Patience 早停自动收敛",
    )

    c1, c2, c3, c4 = st.columns(4)
    if auto_epochs:
        epochs = st.session_state.get("_tr_epochs", 300)
        c1.metric("Epochs (自动)", f"{epochs}（上限）")
    else:
        epochs = c1.number_input("Epochs (手动)", min_value=1, max_value=500, key="_tr_epochs")
    batch = c2.number_input("Batch Size", min_value=1, max_value=64, key="_tr_batch")
    imgsz = c3.number_input("Image Size", min_value=320, max_value=1280, step=32, key="_tr_imgsz")
    lr0 = c4.number_input("Learning Rate", min_value=0.0001, max_value=0.1, format="%.4f", key="_tr_lr0")

    c5, c6, c7 = st.columns(3)
    close_mosaic = c5.number_input("Close Mosaic", min_value=0, max_value=50, step=5, key="_tr_close_mosaic", help="在第 N 个 epoch 关闭 mosaic")
    patience = c6.number_input("Patience (早停)", min_value=10, max_value=200, step=10, key="_tr_patience", help="连续 N 个 epoch 无提升则自动停止")
    project_name = c7.text_input("输出目录名", value="fire_mobilenet")

    ui_section("训练设备", "检查当前环境是否有 GPU（CUDA / MPS），并手动选择本次训练使用的设备。", "DEVICE")
    device_info = get_compute_devices()
    device_options = ["CPU"]
    device_labels = {"CPU": "cpu"}
    if device_info["mps_available"]:
        option = "MPS (Apple GPU)"
        device_options.append(option)
        device_labels[option] = "mps"
    elif device_info["cuda_available"]:
        for i, gpu_name in enumerate(device_info["gpus"]):
            option = f"GPU {i}: {gpu_name}"
            device_options.append(option)
            device_labels[option] = str(i)
    else:
        for gpu_name in device_info["gpus"]:
            option = f"GPU: {gpu_name}"
            device_options.append(option)
            device_labels[option] = "cpu"

    default_device_idx = 1 if len(device_options) > 1 else 0
    selected_device = st.radio(
        "训练设备",
        device_options,
        index=default_device_idx,
        horizontal=True,
        key="tr_device_choice",
    )
    device = device_labels[selected_device]

    # 设备状态展示
    gpu_type = "MPS" if device_info["mps_available"] else "CUDA" if device_info["cuda_available"] else "无"
    gpu_label = "MPS (Metal)" if device_info["mps_available"] else f"{device_info['cuda_count']} 个"

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Torch", "可用" if device_info["torch_available"] else "不可用")
    d2.metric("加速后端", gpu_type)
    d3.metric("GPU", gpu_label)
    d4.metric("本次训练", selected_device)
    if device_info["error"]:
        st.warning(f"设备检测失败: {device_info['error']}")
    if selected_device == "CPU":
        st.info("当前将使用 CPU 训练，速度通常明显慢于 GPU。")

    ui_section("执行", "启动后训练在后台运行，可随时停止。", "RUN")
    training_state = st.session_state.get("training_status", "未启动")
    status_cols = st.columns(4)
    status_cols[0].metric("训练状态", training_state)
    status_cols[1].metric("设备参数", device)
    status_cols[2].metric("输出目录", project_name)
    status_cols[3].metric("日志窗口", "最近 2500 字符")

    if st.button("开始训练", type="primary", use_container_width=True):
        if not yaml_path or not Path(yaml_path).exists():
            st.error("请先选择有效的训练数据集")
            st.session_state["training_status"] = "配置错误"
            return
        if not model_yaml or not Path(model_yaml).exists():
            st.error(f"模型配置文件不存在: {model_yaml}")
            st.session_state["training_status"] = "配置错误"
            return

        import json as _json
        train_args = {
            "model_yaml": str(model_yaml),
            "data_yaml": str(yaml_path),
            "epochs": epochs,
            "imgsz": imgsz,
            "batch": batch,
            "device": str(device),
            "project": str(SCRIPT_DIR / "runs" / "detect"),
            "name": project_name,
            "lr0": lr0,
            "close_mosaic": close_mosaic,
            "patience": patience,
            "script_dir": str(SCRIPT_DIR),
        }
        args_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", prefix="_train_tmp_", delete=False, dir=str(SCRIPT_DIR))
        args_file.write(_json.dumps(train_args))
        args_file.close()

        cmd = [
            sys.executable, "-c",
            "import json, sys, pathlib; "
            "args = json.load(open(sys.argv[1])); "
            "sys.path.insert(0, args['script_dir']); "
            "import models.yolo_mobilenet\n"
            "try:\n    import models.yolo_mobilenet_slimneck\n"
            "except ImportError:\n    pass\n"
            "from ultralytics import YOLO; "
            "m = YOLO(args['model_yaml']); "
            "m.train(data=args['data_yaml'], epochs=args['epochs'], imgsz=args['imgsz'], "
            "batch=args['batch'], device=args['device'], project=args['project'], "
            "name=args['name'], optimizer='auto', lr0=args['lr0'], "
            "close_mosaic=args['close_mosaic'], patience=args['patience']); "
            "pathlib.Path(sys.argv[1]).unlink(missing_ok=True)",
            args_file.name,
        ]

        log_path = str(SCRIPT_DIR / "training.log")
        log_file = open(log_path, "w")
        process = subprocess.Popen(
            cmd, stdout=log_file, stderr=subprocess.STDOUT,
            text=True, cwd=str(SCRIPT_DIR),
            start_new_session=True,
        )
        log_file.close()

        st.session_state.pop("_train_exit_code", None)   # 清除上次训练的退出码
        st.session_state.pop("_train_was_stopped", None)
        st.session_state.pop("last_train_dir", None)     # 清除上次训练结果
        st.session_state["_train_running"] = True
        st.session_state["_train_pid"] = process.pid
        st.session_state["_train_log_path"] = log_path
        st.session_state["_train_project_name"] = project_name
        st.session_state["_train_args_file"] = args_file.name
        st.session_state["_train_was_stopped"] = False
        st.session_state["_train_start_time"] = time.time()
        st.session_state["_train_total_epochs"] = epochs
        st.session_state["training_status"] = f"训练中 ({selected_device})"
        st.rerun()

    # 显示最近训练结果（非本次训练）
    last_dir = st.session_state.get("last_train_dir")
    just_finished = st.session_state.pop("_training_just_finished", False)
    if last_dir and not just_finished:
        result_dir = Path(last_dir)
        if result_dir.exists():
            results_img = result_dir / "results.png"
            if results_img.exists():
                with st.expander("最近训练结果", expanded=False):
                    st.image(str(results_img), caption="训练曲线", use_container_width=True)
                    ts_recent = datetime.now().strftime("%Y%m%d_%H%M%S")
                    with open(results_img, "rb") as f:
                        st.download_button("下载训练曲线 (PNG)", f.read(),
                                           f"results_{ts_recent}.png", "image/png",
                                           key="dl_recent_results", use_container_width=True)


