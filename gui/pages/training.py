"""页面: Training"""

import os
import sys
import subprocess
from pathlib import Path
import streamlit as st
from gui import SCRIPT_DIR
from gui.components import ui_page_header, ui_section, ui_path_chip
from gui.selectors import dataset_selector, model_config_selector
from gui.resources import scan_models, get_compute_devices

def page_training():
    import signal as _signal

    ui_page_header(
        "训练管理",
        "配置数据集、模型结构和关键超参数，并直接启动 YOLO 训练任务。",
        "Training Console",
        ["YOLOv11", "MobileNetV3", "Slim-Neck", "P2 小目标"],
    )

    # ── 训练运行中：展示实时日志 + 停止按钮 ──
    train_running = st.session_state.get("_train_running", False)
    if train_running:
        log_path = st.session_state.get("_train_log_path", "")
        train_pid = st.session_state.get("_train_pid", 0)
        train_project = st.session_state.get("_train_project_name", "")

        # 检查进程是否还活着
        process_alive = False
        if train_pid:
            try:
                os.kill(train_pid, 0)
                process_alive = True
            except (OSError, ProcessLookupError):
                process_alive = False

        if process_alive:
            st.session_state["training_status"] = "训练中"
            st.warning("训练进行中，可通过下方按钮停止。页面每 3 秒自动刷新。")

            # 显示最新日志
            if log_path and Path(log_path).exists():
                with open(log_path) as f:
                    log_content = f.read()
                st.code(log_content[-2500:] or "(等待训练输出...)")

            col_stop, col_info = st.columns([1, 3])
            with col_stop:
                if st.button("停止训练", type="primary", key="tr_stop_btn"):
                    try:
                        os.killpg(train_pid, _signal.SIGTERM)
                    except OSError:
                        pass
                    import time as _t2
                    _t2.sleep(2)
                    try:
                        os.killpg(train_pid, _signal.SIGKILL)
                    except OSError:
                        pass
                    st.session_state["_train_running"] = False
                    st.session_state["training_status"] = "已手动停止"
                    st.session_state["_train_was_stopped"] = True
                    st.rerun()
            with col_info:
                st.caption(f"PID: {train_pid} | 输出目录: {train_project}")

            import time as _time
            _time.sleep(3)
            st.rerun()
            return
        else:
            # 进程已结束
            st.session_state["_train_running"] = False
            result_dir = SCRIPT_DIR / "runs" / "detect" / train_project
            args_file_path = st.session_state.pop("_train_args_file", "")
            if args_file_path and Path(args_file_path).exists():
                try:
                    Path(args_file_path).unlink()
                except OSError:
                    pass

            if st.session_state.pop("_train_was_stopped", False):
                st.session_state["training_status"] = "已手动停止"
                st.warning("训练已被用户手动停止")
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
            st.rerun()
            return

    # ── 正常配置表单 ──
    # 数据集选择
    ui_section("训练输入", "先确定数据集和模型结构，下面的训练命令会沿用这些路径。", "SETUP")
    yaml_path = dataset_selector("tr", "训练数据集")

    model_yaml = model_config_selector("tr", "模型配置")

    if not model_yaml:
        st.info("请选择模型配置文件")
        return

    ui_path_chip(model_yaml, "模型配置")

    ui_section("超参数", "保持默认值即可跑通基线，需要微调时再改 batch、imgsz 和学习率。", "PARAMS")

    auto_epochs = st.checkbox("自动确定最佳 Epoch（根据 Patience 早停）", value=True,
                              help="开启后自动设置较高 epoch 上限，靠 Patience 早停自动收敛")

    c1, c2, c3, c4 = st.columns(4)
    if auto_epochs:
        epochs = 300
        c1.metric("Epochs (自动)", f"{epochs}（上限）")
    else:
        epochs = c1.number_input("Epochs (手动)", 1, 500, 150, 10)
    batch = c2.number_input("Batch Size", 1, 64, 8, 2)
    imgsz = c3.number_input("Image Size", 320, 1280, 640, 32)
    lr0 = c4.number_input("Learning Rate", 0.0001, 0.1, 0.01, format="%.4f")

    c5, c6, c7 = st.columns(3)
    close_mosaic = c5.number_input("Close Mosaic", 0, 50, 20, 5, help="在第 N 个 epoch 关闭 mosaic")
    patience = c6.number_input("Patience (早停)", 10, 200, 50, 10, help="连续 N 个 epoch 无提升则自动停止")
    project_name = c7.text_input("输出目录名", value="fire_mobilenet_slimneck")

    ui_section("训练设备", "检查当前环境是否有 GPU，并手动选择本次训练使用 CPU 还是 GPU。", "DEVICE")
    device_info = get_compute_devices()
    device_options = ["CPU"]
    device_labels = {"CPU": "cpu"}
    for gpu in device_info["gpus"]:
        option = f"GPU {gpu['id']}: {gpu['name']}"
        device_options.append(option)
        device_labels[option] = str(gpu["id"])

    default_device_idx = 1 if len(device_options) > 1 else 0
    selected_device = st.radio(
        "训练设备",
        device_options,
        index=default_device_idx,
        horizontal=True,
        key="tr_device_choice",
    )
    device = device_labels[selected_device]

    # 验证设备选择
    if selected_device != "CPU":
        gpu_id = int(device)
        if gpu_id >= device_info["cuda_count"]:
            st.error(f"GPU {gpu_id} 不存在（共 {device_info['cuda_count']} 个 GPU），请选择可用设备。")
            if not st.session_state.get("training_status"):
                st.session_state["training_status"] = "配置错误"

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Torch", "可用" if device_info["torch_available"] else "不可用")
    d2.metric("CUDA", "可用" if device_info["cuda_available"] else "不可用")
    d3.metric("GPU 数量", device_info["cuda_count"])
    d4.metric("本次训练", selected_device)
    if device_info["error"]:
        st.warning(f"设备检测失败: {device_info['error']}")
    if selected_device == "CPU":
        st.info("当前将使用 CPU 训练，速度通常明显慢于 GPU。")
    elif not device_info["cuda_available"]:
        st.warning("当前环境未检测到 CUDA，但选择了 GPU。请检查 PyTorch/CUDA 环境。")

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
        import tempfile as _tempfile
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
        args_file = _tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir=str(SCRIPT_DIR))
        args_file.write(_json.dumps(train_args))
        args_file.close()

        cmd = [
            sys.executable, "-c",
            "import json, sys, pathlib; "
            "args = json.load(open(sys.argv[1])); "
            "sys.path.insert(0, args['script_dir']); "
            "import custom_models.custom_yolov11_mobilenetv3; "
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

        st.session_state["_train_running"] = True
        st.session_state["_train_pid"] = process.pid
        st.session_state["_train_log_path"] = log_path
        st.session_state["_train_project_name"] = project_name
        st.session_state["_train_args_file"] = args_file.name
        st.session_state["_train_was_stopped"] = False
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


