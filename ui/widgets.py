"""数据集/模型/配置选择器（含拖拽上传 + 自动扫描 + 手动输入）"""

import os
import hashlib
import zipfile
import shutil
from pathlib import Path

import streamlit as st
import yaml

from ui import UPLOAD_DIR
from ui.components import ui_path_chip
from ui.scanner import (
    scan_datasets, scan_models, scan_model_configs,
    parse_data_yaml, save_uploaded_file, load_model_cached,
)


def _check_and_set_fingerprint(key: str, data: bytes) -> bool:
    """检查数据指纹是否已处理过，未处理则更新并返回 True"""
    fp = hashlib.sha256(data).hexdigest()
    if st.session_state.get(key) == fp:
        return False
    st.session_state[key] = fp
    return True


def _extract_dataset_zip(uploaded_zip) -> str | None:
    """解压数据集 zip，找到 data.yaml 并修复相对路径，返回 yaml 路径"""
    extract_dir = UPLOAD_DIR / "datasets_extracted"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True)
    # 防 zip slip 路径穿越
    safe_root = extract_dir.resolve()
    with zipfile.ZipFile(uploaded_zip) as zf:
        for member in zf.namelist():
            member_path = (extract_dir / member).resolve()
            if not str(member_path).startswith(str(safe_root) + os.sep):
                st.error(f"压缩包包含非法路径: {member}")
                shutil.rmtree(extract_dir)
                return None
        zf.extractall(extract_dir)
    yaml_candidates = sorted(extract_dir.rglob("data*.yaml"))
    if not yaml_candidates:
        st.error("压缩包中未找到 data.yaml，请确保 zip 内包含完整的数据集目录结构。")
        return None
    yaml_path = yaml_candidates[0]
    yaml_dir = yaml_path.parent
    with open(yaml_path, encoding="utf-8") as f:
        ydata = yaml.safe_load(f) or {}
    fixed = False
    for key in ["train", "val", "test"]:
        p = ydata.get(key, "")
        if not p or Path(p).is_absolute():
            continue
        found = None
        # 策略 1: 直接拼到 yaml_dir 下
        candidate = (yaml_dir / p).resolve()
        if candidate.exists():
            found = candidate
        # 策略 2: 去掉开头可能多余的 ../（Roboflow 常见问题）
        if not found:
            stripped = str(p)
            while stripped.startswith("../"):
                stripped = stripped[3:]
            candidate = (yaml_dir / stripped).resolve()
            if candidate.exists():
                found = candidate
        # 策略 3: 按路径末尾的 train/images 模式在 yaml_dir 下搜索
        if not found:
            parts = Path(p).parts
            for n in [2, 1]:
                if len(parts) >= n:
                    sub = Path(*parts[-n:])
                    candidate = (yaml_dir / sub).resolve()
                    if candidate.exists():
                        found = candidate
                        break
        if found:
            ydata[key] = str(found.resolve())
            fixed = True
    if fixed:
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(ydata, f)
    st.success(f"数据集已解压至 {extract_dir}")
    ui_path_chip(str(yaml_path), "已导入数据集")
    return str(yaml_path.resolve())


def dataset_selector(key_prefix: str, label: str = "数据集"):
    """数据集下拉选择器，拖拽上传（zip 或 yaml） + 自动扫描 + 手动输入"""
    datasets = scan_datasets()

    options = ["-- 手动输入路径 --"] + [d["label"] for d in datasets]
    if "dataset_custom" not in st.session_state:
        st.session_state["dataset_custom"] = False

    tab1, tab2 = st.tabs(["拖拽上传 zip (推荐)", "拖拽上传 yaml"])

    with tab1:
        zip_upload = st.file_uploader(
            f"拖拽数据集 zip 压缩包",
            type=["zip"],
            key=f"{key_prefix}_zip_upload",
            help="将完整数据集文件夹（含 data.yaml + train/valid/test 子目录）打包为 zip，拖入即可自动解压导入。",
        )
        if zip_upload is not None:
            if _check_and_set_fingerprint(f"{key_prefix}_zip_processed", zip_upload.getbuffer()):
                result = _extract_dataset_zip(zip_upload)
                if result:
                    st.session_state[f"{key_prefix}_last_ds"] = result
                    scan_datasets.clear()
                    return result
            else:
                persisted = st.session_state.get(f"{key_prefix}_last_ds", "")
                if persisted and Path(persisted).exists():
                    return persisted

    with tab2:
        uploaded = st.file_uploader(
            f"拖拽上传 {label} YAML",
            type=["yaml", "yml"],
            key=f"{key_prefix}_ds_upload",
            help="仅上传 data.yaml。若内部使用相对路径，图片目录需手动放置在 WSL 中。",
        )
        if uploaded is not None:
            if _check_and_set_fingerprint(f"{key_prefix}_yaml_processed", uploaded.getbuffer()):
                uploaded_path = save_uploaded_file(uploaded, "datasets")
                ui_path_chip(uploaded_path, "已上传数据集配置")
                parsed = parse_data_yaml(uploaded_path)
                if parsed:
                    missing = []
                    for split_name in ["train", "val", "test"]:
                        sp = parsed.get(split_name, "")
                        if sp and not Path(sp).exists():
                            missing.append(split_name)
                    if missing:
                        st.warning(
                            f"数据集目录缺失: {', '.join(missing)}。"
                            "建议将完整数据集打包为 zip 通过左侧 Tab 上传，"
                            "或将图片目录手动放入 WSL 后使用下方「手动输入路径」。",
                        )
                st.session_state[f"{key_prefix}_last_ds"] = uploaded_path
                return uploaded_path
            else:
                persisted = st.session_state.get(f"{key_prefix}_last_ds", "")
                if persisted and Path(persisted).exists():
                    return persisted

    col1, col2 = st.columns([2, 1])
    with col1:
        selected = st.selectbox(
            f"{label} (自动发现)",
            options,
            key=f"{key_prefix}_ds_select",
        )
    with col2:
        manual = st.text_input(
            "或手动输入路径",
            placeholder="data.yaml 路径",
            key=f"{key_prefix}_ds_manual",
        )

    if manual:
        st.session_state[f"{key_prefix}_last_ds"] = manual
        return manual
    if selected and selected != "-- 手动输入路径 --":
        for d in datasets:
            if d["label"] == selected:
                st.session_state[f"{key_prefix}_last_ds"] = d["path"]
                return d["path"]
    persisted = st.session_state.get(f"{key_prefix}_last_ds", "")
    if persisted and Path(persisted).exists():
        return persisted
    return ""


