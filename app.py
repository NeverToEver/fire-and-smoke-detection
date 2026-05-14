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

# ── CLA 设计语言 · 自定义样式 ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;0,700;0,800;1,500&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ═══════════════════════════════════════════
   DESIGN TOKENS — Claude-inspired warm editorial
   ═══════════════════════════════════════════ */
:root {
    --font-display: "Playfair Display", "Noto Serif SC", Georgia, serif;
    --font-body: "Inter", "Noto Sans SC", system-ui, sans-serif;
    --font-mono: "JetBrains Mono", "Fira Code", ui-monospace, monospace;

    /* Warm cream + ink palette */
    --bg: #FAF8F5;
    --surface: #FFFFFF;
    --surface-raised: #FCFAF7;
    --ink: #1A1815;
    --ink-2: #3D3833;
    --muted: #78716C;
    --faint: #A8A29E;
    --line: #E7E2DB;
    --line-strong: #D1CCC4;

    /* Amber accent — Claude's signature */
    --brand: #D97706;
    --brand-hover: #B45309;
    --brand-soft: rgba(217, 119, 6, 0.08);
    --brand-glow: rgba(217, 119, 6, 0.15);

    /* Semantic */
    --signal: #0F766E;
    --signal-soft: rgba(15, 118, 110, 0.08);
    --success: #15803D;
    --success-soft: rgba(21, 128, 61, 0.08);
    --warning: #B45309;
    --warning-soft: rgba(180, 83, 9, 0.08);
    --danger: #B91C1C;
    --danger-soft: rgba(185, 28, 28, 0.06);

    --radius-sm: 6px;
    --radius: 10px;
    --radius-lg: 14px;
    --radius-full: 999px;

    --shadow-sm: 0 1px 2px rgba(26, 24, 21, 0.04);
    --shadow: 0 1px 3px rgba(26, 24, 21, 0.06), 0 4px 16px rgba(26, 24, 21, 0.04);
    --shadow-lg: 0 2px 6px rgba(26, 24, 21, 0.05), 0 8px 32px rgba(26, 24, 21, 0.06);

    /* Layout */
    --sidebar-width: 17rem;
    --content-max: 1200px;

    /* Sidebar (light) */
    --sidebar-bg: #F5F1EB;
    --sidebar-border: #E7E2DB;
    --sidebar-text: #3D3833;
    --sidebar-muted: #78716C;
}

/* ═══════════════════════════════════════════
   DARK MODE — warm dark, not cold
   ═══════════════════════════════════════════ */
:root.theme-dark,
:root:has(#fs-theme-dark) {
    --bg: #1A1815;
    --surface: #252220;
    --surface-raised: #2D2A27;
    --ink: #F5F1EB;
    --ink-2: #D1CCC4;
    --muted: #A8A29E;
    --faint: #78716C;
    --line: #3D3833;
    --line-strong: #57534E;
    --brand-soft: rgba(217, 119, 6, 0.14);
    --signal-soft: rgba(45, 212, 191, 0.10);
    --success-soft: rgba(74, 222, 128, 0.10);
    --warning-soft: rgba(245, 158, 11, 0.10);
    --danger-soft: rgba(248, 113, 113, 0.10);
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.18);
    --shadow: 0 1px 3px rgba(0, 0, 0, 0.22), 0 4px 16px rgba(0, 0, 0, 0.16);
    --shadow-lg: 0 2px 6px rgba(0, 0, 0, 0.24), 0 8px 32px rgba(0, 0, 0, 0.22);
    --sidebar-bg: #211E1B;
    --sidebar-border: #3D3833;
    --sidebar-text: #D1CCC4;
    --sidebar-muted: #78716C;
}

/* ═══════════════════════════════════════════
   RESET & BASE
   ═══════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: var(--font-body);
    font-size: 16px;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

.stApp {
    background: var(--bg);
    color: var(--ink);
}

/* Hide Streamlit chrome */
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
#MainMenu, footer,
.stDeployButton { display: none !important; }

[data-testid="stAppViewContainer"] { background: transparent; }

.main .block-container {
    max-width: var(--content-max);
    padding: 2rem 2.5rem 5rem;
}

