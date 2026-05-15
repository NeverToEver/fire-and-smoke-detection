"""页面: Dataset"""

from pathlib import Path
import streamlit as st
import cv2
from gui.components import ui_page_header, ui_section, ui_path_chip
from gui.selectors import dataset_selector
from gui.resources import parse_data_yaml
from gui.utils import find_label_path, draw_boxes_cv2, get_image_files

def page_dataset():
    ui_page_header(
        "数据集浏览",
        "检查 data.yaml、样本数量和标注框质量，用于训练前的数据巡检。",
        "Dataset Console",
        ["自动扫描 data.yaml", "标注框预览", "分页浏览"],
    )

    ui_section("数据源", "选择已发现的数据集，或手动指定 data.yaml 路径。", "INPUT")
    yaml_path = dataset_selector("ds", "数据集")

    if not yaml_path or not Path(yaml_path).exists():
        if yaml_path:
            st.warning(f"文件不存在: {yaml_path}")
        else:
            st.info("请选择或输入数据集 data.yaml 路径")
        return

    data_info = parse_data_yaml(yaml_path)
    if data_info is None:
        return

    train_images = get_image_files(data_info["train"])
    val_images = get_image_files(data_info["val"])
    test_images = get_image_files(data_info.get("test", ""))

    ui_path_chip(yaml_path, "数据集配置")

    # 统计
    ui_section("数据概览", "快速确认训练、验证、测试分布和类别定义。", "SUMMARY")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("训练集", f"{len(train_images)} 张")
    c2.metric("验证集", f"{len(val_images)} 张")
    c3.metric("测试集", f"{len(test_images)} 张" if test_images else "—")
    names_dict = data_info["names"]
    if isinstance(names_dict, dict):
        c4.metric("类别", ", ".join(str(names_dict.get(i, i)) for i in range(data_info["nc"])))
    else:
        c4.metric("类别数", data_info["nc"])

    # 选择浏览来源
    sources = []
    if train_images:
        sources.append("训练集")
    if val_images:
        sources.append("验证集")
    if test_images:
        sources.append("测试集")
    if not sources:
        st.warning("未找到任何图片")
        return

    ui_section("样本预览", "抽检图片和 YOLO 标注框是否对齐。", "PREVIEW")
    source = st.radio("浏览来源", sources, horizontal=True, key="ds_browse_source")
    pool_map = {"训练集": train_images, "验证集": val_images, "测试集": test_images}
    pool = pool_map.get(source, train_images)

    show_boxes = st.checkbox("显示标注框", value=True)
    per_page = 12
    total_pages = max(1, (len(pool) + per_page - 1) // per_page)

    # 分页控制 — key 包含数据集路径和来源，避免切换时页码越界
    page_key = f"ds_page_{yaml_path}_{source}"
    col_page, col_info = st.columns([3, 1])
    with col_page:
        cur_page = st.session_state.get(page_key, 1)
        if cur_page > total_pages:
            cur_page = 1
        page = st.select_slider(
            "翻页", options=list(range(1, total_pages + 1)),
            value=min(cur_page, total_pages),
            key=page_key,
        )
    with col_info:
        st.metric("当前页", f"{page}/{total_pages}")
    st.caption(f"共 {len(pool)} 张样本")

    start = (page - 1) * per_page
    samples = pool[start:start + per_page]

    cols = st.columns(4)
    names_map = {}
    if isinstance(data_info["names"], dict):
        names_map = {int(k): str(v) for k, v in data_info["names"].items()}
    else:
        names_map = {0: "fire", 1: "smoke"}

    for i, img_path in enumerate(samples):
        col = cols[i % 4]
        try:
            img = cv2.imread(img_path)
            if img is None:
                col.warning(f"无法读取: {Path(img_path).name}")
                continue
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if show_boxes:
                label_path = find_label_path(img_path)
                if label_path:
                    img = draw_boxes_cv2(img.copy(), label_path, names_map)
            col.image(img, caption=Path(img_path).name, use_container_width=True)
        except Exception:
            col.warning(f"加载失败: {Path(img_path).name}")