def model_selector(key_prefix: str, label: str = "模型权重", allow_upload: bool = True):
    """模型下拉选择器，拖拽上传 + 自动扫描 + 手动输入"""
    models = scan_models()
    options = ["-- 手动输入路径 --"] + [m["label"] for m in models]

    if allow_upload:
        uploaded = st.file_uploader(
            f"拖拽上传 {label}",
            type=["pt"],
            key=f"{key_prefix}_mdl_upload",
            help="支持拖入 best.pt / last.pt。上传后会保存到项目的 .streamlit_uploads/models 目录。",
        )
        if uploaded is not None:
            if _check_and_set_fingerprint(f"{key_prefix}_mdl_processed", uploaded.getbuffer()):
                uploaded_path = save_uploaded_file(uploaded, "models")
                ui_path_chip(uploaded_path, "已上传模型权重")
                load_model_cached.clear()
                st.session_state[f"{key_prefix}_last_mdl"] = uploaded_path
                return uploaded_path
            else:
                persisted = st.session_state.get(f"{key_prefix}_last_mdl", "")
                if persisted and Path(persisted).exists():
                    return persisted

    col1, col2 = st.columns([2, 1])
    with col1:
        selected = st.selectbox(f"{label} (已训练模型)", options, key=f"{key_prefix}_mdl_select")
    with col2:
        manual = st.text_input("或手动输入路径", placeholder="best.pt 路径", key=f"{key_prefix}_mdl_manual")

    if manual:
        st.session_state[f"{key_prefix}_last_mdl"] = manual
        return manual
    if selected and selected != "-- 手动输入路径 --":
        for m in models:
            if m["label"] == selected:
                st.session_state[f"{key_prefix}_last_mdl"] = m["path"]
                return m["path"]
    persisted = st.session_state.get(f"{key_prefix}_last_mdl", "")
    if persisted and Path(persisted).exists():
        return persisted
    return ""


def model_config_selector(key_prefix: str, label: str = "模型配置"):
    """模型 YAML 配置选择器，拖拽上传 + 自动扫描 + 手动输入"""
    uploaded = st.file_uploader(
        f"拖拽上传 {label} YAML",
        type=["yaml", "yml"],
        key=f"{key_prefix}_cfg_upload",
        help="支持拖入模型结构 YAML，例如 configs/yolo11-mobilenetv3-slimneck-p2.yaml。",
    )
    if uploaded is not None:
        if _check_and_set_fingerprint(f"{key_prefix}_cfg_processed", uploaded.getbuffer()):
            uploaded_path = save_uploaded_file(uploaded, "model_configs")
            ui_path_chip(uploaded_path, "已上传模型配置")
            st.session_state[f"{key_prefix}_last_cfg"] = uploaded_path
            return uploaded_path
        else:
            persisted = st.session_state.get(f"{key_prefix}_last_cfg", "")
            if persisted and Path(persisted).exists():
                return persisted
            for c in scan_model_configs():
                if c["path"].endswith(Path(uploaded.name).name):
                    return c["path"]
            return ""

    configs = scan_model_configs()
    cfg_options = [c["label"] for c in configs]
    default_idx = 0
    for i, c in enumerate(configs):
        if "slimneck" in c["label"].lower():
            default_idx = i
            break

    col1, col2 = st.columns([2, 1])
    with col1:
        if cfg_options:
            cfg_selected = st.selectbox(label, cfg_options, index=default_idx, key=f"{key_prefix}_cfg")
            model_yaml = next((c["path"] for c in configs if c["label"] == cfg_selected), "")
        else:
            model_yaml = ""
    with col2:
        manual_cfg = st.text_input("或手动输入", placeholder="模型 yaml 路径", key=f"{key_prefix}_cfg_manual")
    if manual_cfg:
        model_yaml = manual_cfg
        st.session_state[f"{key_prefix}_last_cfg"] = manual_cfg
    if not model_yaml:
        persisted = st.session_state.get(f"{key_prefix}_last_cfg", "")
        if persisted and Path(persisted).exists():
            model_yaml = persisted
    return model_yaml