/* ═══════════════════════════════════════════
   SIDEBAR
   ═══════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    display: flex !important;
    visibility: visible !important;
    width: var(--sidebar-width) !important;
    min-width: var(--sidebar-width) !important;
    transform: none !important;
    transition: none !important;
    background: var(--sidebar-bg);
    border-right: 1px solid var(--sidebar-border);
}
button[data-testid="stSidebarCloseButton"],
[data-testid="stSidebarCollapseButton"] { display: none !important; }

[data-testid="stSidebar"] > div { padding: 1.5rem 1rem; }

[data-testid="stSidebar"] * { color: var(--sidebar-text) !important; }

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] small { color: var(--sidebar-muted) !important; }

/* Sidebar: brand card */
.sidebar-brand {
    border: 1px solid var(--sidebar-border);
    border-radius: var(--radius);
    padding: 16px 18px 14px;
    background: var(--surface);
    margin-bottom: 18px;
}
.sidebar-brand__eyebrow {
    font-family: var(--font-mono);
    font-size: 0.65rem;
    color: var(--brand) !important;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.sidebar-brand__title {
    font-family: var(--font-display);
    font-size: 1.15rem;
    line-height: 1.2;
    font-weight: 700;
    color: var(--ink) !important;
}
.sidebar-brand__meta {
    margin-top: 8px;
    font-size: 0.78rem;
    color: var(--muted) !important;
    font-family: var(--font-mono);
}

/* Sidebar: stat grid */
.sidebar-stat-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 6px;
    margin: 14px 0 20px;
}
.sidebar-stat {
    text-align: center;
    border: 1px solid var(--sidebar-border);
    border-radius: var(--radius-sm);
    padding: 10px 6px;
    background: var(--surface);
}
.sidebar-stat b {
    display: block;
    font-family: var(--font-display);
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--ink) !important;
}
.sidebar-stat span {
    display: block;
    margin-top: 2px;
    font-size: 0.65rem;
    font-family: var(--font-mono);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted) !important;
}

/* Sidebar: radio navigation */
[data-testid="stSidebar"] [role="radiogroup"] { gap: 4px; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    min-height: 40px;
    padding: 8px 12px;
    margin-bottom: 0;
    border: 1px solid transparent;
    border-radius: var(--radius-sm);
    background: transparent;
    transition: background 150ms ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label p {
    font-family: var(--font-body);
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: var(--sidebar-text) !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: var(--brand-soft);
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: var(--brand-soft);
    border-color: var(--brand);
}
[data-testid="stSidebar"] .stRadio > label {
    font-family: var(--font-mono) !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: var(--sidebar-muted) !important;
}

/* Sidebar: buttons */
[data-testid="stSidebar"] button {
    min-height: 38px;
    border-radius: var(--radius-sm) !important;
    font-family: var(--font-body) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    background: var(--surface) !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    transition: all 150ms ease;
}
[data-testid="stSidebar"] button:hover {
    border-color: var(--brand) !important;
    background: var(--brand-soft) !important;
}

/* ═══════════════════════════════════════════
   PAGE HERO — editorial header
   ═══════════════════════════════════════════ */
.fs-hero {
    position: relative;
    border: 1px solid var(--line);
    border-radius: var(--radius-lg);
    padding: 32px 36px;
    margin: 0 0 32px;
    background: var(--surface);
    box-shadow: var(--shadow-sm);
}
.fs-hero__kicker {
    display: inline-flex;
    align-items: center;
    min-height: 26px;
    padding: 4px 10px;
    border: 1px solid var(--brand-glow);
    border-radius: var(--radius-full);
    color: var(--brand);
    background: var(--brand-soft);
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.fs-hero__title {
    margin: 14px 0 10px;
    font-family: var(--font-display);
    color: var(--ink);
    font-size: clamp(1.8rem, 3vw, 2.6rem);
    line-height: 1.12;
    font-weight: 700;
    letter-spacing: -0.01em;
}
.fs-hero__desc {
    max-width: 720px;
    color: var(--muted);
    font-size: 1rem;
    line-height: 1.7;
    margin: 0;
    font-family: var(--font-body);
}
.fs-hero__rail {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 18px;
}
.fs-chip {
    display: inline-flex;
    align-items: center;
    min-height: 30px;
    padding: 4px 12px;
    border-radius: var(--radius-full);
    border: 1px solid var(--line);
    background: var(--surface-raised);
    color: var(--ink-2);
    font-family: var(--font-mono);
    font-size: 0.72rem;
    font-weight: 500;
}

/* ═══════════════════════════════════════════
   SECTION TITLES
   ═══════════════════════════════════════════ */
.section-title {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
    margin: 32px 0 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--line);
}
.section-title h2 {
    margin: 0 !important;
    font-family: var(--font-display) !important;
    font-size: 1.15rem !important;
    line-height: 1.3 !important;
    font-weight: 600 !important;
    color: var(--ink) !important;
    letter-spacing: -0.01em !important;
}
.section-title p {
    margin: 4px 0 0 !important;
    color: var(--muted) !important;
    font-size: 0.85rem !important;
}
.section-title__tag {
    flex: 0 0 auto;
    font-family: var(--font-mono);
    font-size: 0.68rem;
    color: var(--signal);
    border: 1px solid rgba(15, 118, 110, 0.2);
    background: var(--signal-soft);
    border-radius: var(--radius-full);
    padding: 4px 10px;
    font-weight: 500;
}

.path-chip {
    display: inline-block;
    max-width: 100%;
    padding: 6px 12px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--line);
    background: var(--surface-raised);
    color: var(--ink-2);
    font-family: var(--font-mono);
    font-size: 0.76rem;
    overflow-wrap: anywhere;
}

