"""
火焰烟雾检测平台 — Streamlit GUI
启动方式: streamlit run app.py
"""

import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from html import escape
from pathlib import Path

import streamlit as st
import yaml

st.set_page_config(
    page_title="火焰烟雾检测平台",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════
# 工业实验控制台风格自定义样式
# ═══════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap');

:root {
    --bg: #090705;
    --bg-grid: rgba(251, 146, 60, 0.08);
    --surface: #15110D;
    --surface-raised: #1D1711;
    --surface-strong: #080604;
    --ink: #FFF7ED;
    --ink-2: #FED7AA;
    --muted: #C9A586;
    --faint: #8B735F;
    --line: rgba(251, 146, 60, 0.20);
    --line-strong: rgba(251, 146, 60, 0.42);
    --brand: #EA580C;
    --brand-soft: rgba(234, 88, 12, 0.16);
    --signal: #2DD4BF;
    --signal-soft: rgba(45, 212, 191, 0.14);
    --success: #4ADE80;
    --warning: #F59E0B;
    --danger: #F87171;
    --blueprint: #60A5FA;
    --radius: 8px;
    --shadow: 0 18px 44px rgba(0, 0, 0, 0.42);
    --shadow-soft: 0 8px 24px rgba(0, 0, 0, 0.26);
    --app-bg: radial-gradient(circle at 18% 0%, rgba(234, 88, 12, 0.28), transparent 34rem),
        radial-gradient(circle at 88% 18%, rgba(249, 115, 22, 0.16), transparent 28rem),
        linear-gradient(180deg, #0D0906 0%, #090705 54%, #130C07 100%);
    --header-border: rgba(251, 146, 60, 0.16);
    --sidebar-bg: radial-gradient(circle at 50% 0%, rgba(234, 88, 12, 0.28), transparent 18rem),
        linear-gradient(180deg, #130C07 0%, #0B0907 48%, #090705 100%);
    --sidebar-border: rgba(251, 146, 60, 0.18);
    --sidebar-text: #F3F4F6;
    --sidebar-title: #FFFFFF;
    --sidebar-muted: #AEB7C6;
    --sidebar-eyebrow: #FDBA74;
    --sidebar-meta: #CBD5E1;
    --sidebar-brand-border: rgba(251, 146, 60, 0.22);
    --sidebar-brand-bg: linear-gradient(135deg, rgba(234, 88, 12, 0.24), rgba(146, 64, 14, 0.12)),
        rgba(255, 247, 237, 0.035);
    --sidebar-brand-shadow: inset 0 1px 0 rgba(255, 247, 237, 0.08);
    --sidebar-card-border: rgba(251, 146, 60, 0.16);
    --sidebar-card-bg: rgba(255, 247, 237, 0.04);
    --sidebar-radio-bg: rgba(255, 247, 237, 0.035);
    --sidebar-radio-hover-bg: rgba(234, 88, 12, 0.14);
    --sidebar-radio-hover-border: rgba(251, 146, 60, 0.45);
    --sidebar-radio-selected-bg: linear-gradient(135deg, rgba(234, 88, 12, 0.26), rgba(15, 118, 110, 0.18));
    --sidebar-radio-selected-border: rgba(251, 146, 60, 0.65);
    --sidebar-path-bg: rgba(255, 255, 255, 0.055);
    --sidebar-path-text: #CBD5E1;
    --hero-border: rgba(251, 146, 60, 0.28);
    --hero-bg: radial-gradient(circle at 14% 18%, rgba(249, 115, 22, 0.35), transparent 20rem),
        linear-gradient(120deg, rgba(234, 88, 12, 0.22), transparent 38%),
        linear-gradient(135deg, #17100B 0%, #0B0907 58%, #231306 100%);
    --hero-desc: #CBD5E1;
    --hero-grid-y: rgba(255, 255, 255, 0.06);
    --hero-grid-x: rgba(255, 255, 255, 0.05);
    --chip-border: rgba(255, 255, 255, 0.14);
    --chip-bg: rgba(255, 255, 255, 0.08);
    --chip-text: #E5E7EB;
    --path-bg: rgba(21, 17, 13, 0.86);
    --button-bg: #1D1711;
    --button-hover-shadow: 0 10px 24px rgba(0, 0, 0, 0.24);
    --dropzone-bg: linear-gradient(135deg, rgba(234, 88, 12, 0.12), rgba(21, 17, 13, 0.92));
    --table-header-bg: #21170F;
    --image-bg: #111827;
    --code-border: rgba(251, 146, 60, 0.24);
    --tab-bg: rgba(21, 17, 13, 0.58);
    --popover-bg: #15110D;
    --option-bg: #15110D;
    --option-hover-bg: rgba(234, 88, 12, 0.18);
    --alert-bg: rgba(21, 17, 13, 0.92);
    --input-bg: #17110D;
    --input-text: #FFF7ED;
    --input-placeholder: #E7C49F;
    --upload-button-bg: #FFF7ED;
    --upload-button-text: #9A3412;
}

@media (prefers-color-scheme: light) {
    :root {
        --bg: #FFF7ED;
        --bg-grid: rgba(234, 88, 12, 0.10);
        --surface: #FFFFFF;
        --surface-raised: #FFFBF6;
        --surface-strong: #FFF7ED;
        --ink: #1C120A;
        --ink-2: #4A2D1C;
        --muted: #7C5F4B;
        --faint: #A78B75;
        --line: rgba(194, 101, 32, 0.24);
        --line-strong: rgba(234, 88, 12, 0.45);
        --brand-soft: rgba(234, 88, 12, 0.10);
        --signal: #0F766E;
        --signal-soft: rgba(15, 118, 110, 0.10);
        --success: #15803D;
        --warning: #B45309;
        --danger: #B91C1C;
        --blueprint: #1D4ED8;
        --shadow: 0 18px 44px rgba(124, 45, 18, 0.13);
        --shadow-soft: 0 8px 24px rgba(124, 45, 18, 0.09);
        --app-bg: radial-gradient(circle at 16% 0%, rgba(251, 146, 60, 0.30), transparent 31rem),
            radial-gradient(circle at 88% 20%, rgba(253, 186, 116, 0.24), transparent 26rem),
            linear-gradient(180deg, #FFF7ED 0%, #FFF3E6 48%, #FFFCF8 100%);
        --header-border: rgba(194, 101, 32, 0.22);
        --sidebar-bg: radial-gradient(circle at 50% 0%, rgba(251, 146, 60, 0.30), transparent 16rem),
            linear-gradient(180deg, #FFF4E8 0%, #FFE9D2 52%, #FFF9F2 100%);
        --sidebar-border: rgba(194, 101, 32, 0.24);
        --sidebar-text: #3A2414;
        --sidebar-title: #1C120A;
        --sidebar-muted: #7C5F4B;
        --sidebar-eyebrow: #C2410C;
        --sidebar-meta: #6B4A33;
        --sidebar-brand-border: rgba(234, 88, 12, 0.28);
        --sidebar-brand-bg: linear-gradient(135deg, rgba(255, 255, 255, 0.72), rgba(255, 237, 213, 0.68)),
            rgba(255, 255, 255, 0.50);
        --sidebar-brand-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
        --sidebar-card-border: rgba(234, 88, 12, 0.20);
        --sidebar-card-bg: rgba(255, 255, 255, 0.58);
        --sidebar-radio-bg: rgba(255, 255, 255, 0.54);
        --sidebar-radio-hover-bg: rgba(234, 88, 12, 0.12);
        --sidebar-radio-hover-border: rgba(234, 88, 12, 0.42);
        --sidebar-radio-selected-bg: linear-gradient(135deg, rgba(234, 88, 12, 0.16), rgba(15, 118, 110, 0.10));
        --sidebar-radio-selected-border: rgba(234, 88, 12, 0.56);
        --sidebar-path-bg: rgba(255, 255, 255, 0.68);
        --sidebar-path-text: #6B4A33;
        --path-bg: rgba(255, 255, 255, 0.78);
        --button-bg: #FFFFFF;
        --button-hover-shadow: 0 10px 24px rgba(124, 45, 18, 0.12);
        --dropzone-bg: linear-gradient(135deg, rgba(255, 247, 237, 0.96), rgba(255, 255, 255, 0.92));
        --table-header-bg: #FFF1E3;
        --code-border: rgba(234, 88, 12, 0.20);
        --tab-bg: rgba(255, 255, 255, 0.66);
        --popover-bg: #FFFFFF;
        --option-bg: #FFFFFF;
        --option-hover-bg: rgba(234, 88, 12, 0.12);
        --alert-bg: rgba(255, 255, 255, 0.92);
        --input-bg: #FFFFFF;
        --input-text: #1C120A;
        --input-placeholder: #7C5F4B;
        --upload-button-bg: #FFFFFF;
        --upload-button-text: #C2410C;
    }
}

:root.theme-light,
:root:has(#fs-theme-light) {
    --bg: #FFF7ED;
    --bg-grid: rgba(234, 88, 12, 0.10);
    --surface: #FFFFFF;
    --surface-raised: #FFFBF6;
    --surface-strong: #FFF7ED;
    --ink: #1C120A;
    --ink-2: #4A2D1C;
    --muted: #7C5F4B;
    --faint: #A78B75;
    --line: rgba(194, 101, 32, 0.24);
    --line-strong: rgba(234, 88, 12, 0.45);
    --brand-soft: rgba(234, 88, 12, 0.10);
    --signal: #0F766E;
    --signal-soft: rgba(15, 118, 110, 0.10);
    --success: #15803D;
    --warning: #B45309;
    --danger: #B91C1C;
    --blueprint: #1D4ED8;
    --shadow: 0 18px 44px rgba(124, 45, 18, 0.13);
    --shadow-soft: 0 8px 24px rgba(124, 45, 18, 0.09);
    --app-bg: radial-gradient(circle at 16% 0%, rgba(251, 146, 60, 0.30), transparent 31rem),
        radial-gradient(circle at 88% 20%, rgba(253, 186, 116, 0.24), transparent 26rem),
        linear-gradient(180deg, #FFF7ED 0%, #FFF3E6 48%, #FFFCF8 100%);
    --header-border: rgba(194, 101, 32, 0.22);
    --sidebar-bg: radial-gradient(circle at 50% 0%, rgba(251, 146, 60, 0.30), transparent 16rem),
        linear-gradient(180deg, #FFF4E8 0%, #FFE9D2 52%, #FFF9F2 100%);
    --sidebar-border: rgba(194, 101, 32, 0.24);
    --sidebar-text: #3A2414;
    --sidebar-title: #1C120A;
    --sidebar-muted: #7C5F4B;
    --sidebar-eyebrow: #C2410C;
    --sidebar-meta: #6B4A33;
    --sidebar-brand-border: rgba(234, 88, 12, 0.28);
    --sidebar-brand-bg: linear-gradient(135deg, rgba(255, 255, 255, 0.72), rgba(255, 237, 213, 0.68)),
        rgba(255, 255, 255, 0.50);
    --sidebar-brand-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
    --sidebar-card-border: rgba(234, 88, 12, 0.20);
    --sidebar-card-bg: rgba(255, 255, 255, 0.58);
    --sidebar-radio-bg: rgba(255, 255, 255, 0.54);
    --sidebar-radio-hover-bg: rgba(234, 88, 12, 0.12);
    --sidebar-radio-hover-border: rgba(234, 88, 12, 0.42);
    --sidebar-radio-selected-bg: linear-gradient(135deg, rgba(234, 88, 12, 0.16), rgba(15, 118, 110, 0.10));
    --sidebar-radio-selected-border: rgba(234, 88, 12, 0.56);
    --sidebar-path-bg: rgba(255, 255, 255, 0.68);
    --sidebar-path-text: #6B4A33;
    --path-bg: rgba(255, 255, 255, 0.78);
    --button-bg: #FFFFFF;
    --button-hover-shadow: 0 10px 24px rgba(124, 45, 18, 0.12);
    --dropzone-bg: linear-gradient(135deg, rgba(255, 247, 237, 0.96), rgba(255, 255, 255, 0.92));
    --table-header-bg: #FFF1E3;
    --code-border: rgba(234, 88, 12, 0.20);
    --tab-bg: rgba(255, 255, 255, 0.66);
    --popover-bg: #FFFFFF;
    --option-bg: #FFFFFF;
    --option-hover-bg: rgba(234, 88, 12, 0.12);
    --alert-bg: rgba(255, 255, 255, 0.92);
    --input-bg: #FFFFFF;
    --input-text: #1C120A;
    --input-placeholder: #7C5F4B;
    --upload-button-bg: #FFFFFF;
    --upload-button-text: #C2410C;
}

:root.theme-dark,
:root:has(#fs-theme-dark) {
    --bg: #090705;
    --bg-grid: rgba(251, 146, 60, 0.08);
    --surface: #15110D;
    --surface-raised: #1D1711;
    --surface-strong: #080604;
    --ink: #FFF7ED;
    --ink-2: #FED7AA;
    --muted: #C9A586;
    --faint: #8B735F;
    --line: rgba(251, 146, 60, 0.20);
    --line-strong: rgba(251, 146, 60, 0.42);
    --brand-soft: rgba(234, 88, 12, 0.16);
    --signal: #2DD4BF;
    --signal-soft: rgba(45, 212, 191, 0.14);
    --success: #4ADE80;
    --warning: #F59E0B;
    --danger: #F87171;
    --blueprint: #60A5FA;
    --shadow: 0 18px 44px rgba(0, 0, 0, 0.42);
    --shadow-soft: 0 8px 24px rgba(0, 0, 0, 0.26);
    --app-bg: radial-gradient(circle at 18% 0%, rgba(234, 88, 12, 0.28), transparent 34rem),
        radial-gradient(circle at 88% 18%, rgba(249, 115, 22, 0.16), transparent 28rem),
        linear-gradient(180deg, #0D0906 0%, #090705 54%, #130C07 100%);
    --header-border: rgba(251, 146, 60, 0.16);
    --sidebar-bg: radial-gradient(circle at 50% 0%, rgba(234, 88, 12, 0.28), transparent 18rem),
        linear-gradient(180deg, #130C07 0%, #0B0907 48%, #090705 100%);
    --sidebar-border: rgba(251, 146, 60, 0.18);
    --sidebar-text: #F3F4F6;
    --sidebar-title: #FFFFFF;
    --sidebar-muted: #AEB7C6;
    --sidebar-eyebrow: #FDBA74;
    --sidebar-meta: #CBD5E1;
    --sidebar-brand-border: rgba(251, 146, 60, 0.22);
    --sidebar-brand-bg: linear-gradient(135deg, rgba(234, 88, 12, 0.24), rgba(146, 64, 14, 0.12)),
        rgba(255, 247, 237, 0.035);
    --sidebar-brand-shadow: inset 0 1px 0 rgba(255, 247, 237, 0.08);
    --sidebar-card-border: rgba(251, 146, 60, 0.16);
    --sidebar-card-bg: rgba(255, 247, 237, 0.04);
    --sidebar-radio-bg: rgba(255, 247, 237, 0.035);
    --sidebar-radio-hover-bg: rgba(234, 88, 12, 0.14);
    --sidebar-radio-hover-border: rgba(251, 146, 60, 0.45);
    --sidebar-radio-selected-bg: linear-gradient(135deg, rgba(234, 88, 12, 0.26), rgba(15, 118, 110, 0.18));
    --sidebar-radio-selected-border: rgba(251, 146, 60, 0.65);
    --sidebar-path-bg: rgba(255, 255, 255, 0.055);
    --sidebar-path-text: #CBD5E1;
    --path-bg: rgba(21, 17, 13, 0.86);
    --button-bg: #1D1711;
    --button-hover-shadow: 0 10px 24px rgba(0, 0, 0, 0.24);
    --dropzone-bg: linear-gradient(135deg, rgba(234, 88, 12, 0.12), rgba(21, 17, 13, 0.92));
    --table-header-bg: #21170F;
    --code-border: rgba(251, 146, 60, 0.24);
    --tab-bg: rgba(21, 17, 13, 0.58);
    --popover-bg: #15110D;
    --option-bg: #15110D;
    --option-hover-bg: rgba(234, 88, 12, 0.18);
    --alert-bg: rgba(21, 17, 13, 0.92);
    --input-bg: #17110D;
    --input-text: #FFF7ED;
    --input-placeholder: #E7C49F;
    --upload-button-bg: #FFF7ED;
    --upload-button-text: #9A3412;
}

* {
    box-sizing: border-box;
}

html, body, [class*="css"] {
    font-family: "Fira Sans", "Noto Sans SC", system-ui, -apple-system, sans-serif;
}

.stApp {
    background: var(--app-bg);
    color: var(--ink);
}

.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background:
        linear-gradient(var(--bg-grid) 1px, transparent 1px),
        linear-gradient(90deg, var(--bg-grid) 1px, transparent 1px);
    background-size: 32px 32px;
    mask-image: linear-gradient(180deg, rgba(0,0,0,0.75), transparent 68%);
    z-index: 0;
}

[data-testid="stAppViewContainer"],
[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
#MainMenu,
footer {
    display: none !important;
}

/* 侧边栏永不收起 */
section[data-testid="stSidebar"] {
    display: flex !important;
    visibility: visible !important;
    width: 21rem !important;
    min-width: 21rem !important;
    transform: none !important;
    transition: none !important;
}
/* 隐藏侧边栏关闭按钮 */
button[data-testid="stSidebarCloseButton"],
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stText"] {
    color: var(--ink-2);
}

[data-testid="stHeader"] {
    border-bottom: 1px solid var(--header-border);
    backdrop-filter: blur(14px);
}

.main .block-container {
    position: relative;
    z-index: 1;
    max-width: 1440px;
    padding-top: 1.25rem;
    padding-bottom: 4rem;
}

/* 侧边栏 */
[data-testid="stSidebar"] {
    background: var(--sidebar-bg);
    border-right: 1px solid var(--sidebar-border);
}

[data-testid="stSidebar"] > div {
    padding-top: 1.2rem;
}

[data-testid="stSidebar"] * {
    color: var(--sidebar-text) !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small {
    color: #AEB7C6 !important;
    color: var(--sidebar-muted) !important;
}

.sidebar-brand {
    border: 1px solid var(--sidebar-brand-border);
    border-radius: 10px;
    padding: 16px 16px 14px;
    background: var(--sidebar-brand-bg);
    box-shadow: var(--sidebar-brand-shadow);
    margin-bottom: 16px;
}

.sidebar-brand__eyebrow {
    font-family: "Fira Code", monospace;
    font-size: 0.68rem;
    color: var(--sidebar-eyebrow) !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.sidebar-brand__title {
    font-size: 1.2rem;
    line-height: 1.25;
    font-weight: 700;
    color: var(--sidebar-title) !important;
}

.sidebar-brand__meta {
    margin-top: 10px;
    font-size: 0.82rem;
    color: var(--sidebar-meta) !important;
}

.sidebar-stat-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
    margin: 14px 0 18px;
}

.sidebar-stat {
    min-height: 54px;
    border: 1px solid var(--sidebar-card-border);
    border-radius: 8px;
    padding: 8px;
    background: var(--sidebar-card-bg);
}

.sidebar-stat b {
    display: block;
    font-family: "Fira Code", monospace;
    font-size: 1rem;
    color: var(--sidebar-title) !important;
}

.sidebar-stat span {
    display: block;
    margin-top: 2px;
    font-size: 0.7rem;
    color: var(--sidebar-muted) !important;
}

[data-testid="stSidebar"] [role="radiogroup"] label {
    min-height: 44px;
    padding: 9px 10px;
    margin-bottom: 8px;
    border: 1px solid var(--sidebar-card-border);
    border-radius: 8px;
    background: var(--sidebar-radio-bg);
    transition: background 180ms ease, border-color 180ms ease, transform 180ms ease;
}

[data-testid="stSidebar"] [role="radiogroup"] {
    gap: 8px;
}

[data-testid="stSidebar"] [role="radiogroup"] label p {
    color: var(--sidebar-text) !important;
    font-weight: 700;
}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: var(--sidebar-radio-hover-bg);
    border-color: var(--sidebar-radio-hover-border);
    transform: translateX(2px);
}

[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: var(--sidebar-radio-selected-bg);
    border-color: var(--sidebar-radio-selected-border);
}

[data-testid="stSidebar"] .stRadio > label {
    color: var(--sidebar-muted) !important;
    font-family: "Fira Code", monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}

[data-testid="stSidebar"] button {
    min-height: 44px;
    background: #F97316 !important;
    color: #111827 !important;
    border: 0 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
}

/* 页面页头和分区 */
.fs-hero {
    position: relative;
    overflow: hidden;
    border: 1px solid var(--hero-border);
    border-radius: 12px;
    padding: 24px 26px;
    margin: 0 0 22px;
    color: #FFFFFF;
    background: var(--hero-bg);
    box-shadow: var(--shadow);
}

.fs-hero::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        linear-gradient(var(--hero-grid-y) 1px, transparent 1px),
        linear-gradient(90deg, var(--hero-grid-x) 1px, transparent 1px);
    background-size: 28px 28px;
    opacity: 0.35;
}

.fs-hero > * {
    position: relative;
    z-index: 1;
}

.fs-hero__kicker {
    display: inline-flex;
    align-items: center;
    min-height: 28px;
    padding: 5px 9px;
    border: 1px solid rgba(253, 186, 116, 0.42);
    border-radius: 999px;
    color: #FDBA74;
    background: rgba(234, 88, 12, 0.12);
    font-family: "Fira Code", monospace;
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.fs-hero__title {
    margin: 14px 0 8px;
    color: #FFFFFF;
    font-size: clamp(1.75rem, 3vw, 2.7rem);
    line-height: 1.08;
    font-weight: 700;
}

.fs-hero__desc {
    max-width: 860px;
    color: var(--hero-desc);
    font-size: 1rem;
    line-height: 1.75;
    margin: 0;
}

.fs-hero__rail {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 18px;
}

.fs-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-height: 32px;
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid var(--chip-border);
    background: var(--chip-bg);
    color: var(--chip-text);
    font-family: "Fira Code", monospace;
    font-size: 0.76rem;
}

.section-title {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 18px;
    margin: 24px 0 12px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--line);
}

.section-title h2 {
    margin: 0 !important;
    color: var(--ink) !important;
    font-size: 1.12rem !important;
    line-height: 1.2 !important;
    font-weight: 700 !important;
}

.section-title p {
    margin: 6px 0 0 !important;
    color: var(--muted) !important;
    font-size: 0.9rem !important;
}

.section-title__tag {
    flex: 0 0 auto;
    font-family: "Fira Code", monospace;
    font-size: 0.72rem;
    color: var(--signal);
    border: 1px solid rgba(15, 118, 110, 0.25);
    background: var(--signal-soft);
    border-radius: 999px;
    padding: 5px 9px;
}

.inline-note {
    border-left: 3px solid var(--brand);
    background: var(--brand-soft);
    color: #FED7AA;
    padding: 10px 12px;
    border-radius: 0 8px 8px 0;
    font-size: 0.9rem;
    line-height: 1.55;
}

.path-chip {
    display: inline-block;
    max-width: 100%;
    padding: 6px 9px;
    border-radius: 7px;
    border: 1px solid var(--line);
    background: var(--path-bg);
    color: var(--ink-2);
    font-family: "Fira Code", monospace;
    font-size: 0.78rem;
    overflow-wrap: anywhere;
}

[data-testid="stSidebar"] .path-chip {
    border-color: rgba(255, 255, 255, 0.12);
    background: var(--sidebar-path-bg);
    color: var(--sidebar-path-text) !important;
}

/* 标题系统 */
h1, h2, h3, h4,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-family: "Fira Sans", "Noto Sans SC", sans-serif !important;
    letter-spacing: 0 !important;
    color: var(--ink) !important;
}

h1 {
    font-size: 1.7rem !important;
    font-weight: 700 !important;
}

h2 {
    font-size: 1.26rem !important;
    font-weight: 700 !important;
}

h3 {
    font-size: 1.06rem !important;
    font-weight: 700 !important;
    color: var(--ink-2) !important;
}

/* 指标卡 */
[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 15px 16px !important;
    box-shadow: var(--shadow-soft);
    min-height: 104px;
    position: relative;
    overflow: hidden;
}

[data-testid="stMetric"]::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, var(--brand), var(--signal));
}

[data-testid="stMetric"]:hover {
    border-color: var(--line-strong);
    box-shadow: var(--shadow);
}

[data-testid="stMetric"] label {
    font-family: "Fira Code", monospace !important;
    font-size: 0.72rem !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-family: "Fira Code", monospace !important;
    font-weight: 600 !important;
    font-size: 1.35rem !important;
    color: var(--ink) !important;
}

/* 表单和按钮 */
.stButton > button,
.stDownloadButton > button {
    min-height: 44px !important;
    border-radius: 8px !important;
    font-family: "Fira Sans", "Noto Sans SC", sans-serif !important;
    font-weight: 700 !important;
    border: 1px solid var(--line-strong) !important;
    background: var(--button-bg) !important;
    color: var(--ink) !important;
    transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease, background 160ms ease !important;
}

.stButton > button {
    cursor: pointer;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-1px) !important;
    border-color: var(--brand) !important;
    box-shadow: var(--button-hover-shadow) !important;
}

.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {
    background: linear-gradient(135deg, #EA580C 0%, #F59E0B 100%) !important;
    color: #111827 !important;
    border-color: transparent !important;
    box-shadow: 0 12px 24px rgba(234, 88, 12, 0.24) !important;
}

.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible,
input:focus,
textarea:focus,
[data-baseweb="select"]:focus-within {
    outline: 3px solid rgba(234, 88, 12, 0.25) !important;
    outline-offset: 2px !important;
}

.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"],
.stTextInput input,
.stNumberInput input,
.stFileUploader [data-testid="stFileUploaderDropzone"] {
    border-radius: 8px !important;
    border-color: var(--line) !important;
    background: var(--input-bg) !important;
    min-height: 44px;
    font-family: "Fira Sans", "Noto Sans SC", sans-serif !important;
    font-size: 0.92rem !important;
}

.stTextInput input,
.stNumberInput input,
textarea {
    color: var(--input-text) !important;
}

.stTextInput input::placeholder,
.stNumberInput input::placeholder {
    color: var(--input-placeholder) !important;
    opacity: 1 !important;
}

.stSelectbox [data-baseweb="select"] *,
.stMultiSelect [data-baseweb="select"] * {
    color: var(--input-text) !important;
}

.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div,
.stSelectbox [data-baseweb="select"] input,
.stMultiSelect [data-baseweb="select"] input {
    background: var(--input-bg) !important;
    color: var(--input-text) !important;
}

.stSelectbox [data-baseweb="select"] [aria-disabled="true"],
.stSelectbox [data-baseweb="select"] [data-testid="stWidgetLabel"],
.stSelectbox [data-baseweb="select"] span,
.stMultiSelect [data-baseweb="select"] span {
    color: var(--input-placeholder) !important;
}

.stSelectbox [data-baseweb="select"]:hover,
.stTextInput input:hover,
.stNumberInput input:hover,
.stFileUploader [data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--line-strong) !important;
}

.stSlider [data-baseweb="slider"] [role="slider"],
[data-baseweb="slider"] [data-baseweb="slider__thumb"] {
    background: var(--brand) !important;
    border-color: var(--brand) !important;
}

.stCheckbox label,
.stRadio label,
.stSelectbox label,
.stTextInput label,
.stNumberInput label,
.stSlider label,
.stFileUploader label,
.stMultiSelect label {
    color: var(--ink-2) !important;
    font-weight: 600 !important;
}

.stFileUploader [data-testid="stFileUploaderDropzone"] {
    border-style: dashed !important;
    background: var(--dropzone-bg) !important;
}

.stFileUploader [data-testid="stFileUploaderDropzone"] * {
    color: var(--ink-2) !important;
}

.stFileUploader [data-testid="stFileUploaderDropzone"] button {
    background: var(--upload-button-bg) !important;
    color: var(--upload-button-text) !important;
    border-color: var(--line-strong) !important;
    box-shadow: 0 8px 18px rgba(0, 0, 0, 0.18) !important;
}

.stRadio [role="radiogroup"] {
    gap: 8px;
}

.stRadio [role="radiogroup"] label {
    min-height: 44px;
}

/* 表格、图表、输出 */
[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    overflow: hidden !important;
    border: 1px solid var(--line) !important;
    box-shadow: var(--shadow-soft);
}

[data-testid="stDataFrame"] th {
    font-family: "Fira Sans", "Noto Sans SC", sans-serif !important;
    font-weight: 600 !important;
    background: var(--table-header-bg) !important;
    color: var(--ink-2) !important;
}

[data-testid="stDataFrame"] td {
    font-family: "Fira Code", monospace !important;
    font-size: 0.88rem !important;
    color: var(--ink) !important;
}

[data-testid="stImage"] {
    border-radius: 10px;
    overflow: hidden;
}

[data-testid="stImage"] img {
    border-radius: 10px;
    border: 1px solid var(--line);
    background: var(--image-bg);
    box-shadow: var(--shadow-soft);
}

[data-testid="stImageCaption"] {
    color: var(--muted) !important;
    font-family: "Fira Code", monospace !important;
    font-size: 0.78rem !important;
}

[data-testid="stCodeBlock"] {
    border: 1px solid var(--code-border) !important;
    border-radius: 8px !important;
    box-shadow: var(--shadow-soft);
}

pre, code {
    font-family: "Fira Code", ui-monospace, SFMono-Regular, Menlo, monospace !important;
}

/* Tabs、展开器和提示 */
.stTabs [data-baseweb="tab"] {
    min-height: 44px;
    padding: 10px 18px !important;
    font-weight: 700 !important;
    color: var(--muted) !important;
    border-radius: 8px 8px 0 0 !important;
    background: var(--tab-bg) !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--ink) !important;
    background: rgba(234, 88, 12, 0.08) !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--brand) !important;
    border-bottom-color: var(--brand) !important;
}

[data-testid="stExpander"] {
    border: 1px solid var(--line) !important;
    border-radius: var(--radius) !important;
    background: var(--surface) !important;
    box-shadow: var(--shadow-soft);
}

[data-testid="stExpander"] * {
    color: var(--ink-2);
}

[role="listbox"],
[data-baseweb="popover"] {
    background: var(--popover-bg) !important;
    border: 1px solid var(--line) !important;
}

[role="option"] {
    color: var(--ink) !important;
    background: var(--option-bg) !important;
}

[role="option"]:hover {
    background: var(--option-hover-bg) !important;
}

[data-testid="stAlert"] {
    border-radius: 8px !important;
    border: 1px solid var(--line) !important;
    background: var(--alert-bg) !important;
    border-left-width: 4px !important;
    box-shadow: var(--shadow-soft);
}

[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, var(--brand), var(--signal)) !important;
}

