# Changelog

## v1.6.0+local.10x - 2026-09-12（本机适配，非上游发布）

在 **剪映 10.5.0.13988 / Windows 11** 上实测并补齐的适配，未合并到上游。
`git pull` 后会丢失，需按 `docs/local-patches-jianying-10x.md` 重打。

- **剪映 10.x 兼容**：
  - `create_draft()` 写入真实草稿元数据，不再完全依赖剪映启动自愈
  - 保存时镜像 `draft_content.json`（10.x 索引指向它）
  - `export_draft()` 增加 accessibility 预检，不可用时立即报错而非干等 20 分钟
  - `auto_exporter.py` 返回独立错误码 `ui_automation_unavailable`
  - 新增 `scripts/env_doctor.py` 环境自检
- **新增文档**：
  - `docs/subtitle-calibration.md`：字幕 `size` / `transform_y` 的实测像素换算公式
  - `docs/local-patches-jianying-10x.md`：补丁清单 + GUI 操作姿势 + 重打步骤
- **新增工具**（`scripts/tools/`）：
  - `jy_gui.py`：无 accessibility 时的坐标级 GUI 自动化（激活/截图/点击/拖拽/按键）
  - `sticker_to_overlay.py`：剪映收藏贴纸 → 带 alpha 的 ProRes 4444 overlay 视频
  - `subtitle_calib.py`：字幕标定草稿生成器
- **跨机器安装（新增）**：
  - `scripts/utils/jy_paths.py`：**跨平台路径自动探测**（剪映安装位置/草稿目录/
    ffmpeg/贴纸缓存），支持 Windows + macOS，可用 `JY_*` 环境变量覆盖。
    换电脑不用改任何代码。
  - `scripts/setup/install.py`：一键安装/自检，支持注册到
    Claude Code / WorkBuddy / Codex / Trae / Antigravity，
    并为项目内安装自动生成 `AGENTS.md`。
  - `INSTALL.md`：新机器安装与配置指南；README 增加快速安装入口。
- **文档脱敏**：清除全部本机硬编码路径，改为环境变量 / 占位符。
- **已知限制**：贴纸无法程序化写入 10.5 草稿（草稿被存成私有加密格式）；
  替代方案见 `sticker_to_overlay.py`，但会丢失贴纸动画。

## v1.6.0 - 2026-04-19
- **Core Enhancements**:
  - **Intelligent TTS (Narrated Subtitles)**: Unified `add_narrated_subtitles` API for one-click script-to-video workflow.
  - **Auto-healing System**: Modernized draft generator to support `draft_info.json` (v5.9+) and automatic repair of corrupted projects.
- **MacOS Compatibility**:
  - Full path resolution for Apple Silicon and Intel Macs.
  - Integrated `avfoundation` for high-performance screen recording on macOS.
- **Ecosystem Tools**:
  - `build_cloud_music_library.py`: Automated scanning of local drafts to index used cloud assets.
  - `web_recorder.py`: Pro-grade recording engine for web-based VFX assets.
- **Bug Fixes & API Polish**:
  - Fixed `pyJianYingDraft` export issues for `Transition`, `Filter`, and `Mask`.
  - Refactored `VfxOpsMixin` to use correct segment-level API calls.
  - Improved error handling for cloud music fallbacks.

## v1.5.0 - 2026-03-04
- Security hardening:
  - sanitized draft project names and blocked path traversal/out-of-root delete.
  - restored TLS verification for SAMI TTS by default.
  - added cloud download URL/header/size guards.
- API/CLI standardization:
  - unified machine-readable `--json` output for key scripts.
  - added strict mode for validator (`--strict`).
  - centralized runtime config (`scripts/utils/config.py`).
- Quality engineering:
  - expanded unit tests for security guards.
  - added repo hygiene and data schema checks.
  - added CI lint/format/test/schema pipeline.
- Repo organization:
  - removed tracked runtime artifacts and cache binaries.
  - added compatibility wrappers and common logger utility.