/* ═══════════════════════════════════════════
   TYPOGRAPHY
   ═══════════════════════════════════════════ */
h1, h2, h3, h4,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-family: var(--font-display) !important;
    letter-spacing: -0.01em !important;
    color: var(--ink) !important;
}
h1 { font-size: 1.8rem !important; font-weight: 700 !important; }
h2 { font-size: 1.25rem !important; font-weight: 600 !important; }
h3 { font-size: 1.05rem !important; font-weight: 600 !important; color: var(--ink-2) !important; }

pre, code {
    font-family: var(--font-mono) !important;
    font-size: 0.84rem;
}

/* ═══════════════════════════════════════════
   METRIC CARDS — clean, minimal
   ═══════════════════════════════════════════ */
[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 16px 20px !important;
    box-shadow: none;
    min-height: 96px;
    transition: border-color 150ms ease, box-shadow 150ms ease;
}
[data-testid="stMetric"]:hover {
    border-color: var(--line-strong);
    box-shadow: var(--shadow);
}
[data-testid="stMetric"] label {
    font-family: var(--font-mono) !important;
    font-size: 0.68rem !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    font-weight: 500 !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-family: var(--font-display) !important;
    font-weight: 600 !important;
    font-size: 1.5rem !important;
    color: var(--ink) !important;
}

/* ═══════════════════════════════════════════
   BUTTONS — warm, refined
   ═══════════════════════════════════════════ */
.stButton > button,
.stDownloadButton > button {
    min-height: 44px !important;
    border-radius: var(--radius-sm) !important;
    font-family: var(--font-body) !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    border: 1px solid var(--line) !important;
    background: var(--surface) !important;
    color: var(--ink) !important;
    transition: all 150ms ease !important;
    cursor: pointer;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: var(--brand) !important;
    background: var(--brand-soft) !important;
    box-shadow: var(--shadow-sm);
    transform: none !important;
}
.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {
    background: var(--brand) !important;
    color: #FFFFFF !important;
    border-color: var(--brand) !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover {
    background: var(--brand-hover) !important;
    border-color: var(--brand-hover) !important;
}

/* Focus ring */
.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible,
input:focus, textarea:focus,
[data-baseweb="select"]:focus-within {
    outline: 2px solid var(--brand) !important;
    outline-offset: 2px !important;
}

/* ═══════════════════════════════════════════
   FORMS & INPUTS
   ═══════════════════════════════════════════ */
.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"],
.stTextInput input,
.stNumberInput input,
.stFileUploader [data-testid="stFileUploaderDropzone"] {
    border-radius: var(--radius-sm) !important;
    border-color: var(--line) !important;
    background: var(--surface) !important;
    min-height: 44px;
    font-family: var(--font-body) !important;
    font-size: 0.9rem !important;
}
.stTextInput input,
.stNumberInput input,
textarea { color: var(--ink) !important; }
.stTextInput input::placeholder,
.stNumberInput input::placeholder {
    color: var(--faint) !important;
    opacity: 1 !important;
}
.stSelectbox [data-baseweb="select"] *,
.stMultiSelect [data-baseweb="select"] * { color: var(--ink) !important; }
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div,
.stSelectbox [data-baseweb="select"] input,
.stMultiSelect [data-baseweb="select"] input {
    background: var(--surface) !important;
    color: var(--ink) !important;
}
.stSelectbox [data-baseweb="select"]:hover,
.stTextInput input:hover,
.stNumberInput input:hover,
.stFileUploader [data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--line-strong) !important;
}

