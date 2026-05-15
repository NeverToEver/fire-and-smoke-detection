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

from ui import SCRIPT_DIR, UPLOAD_DIR
from ui.theme import CSS_STYLE, apply_theme_marker
from ui.scanner import scan_datasets, scan_models, scan_model_configs, load_model_cached
from ui.pages.dataset import page_dataset
from ui.pages.training import page_training
from ui.pages.inference import page_inference
from ui.pages.evaluation import page_evaluation
from ui.pages.hardware import page_hardware
from ui.pages.optimization import page_optimization

from models.registry import register_custom_modules

# 注册项目内受信任的自定义模块到 Ultralytics
register_custom_modules()

# 注入 CSS
st.markdown(CSS_STYLE, unsafe_allow_html=True)


def _safe_mtime(f: os.PathLike) -> float | None:
    """安全获取文件修改时间，失败返回 None"""
    try:
        return os.path.getmtime(f)
    except (OSError, FileNotFoundError):
        return None


def _cleanup_old_files():
    """清理过期临时文件，避免自动删除训练结果和导出产物。"""

    # eval_results: 保留最近 10 个
    d = SCRIPT_DIR / "eval_results"
    if d.exists():
        try:
            files = sorted(d.glob("*"), key=lambda f: _safe_mtime(f) or 0, reverse=True)
            for f in files[10:]:
                try:
                    if f.is_dir():
                        _shutil.rmtree(f)
                    else:
                        f.unlink()
                except OSError:
                    pass
        except Exception:
            pass

    # training.log: 超过 7 天删除
    log_path = SCRIPT_DIR / "training.log"
    if log_path.exists():
        mtime = _safe_mtime(log_path)
        if mtime is not None and _time.time() - mtime > 7 * 86400:
            try:
                log_path.unlink()
            except OSError:
                pass

    # 上传目录: 只自动清理解压缓存，用户上传的模型/YAML 保留
    for subdir in ["datasets_extracted"]:
        d = UPLOAD_DIR / subdir
        if d.exists():
            cutoff = _time.time() - 7 * 86400
            try:
                for f in sorted(d.rglob("*"), key=lambda x: _safe_mtime(x) or 0, reverse=True):
                    mtime = _safe_mtime(f)
                    if mtime is None or mtime >= cutoff:
                        continue
                    try:
                        if f.is_dir():
                            _shutil.rmtree(f)
                        else:
                            f.unlink()
                    except OSError:
                        pass
            except Exception:
                pass

    # 清理滞留的临时训练 args JSON 文件
    for tf in SCRIPT_DIR.glob("_train_tmp_*.json"):
        try:
            tf.unlink()
        except OSError:
            pass


def main():
    # 定期重清理：每 30 分钟或首次访问
    last_cleanup = st.session_state.get("_cleanup_ts", 0)
    if _time.time() - last_cleanup > 1800:
        _cleanup_old_files()
        st.session_state["_cleanup_ts"] = _time.time()

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
