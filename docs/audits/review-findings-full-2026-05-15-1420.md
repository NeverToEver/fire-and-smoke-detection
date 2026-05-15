# Code Review: 火焰烟雾检测平台 — 全量审查

Date: 2026-05-15
Reviewer: AI Agent (fresh context)

## Summary

- **Files reviewed:** 19 Python files
- **Issues found:** 20 (0 critical, 6 major, 7 minor, 7 nit)
- **Zero security vulnerabilities detected**

---

## Major Issues

### M1. [OBS] 项目完全缺失日志系统

- **文件:** 全部 19 个 .py 文件
- **严重:** 无 `import logging`、无日志记录
- 训练通过 subprocess 执行但未有结构化日志，模型评估、文件操作均无记录，出问题时难以回溯。

### M2. [ERR] `gui/resources.py:43,68-70,88-89` — 空 except 静默吞错误

```python
# scan_datasets() L43:
except Exception:
    pass

# scan_models() L68-70:
except Exception:
    pass

# scan_model_configs() L88-89:
except Exception:
    pass
```

损坏的 YAML、权限错误等全部静默跳过。应至少记录 warning。

### M3. [ERR] `gui/utils.py:73-79` — FLOPs 计算失败时静默返回 0

```python
try:
    from thop import profile
    ...
    flops_g = flops / 1e9
except Exception:
    pass  # flops_g stays 0.0, user never knows it failed
```

### M4. [ERR] `gui/utils.py:84-97` — `_run_eval` 无异常处理

`model.val()` 失败时异常直接传播到 UI 层，缺少中间层的错误上下文（模型路径、数据集路径、时间戳）。

### M5. [OBS] `gui/pages/training.py:228-233` — 训练子进程无退出码检查

```python
process = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT, ...)
```

stderr 合并入 stdout，子进程崩溃时无退出码监控。若进程被 OOM Killer 杀死，用户只看到"日志窗口"无输出，不知道发生了什么。

### M6. [ARCH] `gui/utils.py` — `_run_eval` / `_get_model_info` 命名以 `_` 开头表示私有

但在 `gui/pages/evaluation.py:11` 被直接导入使用：
```python
from gui.utils import _get_model_info, _run_eval
```

违反 Python 命名约定，要么是公共 API 就应该去掉 `_` 前缀。

---

## Minor Issues

### N1. [PAT] `gui/pages/hardware.py:182-454` — `render_benchmark_ui` 在页面模块中占 270 行

硬体模拟 UI 逻辑内嵌在页面模块，应提取到 `hw_bench.py` 或独立的 `gui/pages/hardware_bench.py`。

### N2. [PAT] `gui/selectors.py` — 三处重复的 fingerprint + session_state 模式

`dataset_selector` (L100-108, L123-143)、`model_selector` (L190-201)、`model_config_selector` (L233-243) 有完全相同的模式：
```python
fp = hashlib.sha256(...).hexdigest()
if st.session_state.get(key) != fp:
    st.session_state[key] = fp
    # process...
else:
    return persisted
```
可抽取为 decorator 或 helper 函数。

### N3. [PAT] `estimate_memory` 在两处独立定义

- `hw_bench.py:113-134` — `estimate_memory()`
- `gui/utils.py:100-122` — `estimate_memory()`

两处实现完全一致。修改时需手动同步，容易漂移。`gui/utils.py` 版本应删除并从 `hw_bench` 导入。

### N4. [ARCH] `custom_yolov11_mobilenetv3` 三层重导出

```
__init__.py (root)
  → custom_yolov11_mobilenetv3.py (root)
    → models/__init__.py
      → custom_yolov11_mobilenetv3.py (actual impl)
```

三层包装对单一模块过度。根级 `__init__.py` 和 `custom_yolov11_mobilenetv3.py` 可合并。

### N5. [PAT] `gui/pages/inference.py` — import 分散在函数体内

`import cv2` 出现在 L63, L174; `import numpy as np` 出现在 L64, L175, L245。应全部移到文件顶部。

### N6. [CFG] `train.py:14-26` — 训练超参数硬编码

epochs=150, batch=8, imgsz=640, lr0=0.01 等均为硬编码。CLI 仅暴露 `--data` 和 `--model`。

### N7. [ERR] `gui/resources.py:134-135` — `save_uploaded_file` 非原子写入

```python
with open(target_path, "wb") as f:
    f.write(uploaded_file.getbuffer())
```

若写入期间进程崩溃，目标文件为部分写入状态。应先写临时文件再 rename。

---

## Nit

### T1. `gui/pages/dataset.py:100` — `import cv2` 在 for 循环内部

### T2. `gui/pages/evaluation.py` — `from io import BytesIO` 和 `import matplotlib.pyplot as plt` 在两处重复导入 (L84-85, L275-276)

### T3. `gui/pages/hardware.py:426-453` — 多余的空行（函数间 3-4 个空行）

### T4. `hw_bench.py:298-304` — 使用 `locals()` 做资源清理

```python
for _var in ("model", "dummy"):
    v = locals().get(_var)
    if v is not None:
        del v
```

`locals()` 在 CPython 中修改不可靠。应用显式的 `del model, dummy`。

### T5. `app.py:105-178` — `main()` 函数 73 行，所有页面路由 + sidebar 渲染 / cleanup 逻辑均在一个函数

### T6. `gui/selectors.py:100` — `import hashlib as _hashlib` 重复导入 3 次（L100, L122, L189, L232）

### T7. `gui/theme.py` — `apply_theme_marker` 的 JS payload 在每次 Streamlit re-run 时重新注入 `<script>` 标签，累计产生多个 DOM 监听器

---

## Dimensions Covered (Zero-Findings Guard Attestation)

| Dimension | Examined | Result |
|-----------|----------|--------|
| **Security (secrets)** | All 19 files + .gitignore | No hardcoded credentials, `.streamlit/secrets.toml` in .gitignore ✅ |
| **Security (injection)** | `gui/selectors.py` (zip slip), `gui/theme.py` (escape usage) | Zip path validated via `.resolve()`; html.escape used for all user input ✅ |
| **Security (auth)** | Full codebase | This is a local-only research tool, no auth required ✅ |
| **Data integrity** | `gui/resources.py` file ops, `app.py` cleanup | No transactional writes on uploads; cleanup has OSError guards ✅ |
| **Resource leaks** | `hw_bench.py` finally block, `subprocess.Popen` in training.py | GPU cleanup exists but fragile; subprocess never waited/checked ✅ |
| **Architecture** | 19 files, 5 packages | `gui/` modularized well; root `__init__`/`custom_yolov11_mobilenetv3.py` redundant ✅ |
| **Testing** | Search for `test_*`, `*_test*`, `unittest`, `pytest` | Zero tests found ❌ |
| **Dependencies** | `requirements.txt` | All pinned with >= lower bounds, no upper bounds ⚠️ |
| **Configuration** | `.streamlit/config.toml`, `train.py` args | Streamlit theme configured; training params mostly hardcoded ✅ |

---

## Rules Applied

- Security Principles (secrets, injection, auth)
- Error Handling Principles (empty catch, silent failures)
- Architectural Pattern (layering, public/private boundaries)
- Code Organization (duplication, module size, import hygiene)
- Logging and Observability Mandate (logging, error context)