/* Sliders */
.stSlider [data-baseweb="slider"] [role="slider"],
[data-baseweb="slider"] [data-baseweb="slider__thumb"] {
    background: var(--brand) !important;
    border-color: var(--brand) !important;
}

/* Labels */
.stCheckbox label, .stRadio label,
.stSelectbox label, .stTextInput label,
.stNumberInput label, .stSlider label,
.stFileUploader label, .stMultiSelect label {
    color: var(--ink-2) !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
}

/* File uploader dropzone */
.stFileUploader [data-testid="stFileUploaderDropzone"] {
    border-style: dashed !important;
    border-color: var(--line) !important;
    background: var(--surface-raised) !important;
    border-radius: var(--radius) !important;
}
.stFileUploader [data-testid="stFileUploaderDropzone"] * { color: var(--muted) !important; }
.stFileUploader [data-testid="stFileUploaderDropzone"] button {
    background: var(--surface) !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--radius-sm) !important;
    font-family: var(--font-body) !important;
    font-size: 0.85rem !important;
}

.stRadio [role="radiogroup"] { gap: 6px; }
.stRadio [role="radiogroup"] label { min-height: 40px; }

/* ═══════════════════════════════════════════
   TABLES & DATA
   ═══════════════════════════════════════════ */
[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    overflow: hidden !important;
    border: 1px solid var(--line) !important;
    box-shadow: none;
}
[data-testid="stDataFrame"] th {
    font-family: var(--font-mono) !important;
    font-weight: 500 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background: var(--surface-raised) !important;
    color: var(--muted) !important;
    border-bottom: 1px solid var(--line) !important;
}
[data-testid="stDataFrame"] td {
    font-family: var(--font-mono) !important;
    font-size: 0.85rem !important;
    color: var(--ink) !important;
}

/* ═══════════════════════════════════════════
   IMAGES
   ═══════════════════════════════════════════ */
[data-testid="stImage"] { border-radius: var(--radius); overflow: hidden; }
[data-testid="stImage"] img {
    border-radius: var(--radius);
    border: 1px solid var(--line);
    background: var(--surface);
}
[data-testid="stImageCaption"] {
    color: var(--muted) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.74rem !important;
}

/* ═══════════════════════════════════════════
   CODE BLOCKS
   ═══════════════════════════════════════════ */
[data-testid="stCodeBlock"] {
    border: 1px solid var(--line) !important;
    border-radius: var(--radius-sm) !important;
    background: var(--surface-raised) !important;
}

/* ═══════════════════════════════════════════
   TABS
   ═══════════════════════════════════════════ */
.stTabs [data-baseweb="tab"] {
    min-height: 42px;
    padding: 8px 20px !important;
    font-family: var(--font-body) !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    color: var(--muted) !important;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
    background: transparent !important;
    border-bottom: 2px solid transparent;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--ink) !important;
    background: var(--brand-soft) !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--brand) !important;
    border-bottom-color: var(--brand) !important;
}

/* ═══════════════════════════════════════════
   EXPANDER
   ═══════════════════════════════════════════ */
[data-testid="stExpander"] {
    border: 1px solid var(--line) !important;
    border-radius: var(--radius) !important;
    background: var(--surface) !important;
}
[data-testid="stExpander"] * { color: var(--ink-2); }

/* ═══════════════════════════════════════════
   POPOVER / DROPDOWN
   ═══════════════════════════════════════════ */
[role="listbox"], [data-baseweb="popover"] {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: var(--shadow-lg) !important;
}
[role="option"] {
    color: var(--ink) !important;
    background: var(--surface) !important;
    font-family: var(--font-body) !important;
}
[role="option"]:hover { background: var(--brand-soft) !important; }

/* ═══════════════════════════════════════════
   ALERTS
   ═══════════════════════════════════════════ */
[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--line) !important;
    background: var(--surface) !important;
    font-family: var(--font-body) !important;
}

/* ═══════════════════════════════════════════
   PROGRESS
   ═══════════════════════════════════════════ */
[data-testid="stProgress"] > div > div {
    background: var(--brand) !important;
}

/* ═══════════════════════════════════════════
   CHARTS
   ═══════════════════════════════════════════ */