[data-testid="stArrowVegaLiteChart"],
[data-testid="stPyplotGlobalUseContainer"] {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--radius) !important;
    padding: 16px !important;
    box-shadow: var(--shadow-soft);
}

hr, .stDivider {
    border-color: var(--line) !important;
    margin: 1.35rem 0 !important;
}

.stCaption, .stMarkdown small {
    color: var(--muted) !important;
    font-size: 0.82rem !important;
}

/* Streamlit 默认块间距略收紧，保留数据密度 */
div[data-testid="stVerticalBlock"] {
    gap: 0.75rem;
}

@media (max-width: 768px) {
    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        padding-top: 1rem;
    }
    .fs-hero {
        padding: 18px;
        border-radius: 10px;
    }
    .fs-hero__title {
        font-size: 1.65rem;
    }
    .section-title {
        align-items: flex-start;
        flex-direction: column;
        gap: 8px;
    }
    [data-testid="stMetric"] {
        min-height: 92px;
        padding: 12px 14px !important;
    }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
    }
}
</style>
""", unsafe_allow_html=True)

SCRIPT_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = SCRIPT_DIR / ".streamlit_uploads"


# ═══════════════════════════════════════════
# 展示组件
# ═══════════════════════════════════════════

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
    caption_html = f"<p>{escape(caption)}</p>" if caption else ""
    tag_html = f'<span class="section-title__tag">{escape(tag)}</span>' if tag else ""
    st.markdown(
        f"""
        <div class="section-title">
            <div>
                <h2>{escape(title)}</h2>
                {caption_html}
            </div>
            {tag_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def ui_path_chip(path: str, label: str = "当前路径"):
    st.markdown(
        f'<div class="path-chip">{escape(label)}: {escape(path)}</div>',
        unsafe_allow_html=True,
    )


def apply_theme_marker(theme_mode: str):
    marker = {
        "白天模式": "fs-theme-light",
        "夜间模式": "fs-theme-dark",
    }.get(theme_mode)
    if not marker:
        return
    st.markdown(f'<span id="{marker}" hidden></span>', unsafe_allow_html=True)


def save_uploaded_file(uploaded_file, subdir: str) -> str:
    """保存拖拽上传文件，并返回可供现有逻辑使用的本地路径。"""
    safe_name = Path(uploaded_file.name).name
    target_dir = UPLOAD_DIR / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / safe_name
    with open(target_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(target_path.resolve())


# ═══════════════════════════════════════════
# 资源扫描
# ═══════════════════════════════════════════

@st.cache_data(ttl=10, show_spinner=False)
def scan_datasets(search_dir: str | None = None):
    """扫描目录下所有 data.yaml / dataset.yaml（含上传目录）"""
    bases = [Path(search_dir)] if search_dir else [
        SCRIPT_DIR, UPLOAD_DIR / "datasets", UPLOAD_DIR / "datasets_extracted"
    ]
    datasets = []
    seen = set()
    for base in bases:
        if not base.exists():
            continue
        for yf in sorted(base.rglob("data*.yaml")):
            rp = str(yf.resolve())
            if rp in seen:
                continue
            seen.add(rp)
            try:
                with open(yf) as f:
                    d = yaml.safe_load(f)
                if "train" not in d and "val" not in d:
                    continue
                nc = d.get("nc", "?")
                names = d.get("names", {})
                label = f"{yf.parent.name}/{yf.name}" if yf.parent != base else yf.name
                datasets.append({
                    "label": f"{label} (nc={nc})",
                    "path": rp,
                    "nc": nc,
                    "names": names,
                })
            except Exception:
                pass
    return datasets


@st.cache_data(ttl=10, show_spinner=False)
def scan_models(search_dir: str | None = None):
    """扫描 runs/detect/ 和上传目录下所有 best.pt / last.pt"""
    bases = [Path(search_dir)] if search_dir else [
        SCRIPT_DIR / "runs" / "detect", UPLOAD_DIR / "models"
    ]
    models = []
    seen = set()
    for base in bases:
        if not base.exists():
            continue
        for ptf in sorted(base.rglob("*.pt"), key=os.path.getmtime, reverse=True):
            rp = str(ptf.resolve())
            if rp in seen:
                continue
            seen.add(rp)
            mtime = datetime.fromtimestamp(os.path.getmtime(ptf)).strftime("%m-%d %H:%M")
            label = f"{ptf.parent.name}/{ptf.name}" if ptf.parent != base else ptf.name
            models.append({
                "label": f"{label} ({mtime})",
                "path": rp,
                "date": mtime,
            })
    return models


@st.cache_data(ttl=10, show_spinner=False)
def scan_model_configs(search_dir: str | None = None):
    """扫描模型 YAML 配置文件"""
    base = Path(search_dir) if search_dir else SCRIPT_DIR
    configs = []
    for yf in sorted(base.glob("*.yaml")):
        try:
            with open(yf) as f:
                d = yaml.safe_load(f)
            if "backbone" not in d and "head" not in d:
                continue
            configs.append({
                "label": yf.name,
                "path": str(yf.resolve()),
            })
        except Exception:
            pass
    return configs


# ═══════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════

def parse_data_yaml(yaml_path: str) -> dict | None:
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        st.error(f"无法读取 {yaml_path}: {e}")
        return None

    train_path = data.get("train", "")
    val_path = data.get("val", "")
    test_path = data.get("test", "")
    nc = data.get("nc", 0)
    names = data.get("names", {})

    yaml_dir = Path(yaml_path).parent
    for key in ["train", "val", "test"]:
        p = data.get(key, "")
        if p and not Path(p).is_absolute():
            data[key] = str((yaml_dir / p).resolve())

    return {
        "train": data.get("train", ""),
        "val": data.get("val", ""),
        "test": data.get("test", ""),
        "nc": nc,
        "names": names,
        "yaml_dir": str(yaml_dir),
    }


def find_label_path(image_path: str) -> str | None:
    p = Path(image_path)
    parts = list(p.parts)
    for i, part in enumerate(parts):
        if part == "images":
            parts[i] = "labels"
            break
    label_path = Path(*parts).with_suffix(".txt")
    return str(label_path) if label_path.exists() else None


def draw_boxes_cv2(image, labels_path: str, class_names: dict, conf_threshold=0.0):
    import cv2
    if image is None:
        return image
    h, w = image.shape[:2]
    try:
        with open(labels_path) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                cls_id = int(parts[0])
                cx, cy, bw, bh = map(float, parts[1:5])
                conf = float(parts[5]) if len(parts) >= 6 else 1.0
                if conf < conf_threshold:
                    continue
                x1 = int((cx - bw / 2) * w)
                y1 = int((cy - bh / 2) * h)
                x2 = int((cx + bw / 2) * w)
                y2 = int((cy + bh / 2) * h)
                name = class_names.get(cls_id, str(cls_id))
                color = (0, 0, 255) if cls_id == 0 else (0, 255, 255)
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                label = f"{name} {conf:.2f}"
                cv2.putText(image, label, (x1, max(y1 - 5, 15)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    except Exception:
        pass
    return image


def get_image_files(dir_path: str, limit=500) -> list[str]:
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    files = []
    if not dir_path or not Path(dir_path).exists():
        return files
    for root, _, filenames in os.walk(dir_path):
        for f in filenames:
            if Path(f).suffix.lower() in exts:
                files.append(os.path.join(root, f))
                if len(files) >= limit:
                    return files
    return files


@st.cache_resource(show_spinner=False)
def load_model_cached(model_path: str):
    from ultralytics import YOLO
    return YOLO(model_path)


@st.cache_data(ttl=10, show_spinner=False)
def get_compute_devices() -> dict:
    """检测当前 Python 环境可用的训练设备。"""
    info = {
        "torch_available": False,
        "cuda_available": False,
        "cuda_count": 0,
        "gpus": [],
        "error": "",
    }
    try:
        import torch
        info["torch_available"] = True
        info["cuda_available"] = bool(torch.cuda.is_available())
        info["cuda_count"] = int(torch.cuda.device_count()) if info["cuda_available"] else 0
        for idx in range(info["cuda_count"]):
            info["gpus"].append({
                "id": idx,
                "name": torch.cuda.get_device_name(idx),
            })
    except Exception as e:
        info["error"] = str(e)
    return info


# ═══════════════════════════════════════════
# 通用组件：数据集选择器
# ═══════════════════════════════════════════

def _extract_dataset_zip(uploaded_zip) -> str | None:
    """解压数据集 zip，找到 data.yaml 并修复相对路径，返回 yaml 路径"""
    import zipfile
    import shutil
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
    with open(yaml_path) as f:
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
            # 尝试匹配最后 2 级（如 train/images）
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
        with open(yaml_path, "w") as f:
            yaml.dump(ydata, f)
    st.success(f"数据集已解压至 {extract_dir}")
    ui_path_chip(str(yaml_path), "已导入数据集")
    return str(yaml_path.resolve())


def dataset_selector(key_prefix: str, label: str = "数据集"):
    """数据集下拉选择器，拖拽上传（zip 或 yaml） + 自动扫描 + 手动输入"""
    datasets = scan_datasets()

    options = ["-- 手动输入路径 --"] + [d["label"] for d in datasets]
    if "dataset_custom" not in st.session_state:
        st.session_state.setdefault(f"{key_prefix}_mode", options[0])

    tab1, tab2 = st.tabs(["拖拽上传 zip (推荐)", "拖拽上传 yaml"])

    with tab1:
        zip_upload = st.file_uploader(
            f"拖拽数据集 zip 压缩包",
            type=["zip"],
            key=f"{key_prefix}_zip_upload",
            help="将完整数据集文件夹（含 data.yaml + train/valid/test 子目录）打包为 zip，拖入即可自动解压导入。",
        )
        if zip_upload is not None:
            result = _extract_dataset_zip(zip_upload)
            if result:
                st.session_state[f"{key_prefix}_last_ds"] = result
                return result

    with tab2:
        uploaded = st.file_uploader(
            f"拖拽上传 {label} YAML",
            type=["yaml", "yml"],
            key=f"{key_prefix}_ds_upload",
            help="仅上传 data.yaml。若内部使用相对路径，图片目录需手动放置在 WSL 中。",
        )
        if uploaded is not None:
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
    # 持久化：复用在本次会话中上传或选择过的路径
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
            uploaded_path = save_uploaded_file(uploaded, "models")
            ui_path_chip(uploaded_path, "已上传模型权重")
            st.session_state[f"{key_prefix}_last_mdl"] = uploaded_path
            return uploaded_path

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
    # 持久化：复用在本次会话中上传或选择过的路径
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
        help="支持拖入模型结构 YAML，例如 yolo11-mobilenetv3-slimneck-p2.yaml。",
    )
    if uploaded is not None:
        uploaded_path = save_uploaded_file(uploaded, "model_configs")
        ui_path_chip(uploaded_path, "已上传模型配置")
        return uploaded_path

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
    return model_yaml


# ═══════════════════════════════════════════
# 页面 1：数据集浏览
# ═══════════════════════════════════════════

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
    source = st.radio("浏览来源", sources, horizontal=True)
    pool_map = {"训练集": train_images, "验证集": val_images, "测试集": test_images}
    pool = pool_map.get(source, train_images)

    show_boxes = st.checkbox("显示标注框", value=True)
    per_page = 12
    total_pages = max(1, (len(pool) + per_page - 1) // per_page)

    # 分页控制
    col_page, col_info = st.columns([3, 1])
    with col_page:
        page = st.select_slider(
            "翻页", options=list(range(1, total_pages + 1)),
            key="ds_page",
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
            import cv2
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


# ═══════════════════════════════════════════
# 页面 2：训练管理
# ═══════════════════════════════════════════

def page_training():
    ui_page_header(
        "训练管理",
        "配置数据集、模型结构和关键超参数，并直接启动 YOLO 训练任务。",
        "Training Console",
        ["YOLOv11", "MobileNetV3", "Slim-Neck", "P2 小目标"],
    )

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

    ui_section("执行", "启动后会在页面内持续刷新最近训练日志。", "RUN")
    training_state = st.session_state.get("training_status", "未启动")
    status_cols = st.columns(4)
    status_cols[0].metric("训练状态", training_state)
    status_cols[1].metric("设备参数", device)
    status_cols[2].metric("输出目录", project_name)
    status_cols[3].metric("日志窗口", "最近 35 行")

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
        # 写参数到 JSON 文件，避免命令注入
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

        st.session_state["training_status"] = f"训练中 ({selected_device})"
        st.info("训练已启动，日志实时显示中...")
        log_placeholder = st.empty()
        output_lines = []

        with st.spinner("训练中..."):
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, cwd=str(SCRIPT_DIR),
            )
            for line in process.stdout:
                output_lines.append(line)
                log_placeholder.code("".join(output_lines[-35:]))
            process.wait()

        if process.returncode == 0:
            st.session_state["training_status"] = "训练完成"
            result_dir = SCRIPT_DIR / "runs" / "detect" / project_name
            st.session_state["last_train_dir"] = str(result_dir)
            st.session_state["_training_just_finished"] = True
            st.success(f"训练完成！结果保存在 {result_dir}")
            # 清除模型缓存以便下次扫描到新模型
            scan_models.clear()
            results_img = result_dir / "results.png"
            if results_img.exists():
                ui_section("训练曲线", "本次训练生成的结果图。", "RESULT")
                st.image(str(results_img), caption="训练曲线", use_container_width=True)
        else:
            st.session_state["training_status"] = "训练失败"
            st.error("训练异常退出")

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


# ═══════════════════════════════════════════
# 页面 3：模型推理
# ═══════════════════════════════════════════

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
        model = load_model_cached(model_path)
    except Exception as e:
        st.error(f"模型加载失败: {e}")
        return

    ui_path_chip(model_path, "当前权重")

    # 推理模式
    ui_section("推理设置", "选择推理来源并设置最低置信度。", "CONTROL")
    mode = st.radio("推理模式", ["单张/多张上传", "测试集目录"], horizontal=True)
    conf_threshold = st.slider("置信度阈值", 0.0, 1.0, 0.25, 0.05)

    if mode == "单张/多张上传":
        uploaded_files = st.file_uploader(
            "上传图片", type=["jpg", "jpeg", "png", "bmp"],
            accept_multiple_files=True, key="inf_upload",
        )
        if not uploaded_files:
            st.info("请上传图片进行推理")
            return

        if st.button("运行推理", type="primary", use_container_width=True):
            import cv2
            import numpy as np

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

    else:
        # 测试集目录模式
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
                        # 优先 test，其次 val
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

        if st.button("批量推理", type="primary", use_container_width=True):
            import cv2
            import numpy as np

            total_fire = 0
            total_smoke = 0
            all_confs = []
            results_display = []

            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, img_path in enumerate(test_images):
                img = cv2.imread(img_path)
                if img is None:
                    continue
                results = model.predict(img, conf=conf_threshold, verbose=False)
                boxes = results[0].boxes

                if boxes is not None and len(boxes) > 0:
                    cls_ids = boxes.cls.cpu().numpy().astype(int)
                    confs = boxes.conf.cpu().numpy()
                    total_fire += int((cls_ids == 0).sum())
                    total_smoke += int((cls_ids == 1).sum())
                    all_confs.extend(confs.tolist())

                # 保存部分结果用于展示
                if len(results_display) < max_display:
                    result_img = results[0].plot()
                    result_img = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
                    results_display.append({
                        "name": Path(img_path).name,
                        "img": result_img,
                        "fire": int((cls_ids == 0).sum()) if boxes is not None and len(boxes) > 0 else 0,
                        "smoke": int((cls_ids == 1).sum()) if boxes is not None and len(boxes) > 0 else 0,
                        "has_boxes": boxes is not None and len(boxes) > 0,
                    })

                progress_bar.progress((idx + 1) / len(test_images))
                status_text.text(f"处理中: {idx + 1}/{len(test_images)} — {Path(img_path).name}")

            progress_bar.empty()
            status_text.empty()

            st.session_state["inf_batch"] = {
                "total_images": len(test_images),
                "total_fire": total_fire,
                "total_smoke": total_smoke,
                "avg_conf": np.mean(all_confs) if all_confs else 0,
                "display": results_display,
            }
            st.session_state["inf_batch_has"] = True

        if st.session_state.get("inf_batch_has"):
            import numpy as np
            batch = st.session_state["inf_batch"]
            # 汇总
            ui_section("推理汇总", "批量目录的目标计数和平均置信度。", "SUMMARY")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("测试图片数", batch["total_images"])
            c2.metric("检测火焰总数", batch["total_fire"])
            c3.metric("检测烟雾总数", batch["total_smoke"])
            c4.metric("平均置信度", f"{batch['avg_conf']:.3f}" if batch["avg_conf"] else "—")

            # 展示部分结果
            results_display = batch["display"]
            if results_display:
                ui_section("部分检测结果", f"展示前 {len(results_display)} 张结果图。", "GALLERY")
                cols = st.columns(4)
                for i, r in enumerate(results_display):
                    col = cols[i % 4]
                    cap = f"{r['name']} | 火焰 {r['fire']} | 烟雾 {r['smoke']}" if r["has_boxes"] else f"{r['name']} | 无检测"
                    col.image(r["img"], caption=cap, use_container_width=True)


# ═══════════════════════════════════════════
# 页面 4：模型评估
# ═══════════════════════════════════════════

def _get_model_info(model_path: str) -> dict:
    """获取模型的参数量和 FLOPs"""
    import torch
    import io

    from ultralytics import YOLO
    model = YOLO(model_path)
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    model.info()
    info_str = sys.stdout.getvalue()
    sys.stdout = old_stdout

    params_m = 0.0
    flops_g = 0.0
    for line in info_str.split("\n"):
        if "GFLOPs" in line:
            flops_g = float(line.split()[0])
        if "parameters" in line:
            params_m = float(line.split()[0])
    if params_m == 0:
        total = sum(p.numel() for p in model.model.parameters())
        params_m = total / 1e6
        flops_g = params_m * 640 * 640 / 100000
    return {"params_m": params_m, "flops_g": flops_g}


def _run_eval(model_path: str, data_yaml: str):
    """运行评估，返回指标字典"""
    model = load_model_cached(model_path)
    metrics = model.val(data=data_yaml, verbose=False)
    return {
        "map50": metrics.box.map50,
        "map50_95": metrics.box.map,
        "precision": metrics.box.mp if hasattr(metrics.box, "mp") else 0.0,
        "recall": metrics.box.mr if hasattr(metrics.box, "mr") else 0.0,
    }


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
                    st.session_state["eval_result"] = _run_eval(model_path, yaml_path)
                    st.session_state["eval_model_info"] = _get_model_info(model_path)
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

            # 评估图表
            val_dirs = sorted((SCRIPT_DIR / "runs" / "detect").glob("*val*"), key=os.path.getmtime, reverse=True)
            val_dir = val_dirs[0] if val_dirs else None
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
            from io import BytesIO
            import matplotlib.pyplot as plt

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
                            metrics = _run_eval(path, yaml_path)
                            info = _get_model_info(path)
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
                import matplotlib.pyplot as plt
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

                # 导出对比结果
                ui_section("导出对比", "生成包含全部模型对比指标的汇总图片。", "EXPORT")
                from io import BytesIO
                import matplotlib.pyplot as plt

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


# ═══════════════════════════════════════════
# 硬件配置档案
# ═══════════════════════════════════════════

HARDWARE_PROFILES = {
    "Jetson Nano 2GB": {
        "gpu_memory_gb": 2.0,
        "compute_tflops": 0.472,  # FP16
        "type": "edge",
        "supports_fp16": True,
        "supports_int8": False,
        "recommended_imgsz": 320,
    },
    "Jetson Orin Nano 8GB": {
        "gpu_memory_gb": 8.0,
        "compute_tflops": 40.0,  # INT8
        "type": "edge",
        "supports_fp16": True,
        "supports_int8": True,
        "recommended_imgsz": 640,
    },
    "Raspberry Pi 5 8GB": {
        "gpu_memory_gb": 3.0,
        "compute_tflops": 0.1,
        "type": "edge_cpu",
        "supports_fp16": False,
        "supports_int8": True,
        "recommended_imgsz": 320,
    },
    "RTX 3060 12GB": {
        "gpu_memory_gb": 12.0,
        "compute_tflops": 12.7,
        "type": "desktop",
        "supports_fp16": True,
        "supports_int8": True,
        "recommended_imgsz": 640,
    },
    "RTX 4090 24GB": {
        "gpu_memory_gb": 24.0,
        "compute_tflops": 82.6,
        "type": "desktop",
        "supports_fp16": True,
        "supports_int8": True,
        "recommended_imgsz": 640,
    },
    "AWS T4 16GB": {
        "gpu_memory_gb": 16.0,
        "compute_tflops": 8.1,
        "type": "cloud",
        "supports_fp16": True,
        "supports_int8": True,
        "recommended_imgsz": 640,
    },
}


def estimate_memory(params_m: float, imgsz: int, batch: int, fp16: bool = False) -> dict:
    """估算显存占用"""
    bytes_per_param = 2 if fp16 else 4
    model_mem_mb = params_m * bytes_per_param * 1.2  # 含 overhead

    # 激活内存粗略估算
    activation_mb = batch * (imgsz ** 2) * 3 * bytes_per_param * 0.004

    inference_mb = model_mem_mb + activation_mb
    training_mb = model_mem_mb * 3 + activation_mb * 2  # 梯度 + 优化器

    return {
        "model_mb": round(model_mem_mb, 1),
        "activation_mb": round(activation_mb, 1),
        "inference_mb": round(inference_mb, 1),
        "training_mb": round(training_mb, 1),
        "inference_gb": round(inference_mb / 1024, 2),
        "training_gb": round(training_mb / 1024, 2),
    }


# ═══════════════════════════════════════════
# 页面 5：硬件预估
# ═══════════════════════════════════════════

def page_hardware():
    ui_page_header(
        "硬件需求预估",
        "根据模型复杂度、输入尺寸、batch 和精度模式，估算推理/训练显存需求。",
        "Hardware Console",
        ["边缘设备", "显存估算", "FP16", "兼容性表"],
    )

    ui_section("模型来源", "可以用 YAML 结构配置，也可以直接读取已训练权重。", "TARGET")
    tab1, tab2 = st.tabs(["从模型配置预估", "从已训练模型预估"])

    with tab1:
        config_target = model_config_selector("hw", "选择模型配置")

    with tab2:
        model_target = model_selector("hw", "已训练模型")

    target = model_target or config_target

    if not target or not Path(target).exists():
        st.info("请选择模型配置或已训练模型文件")
        return

    ui_path_chip(target, "分析目标")

    ui_section("预估参数", "输入尺寸、Batch 和精度模式会直接影响显存峰值。", "PARAMS")
    col1, col2, col3 = st.columns(3)
    imgsz = col1.selectbox("输入尺寸", [320, 416, 512, 640, 800, 1024], index=3, key="hw_imgsz")
    batch = col2.slider("Batch Size", 1, 64, 1, key="hw_batch")
    fp16_mode = col3.checkbox("FP16 模式", value=False, key="hw_fp16",
                               help="开启后半精度，显存需求约减半")

    if st.button("开始预估", type="primary", use_container_width=True):
        with st.spinner("正在分析模型..."):
            import torch
            import io

            try:
                # 构建模型并获取信息
                from ultralytics import YOLO

                # 捕获 model.info() 输出
                model = YOLO(target)
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                model.info()
                info_str = sys.stdout.getvalue()
                sys.stdout = old_stdout

                # 解析 FLOPs 和 Params
                params_m = 0.0
                flops_g = 0.0
                for line in info_str.split("\n"):
                    if "GFLOPs" in line:
                        flops_g = float(line.split()[0])
                    if "parameters" in line:
                        params_m = float(line.split()[0])

                if params_m == 0 and flops_g == 0:
                    # 回退到 torch 直接统计
                    total = sum(p.numel() for p in model.model.parameters())
                    params_m = total / 1e6
                    flops_g = params_m * imgsz * imgsz / 100000

                memory = estimate_memory(params_m, imgsz, batch, fp16_mode)

                st.session_state["hw_params_m"] = params_m
                st.session_state["hw_flops_g"] = flops_g
                st.session_state["hw_memory"] = memory
                st.session_state["hw_saved_imgsz"] = imgsz
                st.session_state["hw_saved_fp16"] = fp16_mode
                st.session_state["hw_has_result"] = True

            except Exception as e:
                st.error(f"模型分析失败: {e}")
                st.session_state["hw_has_result"] = False

    if st.session_state.get("hw_has_result"):
        params_m = st.session_state["hw_params_m"]
        flops_g = st.session_state["hw_flops_g"]
        memory = st.session_state["hw_memory"]
        imgsz = st.session_state["hw_saved_imgsz"]
        fp16_mode = st.session_state["hw_saved_fp16"]

        # 展示预估结果
        ui_section("模型复杂度", "从 Ultralytics 模型信息解析出的参数量和 GFLOPs。", "MODEL")
        c1, c2, c3 = st.columns(3)
        c1.metric("参数量", f"{params_m:.1f} M")
        c2.metric("计算量", f"{flops_g:.1f} GFLOPs")
        c3.metric("模型文件大小 (估)", f"{params_m * 4:.0f} MB" if not fp16_mode else f"{params_m * 2:.0f} MB")

        ui_section("显存 / 内存预估", "粗略估算推理和训练峰值，便于选择部署硬件。", "MEMORY")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("模型占用", f"{memory['model_mb']:.0f} MB")
        c2.metric("激活值", f"{memory['activation_mb']:.0f} MB")
        c3.metric("推理峰值", f"{memory['inference_mb']:.0f} MB ({memory['inference_gb']:.1f} GB)")
        c4.metric("训练峰值", f"{memory['training_mb']:.0f} MB ({memory['training_gb']:.1f} GB)")

        # 硬件兼容性
        ui_section("硬件兼容性", "按 85% 可用显存阈值给出运行建议。", "DEVICE")
        rows = []
        for hw_name, hw in HARDWARE_PROFILES.items():
            mem_ok = memory["inference_gb"] <= hw["gpu_memory_gb"] * 0.85
            status = "可运行" if mem_ok else "显存不足"
            note = ""
            if mem_ok and hw["recommended_imgsz"] < imgsz:
                note = f"建议降 imgsz 至 {hw['recommended_imgsz']}"
            if hw.get("type") == "edge_cpu" and params_m > 20:
                note = "CPU 推理可能较慢"
            rows.append({
                "硬件": hw_name,
                "可用显存": f"{hw['gpu_memory_gb']} GB",
                "推理需求": f"{memory['inference_gb']:.1f} GB",
                "状态": status,
                "建议": note or "—",
            })

        import pandas as pd
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════
# 页面 6：模型优化
# ═══════════════════════════════════════════

def page_optimization():
    ui_page_header(
        "模型优化",
        "把训练好的 YOLO 权重导出为更适合目标硬件的部署格式。",
        "Optimization Console",
        ["ONNX", "FP16", "INT8", "输入尺寸缩减"],
    )

    ui_section("待优化模型", "选择训练好的 .pt 权重，后续导出流程会基于它执行。", "MODEL")
    target_model = model_selector("opt", "待优化模型")

    if not target_model or not Path(target_model).exists():
        st.info("请选择已训练的 .pt 模型")
        return

    # 读取模型基本信息
    model_size_mb = round(os.path.getsize(target_model) / 1024 / 1024, 1)
    ui_path_chip(target_model, "待优化权重")
    st.metric("当前模型大小", f"{model_size_mb} MB")

    # 目标硬件
    ui_section("目标硬件", "不同硬件支持的导出格式和推荐输入尺寸不同。", "DEVICE")
    hw_options = list(HARDWARE_PROFILES.keys())
    target_hw = st.selectbox("目标硬件", hw_options, key="opt_hw")
    hw = HARDWARE_PROFILES[target_hw]

    # 显示硬件信息
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("可用显存", f"{hw['gpu_memory_gb']} GB")
    col_b.metric("类型", hw["type"])
    col_c.metric("推荐 imgsz", hw["recommended_imgsz"])

    ui_section("优化方案", "按硬件能力选择导出格式，可同时勾选多个方案。", "PLAN")

    opt_col1, opt_col2 = st.columns(2)

    with opt_col1:
        st.markdown("**方案 A: FP16 半精度**")
        st.caption("模型大小减半，精度几乎无损")
        if hw["supports_fp16"]:
            st.success("该硬件支持 FP16")
        else:
            st.warning("该硬件不支持 FP16，请选 INT8")
        export_fp16 = st.checkbox("导出 FP16 ONNX", value=hw["supports_fp16"], key="opt_fp16")

        st.markdown("**方案 C: INT8 量化**")
        st.caption("模型大小减少 ~75%，轻微精度损失")
        if hw["supports_int8"]:
            st.success("该硬件支持 INT8")
        else:
            st.warning("该硬件不支持 INT8 量化")
        export_int8 = st.checkbox("导出 INT8 TFLite", value=hw["supports_int8"] and not hw["supports_fp16"], key="opt_int8")

    with opt_col2:
        st.markdown("**方案 B: ONNX 导出**")
        st.caption("通用跨平台格式，保持 FP32")
        export_onnx = st.checkbox("导出 FP32 ONNX", value=False, key="opt_onnx")

        st.markdown("**方案 D: 缩减输入尺寸**")
        st.caption("降低 imgsz 直接减少计算量")
        reduced_imgsz = st.selectbox(
            "目标 imgsz",
            [160, 224, 320, 416, 512],
            index=[160, 224, 320, 416, 512].index(
                min([160, 224, 320, 416, 512], key=lambda x: abs(x - hw["recommended_imgsz"]))
            ),
            key="opt_imgsz",
        )
        st.caption(f"原 640 → {reduced_imgsz}，计算量约降至 {(reduced_imgsz/640)**2:.0%}")

    ui_section("执行", "导出产物会写入 Ultralytics 返回的模型路径。", "EXPORT")

    if st.button("执行优化", type="primary", use_container_width=True):
        results = []
        export_dir = SCRIPT_DIR / "runs" / "optimize"
        export_dir.mkdir(parents=True, exist_ok=True)
        model_name = Path(target_model).stem

        model = load_model_cached(target_model)

        if export_fp16:
            with st.spinner("导出 FP16 ONNX..."):
                try:
                    out = model.export(format="onnx", half=True, imgsz=reduced_imgsz)
                    out_size = round(os.path.getsize(out) / 1024 / 1024, 1)
                    results.append(("FP16 ONNX", str(out), out_size, "通用硬件，半精度"))
                except Exception as e:
                    st.error(f"FP16 导出失败: {e}")

        if export_onnx:
            with st.spinner("导出 FP32 ONNX..."):
                try:
                    out = model.export(format="onnx", half=False, imgsz=reduced_imgsz)
                    out_size = round(os.path.getsize(out) / 1024 / 1024, 1)
                    results.append(("FP32 ONNX", str(out), out_size, "通用跨平台部署"))
                except Exception as e:
                    st.error(f"ONNX 导出失败: {e}")

        if export_int8:
            with st.spinner("导出 INT8 TFLite（需较长时间）..."):
                try:
                    out = model.export(format="tflite", int8=True, imgsz=reduced_imgsz)
                    out_size = round(os.path.getsize(out) / 1024 / 1024, 1)
                    results.append(("INT8 TFLite", str(out), out_size, "边缘设备，极致压缩"))
                except Exception as e:
                    st.error(f"INT8 导出失败: {e}。可能需要代表性数据集校准，尝试无量化导出...")
                    try:
                        out = model.export(format="tflite", imgsz=reduced_imgsz)
                        out_size = round(os.path.getsize(out) / 1024 / 1024, 1)
                        results.append(("FP32 TFLite", str(out), out_size, "边缘设备备用"))
                    except Exception as e2:
                        st.error(f"TFLite 导出也失败: {e2}")

        st.session_state["opt_results"] = results
        st.session_state["opt_model_size"] = model_size_mb
        st.session_state["opt_has_result"] = bool(results)

    if st.session_state.get("opt_has_result"):
        results = st.session_state["opt_results"]
        model_size_mb = st.session_state["opt_model_size"]
        st.success(f"优化完成！共生成 {len(results)} 个模型文件")
        ui_section("优化结果", "导出文件路径、大小和压缩比例。", "OUTPUT")
        for name, path, size, desc in results:
            c1, c2, c3 = st.columns([2, 1, 2])
            c1.code(f"{name}: {path}")
            c2.metric("大小", f"{size} MB", f"{(1 - size/model_size_mb)*100:.0f}%" if model_size_mb else "")
            c3.caption(desc)


# ═══════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════

def _cleanup_old_files():
    """清理过期文件，防止无限累积"""
    # eval_results: 保留最近 10 个
    for sub in ["eval_results"]:
        d = SCRIPT_DIR / sub
        if d.exists():
            files = sorted(d.glob("*"), key=os.path.getmtime, reverse=True)
            for f in files[10:]:
                try:
                    f.unlink()
                except OSError:
                    pass
    # 上传目录: 清理 7 天前的文件
    import time as _time
    import shutil as _shutil
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
        f'<div class="path-chip">工作目录: {escape(str(SCRIPT_DIR))}</div>',
        unsafe_allow_html=True,
    )

    # 刷新缓存按钮
    if st.sidebar.button("刷新资源列表"):
        scan_datasets.clear()
        scan_models.clear()
        scan_model_configs.clear()
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
