---
name: jianying-editor
description: 剪映 (JianYing) AI自动化剪辑的高级封装 API (JyWrapper)，提供开箱即用的 Python 接口，支持录屏、素材导入、字幕生成、Web 动效合成及项目导出。全面适配 MacOS (Apple Silicon/Intel) 与 Windows，支持 v5.9+ (draft_info.json) 架构、工程自修复、智能配音字幕及录屏变焦。
---

# JianYing Editor Skill

## 自动分流：TikTok 电商短视频

当用户提出以下类型的请求时，先读取并执行
[通用 TikTok 电商剪辑 Skill](skills/tiktok-commerce-video-editor/SKILL.md)：

- 制作或批量制作 TikTok / TikTok Shop 带货视频
- 需要商品展示、达人开场、卖点步骤、印尼语字幕、网感节奏、动态元素或带货收尾
- 用户提供了商品素材、参考视频、参考动效或背景音乐，希望按内容完成短视频

该子 Skill 是通用流程，不假设产品、素材顺序、语言、市场或音乐固定为某个项目。第一次剪辑时按对话流程询问音乐；不要要求普通创作者手动编辑 JSON。

如果用户只是要求普通剪映剪辑、草稿生成、字幕、配音、转场或导出，不涉及 TikTok 电商带货，则继续使用本 Skill 后面的常规规则。

安装本仓库后，两套能力会同时可用：本文件负责剪映底层编辑能力，子 Skill 负责通用 TikTok 电商成片流程。不要把子 Skill 的示例项目规则当作默认产品规则。

Use this skill when the user wants to automate video editing, generate drafts, or manipulate media assets in JianYing Pro.

Agent execution playbook: [docs/agent-playbook.md](docs/agent-playbook.md)
Minimal command SOP: [docs/minimal-command-sop.md](docs/minimal-command-sop.md)
Natural language usage guide: [usage.md](usage.md)
Draft inspector CLI:
`python <SKILL_ROOT>/scripts/draft_inspector.py list --limit 20`
`python <SKILL_ROOT>/scripts/draft_inspector.py summary --name "DraftName"`
`python <SKILL_ROOT>/scripts/draft_inspector.py show --name "DraftName" --kind content --json`
For generic editing requests, always follow the "Quick Edit Runtime Template" and "Acceptance Checklist" in that playbook.

## 🔍 环境自检（动手前先跑一遍）

```
python <SKILL_ROOT>/scripts/env_doctor.py
```

一次性确认：剪映版本、草稿目录、`ffmpeg/ffprobe`、Python 依赖，以及**自动导出是否可用**。
输出为一句话结论表。加 `--json` 拿机器可读结果。
出现任何问题先按它给的建议补齐环境，再开始剪辑。

## ⚠️ 版本兼容矩阵（本机实测）

| 能力 | 实现方式 | 剪映 5.9~6.x | 剪映 10.x |
| --- | --- | --- | --- |
| 生成/编辑草稿（素材、文字、字幕、音效、关键帧、复合片段） | 纯写草稿 JSON 文件 | ✅ | ✅ **已实测可用**（10.5.0.13988） |
| 自动导出 MP4 | UI Automation 控件定位 | ✅ | ❌ **不可用** |
| 直接渲染最终 MP4 | 本机 FFmpeg/FFprobe | ✅ | ✅ **不依赖剪映导出界面** |

**为什么 10.x 不能自动导出**：剪映 10.x 前端改为 QML，已不对外暴露 accessibility 树
（UIA 有效节点数 0~1，原生 MSAA `accChildCount` 也返回 0）。原实现靠
`HomePageDraftTitle:`、`MainWindowTitleBarExportBtn`、`ExportOkBtn` 等控件名定位，
在 10.x 上永远找不到。这是剪映版本层面的限制，**改控件名无法绕过**。

在 10.x 上因此也失效的派生能力：`script/project_base.py` 的工程锁自动释放
（`_try_release_project_lock`）——它被 try/except 包住不会崩，只是会提示手动切回首页。

