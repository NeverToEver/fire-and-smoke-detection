"""共享 UI 组件 — 页面标题、节标题、路径标签"""

from html import escape

import streamlit as st


def ui_page_header(title: str, subtitle: str, eyebrow: str, chips: list[str] | None = None):
    chips = chips or []
    chip_html = "".join(f'<span class="fs-chip">{escape(chip)}</span>' for chip in chips)
    st.markdown(
        f"""
        <div class="fs-hero">
            <div class="fs-hero__kicker">{escape(eyebrow)}</div>
            <div class="fs-hero__title">{escape(title)}</div>
            <p class="fs-hero__desc">{escape(subtitle)}</p>
            <div class="fs-hero__rail">{chip_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def ui_section(title: str, caption: str = "", tag: str = ""):
    parts = [f"<h2>{escape(title)}</h2>"]
    if caption:
        parts.append(f"<p>{escape(caption)}</p>")
    tag_html = f'<span class="section-title__tag">{escape(tag)}</span>' if tag else ""
    inner = f'<div>{"".join(parts)}</div>{tag_html}'
    st.markdown(f'<div class="section-title">{inner}</div>', unsafe_allow_html=True)


def ui_path_chip(path: str, label: str = "当前路径"):
    st.markdown(
        f'<div style="margin: 0 0 16px;">'
        f'<span style="font-size:0.7rem;color:var(--muted);text-transform:uppercase;">{escape(label)}</span> '
        f'<span class="path-chip">{escape(path)}</span></div>',
        unsafe_allow_html=True,
    )
