# 安装与配置（任意电脑 / 任意 AI 编辑器）

> 目标：在**一台新电脑**上装好这个 skill，然后就能用 Codex、Claude Code、Cursor、
> Trae、WorkBuddy 等任意支持 skill / AGENTS.md 的 agent 驱动剪映自动剪辑。
>
> **全程不用改代码**——所有平台路径由 `scripts/utils/jy_paths.py` 自动探测。

---

## 一、前置条件

| 项 | 要求 | 说明 |
| --- | --- | --- |
| 操作系统 | **Windows 10/11**（推荐） | macOS 可生成草稿，但未完整验证 |
| 剪映专业版 | **5.9 ~ 10.x** | 10.x 能生成草稿，但**不能自动导出**（见下方「已知限制」） |
| Python | **3.9+** | 建议 3.10 以上 |
| ffmpeg / ffprobe | 装在 PATH 里 | 用于读时长、合成素材；不装的话草稿生成受限 |
| 剪映登录 | 需要登录账号 | 否则打开草稿会受限 |

### 剪映版本怎么选

- **要全自动导出** → 装剪映 **5.9 或更低**（`uiautomation` 能定位导出按钮）
- **只用来自动生成草稿、手动点导出** → 10.x 也可以，本仓库已适配

---

## 二、安装（三步）

### 1. 拿到代码

```bash
git clone https://github.com/<你的用户名>/jianying-editor-10x.git
cd jianying-editor-10x
```

### 2. 装 Python 依赖

```bash
python scripts/setup/install.py --deps
```

（等价于 `pip install -r requirements.txt`）

### 3. 自检 + 注册到你的编辑器

```bash
# 先看环境探测结果，确认剪映/ffmpeg/草稿目录都找到了
python scripts/setup/install.py --check
```

输出应该像这样：

```
✅ 剪映安装      : D:\JianyingPro\JianyingPro.exe
✅ 剪映版本      : 10.5.0.13988
✅ 草稿目录      : C:\Users\你\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft
✅ ffmpeg        : ...
✅ ffprobe       : ...
✅ 依赖齐全
自检结论: 全部通过 ✅
```

确认无误后，按你用的编辑器选一条：

```bash
# Claude Code（装到用户级，所有项目可用）
python scripts/setup/install.py --editor claude

# WorkBuddy
python scripts/setup/install.py --editor workbuddy

# Codex / Cursor / Trae 等（装到某个项目里，并在项目根生成 AGENTS.md）
python scripts/setup/install.py --editor codex  --project "D:\my-video"
python scripts/setup/install.py --editor trae   --project "D:\my-video"
python scripts/setup/install.py --editor agent  --project "D:\my-video"
```

---

## 三、各编辑器怎么用

### Claude Code

装到 `~/.claude/skills/jianying-editor` 后，直接说需求即可，例如：

> 帮我把 D:\素材 里的视频按顺序拼成一条，加中文字幕，输出到剪映草稿

Claude Code 会自动读到 `SKILL.md`。

### Codex / Cursor / Trae（走 AGENTS.md）

`--editor codex --project <目录>` 会在项目根生成 `AGENTS.md`，
里面写明了 skill 位置、使用约定和自检命令。

在项目里对话时说：

> 用 jianying-editor skill，把素材目录里的片段合成一条 30 秒的成片

agent 会按 `AGENTS.md` 的指引去读 `SKILL.md`。

### WorkBuddy

装到 `~/.workbuddy/skills/jianying-editor`，之后在对话里提需求即可。

### 通用兜底（任何 agent 都能用）

不想装到编辑器目录，也可以**直接跑命令行**：

```bash
# 环境自检
python <SKILL_ROOT>/scripts/env_doctor.py

# 看本机剪映/ffmpeg 探测结果
python <SKILL_ROOT>/scripts/utils/jy_paths.py

# 列出现有草稿
python <SKILL_ROOT>/scripts/draft_inspector.py list --limit 20

# 列出现有收藏的贴纸
python <SKILL_ROOT>/scripts/tools/sticker_to_overlay.py --list
```

把 `<SKILL_ROOT>` 换成实际路径，或者设环境变量 `JY_SKILL_ROOT`。

