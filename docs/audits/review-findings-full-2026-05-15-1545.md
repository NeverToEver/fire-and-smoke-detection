# Code Review: 全量审查（重构后）

Date: 2026-05-15
Reviewer: 3 AI Agents (independent review)

## Summary

- **Files reviewed:** 21 Python files
- **Issues found:** 24 (2 fatal, 8 high, 14 medium, low/nit omitted for brevity)
- **New since last review:** 重构引入的 `datetime` 缺失导入、GPU 选择逻辑 bug
- **Security:** zip slip 部分缓解、无硬编码密钥 ✅

---

## P0 · Fatal (运行时崩毁)

### P0-1. `training.py` — `datetime` 未导入，训练完成时 `NameError`

- **文件:** `ui/pages/training.py:121, 285`
- `datetime.now().strftime(...)` 被调用但 `datetime` 从未导入。
- 触发条件：训练结束→显示训练曲线+下载按钮→页面崩溃。

**修复:** 文件顶部添加 `from datetime import datetime`。

---

## P1 · High

### P1-1. `training.py` — GPU 设备选择逻辑 bug

- **文件:** `ui/pages/training.py:166-177`
- 循环内对每个 GPU 判断 `device_info["mps_available"]`，若为 True 则全部标记为 MPS，产生重复选项。
- 第 175 行 `device_labels[option] = "cuda"`：当 CUDA/MPS 均不可用时仍设为 `"cuda"`，训练崩溃。

### P1-2. `inference.py` — `cls_ids` 跨作用域引用

- **文件:** `ui/pages/inference.py:189-203`
- `cls_ids` 在 `if boxes is not None` 内定义，外层第 200-201 行通过三元表达式守卫访问。当前不会报错但极其脆弱，重构易崩。

### P1-3. `benchmark.py` — 模型加载失败错误标记为 OOM

- **文件:** `engine/benchmark.py:302-305`
- 模型加载异常设 `result["oom"] = True`，导致 UI 显示 "OOM" 而实为加载失败，误导排查方向。

### P1-4. `yolo_mobilenet.py` — Monkey-patch `tasks.__dict__` 极其脆弱

- **文件:** `models/yolo_mobilenet.py:143-148`
- 直接修改 ultralytics 内部 `__dict__`，库升级后可能静默失效。应注册后显式验证。

### P1-5. `train.py` — 训练入口无错误处理

- **文件:** `train.py:24-37`
- YAML 加载失败、训练 OOM、数据路径不存在等异常直接传播，无用户友好提示。

### P1-6. `image_utils.py` — `draw_boxes_cv2` 静默吞所有异常

- **文件:** `ui/image_utils.py:48-49`
- `except Exception: pass` — 标注损坏/格式错误完全不可见。

### P1-7. `theme.py` — 旧浏览器深色模式完全失效

- **文件:** `ui/theme.py:68`
- `:has(#fs-theme-dark)` 在 Chrome<105 / Safari<15.4 不支持。代码备选方案 `:root.theme-dark` 无代码设置该类，深色模式静默失效。

### P1-8. `yolo_mobilenet.py` — 可变默认参数

- **文件:** `models/yolo_mobilenet.py:79`
- `def __init__(self, ch=[24, 40, 80, 160])` 为 Python 反模式。

---

## P2 · Medium

| # | 问题 | 位置 |
|---|------|------|
| M1 | 死 session state 键 `{key_prefix}_mode`，设置但从未读取 | `ui/widgets.py:98` |
| M2 | `open()` 缺 `encoding='utf-8'`，非 UTF-8 平台 YAML 损坏（6处） | `ui/scanner.py:34,85,100`, `ui/widgets.py:51,85` |
| M3 | `benchmark.py` 重复函数 `_reset_cuda_stats` / `_reset_cuda_and_cache` | `engine/benchmark.py:213-220` |
| M4 | `benchmark.py` psutil 导入无 ImportError 保护，MPS 内存信息静默丢失 | `engine/benchmark.py:61` |
| M5 | `generate_charts()` KeyError 风险 — `[]` 应改为 `.get()` | `engine/benchmark.py:513,569` |
| M6 | 内存/FPS 测量迭代数不一致 — 内存硬编码 min(50,10)=10 | `engine/benchmark.py:366,383` |
| M7 | `HARDWARE_PROFILES` 与 `PRESET_PROFILES` 重复定义，字段不同 | `ui/image_utils.py:119-168` vs `engine/benchmark.py:442-486` |
| M8 | `ui/__init__.py` 旧文档字符串 "GUI 包" | `ui/__init__.py:1` |
| M9 | `_get_model_info` / `_run_eval` 向后兼容别名无人使用 | `ui/image_utils.py:111-112` |
| M10 | `evaluation.py` 死导入 `load_model_cached` | `ui/pages/evaluation.py:18` |
| M11 | `optimization.py` 重复导入 `shutil` | `ui/pages/optimization.py:5,88` |
| M12 | `_train_exit_code` session state 泄漏到下次训练 | `ui/pages/training.py:38-43,91-96` |
| M13 | 指纹未命中时 session state 无 fallback，返回空字符串 | `ui/widgets.py:116-119` |
| M14 | MPS 峰值内存度量不准 — `driver_allocated_memory()` 非 peak 值 | `engine/benchmark.py:133-138` |

---

## Dimensions Covered

| Dimension | Status |
|-----------|--------|
| Security (secrets, injection, auth) | ✅ 无硬编码密钥, XSS 通过 `html.escape` 防护, zip slip 有路径检查但可加固 |
| Data integrity | ⚠️ YAML 写入缺 encoding, 非原子写入已修复 |
| Error handling | ❌ 3 处 `except:pass`, train.py 无错误处理, datetime 缺失导致崩溃 |
| Observability | ⚠️ logging 已接入但覆盖不全 (draw_boxes_cv2, save_uploaded_file 等未记日志) |
| Architecture | ⚠️ monkey-patch 注册脆弱, 旧浏览器深色模式失效 |
| Configuration | ⚠️ 硬编码魔法数字散落, 分页/chunk 常量分散在多文件 |

---

## Rules Applied

- Security Principles (injection, XSS, zip slip)
- Error Handling Principles (empty catch, silent failures, unguarded access)
- Architectural Pattern (monkey-patch, mutable defaults, dead code)
- Code Organization (session state hygiene, import cleanliness, naming consistency)