[data-testid="stArrowVegaLiteChart"],
[data-testid="stPyplotGlobalUseContainer"] {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--radius) !important;
    padding: 20px !important;
}

hr, .stDivider {
    border-color: var(--line) !important;
    margin: 1.5rem 0 !important;
}

.stCaption, .stMarkdown small {
    color: var(--muted) !important;
    font-size: 0.8rem !important;
}

div[data-testid="stVerticalBlock"] { gap: 0.75rem; }

/* ═══════════════════════════════════════════
   RESPONSIVE
   ═══════════════════════════════════════════ */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem 1rem 3rem;
    }
    .fs-hero {
        padding: 22px 20px;
        border-radius: var(--radius);
    }
    .fs-hero__title { font-size: 1.5rem; }
    .section-title { flex-direction: column; align-items: flex-start; gap: 6px; }
    [data-testid="stMetric"] { min-height: 88px; padding: 12px 16px !important; }
    section[data-testid="stSidebar"] {
        width: 100% !important;
        min-width: unset !important;
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

# 注册自定义模块到 ultralytics，使 YOLO() 能识别 MobileNetV3_Backbone 等自定义组件
import custom_models.custom_yolov11_mobilenetv3  # noqa: F401


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

    if not isinstance(data, dict):
        st.error(f"{yaml_path} 内容格式错误：需要 YAML 字典，实际为 {type(data).__name__}")
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


@st.cache_resource(show_spinner=False, max_entries=3)
def load_model_cached(model_path: str, _mtime: float = 0.0):
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
            import hashlib as _hashlib
            zip_fingerprint = _hashlib.sha256(zip_upload.getbuffer()).hexdigest()
            if st.session_state.get(f"{key_prefix}_zip_processed") != zip_fingerprint:
                result = _extract_dataset_zip(zip_upload)
                if result:
                    st.session_state[f"{key_prefix}_zip_processed"] = zip_fingerprint
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
            import hashlib as _hashlib
            yaml_fp = _hashlib.sha256(uploaded.getbuffer()).hexdigest()
            if st.session_state.get(f"{key_prefix}_yaml_processed") != yaml_fp:
                st.session_state[f"{key_prefix}_yaml_processed"] = yaml_fp
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
            import hashlib as _hashlib
            mdl_fp = _hashlib.sha256(uploaded.getbuffer()).hexdigest()
            if st.session_state.get(f"{key_prefix}_mdl_processed") != mdl_fp:
                st.session_state[f"{key_prefix}_mdl_processed"] = mdl_fp
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
        import hashlib as _hashlib
        cfg_fp = _hashlib.sha256(uploaded.getbuffer()).hexdigest()
        if st.session_state.get(f"{key_prefix}_cfg_processed") != cfg_fp:
            st.session_state[f"{key_prefix}_cfg_processed"] = cfg_fp
            uploaded_path = save_uploaded_file(uploaded, "model_configs")
            ui_path_chip(uploaded_path, "已上传模型配置")
            return uploaded_path
        else:
            # 用已保存的路径
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

            # 导出推理结果
            ui_section("导出结果", "打包所有检测结果图片。", "EXPORT")
            import io as _io
            import zipfile as _zipfile
            buf = _io.BytesIO()
            with _zipfile.ZipFile(buf, "w", _zipfile.ZIP_DEFLATED) as zf:
                for i, r in enumerate(results_list):
                    import cv2 as _cv2
                    img_bytes = _cv2.imencode(".jpg", _cv2.cvtColor(r["img"], _cv2.COLOR_RGB2BGR))[1].tobytes()
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

            import cv2
            import numpy as np
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
                if boxes is not None and len(boxes) > 0:
                    cls_ids = boxes.cls.cpu().numpy().astype(int)
                    confs = boxes.conf.cpu().numpy()
                    total_fire += int((cls_ids == 0).sum())
                    total_smoke += int((cls_ids == 1).sum())
                    all_confs.extend(confs.tolist())
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
            import numpy as np
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
            import json as _json
            import io as _io
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


# ═══════════════════════════════════════════
# 页面 4：模型评估
# ═══════════════════════════════════════════

def _get_model_info(model_path: str) -> dict:
    """获取模型的参数量和 FLOPs"""
    import torch
    from ultralytics import YOLO

    model = YOLO(model_path)
    total = sum(p.numel() for p in model.model.parameters())
    params_m = total / 1e6

    flops_g = 0.0
    try:
        from thop import profile
        dummy = torch.randn(1, 3, 640, 640)
        flops, _ = profile(model.model, inputs=(dummy,), verbose=False)
        flops_g = flops / 1e9
    except Exception:
        pass

    return {"params_m": params_m, "flops_g": flops_g}


def _run_eval(model_path: str, data_yaml: str):
    """运行评估，返回指标字典"""
    mtime = os.path.getmtime(model_path)
    model = load_model_cached(model_path, mtime)
    metrics = model.val(data=data_yaml, verbose=False)
    save_dir = getattr(metrics, "save_dir", None)
    return {
        "map50": metrics.box.map50,
        "map50_95": metrics.box.map,
        "precision": metrics.box.mp if hasattr(metrics.box, "mp") else 0.0,
        "recall": metrics.box.mr if hasattr(metrics.box, "mr") else 0.0,
        "save_dir": str(save_dir) if save_dir else "",
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
                plt.close(fig)

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
    """估算显存占用

    基于 MobileNetV3 + Slim-Neck YOLO 检测器架构的经验公式。
    基准：640×640、batch=1、FP16 时激活约 250 MB。
    训练额外计入：梯度(FP32) + Adam 优化器状态(m+v, FP32) + 反向传播中间激活 + 工作区。
    """
    bytes_per_param = 2 if fp16 else 4
    scale = (imgsz / 640) ** 2

    # 模型权重及其运行时结构开销
    model_mb = params_m * bytes_per_param * 1.3

    # 中间激活：按输入面积和 batch 线性缩放
    base_activation_mb = 250 if fp16 else 500
    activation_mb = batch * scale * base_activation_mb

    # CUDA 运行时固定开销（驱动、context、cuDNN workspace、PyTorch 缓存分配器）
    cuda_overhead_mb = 250

    inference_mb = model_mb + activation_mb + cuda_overhead_mb

    # 训练额外显存
    grad_opt_mb = params_m * 4 * 3 * 1.1          # 梯度(FP32) + Adam m(FP32) + Adam v(FP32)
    extra_activation_mb = activation_mb * 1.5      # 反向传播需额外存储的中间值
    train_workspace_mb = 200                        # 训练专有工作区

    training_mb = inference_mb + grad_opt_mb + extra_activation_mb + train_workspace_mb

    return {
        "model_mb": round(model_mb, 1),
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
    source_mode = st.radio("选择来源", ["从模型配置预估", "从已训练模型预估"], horizontal=True, key="hw_source")

    if source_mode == "从模型配置预估":
        target = model_config_selector("hw", "选择模型配置")
    else:
        target = model_selector("hw", "已训练模型")

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

    # 签名跟踪：目标文件 mtime + 参数，检测变化时清除旧结果
    try:
        cur_sig = f"{target}:{os.path.getmtime(target)}:{imgsz}:{batch}:{fp16_mode}"
    except OSError:
        cur_sig = ""
    if st.session_state.get("hw_sig") != cur_sig:
        st.session_state["hw_has_result"] = False
        st.session_state["hw_sig"] = cur_sig

    if st.button("开始预估", type="primary", use_container_width=True):
        with st.spinner("正在分析模型..."):
            import torch
            from ultralytics import YOLO

            try:
                model = YOLO(target)
                total = sum(p.numel() for p in model.model.parameters())
                params_m = total / 1e6

                flops_g = 0.0
                try:
                    from thop import profile
                    dummy = torch.randn(1, 3, imgsz, imgsz)
                    flops, _ = profile(model.model, inputs=(dummy,), verbose=False)
                    flops_g = flops / 1e9
                except Exception:
                    pass

                memory = estimate_memory(params_m, imgsz, batch, fp16_mode)

                st.session_state["hw_params_m"] = params_m
                st.session_state["hw_flops_g"] = flops_g
                st.session_state["hw_memory"] = memory
                st.session_state["hw_saved_imgsz"] = imgsz
                st.session_state["hw_saved_batch"] = batch
                st.session_state["hw_saved_fp16"] = fp16_mode
                st.session_state["hw_target"] = target
                st.session_state["hw_has_result"] = True
                st.session_state["hw_sig"] = cur_sig

            except Exception as e:
                st.error(f"模型分析失败: {e}")
                st.session_state["hw_has_result"] = False

    if st.session_state.get("hw_has_result"):
        params_m = st.session_state["hw_params_m"]
        flops_g = st.session_state["hw_flops_g"]
        memory = st.session_state["hw_memory"]
        imgsz = st.session_state["hw_saved_imgsz"]
        batch = st.session_state.get("hw_saved_batch", 1)
        fp16_mode = st.session_state["hw_saved_fp16"]
        target = st.session_state.get("hw_target", "")

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

        # 导出硬件预估报告
        ui_section("导出报告", "将预估结果导出为 JSON 文件。", "EXPORT")
        import json as _json
        import io as _io
        report = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target": target,
            "params_m": round(params_m, 2),
            "flops_g": round(flops_g, 2),
            "imgsz": imgsz,
            "batch": batch,
            "fp16": fp16_mode,
            "memory": memory,
            "compatibility": rows,
        }
        buf = _io.BytesIO()
        buf.write(_json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8"))
        buf.seek(0)
        st.download_button(
            label="下载硬件预估报告 (JSON)", data=buf,
            file_name=f"hardware_est_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )


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
        import shutil as _shutil
        results = []
        export_dir = SCRIPT_DIR / "runs" / "optimize"
        export_dir.mkdir(parents=True, exist_ok=True)
        model_name = Path(target_model).stem

        mtime = os.path.getmtime(target_model)
        model = load_model_cached(target_model, mtime)

        if export_fp16:
            with st.spinner("导出 FP16 ONNX..."):
                try:
                    out = model.export(format="onnx", half=True, imgsz=reduced_imgsz)
                    dest = export_dir / f"{model_name}_fp16_{reduced_imgsz}.onnx"
                    _shutil.copy2(out, dest)
                    out_size = round(os.path.getsize(dest) / 1024 / 1024, 1)
                    results.append(("FP16 ONNX", str(dest), out_size, "通用硬件，半精度"))
                except Exception as e:
                    st.error(f"FP16 导出失败: {e}")

        if export_onnx:
            with st.spinner("导出 FP32 ONNX..."):
                try:
                    out = model.export(format="onnx", half=False, imgsz=reduced_imgsz)
                    dest = export_dir / f"{model_name}_fp32_{reduced_imgsz}.onnx"
                    _shutil.copy2(out, dest)
                    out_size = round(os.path.getsize(dest) / 1024 / 1024, 1)
                    results.append(("FP32 ONNX", str(dest), out_size, "通用跨平台部署"))
                except Exception as e:
                    st.error(f"ONNX 导出失败: {e}")

        if export_int8:
            with st.spinner("导出 INT8 TFLite（需较长时间）..."):
                try:
                    out = model.export(format="tflite", int8=True, imgsz=reduced_imgsz)
                    dest = export_dir / f"{model_name}_int8_{reduced_imgsz}.tflite"
                    _shutil.copy2(out, dest)
                    out_size = round(os.path.getsize(dest) / 1024 / 1024, 1)
                    results.append(("INT8 TFLite", str(dest), out_size, "边缘设备，极致压缩"))
                except Exception as e:
                    st.error(f"INT8 导出失败: {e}。可能需要代表性数据集校准，尝试无量化导出...")
                    try:
                        out = model.export(format="tflite", imgsz=reduced_imgsz)
                        dest = export_dir / f"{model_name}_fp32_{reduced_imgsz}.tflite"
                        _shutil.copy2(out, dest)
                        out_size = round(os.path.getsize(dest) / 1024 / 1024, 1)
                        results.append(("FP32 TFLite", str(dest), out_size, "边缘设备备用"))
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

        # 导出优化汇总
        ui_section("导出优化报告", "将优化结果导出为 JSON 汇总。", "EXPORT")
        import json as _json
        import io as _io
        report = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_model": target_model,
            "original_size_mb": model_size_mb,
            "target_hardware": target_hw,
            "results": [{"format": r[0], "path": r[1], "size_mb": r[2]} for r in results],
        }
        buf = _io.BytesIO()
        buf.write(_json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8"))
        buf.seek(0)
        st.download_button(
            label="下载优化报告 (JSON)", data=buf,
            file_name=f"optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )


# ═══════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════

def _cleanup_old_files():
    """清理过期文件，防止无限累积"""
    import time as _time
    import shutil as _shutil

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

    # runs/detect: 保留最近 5 次训练结果，删除其余
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
        f'<div class="path-chip">工作目录: {escape(str(SCRIPT_DIR))}</div>',
        unsafe_allow_html=True,
    )

    # 刷新缓存按钮
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
