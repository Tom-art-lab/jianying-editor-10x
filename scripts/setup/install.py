# -*- coding: utf-8 -*-
"""剪映 10.x Skill 一键安装 / 自检。

设计目标：**换一台电脑，一条命令装完**，支持 Claude Code / Codex / Cursor /
Trae / Antigravity / WorkBuddy 等。

用法：
    python scripts/setup/install.py --check
        只做环境自检，不改任何文件

    python scripts/setup/install.py --editor claude
        注册到 Claude Code（~/.claude/skills/jianying-editor）

    python scripts/setup/install.py --editor agents --project "D:\\my-video"
        在项目里生成 AGENTS.md + .agent/skills/ 副本（Codex / Cursor / Trae 通用）

    python scripts/setup/install.py --editor workbuddy
        注册到 WorkBuddy（~/.workbuddy/skills/jianying-editor）

    python scripts/setup/install.py --deps
        只安装 Python 依赖

不加 --editor 时等价于 --check。
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))          # scripts/setup
SKILL_ROOT = os.path.dirname(os.path.dirname(_HERE))        # skill 根目录
sys.path.insert(0, os.path.join(SKILL_ROOT, "scripts", "utils"))

try:
    import jy_paths
except ImportError:
    jy_paths = None


EDITOR_TARGETS = {
    "claude":     ("~/.claude/skills/jianying-editor",      "Claude Code"),
    "workbuddy":  ("~/.workbuddy/skills/jianying-editor",   "WorkBuddy"),
    "trae":       (".trae/skills/jianying-editor",          "Trae（项目内）"),
    "agent":      (".agent/skills/jianying-editor",         "Antigravity / 通用 .agent（项目内）"),
    "codex":      (".codex/skills/jianying-editor",         "Codex（项目内）"),
}

AGENTS_MD = """# AGENTS.md —— 剪映自动剪辑 Skill 接入说明

本项目已接入 **jianying-editor** skill（剪映 AI 自动化剪辑）。
任何支持 AGENTS.md 约定的 agent（Codex / Cursor / Trae / Claude Code 等）都按下述方式使用。

## Skill 位置

- 项目内副本：`{copy_path}`
- 入口文档：`{copy_path}/SKILL.md`
- 环境自检：`python {copy_path}/scripts/env_doctor.py`

## 使用约定

1. **动手前先跑环境自检**，确认草稿目录、ffmpeg、剪映版本：
   ```bash
   python {copy_path}/scripts/env_doctor.py
   ```
2. 涉及脚本编写时，先读 `{copy_path}/SKILL.md` 和
   `{copy_path}/docs/agent-playbook.md` 里的 Quick Edit Runtime Template。
3. **剪辑脚本写在业务项目根目录**，不要写进 skill 目录。
4. 剪映 **10.x 上自动导出不可用**（前端 QML 不暴露 accessibility）。
   草稿生成后需要**人工在剪映里点导出**。
   细节见 `{copy_path}/docs/local-patches-jianying-10x.md`。
5. 字幕字号/位置有实测换算公式，直接套用，不要凭感觉填：
   见 `{copy_path}/docs/subtitle-calibration.md`

## 快速开始

```bash
# 1) 自检环境
python {copy_path}/scripts/env_doctor.py

# 2) 看剪映安装与草稿目录探测结果
python {copy_path}/scripts/utils/jy_paths.py

# 3) 列出现有草稿
python {copy_path}/scripts/draft_inspector.py list --limit 20
```

## 环境变量（可选，探测失败时才需要）

