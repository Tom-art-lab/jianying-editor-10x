# -*- coding: utf-8 -*-
"""标定草稿：实测剪映的字号(size) / 垂直位置(transform_y) → 像素 映射。

4 条字幕**同一时段同时显示**、位置错开，一次截图即可读出
4 组 (size, transform_y) → (像素高度, 像素中心y)。

用法:
    python subtitle_calib.py                        # 纯黑底（测量最准）
    python subtitle_calib.py --palette <视频路径>    # 用指定视频当底
"""
import argparse
import os
import sys

# 自动定位 skill 根目录：优先 JY_SKILL_ROOT，其次从本文件向上探测
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "utils"))
from skill_path import ensure_skill_scripts_on_path  # noqa: E402

SKILL = os.environ.get("JY_SKILL_ROOT") or ensure_skill_scripts_on_path(_HERE)
os.environ["JY_SKILL_ROOT"] = SKILL
sys.path.insert(0, os.path.join(SKILL, "scripts", "vendor"))

from jy_wrapper import JyProject  # noqa: E402
import pyJianYingDraft as draft  # noqa: E402

W, H, FPS = 1080, 1920, 60
TEXT = "MESIN MENYALA"

# (size, transform_y) —— 一个变量一组，位置错开便于分辨
CASES = [
    (5.0, -0.80),
    (8.0, -0.30),
    (11.0, 0.20),
    (15.0, 0.70),
]

_ap = argparse.ArgumentParser(description="生成字幕标定草稿")
_ap.add_argument("--palette", default=os.environ.get("JY_CALIB_PALETTE"),
                 help="可选：垫底视频路径。不指定则用纯黑画布（测白字更准）")
_args = _ap.parse_args()

name = "ZZ_SUB_CALIB"
p = JyProject(name, width=W, height=H, overwrite=True)
p.script.fps = FPS

if _args.palette and os.path.exists(_args.palette):
    p.add_media_safe(_args.palette, "0us", duration="5s", track_name="VideoTrack")
    print("  垫底视频已加")
elif _args.palette:
    print(f"  ⚠ 垫底视频不存在，改用纯黑画布: {_args.palette}")
else:
    print("  使用纯黑画布（不垫底）")

for i, (size, ty) in enumerate(CASES):
    try:
        # 每条独立文字轨，避免同轨重叠限制
        p.add_text_simple(
            TEXT, start_time="0us", duration="5s",
            track_name=f"Subtitles{i+1}",
            font=getattr(draft.FontType, "Poppins_Bold"),
            style=draft.TextStyle(size=size, bold=True),
            border=draft.TextBorder(color=(0.0, 0.0, 0.0), alpha=1.0, width=40.0),
            clip_settings=draft.ClipSettings(transform_y=ty),
        )
        print(f"  size={size:<5} transform_y={ty:<6} OK")
    except Exception as e:
        print(f"  size={size} 失败: {e}")

p.save()
print(f"\n标定草稿已建: {name}（4 条字幕同时显示 0~5s）")