**10.x 上的推荐姿势**：草稿全程由 Skill 生成；需要自动得到 MP4 时，优先使用本机 FFmpeg 直接渲染。
如果必须使用剪映 10.x 内置导出界面，仍需手动点「导出」；5.9 及更低版本才适合使用原有 UI 自动导出脚本。

## 🧩 本机增强（10.5 适配补丁，非上游自带）

以下能力是在 **剪映 10.5.0.13988 / Windows** 上实测补齐的。上游 `git pull` 会覆盖，
需按 [docs/local-patches-jianying-10x.md](docs/local-patches-jianying-10x.md) 重打。

| 主题 | 文档 / 工具 | 解决什么 |
| --- | --- | --- |
| 10.x 补丁总览与重打步骤 | [docs/local-patches-jianying-10x.md](docs/local-patches-jianying-10x.md) | 草稿元数据自愈、双写 `draft_content.json`、导出预检、环境自检 |
| **字幕字号/位置标定** | [docs/subtitle-calibration.md](docs/subtitle-calibration.md) | `TextStyle.size` / `transform_y` 无官方像素说明，实测给出换算公式 |
| **GUI 自动化（10.x 无 accessibility）** | `scripts/tools/jy_gui.py` | 激活 / 截图 / 点击 / 拖拽 / 按键，全靠坐标 |
| **收藏贴纸 → 可用素材** | `scripts/tools/sticker_to_overlay.py` | 贴纸无法程序化写入草稿，改为渲染成带 alpha 的 overlay 视频 |
| 字幕标定草稿生成 | `scripts/tools/subtitle_calib.py` | 一键生成 4 条不同参数字幕，用于实测标定 |

### 字幕参数速查（Poppins_Bold / 1080×1920 画布）

```
白字高(px)     = 7.5 + 2.4 × size
画面高度百分比 = 49.76 − 49.8 × transform_y
```

常用取值：`size=16 / transform_y=-0.39` → 字高 46px、画面 69%
（对齐印尼 TikTok 达人素材的内嵌字幕）。

**注意**：全大写文本比句子式宽 15~20%，长文案建议开
`auto_wrapping=True, max_line_width=0.86` 让它自动换行。

### 10.x 上做不了的事

**贴纸（sticker）无法程序化写入草稿** —— 剪映 10.5 会把草稿写成私有加密格式，
拿不到它写入贴纸所需的完整元数据（写进 `materials.stickers` 后界面不显示）。
替代方案：`sticker_to_overlay.py` 把贴纸资产渲染成 overlay 视频，
但会**丢失贴纸自带的动画**；要保留动态效果只能在剪映界面里手动拖。

## 🚨 重要开发原则 (CRITICAL DEVELOPER RULES)
1.  **脚本位置**：**禁止在 Skill 内部目录创建剪辑脚本**。所有的剪辑逻辑实现代码（`.py` 脚本）必须存放在用户当前项目的**根目录**（或子目录，如 `scripts/`），以保持 Skill 库的纯净和可移植性。
2.  **版本与架构**：
    - **双平台适配**：已全面支持 MacOS (路径探测/录屏) 与 Windows。
    - **Auto-healing**：支持 v5.9+ (`draft_info.json`)。若草稿损坏或版本冲突，使用 `overwrite=True` 初始化 `JyProject` 可触发自动修复。
3.  **配乐选择**：
    - **简单演示使用默认音乐**。实际项目，应优先检索并推荐 `data/cloud_music_library.csv` 中的相关曲目，或根据视频主题（如“科技”、“温暖”）进行关键词过滤。
    - 询问用户：“我发现了几首符合主题的云端音乐，要不要试试？（如：`Illuminate` - 科技感）”。

##  规则指南 (Rules)

Read the individual rule files for specific tasks and constraints:

