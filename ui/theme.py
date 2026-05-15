"""CLA 设计语言 · 自定义样式 + 主题标记"""

import streamlit as st

CSS_STYLE = """
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

/* 根级颜色锁死，防止 Streamlit 自身主题穿透 */
html { background: var(--bg); }
body {
    background: var(--bg);
    color: var(--ink);
}
.stApp {
    background: var(--bg);
    color: var(--ink);
}

/* ═══════════════════════════════════════════
   TEXT LOCKDOWN — 防止任何 Streamlit 默认颜色穿透
   ═══════════════════════════════════════════ */
.main .block-container,
.main .block-container p,
.main .block-container span,
.main .block-container div,
.main .block-container li,
.main .block-container label:not([data-baseweb]) {
    color: var(--ink);
}

/* st.markdown 内所有文字 */
[data-testid="stMarkdownContainer"] {
    color: var(--ink) !important;
}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] em {
    color: var(--ink) !important;
}
[data-testid="stMarkdownContainer"] code {
    color: var(--brand) !important;
    background: var(--brand-soft) !important;
}

/* st.caption / small */
.stCaption, .stMarkdown small, small, caption, .caption {
    color: var(--muted) !important;
}

/* st.info / st.success / st.warning / st.error — 保留语义背景但确保文字可读 */
div[data-testid="stAlert"] {
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--ink) !important;
    font-family: var(--font-body) !important;
}
div[data-testid="stAlert"] * {
    color: var(--ink) !important;
}
div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] {
    color: var(--ink) !important;
}

/* 通知 / Toast */
div[data-testid="stNotification"],
div[data-testid="stNotificationContent"],
div[data-testid="stToast"],
div[data-testid="stToastContainer"] {
    color: var(--ink) !important;
    background: var(--surface) !important;
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
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stCaption *,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] small {
    color: var(--sidebar-muted) !important;
}

/* 侧边栏 radio 内文字强制可见 */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] label *,
[data-testid="stSidebar"] [role="radiogroup"] label p,
[data-testid="stSidebar"] [role="radiogroup"] label span {
    color: var(--sidebar-text) !important;
}

/* 侧边栏 divider 文字 */
[data-testid="stSidebar"] hr,
[data-testid="stSidebar"] .stDivider {
    border-color: var(--sidebar-border) !important;
}

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
    color: var(--ink-2) !important;
    font-family: var(--font-mono);
    font-size: 0.76rem;
    overflow-wrap: anywhere;
}

/* ═══════════════════════════════════════════
   TYPOGRAPHY
   ═══════════════════════════════════════════ */
h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
.stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
    font-family: var(--font-display) !important;
    letter-spacing: -0.01em !important;
    color: var(--ink) !important;
}
h1 { font-size: 1.8rem !important; font-weight: 700 !important; }
h2 { font-size: 1.25rem !important; font-weight: 600 !important; }
h3 { font-size: 1.05rem !important; font-weight: 600 !important; color: var(--ink-2) !important; }
h4 { font-size: 1.0rem !important; font-weight: 600 !important; color: var(--ink) !important; }
h5 { font-size: 0.92rem !important; font-weight: 600 !important; color: var(--ink) !important; }
h6 { font-size: 0.85rem !important; font-weight: 600 !important; color: var(--muted) !important; }

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
/* Metric delta（涨幅指示器） */
[data-testid="stMetricDelta"] {
    font-family: var(--font-body) !important;
    font-size: 0.85rem !important;
}
[data-testid="stMetricDelta"] svg { display: none; }
[data-testid="stMetricDelta"][data-testid*="up"] { color: var(--success) !important; }
[data-testid="stMetricDelta"][data-testid*="down"] { color: var(--danger) !important; }

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
textarea {
    color: var(--ink) !important;
    caret-color: var(--brand) !important;
}
/* 输入框内的值（含只读态） */
.stTextInput input[readonly],
.stNumberInput input[readonly],
input:read-only, input[disabled] {
    color: var(--ink) !important;
    -webkit-text-fill-color: var(--ink) !important;
    opacity: 1 !important;
}
.stTextInput input::placeholder,
.stNumberInput input::placeholder,
textarea::placeholder {
    color: var(--faint) !important;
    opacity: 1 !important;
    -webkit-text-fill-color: var(--faint) !important;
}
/* Select 下拉框值 */
.stSelectbox [data-baseweb="select"] *,
.stMultiSelect [data-baseweb="select"] * {
    color: var(--ink) !important;
}
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div,
.stSelectbox [data-baseweb="select"] input,
.stMultiSelect [data-baseweb="select"] input {
    background: var(--surface) !important;
    color: var(--ink) !important;
}
/* Select 下拉选项面板 */
[role="listbox"] [role="option"],
[data-baseweb="popover"] [role="option"] {
    color: var(--ink) !important;
    background: var(--surface) !important;
}
[role="listbox"] [role="option"]:hover,
[data-baseweb="popover"] [role="option"]:hover {
    background: var(--brand-soft) !important;
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
[data-testid="stDataFrame"],
[data-testid="stTable"] {
    border-radius: var(--radius) !important;
    overflow: hidden !important;
    border: 1px solid var(--line) !important;
    box-shadow: none;
    background: var(--surface) !important;
}
[data-testid="stDataFrame"] th,
[data-testid="stTable"] th {
    font-family: var(--font-mono) !important;
    font-weight: 500 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background: var(--surface-raised) !important;
    color: var(--muted) !important;
    border-bottom: 1px solid var(--line) !important;
}
[data-testid="stDataFrame"] td,
[data-testid="stTable"] td {
    font-family: var(--font-mono) !important;
    font-size: 0.85rem !important;
    color: var(--ink) !important;
    background: var(--surface) !important;
}
/* DataFrame 内所有文字后备保护 */
[data-testid="stDataFrame"] *,
[data-testid="stTable"] * {
    color: var(--ink);
}
/* DataFrame 排序图标 */
[data-testid="stDataFrame"] svg { color: var(--muted) !important; }

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
   ALERTS & NOTIFICATIONS（已被 TEXT LOCKDOWN 段覆盖，此处仅保留结构样式）
   ═══════════════════════════════════════════ */
[data-testid="stAlert"],
[data-testid="stNotification"],
[data-testid="stNotificationContent"],
[data-testid="stToast"],
[data-testid="stToastContainer"] {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--line) !important;
    font-family: var(--font-body) !important;
}

/* ═══════════════════════════════════════════
   PROGRESS & SPINNER
   ═══════════════════════════════════════════ */
[data-testid="stProgress"] > div > div {
    background: var(--brand) !important;
}

/* Spinner 文字 */
[data-testid="stSpinner"] {
    color: var(--muted) !important;
    font-family: var(--font-body) !important;
}

/* st.status 容器 */
[data-testid="stStatus"] {
    border: 1px solid var(--line) !important;
    border-radius: var(--radius-sm) !important;
    background: var(--surface) !important;
    color: var(--ink) !important;
    font-family: var(--font-body) !important;
}
[data-testid="stStatus"] * {
    color: var(--ink) !important;
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
"""


