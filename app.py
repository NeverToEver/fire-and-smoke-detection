"""
火焰烟雾检测平台 — Streamlit GUI
启动方式: streamlit run app.py
"""

import os
import time as _time
import shutil as _shutil

import streamlit as st

st.set_page_config(
    page_title="火焰烟雾检测平台",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

from gui import SCRIPT_DIR, UPLOAD_DIR
from gui.theme import CSS_STYLE, apply_theme_marker
from gui.resources import scan_datasets, scan_models, scan_model_configs, load_model_cached
from gui.pages.dataset import page_dataset
from gui.pages.training import page_training
from gui.pages.inference import page_inference
from gui.pages.evaluation import page_evaluation
from gui.pages.hardware import page_hardware
from gui.pages.optimization import page_optimization

# 注册自定义模块到 ultralytics
import custom_models.custom_yolov11_mobilenetv3  # noqa: F401

# 注入 CSS
st.markdown(CSS_STYLE, unsafe_allow_html=True)


def _cleanup_old_files():
    """清理过期文件，防止无限累积"""
    # eval_results: 保留最近 10 个
    d = SCRIPT_DIR / "eval_results"
    if d.exists():
        files = sorted(d.glob("*"), key=os.path.getmtime, reverse=True)
        for f in files[10:]:
            try:
                f.unlink()
            except OSError:
                pass

    # training.log: 超过 7 天删除
    log_path = SCRIPT_DIR / "training.log"
    if log_path.exists():
        if _time.time() - os.path.getmtime(log_path) > 7 * 86400:
            try:
                log_path.unlink()
            except OSError:
                pass

    # 上传目录: 清理 7 天前的文件
    for subdir in ["models", "datasets", "model_configs", "datasets_extracted"]:
        d = UPLOAD_DIR / subdir
        if d.exists():
            cutoff = _time.time() - 7 * 86400
            for f in d.iterdir():
                if os.path.getmtime(f) < cutoff:
                    try:
                        if f.is_dir():
                            _shutil.rmtree(f)
                        else:
                            f.unlink()
                    except OSError:
                        pass

    # runs/detect: 保留最近 5 次训练结果
    runs_dir = SCRIPT_DIR / "runs" / "detect"
    if runs_dir.exists():
        subdirs = sorted(runs_dir.iterdir(), key=os.path.getmtime, reverse=True)
        for sd in subdirs[5:]:
            if sd.is_dir():
                try:
                    _shutil.rmtree(sd)
                except OSError:
                    pass

    # runs/optimize: 清理 7 天前的导出文件
    opt_dir = SCRIPT_DIR / "runs" / "optimize"
    if opt_dir.exists():
        cutoff = _time.time() - 7 * 86400
        for f in opt_dir.iterdir():
            if os.path.getmtime(f) < cutoff:
                try:
                    if f.is_dir():
                        _shutil.rmtree(f)
                    else:
                        f.unlink()
                except OSError:
                    pass

    # 清理滞留的临时 args JSON 文件
    for tf in SCRIPT_DIR.glob("tmp*.json"):
        try:
            tf.unlink()
        except OSError:
            pass


def main():
    if not st.session_state.get("_cleanup_done"):
        _cleanup_old_files()
        st.session_state["_cleanup_done"] = True

    datasets_count = len(scan_datasets())
    models_count = len(scan_models())
    configs_count = len(scan_model_configs())

    st.sidebar.markdown(
        f"""
        <div class="sidebar-brand">
            <div class="sidebar-brand__eyebrow">Fire & Smoke Vision Lab</div>
            <div class="sidebar-brand__title">火焰烟雾检测平台</div>
            <div class="sidebar-brand__meta">YOLOv11 · MobileNetV3 · Slim-Neck</div>
        </div>
        <div class="sidebar-stat-grid">
            <div class="sidebar-stat"><b>{datasets_count}</b><span>数据集</span></div>
            <div class="sidebar-stat"><b>{models_count}</b><span>权重</span></div>
            <div class="sidebar-stat"><b>{configs_count}</b><span>配置</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    theme_mode = st.sidebar.radio(
        "主题",
        ["跟随系统", "白天模式", "夜间模式"],
        horizontal=True,
        key="theme_mode",
    )
    apply_theme_marker(theme_mode)

    page = st.sidebar.radio(
        "导航",
        ["数据集浏览", "训练管理", "模型推理", "模型评估", "硬件预估", "模型优化"],
        label_visibility="collapsed",
    )

    st.sidebar.divider()
    st.sidebar.markdown(
        f'<div class="path-chip">工作目录: {str(SCRIPT_DIR)}</div>',
        unsafe_allow_html=True,
    )

    col_btn1, col_btn2 = st.sidebar.columns(2)
    with col_btn1:
        if st.button("刷新资源列表", use_container_width=True):
            scan_datasets.clear()
            scan_models.clear()
            scan_model_configs.clear()
            st.rerun()
    with col_btn2:
        if st.button("清理模型缓存", use_container_width=True,
                     help="从内存中卸载已缓存的 YOLO 模型，释放显存"):
            load_model_cached.clear()
            st.rerun()

    if page == "数据集浏览":
        page_dataset()
    elif page == "训练管理":
        page_training()
    elif page == "模型推理":
        page_inference()
    elif page == "模型评估":
        page_evaluation()
    elif page == "硬件预估":
        page_hardware()
    elif page == "模型优化":
        page_optimization()


if __name__ == "__main__":
    main()