- [rules/setup.md](rules/setup.md) - **Mandatory** initialization code for all scripts.
- [rules/core.md](rules/core.md) - Core operations: Saving, Exporting, and Draft management.
- [rules/cli.md](rules/cli.md) - CLI contracts and machine-readable output conventions.
- [rules/media.md](rules/media.md) - Importing assets & **AI Video Analysis Optimization (30m/360p)**.
- [rules/text.md](rules/text.md) - Adding Subtitles, Text, and Captions.
- [rules/keyframes.md](rules/keyframes.md) - **Advanced**: Adding Keyframe animations.
- [rules/effects.md](rules/effects.md) - Searching for and applying Filters, Effects, and Transitions.
- [rules/recording.md](rules/recording.md) - **New**: Screen Recording & Smart Zoom automation.
- [rules/web-vfx.md](rules/web-vfx.md) - Advanced: Web-to-Video generation.
- [rules/generative.md](rules/generative.md) - Chain of Thought for generative editing.
- [rules/audio-voice.md](rules/audio-voice.md) - **New**: TTS Voiceover & BGM sourcing.

## 🎯 Agent Quick Routing

- 云端视频 + 云端音乐：`rules/media.md` + `rules/audio-voice.md` -> `examples/cloud_video_music_tts_demo.py`
- 智能配音与字幕 (Script-to-Video)：`rules/text.md` + `rules/audio-voice.md` -> 核心 API `add_narrated_subtitles`
- 旁白与字幕对齐：`rules/text.md` + `rules/audio-voice.md` -> `examples/cloud_video_music_tts_demo.py`
- 录屏与智能变焦：`rules/recording.md` -> `tools/recording/recorder.py`
- 批量导出/无头导出：`rules/core.md` + `rules/cli.md` -> `examples/robust_auto_export.py`
- 影视解说生成：`rules/generative.md` -> `scripts/movie_commentary_builder.py`

## 📖 经典示例 (Examples)

Refer to these for complete workflows:
- [examples/my_first_vlog.py](examples/my_first_vlog.py) - A complete vlog creation demo with background music and animated text.
- [examples/simple_clip_demo.py](examples/simple_clip_demo.py) - Quick-start tutorial for basic cutting and track management.
- [examples/compound_clip_demo.py](examples/compound_clip_demo.py) - **New**: Professional nested project (Compound Clip) automation.
- [examples/cloud_video_music_tts_demo.py](examples/cloud_video_music_tts_demo.py) - Cloud video + cloud BGM + TTS/subtitle alignment.
- [examples/web_to_video_intro_demo.py](examples/web_to_video_intro_demo.py) - Web-to-Video intro demo (HTML animation -> timeline clip).
- [examples/robust_auto_export.py](examples/robust_auto_export.py) - Stable export workflow and failure handling.
- [examples/auto_exposure_align_demo.py](examples/auto_exposure_align_demo.py) - CV-assisted exposure alignment workflow.
- [examples/video_transcribe_and_match.py](examples/video_transcribe_and_match.py) - **Advanced**: AI-driven workflow (Transcribe Video -> Match B-Roll via AI semantics -> Assemble Draft).

## 🧠 提示词与集成工具 (Prompts & Integrated Tools)

Use these templates and scripts for complex tasks:
- **Asset Search**: Find filters, transitions, and animations by Chinese/English name:
  ```bash
  python <SKILL_ROOT>/scripts/asset_search.py "复古" -c filters
  ```
- **Movie Commentary Builder**: Generate 60s commentary videos from a storyboard JSON:
  ```bash
  python <SKILL_ROOT>/scripts/movie_commentary_builder.py --video "video.mp4" --json "storyboard.json"
  ```
- **Sync Native Assets**: Import your favorited/played BGM/Styles from JianYing App to the Skill:
  ```bash
  python <SKILL_ROOT>/scripts/sync_jy_assets.py
  # Index cloud materials from your existing drafts
  python <SKILL_ROOT>/scripts/build_cloud_music_library.py
  python <SKILL_ROOT>/scripts/build_cloud_text_styles_library.py
  ```
- **README to Tutorial**: Convert a project's README.md into a full installation tutorial video script:
  - Read prompt: `prompts/readme_to_tutorial.md`
  - Inject content into `{{README_CONTENT}}` variable
