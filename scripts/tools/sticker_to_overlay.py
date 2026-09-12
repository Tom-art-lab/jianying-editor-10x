# -*- coding: utf-8 -*-
"""把剪映「我的收藏」里的贴纸渲染成可用的 overlay 视频素材。

背景：剪映 10.x 不认外部构造的贴纸素材（写进 materials.stickers 后界面不显示），
所以退一步——把贴纸资产渲染成**带 alpha 通道的 ProRes 4444 视频**，
再作为普通视频段放到 Overlay 轨。**代价是丢失贴纸自带的动画**。

贴纸资产在剪映本地缓存里：
    <User Data>/Cache/artistEffect/<resource_id>/<hash>/
        SequenceMap.png   精灵图（如 560x560 = 2x2 共 4 帧 280x280）
        ani_info.json     每帧在精灵图中的位置
        heycanInfo.json   frameCount / singleWidth / singleHeight
        infoSticker.lua   动画参数（帧率、循环、入场缩放）

用法:
    python sticker_to_overlay.py --list
        # 列出本机缓存里所有可用的贴纸 resource_id

    python sticker_to_overlay.py --sticker 7480091461778705726 \
        --out ./out/user_arrow.mov
        # 渲染指定贴纸为 1080x1920 / 60fps / 3s 的 ProRes 4444

    python sticker_to_overlay.py --sticker <id> --out <path> \
        --mirror vertical --box 265 --cx 302 --cy 1447 --dur 3
        # 指定镜像方式与画布摆放位置
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "utils"))
try:
    import jy_paths  # noqa: E402
except ImportError:
    jy_paths = None


# ─────────────────────────── 贴纸资产读取 ───────────────────────────

def cache_root() -> str:
    if jy_paths:
        p = jy_paths.find_effect_cache_dir()
        if p:
            return p
    env = os.environ.get("JY_EFFECT_CACHE", "").strip()
    if env:
        return env
    raise RuntimeError(
        "找不到剪映贴纸缓存目录。\n"
        "请先在剪映里打开「贴纸 → 我的 → 收藏」浏览一遍（让它下载到本地），\n"
        "或设置环境变量 JY_EFFECT_CACHE 指向 <User Data>/Cache/artistEffect"
    )


def list_stickers() -> list:
    """列出缓存里所有贴纸，返回 [{id, dir, frames, cell}]。"""
    root = cache_root()
    out = []
    for sid in sorted(os.listdir(root)):
        d = os.path.join(root, sid)
        if not os.path.isdir(d):
            continue
        maps = glob.glob(os.path.join(d, "*", "SequenceMap.png"))
        if not maps:
            continue
        info = {"id": sid, "dir": os.path.dirname(maps[0]),
                "frames": None, "cell": None}
        for hc in glob.glob(os.path.join(d, "*", "heycanInfo.json")):
            try:
                j = json.load(open(hc, encoding="utf-8"))
                info["frames"] = j.get("frameCount")
                info["cell"] = j.get("singleWidth")
            except Exception:
                pass
        if not info["cell"]:
            try:
                w = Image.open(maps[0]).width
                info["cell"] = w // 2
                info["frames"] = info["frames"] or 4
            except Exception:
                pass
        out.append(info)
    return out


def load_frames(sticker_id: str):
    root = os.path.join(cache_root(), sticker_id)
    maps = glob.glob(os.path.join(root, "*", "SequenceMap.png"))
    if not maps:
        raise FileNotFoundError(f"贴纸 {sticker_id} 不在本地缓存里")

    sheet = Image.open(maps[0]).convert("RGBA")

    # 优先读 ani_info.json 拿精确帧坐标
    frames = []
    for ai in glob.glob(os.path.join(root, "*", "ani_info.json")):
        try:
            j = json.load(open(ai, encoding="utf-8"))
            for f in j.get("frames", []):
                fr = f["frame"]
                frames.append(sheet.crop(
                    (fr["x"], fr["y"], fr["x"] + fr["w"], fr["y"] + fr["h"])))
            if frames:
                return frames
        except Exception:
            pass

    # 退化：按方形网格切
    cell = sheet.width // 2
    cols = sheet.width // cell
    n = cols * (sheet.height // cell)
    for i in range(n):
        r, c = divmod(i, cols)
        frames.append(sheet.crop((c * cell, r * cell,
                                  c * cell + cell, r * cell + cell)))
    return frames


# ─────────────────────────── 渲染 ───────────────────────────

def prep(img: Image.Image, mirror: str, box: int) -> Image.Image:
    if mirror == "vertical":
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    elif mirror == "horizontal":
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    bbox = img.split()[3].getbbox()
    if bbox:
        img = img.crop(bbox)
    scale = box / max(img.size)
    nw, nh = max(1, round(img.width * scale)), max(1, round(img.height * scale))
    return img.resize((nw, nh), Image.LANCZOS)


def render(args) -> str:
    ffmpeg, _ = (jy_paths.find_ffmpeg() if jy_paths else (None, None))
    ffmpeg = ffmpeg or shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("找不到 ffmpeg，请装好并加入 PATH 或设置 JY_FFMPEG")

    frames = load_frames(args.sticker)
    if not frames:
        raise RuntimeError("贴纸没有可用的帧")
    print(f"  载入 {len(frames)} 帧，单帧 {frames[0].size}")

    W, H, FPS = args.width, args.height, args.fps
    total = int(FPS * args.dur)
    hold = max(1, total // len(frames))
    intro_frames = int(0.20 * FPS)

    out_abs = os.path.abspath(args.out)
    tmp = args.out_dir or os.path.join(os.path.dirname(out_abs), "_frames_tmp")
    if os.path.isdir(tmp):
        shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)

    prepared = [prep(f, args.mirror, args.box) for f in frames]
    bw, bh = prepared[0].size
    base_x, base_y = args.cx - bw // 2, args.cy - bh // 2
    print(f"  贴纸不透明区 {bw}x{bh}，中心 ({args.cx},{args.cy})")

    blank = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i in range(total):
        spr = prepared[(i // hold) % len(prepared)]
        canvas = blank.copy()
        if i < intro_frames:                       # 入场缩放（模拟贴纸自带 easeIn）
            t = i / max(1, intro_frames - 1)
            s = 0.2 + 0.8 * (1 - (1 - t) ** 3)
            nw, nh = max(1, round(spr.width * s)), max(1, round(spr.height * s))
            canvas.alpha_composite(spr.resize((nw, nh), Image.LANCZOS),
                                   (args.cx - nw // 2, args.cy - nh // 2))
        else:
            canvas.alpha_composite(spr, (base_x, base_y))
        canvas.save(os.path.join(tmp, f"f{i:05d}.png"))

    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    subprocess.run([
        ffmpeg, "-y", "-v", "error",
        "-framerate", str(FPS), "-i", os.path.join(tmp, "f%05d.png"),
        "-c:v", "prores_ks", "-profile:v", "4444",
        "-pix_fmt", "yuva444p10le", "-vendor", "apl0", "-r", str(FPS),
        out_abs,
    ], check=True)
    shutil.rmtree(tmp, ignore_errors=True)

    print(f"  ✅ 已生成 {out_abs} ({os.path.getsize(out_abs)//1024} KB)")
    print(f"  规格: ProRes 4444 / 带 alpha / {W}x{H} / {FPS}fps / {args.dur}s")
    return out_abs


def main():
    ap = argparse.ArgumentParser(
        description="剪映收藏贴纸 → 带 alpha 的 overlay 视频",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="列出本机缓存里的贴纸")
    ap.add_argument("--sticker", help="贴纸 resource_id")
    ap.add_argument("--out", help="输出 .mov 路径")
    ap.add_argument("--out-dir", help="临时帧目录（默认与 --out 同级的 _frames_tmp）")
    ap.add_argument("--mirror", default="none",
                    choices=["none", "vertical", "horizontal"], help="镜像方式")
    ap.add_argument("--box", type=int, default=265, help="贴纸不透明区目标边长(px)")
    ap.add_argument("--cx", type=int, default=302, help="贴纸中心 X（画布坐标）")
    ap.add_argument("--cy", type=int, default=1447, help="贴纸中心 Y（画布坐标）")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--dur", type=float, default=3.0, help="输出时长（秒）")
    args = ap.parse_args()

    if args.list:
        try:
            items = list_stickers()
        except RuntimeError as e:
            print(f"❌ {e}")
            return 1
        if not items:
            print("缓存里还没有贴纸。请先在剪映里打开「贴纸 → 我的 → 收藏」浏览一遍。")
            return 0
        print(f"找到 {len(items)} 个贴纸：")
        for it in items:
            print(f"  {it['id']}   {it['frames']} 帧 x {it['cell']}px")
        return 0

    if not args.sticker or not args.out:
        ap.print_help()
        print("\n提示：先用 --list 看有哪些贴纸")
        return 1

    try:
        render(args)
    except Exception as e:
        print(f"❌ {type(e).__name__}: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
