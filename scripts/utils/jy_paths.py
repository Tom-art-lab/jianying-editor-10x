# -*- coding: utf-8 -*-
"""跨平台路径探测：剪映草稿目录 / 剪映安装位置 / ffmpeg。

设计目标：**换一台电脑不用改任何代码**。
所有平台相关路径都在这里集中探测，其它脚本一律调这里的函数，
不要自己拼路径。

支持 Windows / macOS。探测顺序一律是「环境变量 → 常见路径 → 报错提示」，
并可通过以下环境变量覆盖：

    JY_DRAFT_ROOT      剪映草稿根目录（含 com.lveditor.draft 那一级）
    JY_INSTALL_DIR     剪映安装目录
    JY_FFMPEG          指向 ffmpeg 可执行文件（ffprobe 取同目录）
"""
from __future__ import annotations

import glob
import os
import shutil
import sys
from typing import Dict, List, Optional, Tuple

IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

DRAFT_FOLDER_NAME = "com.lveditor.draft"


# ────────────────────────────── 草稿目录 ──────────────────────────────

def _draft_candidates() -> List[str]:
    cands: List[str] = []

    env = os.environ.get("JY_DRAFT_ROOT", "").strip()
    if env:
        cands.append(env)
        cands.append(os.path.join(env, DRAFT_FOLDER_NAME))

    if IS_WIN:
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            cands.append(os.path.join(
                local, "JianyingPro", "User Data", "Projects", DRAFT_FOLDER_NAME))
        # 国内版可能的另一处位置
        profile = os.environ.get("USERPROFILE", "")
        if profile:
            cands.append(os.path.join(
                profile, "AppData", "Local", "JianyingPro", "User Data",
                "Projects", DRAFT_FOLDER_NAME))

    if IS_MAC:
        home = os.path.expanduser("~")
        cands += [
            os.path.join(home, "Movies", "JianyingPro", "User Data",
                         "Projects", DRAFT_FOLDER_NAME),
            os.path.join(home, "Movies", "CapCut", "User Data",
                         "Projects", "com.lveditor.draft"),
        ]

    # 兜底：家目录下直接找
    home = os.path.expanduser("~")
    for pat in ("*/JianyingPro/User Data/Projects/" + DRAFT_FOLDER_NAME,
                "*/*/JianyingPro/User Data/Projects/" + DRAFT_FOLDER_NAME):
        cands += glob.glob(os.path.join(home, pat))

    # 去重保序
    seen, out = set(), []
    for c in cands:
        c = os.path.abspath(os.path.expandvars(os.path.expanduser(c)))
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def find_draft_root(require_exists: bool = True) -> Optional[str]:
    """返回剪映草稿根目录（`.../Projects/com.lveditor.draft`）。找不到返回 None。"""
    for c in _draft_candidates():
        if not require_exists or os.path.isdir(c):
            return c

    # 再退一步：只要 User Data 存在，就自动补全
    if IS_WIN:
        local = os.environ.get("LOCALAPPDATA", "")
        base = os.path.join(local, "JianyingPro", "User Data", "Projects")
        if os.path.isdir(base):
            return os.path.join(base, DRAFT_FOLDER_NAME)
    return None


def draft_dir_for(draft_name: str, create: bool = False) -> str:
    """返回某个草稿的目录；create=True 时确保草稿根目录存在。"""
    root = find_draft_root(require_exists=False)
    if not root:
        raise RuntimeError(
            "找不到剪映草稿目录。请设置环境变量 JY_DRAFT_ROOT 指向\n"
            "  Windows: %LOCALAPPDATA%\\JianyingPro\\User Data\\Projects\\com.lveditor.draft\n"
            "  macOS:   ~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft"
        )
    if create:
        os.makedirs(root, exist_ok=True)
    return os.path.join(root, draft_name)


def find_user_data_dir() -> Optional[str]:
    """返回剪映 `User Data` 目录（草稿目录往上两级）。"""
    draft = find_draft_root(require_exists=False)
    if draft:
        d = os.path.abspath(os.path.join(draft, "..", ".."))
        if os.path.isdir(d):
            return d
    return None


def find_effect_cache_dir() -> Optional[str]:
    """返回剪映收藏贴纸/特效的本地缓存目录 `User Data/Cache/artistEffect`。

    用户「收藏」的贴纸在剪映里浏览过之后会落到这里，子目录名即 resource_id。
    """
    env = os.environ.get("JY_EFFECT_CACHE", "").strip()
    if env and os.path.isdir(env):
        return env
    ud = find_user_data_dir()
    if ud:
        p = os.path.join(ud, "Cache", "artistEffect")
        if os.path.isdir(p):
            return p
    return None


# ────────────────────────────── 剪映程序 ──────────────────────────────