- **Screen Recorder & Smart Zoom**: Record your screen and auto-apply zoom keyframes:
  ```bash
  python <SKILL_ROOT>/tools/recording/recorder.py
  # Web preview capture (high performance)
  python <SKILL_ROOT>/scripts/web_recorder.py --url "http://localhost:3000" --duration 5
  # Or apply zoom to existing video:
  python <SKILL_ROOT>/scripts/jy_wrapper.py apply-zoom --name "Project" --video "v.mp4" --json "e.json"
  ```
- **Draft Inspector**: Examine draft structure and metadata (v5.9+ support):
  ```bash
  python <SKILL_ROOT>/scripts/draft_inspector.py list --limit 20
  python <SKILL_ROOT>/scripts/draft_inspector.py summary --name "DraftName"
  ```
- **Auto Exporter**: Headless export of a draft to MP4/SRT:
  ```bash
  python <SKILL_ROOT>/scripts/auto_exporter.py "DraftName" "output.mp4" --res 1080 --fps 60
  # For SRT only:
  python <SKILL_ROOT>/scripts/jy_wrapper.py export-srt --name "DraftName"
  ```
- **Template Clone & Replacer**: 安全克隆模板并批量替换物料 (防止损坏原模板):
  ```bash
  # 克隆模板生成新项目
  python <SKILL_ROOT>/scripts/jy_wrapper.py clone --template "酒店模板" --name "客户A_副本"
  ```
- **API Validator**: Run a quick diagnostic of your environment:
  ```bash
  python <SKILL_ROOT>/scripts/api_validator.py
  ```

## 🚀 快速开始示例

```python
import os
import sys

# 1. 环境初始化 (必须同步到脚本开头，支持 Win/Mac)
current_dir = os.path.dirname(os.path.abspath(__file__))
env_root = os.getenv("JY_SKILL_ROOT", "").strip()
# 探测 Skill 路径 (支持 Antigravity, Trae, Claude 等)
skill_root = next((p for p in [
    env_root,
    os.path.join(current_dir, ".agent", "skills", "jianying-editor"),
    os.path.join(current_dir, ".trae", "skills", "jianying-editor"),
    os.path.join(current_dir, ".claude", "skills", "jianying-editor"),
    os.path.join(current_dir, "skills", "jianying-editor"),
    os.path.abspath(".agent/skills/jianying-editor"),
    os.path.abspath(".trae/skills/jianying-editor"),
    os.path.abspath(".claude/skills/jianying-editor"),
    os.path.abspath("skills/jianying-editor"),
    os.path.dirname(current_dir)
] if p and os.path.exists(os.path.join(p, "scripts", "jy_wrapper.py"))), None)

if not skill_root: raise ImportError("Could not find jianying-editor skill root.")
sys.path.insert(0, os.path.join(skill_root, "scripts"))
from jy_wrapper import JyProject

if __name__ == "__main__":
    # 2. 初始化工程 (支持 v5.9+ 及自修复)
    project = JyProject("New AI Video", overwrite=True)
    assets_dir = os.path.join(skill_root, "assets")

    # 3. 智能配音与字幕 (One-click Script-to-Video)
    project.add_narrated_subtitles(
        text="欢迎使用剪映自动化 Skill。这是一个全面适配 MacOS 的进阶版本。",
        speaker="zh_female_xiaopengyou"
    )

    # 4. 导入额外素材
    project.add_media_safe(os.path.join(assets_dir, "video.mp4"), "0s")
    project.add_media_safe(os.path.join(assets_dir, "audio.mp3"), "0s", track_name="Audio")

    # 5. 添加带动画的标题
    project.add_text_simple("剪映自动化开启", start_time="1s", duration="3s", anim_in="复古打字机")

    project.save()
```

## 🛠️ 初始化与项目规范 (Initialization & Project Rules)

在初始化 `JyProject` 时，请务必根据主视频素材的比例设置分辨率。**默认值为横屏 (1920x1080)**。

### 🚨 脚本存放位置规范
**禁止在 Skill 安装目录下创建你的业务剪辑脚本**。
- **正确做法**：将你的剪辑 Python 脚本放在项目的根目录。
- **原因**：Skill 目录应该只包含工具集源码，便于后续 `git pull` 升级。业务代码混入会导致版本管理混乱。