---

## 四、环境变量（只在自动探测失败时才需要）

| 变量 | 用途 | 默认探测 |
| --- | --- | --- |
| `JY_SKILL_ROOT` | skill 根目录 | 从脚本位置向上找 |
| `JY_DRAFT_ROOT` | 剪映草稿根目录 | `%LOCALAPPDATA%\JianyingPro\...` |
| `JY_INSTALL_DIR` | 剪映安装目录 | `C:~\JianyingPro`、注册表、常见盘符 |
| `JY_FFMPEG` | ffmpeg 可执行文件 | PATH |
| `JY_EFFECT_CACHE` | 贴纸缓存目录 | `User Data/Cache/artistEffect` |

Windows 临时设置：

```powershell
$env:JY_DRAFT_ROOT = "E:\JianyingPro\User Data\Projects\com.lveditor.draft"
```

永久设置：`系统属性 → 高级 → 环境变量`。

macOS：

```bash
export JY_DRAFT_ROOT="$HOME/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
```

---

## 五、已知限制（重要）

### 1. 剪映 10.x 不能自动导出

10.x 前端改成 QML，**不暴露 accessibility 树**（UIA 有效节点数为 0），
原实现靠控件名定位导出按钮，在 10.x 上永远找不到。

| 探测方式 | 结果 |
| --- | --- |
| UIA 遍历剪映窗口 | 0 个有效节点 |
| 原生 MSAA `accChildCount` | 0 |
| 对照：微信 / 记事本 | 17 / 35 个节点（证明 UIA 本身正常） |

**所以流程是**：skill 全自动生成草稿 → 你打开剪映手动点「导出」。

想全自动导出，只有两条路：装剪映 5.9，或用图像识别重写导出链路。

### 2. 贴纸无法程序化写入草稿

剪映 10.x 会把草稿存成**私有加密格式**，拿不到写入贴纸所需的完整元数据
（写进 `materials.stickers` 后界面不显示）。

替代方案是把贴纸资产渲染成 overlay 视频：

```bash
python <SKILL_ROOT>/scripts/tools/sticker_to_overlay.py --list
python <SKILL_ROOT>/scripts/tools/sticker_to_overlay.py \
    --sticker <resource_id> --out ./out/sticker.mov --mirror vertical
```

**但会丢失贴纸自带的动画**。要保留动态效果，只能在剪映界面里手动拖。

### 3. 剪映保存过的草稿不要再用脚本改

剪映编辑并保存后，`draft_content.json` 会变成加密格式，无法再用 JSON 解析。
要改草稿就先用 skill 重新生成，别去改剪映存过的那份。

---

## 六、常见问题

**Q: 自检说找不到剪映**
装好剪映专业版，或设 `JY_INSTALL_DIR` 指向安装目录。

**Q: 自检说找不到草稿目录**
先在剪映里新建或打开一个草稿（让它生成目录），或设 `JY_DRAFT_ROOT`。

**Q: 生成了草稿但剪映列表里看不到**
1. 确认草稿目录和剪映用的是同一个（有多用户/多盘符时容易错）
2. 重启剪映，它会重新扫描草稿目录
3. 检查草稿名不要含特殊字符

**Q: 找不到 ffmpeg**
Windows 下载官方 builds 解压后把 `bin` 加进 PATH；
macOS `brew install ffmpeg`。或设 `JY_FFMPEG`。

**Q: 贴纸列表是空的**
先在剪映里打开「贴纸 → 我的 → 收藏」浏览一遍，让它把素材下载到本地缓存。

---

## 七、升级

本仓库是上游 [`luoluoluo22/jianying-editor-skill`](https://github.com/luoluoluo22/jianying-editor-skill)
的 **10.x 适配分支**。上游更新时：

```bash
git remote add upstream https://github.com/luoluoluo22/jianying-editor-skill.git
git fetch upstream
git merge upstream/main     # 注意：10.x 补丁可能冲突，需按 docs/local-patches-jianying-10x.md 重打
```

本仓库新增的补丁与工具清单见
[docs/local-patches-jianying-10x.md](docs/local-patches-jianying-10x.md)。
