# 前端健壮性代码审查

**日期：** 2025-05-27  
**审查范围：** Streamlit 前端 UI 层  
**审查目标：** 识别健壮性问题和潜在 bug

---

## 1. 状态管理竞态问题

**文件：** `ui/pages/training.py:19-54`

`@st.fragment(run_every=3)` 的训练监控存在竞态风险：
- 进程检测使用 `os.kill(pid, 0)` + `os.waitpid(WNOHANG)`，但 Streamlit 重跑时可能在 `waitpid` 前再次触发 fragment，导致 PID 误判
- `_train_exit_code` 使用 `setdefault` 防重复设置，但 `st.rerun()` 可能在赋值前重入

**建议：** 在 fragment 入口加锁标记，或使用 `threading.Lock` 保护 PID 状态读写。

---

## 2. 批量推理状态机泄漏

**文件：** `ui/pages/inference.py:232-314`

批量推理用 6+ 个 session_state key（`_inf_batch_idx`, `_inf_batch_fire`, `_inf_batch_smoke`, ...）模拟状态机：
- 取消按钮点击后 `st.rerun()`，但 `batch_cancelled` 检查在 rerun 之后，可能导致已处理的图片计数丢失
- `_inf_batch_display` 列表在循环中持续增长，大量图片时内存占用高

**建议：** 封装为 `BatchInferenceState` dataclass，统一序列化到单个 session_state key。

---

## 3. 文件上传指纹碰撞

**文件：** `ui/widgets.py:18-24`

`_check_and_set_fingerprint` 使用 SHA-256 整个文件内容做指纹：
- 大文件（>100MB 模型）每次上传都全量哈希，阻塞 UI
- 指纹仅防重复处理，但不防同内容不同名文件的混淆

**建议：** 对大文件改用文件头/尾采样哈希，或结合文件大小+修改时间。

---

## 4. ZIP 解压路径遍历风险

**文件：** `ui/scanner.py:146-165` + `ui/widgets.py:27-82`

`save_uploaded_file` 使用 `os.replace` 原子写入，但：
- `safe_extract_zip` 解压时未验证目标路径是否在 `UPLOAD_DIR` 内
- 恶意 ZIP 可能包含 `../../etc/passwd` 类路径（虽然 Python zipfile 默认会拒绝，但未显式校验）

**建议：** 解压后遍历所有文件，断言每个路径都在 `UPLOAD_DIR` 下。

---

## 5. 空路径/None 传播

**文件：** 多处选择器函数（`dataset_selector`, `model_selector`）

返回值有时是 `""`，有时是 `None`，调用方混用 `if not path` 和 `if path is None`：
- `ui/pages/dataset.py:23` 检查 `if not yaml_path or not Path(yaml_path).exists()` — 空字符串会触发 `Path("").exists()` 返回 False，不会崩溃但语义不清晰
- `ui/pages/inference.py:51` 同样混用

**建议：** 统一选择器返回空字符串 `""`，文档化约定。

---

## 6. 缺少用户反馈的静默失败

**文件：** `ui/pages/inference.py:261-291`

批量推理循环中 `cv2.imread` 失败时 `continue`，但：
- 无任何 UI 提示（跳过了多少张）
- `results_display` 只保留前 N 张，用户不知道被截断

**建议：** 记录失败计数，在汇总区显示 "跳过 N 张无法读取的图片"。

---

## 7. CSS 变量主题切换失效

**文件：** `ui/theme.py:67-90`

暗色主题使用 `:root.theme-dark` 和 `:root:has(#fs-theme-dark)` 双重选择器，但：
- Streamlit 的 `st.radio` 生成的 DOM ID 不稳定，页面刷新后 `#fs-theme-dark` 可能不存在
- 依赖 `apply_theme_marker` 注入隐藏 div，但该函数在 `main()` 中调用时机晚于 CSS 注入

**建议：** 改用 `data-theme` 属性或 localStorage 持久化主题状态。

---

## 8. 模型加载缓存无上限

**文件：** `ui/scanner.py:168-171`

```python
@st.cache_resource(show_spinner=False, max_entries=3)
def load_model_cached(...)
```

- `max_entries=3` 但 YOLO 模型每个占用 50-200MB 显存
- 清理按钮调用 `.clear()` 清空全部缓存，而非 LRU 淘汰
- 多用户并发时无显存保护

**建议：** 根据可用显存动态调整 `max_entries`，或在加载前检查 `torch.cuda.mem_get_info()`。

---

## 总结

| 问题类型 | 严重程度 | 影响 |
|---------|---------|------|
| 状态竞态 | 中 | 训练监控显示异常 |
| 状态机泄漏 | 低 | 大批量时内存增长 |
| 路径遍历 | 低 | 理论安全风险 |
| 空值传播 | 低 | 偶发 UI 报错 |
| 静默失败 | 中 | 用户困惑 |
| 主题切换 | 低 | 视觉不一致 |
| 缓存无上限 | 中 | 多用户时 OOM |

**核心问题：** 前端健壮性不足主要源于 Streamlit 单页应用的状态管理复杂度。建议优先修复 **状态竞态** 和 **批量推理状态机** 两个问题，其余可后续迭代。