| 变量 | 用途 |
| --- | --- |
| `JY_SKILL_ROOT` | skill 根目录（脚本自动探测失败时指定） |
| `JY_DRAFT_ROOT` | 剪映草稿根目录 |
| `JY_INSTALL_DIR` | 剪映安装目录 |
| `JY_FFMPEG` | ffmpeg 可执行文件路径 |
| `JY_EFFECT_CACHE` | 剪映贴纸缓存目录（`Cache/artistEffect`） |
"""


def log(msg: str):
    print(msg, flush=True)


def do_check() -> bool:
    log("=" * 62)
    log("环境自检")
    log("=" * 62)

    ok = True
    log(f"skill 根目录 : {SKILL_ROOT}")
    log(f"Python       : {sys.version.split()[0]}  ({sys.executable})")
    if sys.version_info < (3, 9):
        log("  ⚠ Python 版本偏低，建议 3.9+")
        ok = False

    if jy_paths:
        d = jy_paths.diagnose()
        checks = [
            ("剪映安装", d["jianying_exe"], True),
            ("剪映版本", d["jianying_version"], False),
            ("草稿目录", d["draft_root"], True),
            ("ffmpeg", d["ffmpeg"], True),
            ("ffprobe", d["ffprobe"], True),
        ]
        for label, value, required in checks:
            mark = "✅" if value else ("❌" if required else "–")
            log(f"{mark} {label:10}: {value or '未找到'}")
            if required and not value:
                ok = False
        if d["effect_cache"] if "effect_cache" in d else False:
            pass
        cache = jy_paths.find_effect_cache_dir()
        log(f"{'✅' if cache else '–'} 贴纸缓存    : {cache or '未找到（用到贴纸时才会需要）'}")
    else:
        log("⚠ 未能加载 jy_paths（scripts/utils 目录异常）")
        ok = False

    # 关键依赖
    missing = []
    for mod, pkg in [("PIL", "Pillow"), ("uiautomation", "uiautomation"),
                     ("requests", "requests"), ("psutil", "psutil")]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        log(f"⚠ 缺少依赖: {', '.join(missing)}   → 跑 --deps 安装")
        ok = False
    else:
        log("✅ Python 依赖  : 齐全")

    log("")
    log("自检结论: " + ("全部通过 ✅" if ok else "存在问题，见上面标注 ⚠/❌"))
    return ok


def do_deps() -> bool:
    req = os.path.join(SKILL_ROOT, "requirements.txt")
    if not os.path.isfile(req):
        log(f"⚠ 未找到 {req}，改为安装核心依赖")
        pkgs = ["Pillow", "uiautomation", "requests", "psutil", "numpy"]
    else:
        pkgs = ["-r", req]
    log(f"安装依赖: {' '.join(pkgs)}")
    r = subprocess.run([sys.executable, "-m", "pip", "install", *pkgs],
                       capture_output=True, text=True)
    if r.returncode != 0:
        log(r.stdout[-1500:])
        log(r.stderr[-1500:])
        log("❌ 依赖安装失败")
        return False
    log("✅ 依赖安装完成")
    return True


def _copy_tree(src: str, dst: str) -> None:
    """复制 skill；已存在则先清空目标（只动目标目录，不碰源）。"""
    if os.path.abspath(src) == os.path.abspath(dst):
        log("  ℹ 目标与源相同，跳过复制")
        return
    if os.path.isdir(dst):
        shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copytree(src, dst,
                    ignore=shutil.ignore_patterns(
                        "__pycache__", "*.pyc", ".git", "*.mov", "*_tmp"))


def do_install(editor: str, project: str | None) -> bool:
    if editor not in EDITOR_TARGETS:
        log(f"❌ 未知 editor: {editor}（可选: {', '.join(EDITOR_TARGETS)}）")
        return False

    rel, name = EDITOR_TARGETS[editor]
    if rel.startswith("~"):
        dst = os.path.expanduser(rel)
        in_project = False
    else:
        base = project or os.getcwd()
        dst = os.path.join(base, rel)
        in_project = True

    log("=" * 62)
    log(f"安装到 {name}")
    log("=" * 62)
    log(f"目标: {dst}")

    _copy_tree(SKILL_ROOT, dst)
    log(f"✅ 已复制 {sum(len(f) for _, _, f in os.walk(dst))} 个文件")

    # 项目内安装时，额外生成 AGENTS.md（Codex / Cursor 等靠它发现 skill）
    if in_project:
        agents = os.path.join(project or os.getcwd(), "AGENTS.md")
        copy_path = os.path.join(".", rel).replace("\\", "/")
        content = AGENTS_MD.format(copy_path=copy_path)
        if os.path.exists(agents):
            with open(agents, "r+", encoding="utf-8") as f:
                old = f.read()
                if "jianying-editor" not in old:
                    f.seek(0, os.SEEK_END)
                    f.write("\n\n" + content)
                    log(f"✅ 已追加到已有 AGENTS.md: {agents}")
                else:
                    log(f"ℹ AGENTS.md 里已有 jianying-editor 段落，未重复写入")
        else:
            with open(agents, "w", encoding="utf-8") as f:
                f.write(content)
            log(f"✅ 已生成 {agents}")

    log("")
    log("下一步:")
    log(f"  python \"{os.path.join(dst, 'scripts', 'env_doctor.py')}\"")
    return True


def main():
    ap = argparse.ArgumentParser(
        description="剪映 10.x Skill 一键安装 / 自检",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="只做环境自检")
    ap.add_argument("--deps", action="store_true", help="只安装 Python 依赖")
    ap.add_argument("--editor", choices=list(EDITOR_TARGETS),
                    help="注册到哪个编辑器/agent")
    ap.add_argument("--project", help="项目目录（editor 为项目内类型时使用，默认当前目录）")
    args = ap.parse_args()

    results = []
    if args.deps:
        results.append(do_deps())
    if args.editor:
        results.append(do_install(args.editor, args.project))
    if args.check or (not args.deps and not args.editor):
        results.append(do_check())

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
