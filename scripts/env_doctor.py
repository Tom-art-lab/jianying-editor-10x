# -*- coding: utf-8 -*-
"""剪映自动化环境自检（本地补丁 · 适配剪映 10.x）

一次性回答："这台机器上，这个 Skill 到底哪些能干、哪些不能干？"

用法：
    python scripts/env_doctor.py
    python scripts/env_doctor.py --json
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

REQUIRED_PKGS = [
    ("uiautomation", "uiautomation"),
    ("psutil", "psutil"),
    ("requests", "requests"),
    ("numpy", "numpy"),
    ("PIL", "pillow"),
    ("pymediainfo", "pymediainfo"),
    ("edge_tts", "edge-tts"),
]

OPTIONAL_PKGS = [
    ("playwright", "playwright"),
    ("cv2", "opencv-python"),
    ("pynput", "pynput"),
    ("imageio", "imageio"),
]


def _drafts_root():
    try:
        from utils.formatters import get_default_drafts_root

        return get_default_drafts_root()
    except Exception:
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            return os.path.join(
                local, "JianyingPro", "User Data", "Projects", "com.lveditor.draft"
            )
        return ""


def find_jianying_install():
    """在常见位置找剪映主程序，返回 (exe_path, version)。"""
    local = os.environ.get("LOCALAPPDATA", "")
    patterns = [
        os.path.join(local, "JianyingPro", "Apps", "*", "JianyingPro.exe"),
        os.path.join(local, "JianyingPro", "Apps", "**", "JianyingPro.exe"),
        r"D:\JianyingPro\*\JianyingPro.exe",
        r"C:\JianyingPro\*\JianyingPro.exe",
        r"D:\Program Files\JianyingPro\*\JianyingPro.exe",
        r"C:\Program Files\JianyingPro\*\JianyingPro.exe",
        os.path.join(local, "Programs", "JianyingPro", "JianyingPro.exe"),
    ]
    cands = []
    for p in patterns:
        cands.extend(glob.glob(p, recursive=True))
    if not cands:
        return None, None

    def ver_key(p):
        import re

        m = re.search(r"(\d+\.\d+\.\d+\.\d+)", p)
        if m:
            return tuple(int(x) for x in m.group(1).split("."))
        return (0, 0, 0, 0)

    best = max(cands, key=ver_key)
    import re

    m = re.search(r"(\d+\.\d+\.\d+\.\d+)", best)
    return best, (m.group(1) if m else None)


def jianying_running():
    try:
        import psutil

        names = []
        for p in psutil.process_iter(["name"]):
            n = (p.info.get("name") or "").lower()
            if "jianyingpro" in n:
                names.append(p.info["name"])
        return len(names) > 0
    except Exception:
        return None


def probe_uia(max_depth=6, limit=400):
    """探测剪映窗口是否暴露可用的 UI Automation 树。

    注意：不能用"是否有子控件"判断。实测剪映 10.5 的编辑页窗口
    (MainWindow_QMLTYPE_*) 会返回 1 个残留子控件，但整棵树里没有任何
    可定位的业务控件；首页窗口 (HomePage_QMLTYPE_*) 则为 0。
    因此按整棵树的有效节点数判定。
    """
    res = {
        "available": False,
        "window_found": False,
        "class_name": None,
        "child_count": None,
        "node_count": 0,
        "text_controls": 0,
    }
    try:
        import uiautomation as uia

        uia.SetGlobalSearchTimeout(0.8)
        try:
            uia.SetProcessDpiAwareness(2)
        except Exception:
            pass
        root = uia.GetRootControl()
        win = None
        for w in root.GetChildren():
            if (w.Name or "") == "剪映专业版":
                win = w
                break
        if win is None:
            return res
        res["window_found"] = True
        res["class_name"] = win.ClassName
        res["child_count"] = len(win.GetChildren())

        n = 0
        texts = 0
        for ctrl, _d in uia.WalkControl(win, maxDepth=max_depth):
            n += 1
            if ctrl.ControlTypeName == "TextControl":
                texts += 1
            if n >= limit:
                break
        res["node_count"] = n
        res["text_controls"] = texts

        # 自动导出需要能按 full_description 定位到较深的控件；
        # 有效节点数过少即意味着控件树未被暴露。
        res["available"] = n >= 10
    except Exception as e:
        res["error"] = str(e)
    return res


def collect():
    import platform

    info = {"python": sys.version.split()[0], "platform": platform.platform()}

    exe, ver = find_jianying_install()
    info["jianying_exe"] = exe
    info["jianying_version"] = ver
    info["jianying_running"] = jianying_running()

    root = _drafts_root()
    info["drafts_root"] = root
    info["drafts_root_exists"] = os.path.isdir(root)
    drafts = []
    if info["drafts_root_exists"]:
        try:
            drafts = [
                d
                for d in os.listdir(root)
                if os.path.isdir(os.path.join(root, d)) and not d.startswith(".")
            ]
        except Exception:
            pass
    info["draft_count"] = len(drafts)
    info["drafts"] = sorted(drafts)[:10]

    info["ffmpeg"] = shutil.which("ffmpeg")
    info["ffprobe"] = shutil.which("ffprobe")

    missing, present = [], []
    for mod, pkg in REQUIRED_PKGS:
        try:
            __import__(mod)
            present.append(pkg)
        except Exception:
            missing.append(pkg)
    info["required_pkgs_present"] = present
    info["required_pkgs_missing"] = missing

    opt_missing, opt_present = [], []
    for mod, pkg in OPTIONAL_PKGS:
        try:
            __import__(mod)
            opt_present.append(pkg)
        except Exception:
            opt_missing.append(pkg)
    info["optional_pkgs_present"] = opt_present
    info["optional_pkgs_missing"] = opt_missing

    info["uia"] = probe_uia()

    # ---- 判定 ----
    major = None
    if ver:
        try:
            major = int(ver.split(".")[0])
        except Exception:
            major = None
    info["jianying_major"] = major

    auto_export = False
    uia_res = info["uia"]
    if not uia_res.get("window_found"):
        reason = "未找到剪映窗口（剪映未运行），无法探测 UI Automation"
    elif uia_res.get("available"):
        auto_export = True
        reason = f"控件树有效节点 {uia_res.get('node_count')} 个"
    else:
        reason = (
            f"剪映未暴露 accessibility 树（窗口 {uia_res.get('class_name')}，"
            f"有效节点 {uia_res.get('node_count')} 个）"
        )
    info["auto_export_available"] = auto_export
    info["auto_export_reason"] = reason
    info["draft_generation_available"] = info["drafts_root_exists"] and not missing
    return info


def render(info):
    ok = lambda b: "✅" if b else "❌"  # noqa: E731
    L = []
    L.append("# 剪映自动化环境自检\n")
    L.append(f"- Python: `{info['python']}`")
    L.append(f"- 系统: `{info['platform']}`\n")

    L.append("## 剪映")
    L.append(f"- 版本: **{info['jianying_version'] or '未探测到'}**"
             + (f"（主版本 {info['jianying_major']}）" if info["jianying_major"] else ""))
    L.append(f"- 程序路径: `{info['jianying_exe'] or '未找到'}`")
    L.append(f"- 是否运行中: {ok(info['jianying_running'])} {info['jianying_running']}\n")

    L.append("## 草稿目录")
    L.append(f"- 路径: `{info['drafts_root'] or '未找到'}`")
    L.append(f"- 存在: {ok(info['drafts_root_exists'])}   已有草稿: {info['draft_count']} 个")
    if info["drafts"]:
        L.append(f"- 示例: {', '.join(info['drafts'][:5])}")
    L.append("")

    L.append("## 依赖")
    L.append(f"- 必需包缺失: {info['required_pkgs_missing'] or '无 ✅'}")
    L.append(f"- 可选包缺失: {info['optional_pkgs_missing'] or '无 ✅'}")
    L.append(f"- ffmpeg: `{info['ffmpeg'] or '未安装 ❌（影响素材时长探测/转码）'}`")
    L.append(f"- ffprobe: `{info['ffprobe'] or '未安装 ❌'}`\n")

    L.append("## 能力结论")
    L.append("")
    L.append("| 能力 | 状态 | 说明 |")
    L.append("| --- | --- | --- |")
    L.append(
        f"| 生成/编辑剪映草稿 | {'✅ 可用' if info['draft_generation_available'] else '⚠️ 有缺失'} | "
        "纯写草稿 JSON，不操作剪映进程 |"
    )
    L.append(
        f"| 自动导出 MP4 | {'✅ 可用' if info['auto_export_available'] else '❌ 不可用'} | "
        f"{info['auto_export_reason']} |"
    )
    L.append("")
    if not info["auto_export_available"]:
        L.append(
            "> **自动导出说明**：剪映 10.x 前端为 QML，已不对外暴露 accessibility 树"
            "（UIA 与 MSAA 均读不到控件），依赖控件定位的导出无法工作。\n"
            "> 这是剪映版本层面的限制，改控件名无法绕过。"
            "草稿仍可全自动生成，**导出请在剪映中手动点击「导出」**。"
        )
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="剪映自动化环境自检")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()
    info = collect()
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print(render(info))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
