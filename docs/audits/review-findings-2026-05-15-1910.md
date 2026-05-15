# Code Review: 全量代码审查 — 文件处理、缓存、持久化、健壮性

Date: 2026-05-15
Scope: `ui/` (21 文件), `engine/` (4 文件), `app.py`, `train.py`
Reviewers: Claude Opus 4.7 + 3 sub-agents (multi-perspective, fresh context)

## Summary

- **Files reviewed:** 25
- **Issues found:** 39 (4 critical, 18 major, 14 minor, 3 nit)
- **Referenced rules:** Security, Resource Management, Error Handling, Data Integrity, Observability, Pattern Consistency

---

## Critical Issues

- [ ] **[DATA] `os.waitpid` 原始状态被误用为退出码** — [`ui/pages/training.py:35,146`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/training.py) — `os.waitpid()` 返回原始 wait status（signal info 编码），而非 `exit()` 传入的退出码。进程 exit(1) 时 raw status = 256 (1<<8)；被 signal 9 杀死时 raw status = 9。代码直接使用 raw status 显示为"退出码"并用于诊断提示（"OOM / 路径错误 / 配置不兼容"），导致错误诊断路径。应为 `os.WEXITSTATUS(status)` 提取真实退出码，`os.WIFSIGNALED` 检测信号致死。

- [ ] **[DATA] `_train_exit_code` 在训练 session 间泄漏** — [`ui/pages/training.py:306-370`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/training.py) — 新训练启动时 `_train_exit_code` 未被清除。若上一次训练的退出码残留（如 fragment 设置的 -1），新训练完成后可能被误报为失败。fragment 中的 guard `if "_train_exit_code" not in st.session_state` 阻止覆盖已存在的值。