def apply_theme_marker(theme_mode: str):
    """插入主题标记，供 CSS :root:has() 选择器切换日/夜间模式变量"""
    marker_map = {
        "白天模式": "fs-theme-light",
        "夜间模式": "fs-theme-dark",
        "跟随系统": "fs-theme-light",  # Streamlit base 已固定为 light，跟随系统默认浅色
    }
    marker = marker_map.get(theme_mode)
    if not marker:
        return

    # 跟随系统时，用前端 JS 检测 OS 偏好并切换标记
    if theme_mode == "跟随系统":
        st.markdown(
            """
            <span id="fs-theme-light" hidden></span>
            <script id="fs-theme-script">
            (function() {
                if (window.__fsThemeBound) return;
                const el = document.getElementById('fs-theme-light');
                if (!el) return;
                const apply = function(e) {
                    const dark = e.matches;
                    if (el) el.id = dark ? 'fs-theme-dark' : 'fs-theme-light';
                };
                const mql = window.matchMedia('(prefers-color-scheme: dark)');
                apply(mql);
                mql.addEventListener('change', apply);
                window.__fsThemeBound = true;
            })();
            </script>
            """,
            unsafe_allow_html=True,
        )
    else:
        # 同时设置 :root 类作为旧浏览器 fallback（不支持 :has() 选择器时回退到类选择器）
        root_class = "theme-dark" if theme_mode == "夜间模式" else "theme-light"
        st.markdown(
            f'<span id="{marker}" hidden></span>'
            f'<script>(function(){{document.documentElement.classList.add("{root_class}");}})();</script>',
            unsafe_allow_html=True,
        )