def _install_candidates() -> List[str]:
    cands: List[str] = []
    env = os.environ.get("JY_INSTALL_DIR", "").strip()
    if env:
        cands.append(env)

    if IS_WIN:
        for drive in "CDEFG":
            cands += [
                f"{drive}:\\JianyingPro",
                f"{drive}:\\Program Files\\JianyingPro",
                f"{drive}:\\Program Files (x86)\\JianyingPro",
            ]
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            cands.append(os.path.join(local, "JianyingPro", "Apps"))
        # 注册表探测（可选）
        try:
            import winreg  # type: ignore
            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                for sub in (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\JianyingPro",
                            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\JianyingPro"):
                    try:
                        with winreg.OpenKey(hive, sub) as k:
                            v, _ = winreg.QueryValueEx(k, "InstallLocation")
                            if v:
                                cands.append(v)
                    except OSError:
                        pass
        except Exception:
            pass

    if IS_MAC:
        cands += ["/Applications/VideoFusion-macOS.app",
                  "/Applications/剪映专业版.app",
                  os.path.expanduser("~/Applications/剪映专业版.app")]

    return cands


def find_jianying_exe() -> Optional[str]:
    """返回剪映可执行文件路径（Windows: JianyingPro.exe；macOS: .app 内的可执行文件）。"""
    exe_names = ["JianyingPro.exe"] if IS_WIN else ["JianyingPro", "VideoFusion"]
    for base in _install_candidates():
        if not os.path.isdir(base):
            continue
        for name in exe_names:
            p = os.path.join(base, name)
            if os.path.isfile(p):
                return p
        # 版本子目录（如 D:\JianyingPro\10.5.0.13988\JianyingPro.exe）
        for sub in sorted(glob.glob(os.path.join(base, "*")), reverse=True):
            for name in exe_names:
                p = os.path.join(sub, name)
                if os.path.isfile(p):
                    return p
    return None


def find_jianying_version() -> Optional[str]:
    """推断剪映版本号（如 10.5.0.13988）。

    安装结构通常有两种：
      D:\\JianyingPro\\10.5.0.13988\\JianyingPro.exe   ← 版本在父目录名
      D:\\JianyingPro\\JianyingPro.exe                 ← 版本在同级子目录里
    """
    import re
    exe = find_jianying_exe()
    if not exe:
        return None

    def looks_like_version(s: str) -> bool:
        return bool(re.fullmatch(r"\d+(\.\d+){1,3}", s))

    parent = os.path.basename(os.path.dirname(exe))
    if looks_like_version(parent):
        return parent

    # 同级子目录里找版本号最大的那个
    base = os.path.dirname(exe)
    vers = [d for d in os.listdir(base)
            if os.path.isdir(os.path.join(base, d)) and looks_like_version(d)]
    if vers:
        def key(v: str):
            return [int(x) for x in v.split(".")]
        return max(vers, key=key)
    return None


# ────────────────────────────── ffmpeg ──────────────────────────────

def find_ffmpeg() -> Tuple[Optional[str], Optional[str]]:
    """返回 (ffmpeg, ffprobe)。优先环境变量 / PATH，其次常见安装位置。"""
    env_ff = os.environ.get("JY_FFMPEG", "").strip()
    if env_ff and os.path.isfile(env_ff):
        d = os.path.dirname(env_ff)
        probe = os.path.join(d, "ffprobe.exe" if IS_WIN else "ffprobe")
        return env_ff, (probe if os.path.isfile(probe) else None)

    ff = shutil.which("ffmpeg")
    fp = shutil.which("ffprobe")
    if ff and fp:
        return ff, fp

    searches: List[str] = []
    if IS_WIN:
        for drive in "CDEFG":
            searches += [f"{drive}:\\ffmpeg\\bin", f"{drive}:\\ffmpeg-*\\bin"]
    if IS_MAC:
        searches += ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"]

    for pat in searches:
        for d in sorted(glob.glob(pat)):
            f = os.path.join(d, "ffmpeg.exe" if IS_WIN else "ffmpeg")
            p = os.path.join(d, "ffprobe.exe" if IS_WIN else "ffprobe")
            if os.path.isfile(f):
                return f, (p if os.path.isfile(p) else None)

    return ff, fp


def require_ffprobe() -> str:
    _, fp = find_ffmpeg()
    if not fp:
        raise RuntimeError(
            "找不到 ffprobe。请安装 ffmpeg 并加入 PATH，"
            "或设置环境变量 JY_FFMPEG 指向 ffmpeg 可执行文件。"
        )
    return fp


# ────────────────────────────── 汇总自检 ──────────────────────────────

def diagnose() -> Dict[str, object]:
    """一次性返回本机环境探测结果，供 env_doctor / 安装脚本使用。"""
    ff, fp = find_ffmpeg()
    draft = find_draft_root()
    exe = find_jianying_exe()
    return {
        "platform": sys.platform,
        "python": sys.executable,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "draft_root": draft,
        "draft_root_exists": bool(draft and os.path.isdir(draft)),
        "jianying_exe": exe,
        "jianying_install_dir": os.path.dirname(exe) if exe else None,
        "jianying_version": find_jianying_version(),
        "ffmpeg": ff,
        "ffprobe": fp,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(diagnose(), ensure_ascii=False, indent=2))