- [ ] **[RES] `_cleanup_old_files` 中 `os.path.getmtime()` 无异常保护** — [`app.py:62,75,87`](file:///home/ubt/ml-projects/fireandsomke_detection/app.py) — 若文件在 `iterdir()` 和 `getmtime()` 之间被删除，`FileNotFoundError` 会崩溃整个 `_cleanup_old_files()`，阻止所有后续清理（上传目录、runs 目录、tmp JSON 均不被清理）。此外 `PermissionError` 也会因无权限读取目录而崩溃。

- [ ] **[RES] 上传目录清理仅遍历直接子项，嵌套文件永不清理** — [`app.py:62-69`](file:///home/ubt/ml-projects/fireandsomke_detection/app.py) — `d.iterdir()` 只遍历一级子项。`datasets_extracted/` 内的 `train/images/img001.jpg` 等嵌套文件永远不会被清理条件匹配，磁盘使用随每次 zip 上传无限增长。

---

## Major Issues

- [ ] **[RES] zip 上传指纹锁定后无法重试** — [`ui/widgets.py:109-115,128-146,232-245`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/widgets.py) — `_check_and_set_fingerprint` 在首次处理时写入 session_state，若 `_extract_dataset_zip` 失败（解压/yaml 异常）指纹不被清除。后续 rerun 指纹匹配成功走 fallback 路径，用户永远无法重试同一文件。影响三个 selector。

- [ ] **[RES] `datasets_extracted` 目录每次解压无条件 `rmtree`** — [`ui/widgets.py:32-33`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/widgets.py) — 多个页面共享同一解压目录，上传第二个数据集时第一个数据集的 yaml 路径失效（图片目录还存在但 yaml 被 rmtree 删除）。无用户确认的数据丢失向量。

- [ ] **[RES] `set_num_interop_threads` 不可逆且调用位置在 try 块之外** — [`engine/benchmark.py:208-210,332-345`](file:///home/ubt/ml-projects/fireandsomke_detection/engine/benchmark.py) — PyTorch 文档声明此函数每进程仅可调用一次，第二次抛出 RuntimeError。调用位于 try 块外（line 332），异常不触发 finally 清理。两次 benchmark 运行（不同 CPU 约束）会在同一 Streamlit session 中崩溃。

- [ ] **[RES] hardware.py 评估循环中 YOLO 模型不释放 GPU 显存** — [`ui/pages/hardware.py:69-95`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/hardware.py) — `YOLO(target)` 在按钮 handler 内创建，无显式 `del model` / `torch.cuda.empty_cache()`。用户重复点击按钮导致 GPU 显存累积增长。

- [ ] **[RES] `training_monitor` 每次调用将完整日志读入内存** — [`engine/training_monitor.py:41-42`](file:///home/ubt/ml-projects/fireandsomke_detection/engine/training_monitor.py) — 对长时间训练（数小时），日志文件可达数百 MB。fragment 每 3 秒调用一次此函数，内存中持续缓冲整个文件。无流式读取或增量解析。

- [ ] **[RES] 训练日志文件截断与 fragment 读取之间的 TOCTOU 竞争** — [`ui/pages/training.py:352-359`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/training.py) — `open(log_path, "w")` 截断文件后 subprocess 尚未写入，fragment 可能在 3 秒窗口内读到空/半写入文件。无文件锁或原子写入方案。

- [ ] **[DATA] `yaml.dump` 覆盖原始 data.yaml 丢失注释和格式** — [`ui/widgets.py:85-86`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/widgets.py) — 路径修复后 `yaml.dump(ydata, f)` 覆盖提取的 yaml，丢失原始文件中的所有注释和键顺序。不可恢复的数据修改。

- [ ] **[ERR] evaluation 精度/召回率零值显示为 "---" 但 F1 正常计算** — [`ui/pages/evaluation.py:65-67`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/evaluation.py) — `if eval_result['precision']` 将浮点 `0.0` 视为假值显示 "---"，而 F1 仍用原始 0.0 计算。显示不一致（"---" vs "0.0000"）。

- [ ] **[ERR] evaluation 对比模式手动路径自动选择失效** — [`ui/pages/evaluation.py:233-240`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/evaluation.py) — `st.multiselect` 返回值是临时拷贝，`.append()` 修改无持久效果。手动输入的模型路径永不会被自动选中。

- [ ] **[ERR] Fragment 内 `time.sleep(2)` 阻塞 Streamlit 单线程事件循环** — [`ui/pages/training.py:92`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/training.py) — 停止按钮 handler 中 `time.sleep(2)` 阻塞整个 script 线程 2 秒，期间所有 UI 冻结。

- [ ] **[ERR] Fragment 与 page_training 的 `os.waitpid` 双重 reap 竞态** — [`ui/pages/training.py:29-38,143-148`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/training.py) — fragment 和 page_training 两个路径对同一 PID 调用 `os.waitpid()`。谁先 reap 对方就返回 -1，退出码可能丢失。

- [ ] **[ERR] `st.rerun(scope="app")` 从 fragment 内触发可能无法正确全页重载** — [`ui/pages/training.py:41,98`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/training.py) — 当 `st.rerun(scope="app")` 从 `@st.fragment` 内触发时，不同 Streamlit 版本语义不一致。若未正确升级，cleanup 代码永不被执行，session_state 残留 `_train_running=True`。

- [ ] **[SEC] PID 重用导致误杀无关进程** — [`ui/pages/training.py:27-30,122-127`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/training.py) — 训练进程退出后 `_train_pid` 不清理。若 OS 将同一 PID 分配给新进程，`os.kill(train_pid, 0)` 误报存活，"停止训练" 按钮会向无关进程发送 SIGTERM/SIGKILL。

- [ ] **[DATA] `os.waitpid(0, ...)` 无 guard 可能 reap 任意子进程** — [`ui/pages/training.py:146`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/training.py) — 若 `_train_pid` 为 0（session state 损坏），`os.waitpid(0, os.WNOHANG)` 意味着 "等待任意子进程"，可能 reap 其他页面的 subprocess 并丢失其状态。

- [ ] **[DATA] `_train_exit_code` 在最后一个 epoch 被覆盖为 0** — [`engine/training_monitor.py:125-136`](file:///home/ubt/ml-projects/fireandsomke_detection/engine/training_monitor.py) — 当 `remaining_epochs=0`（最后一轮），`global_eta = eta_seconds + sec_per_epoch * (0-1)` 可能为负，`max(0, ...)` 把正确的 epoch 级 ETA 覆盖为 0。

- [ ] **[RES] `_train_start_time` time.time() 默认值每次 fragment 执行重新评估但永不被存储** — [`ui/pages/training.py:46`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/training.py) — `get("_train_start_time", time.time())` 的默认值在每次 fragment 运行时都会被评估（~每 3 秒），但从未存储回 session_state。若 key 缺失且多次调用间有延迟，start_ts 不断变化导致 ETA 计算不一致。

- [ ] **[OBS] `training_status` session key 无前缀，存在跨页碰撞风险** — [`ui/pages/training.py:44,151,154,163,299,308,313,369`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/training.py) — 多数训练相关键使用 `_train_`/`_tr_` 前缀，`training_status` 是例外。若其他页面加入同名键，碰撞后状态污染难以排查。

- [ ] **[OBS] `scan_model_configs` 仅过滤 `.venv`，`scan_datasets`/`scan_models` 无类似过滤** — [`ui/scanner.py:93` vs `17-49,52-75`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/scanner.py) — 不一致的路径过滤导致 venv 中的 YOLO pt 文件或被误列在模型列表中。

---

## Minor Issues

- [ ] **[ERR] `_extract_dataset_zip` 内 yaml 异常未捕获** — [`ui/widgets.py:51-86`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/widgets.py) — `yaml.safe_load(f)` 的异常会使整个函数崩溃，错误以 Streamlit 回溯呈现而非友好提示。
- [ ] **[ERR] 手动输入路径无验证** — [`ui/widgets.py:167,211,264`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/widgets.py) — `text_input` 返回的路径被直接接受和持久化，不检查文件是否存在。
- [ ] **[ERR] hardware.py `except Exception: pass` 吞没 THOP profiling 的所有异常** — [`ui/pages/hardware.py:82-83`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/hardware.py) — `flops_g = 0.0` 且无任何指示 profiling 失败。
- [ ] **[ERR] `_parse_eta` 不处理 `HH:MM:SS` 格式** — [`engine/training_monitor.py:141-152`](file:///home/ubt/ml-projects/fireandsomke_detection/engine/training_monitor.py) — `"1:2:3"` 仅解析为 62 秒，秒部分被丢弃。
- [ ] **[ERR] `_format_eta` 不显示天数** — [`engine/training_monitor.py:155-165`](file:///home/ubt/ml-projects/fireandsomke_detection/engine/training_monitor.py) — 数天训练只显示 `XhXXm`，缺 `Xd` 单位。
- [ ] **[ERR] `subprocess.Popen` 异常未处理** — [`ui/pages/training.py:354-358`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/training.py) — 若 Popen 失败，`_train_running=True` 已写入 session_state 但进程不存在。
- [ ] **[ERR] `_cleanup_old_files` eval_results 中 `f.unlink()` 对子目录触发 IsADirectoryError** — [`app.py:44`](file:///home/ubt/ml-projects/fireandsomke_detection/app.py) — `eval_results/` 若包含子目录，`unlink()` 失败（虽当前仅有文件）。
- [ ] **[ERR] benchmark MPS OOM 错误分支不可达** — [`engine/benchmark.py:415-418`](file:///home/ubt/ml-projects/fireandsomke_detection/engine/benchmark.py) — `elif "MPS" in str(e)` 被前置的 `if "out of memory"` 覆盖，MPS OOM 专用消息永远不会展示。
- [ ] **[ERR] benchmark 内存测量上限硬编码为 10** — [`engine/benchmark.py:370-371`](file:///home/ubt/ml-projects/fireandsomke_detection/engine/benchmark.py) — `min(num_measure, 10)` 无视调用者传入的 `num_measure` 参数。
- [ ] **[ERR] CPU 模式下 benchmark 内存 headroom 计算错误** — [`engine/benchmark.py:381-382`](file:///home/ubt/ml-projects/fireandsomke_detection/engine/benchmark.py) — GPU 显存约束与 CPU 推理混用，headroom 值无意义。
- [ ] **[RES] `st.cache_data(ttl=10)` TTL 对设备检测和配置扫描过短** — [`ui/scanner.py:17,52,78,169`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/scanner.py) — GPU 设备信息在 session 期间几乎不变，10 秒 TTL 导致不必要的重复计算。
- [ ] **[RES] tmp*.json glob 匹配范围过大** — [`app.py:98`](file:///home/ubt/ml-projects/fireandsomke_detection/app.py) — `SCRIPT_DIR.glob("tmp*.json")` 可能误删用户数据文件。缺少命名空间前缀。
- [ ] **[OBS] `cleanup_old_files` 仅在启动时执行一次** — [`app.py:106-108`](file:///home/ubt/ml-projects/fireandsomke_detection/app.py) — 长时间运行的 Streamlit session 中文件永不清理。
- [ ] **[OBS] benchmark session key 使用 `engine/` 斜杠前缀，与全局 `hw_` 下划线风格不一致** — [`ui/pages/hardware_benchmark.py:181-197`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/hardware_benchmark.py) — 增加了键冲突风险和不一致性。

---

## Nit

- [ ] `uploaded.getbuffer()` 在指纹已处理时仍被调用 — [`ui/widgets.py:110,129,193,233`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/widgets.py) — 大文件每次渲染都复制全量字节 SHA256 哈希，可用 `uploaded.file_id` 替代。
- [ ] FP16 在 CPU 模式下静默禁用无用户提示 — [`ui/pages/hardware_benchmark.py:192`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/hardware_benchmark.py)
- [ ] `_apply_preset` 闭包隐式捕获 `st.session_state` 脆弱 — [`ui/pages/training.py:216-219`](file:///home/ubt/ml-projects/fireandsomke_detection/ui/pages/training.py)

---

## Rules Applied

- Security Principles — PID reuse, zip slip
- Resource Management — file I/O, GPU memory, subprocess reaping
- Error Handling Principles — exception swallowing, TOCTOU, fail-silent branches
- Data Integrity — session state leakage, raw status vs exit code
- Observability — key naming conventions, stale state cleanup, cache TTL strategy
- Pattern Consistency — cross-page section usage, label language, session key prefixes

## Appendix: Positive Observations

1. **CSS 主题系统** (`ui/theme.py`, 907 行) 完整覆盖所有 Streamlit 原生控件，响应式 + dark mode 完善
2. **`ui_page_header` / `ui_section` / `ui_path_chip`** 三大共享组件使所有页面视觉高度一致
3. **签名跟踪模式** 在 evaluation / hardware / inference 中一致用于输入变化检测和过期结果清除
4. **`_extract_dataset_zip` 三种路径修复策略** 对 Roboflow / Kaggle 常见 zip 问题覆盖良好
5. **`save_uploaded_file` 原子写入** (mkstemp + os.replace) 防部分写入
6. **`@st.fragment(run_every=3)`** 有效消除训练进度刷新的整页闪烁
7. **zip slip 基础防护** 已存在（虽有小缺陷），展示了安全意识
