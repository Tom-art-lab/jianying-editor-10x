"""
JianYing Editor Skill - High Level Wrapper (Mixin Based)
旨在解决路径依赖、API 复杂度及严格校验问题。
"""

import json
import os
import shutil
import sys
import time
import uuid
from typing import Union, Optional

# 环境初始化
from utils.env_setup import setup_env
setup_env()

# 导入工具函数
from utils.constants import SYNONYMS
from utils.formatters import (
    resolve_enum_with_synonyms, format_srt_time, safe_tim, 
    get_duration_ffprobe_cached, get_default_drafts_root, get_all_drafts
)

# 导入基类与 Mixins
from core.project_base import JyProjectBase
from core.media_ops import MediaOpsMixin
from core.text_ops import TextOpsMixin
from core.vfx_ops import VfxOpsMixin
from core.mocking_ops import MockingOpsMixin

try:
    import pyJianYingDraft as draft
    from pyJianYingDraft import VideoSceneEffectType, TransitionType
except ImportError:
    draft = None

class JyProject(JyProjectBase, MediaOpsMixin, TextOpsMixin, VfxOpsMixin, MockingOpsMixin):
    """
    高层封装工程类。通过多重继承 Mixins 实现功能解耦。
    """
    def _resolve_enum(self, enum_cls, name: str):
        return resolve_enum_with_synonyms(enum_cls, name, SYNONYMS)

    def add_clip(self, media_path: str, source_start: Union[str, int], duration: Union[str, int], 
                 target_start: Union[str, int] = None, track_name: str = "VideoTrack", **kwargs):
        """高层剪辑接口：从媒体指定位置裁剪指定长度，并放入轨道。"""
        if target_start is None:
            target_start = self.get_track_duration(track_name)
        return self.add_media_safe(media_path, target_start, duration, track_name, source_start=source_start, **kwargs)

    def save(self):
        """保存并执行质检报告。"""
        self.script.save()
        self._patch_cloud_material_ids()
        self._force_activate_adjustments()

        draft_path = os.path.join(self.root, self.name)
        self._mirror_draft_content(draft_path)
        if os.path.exists(draft_path):
            os.utime(draft_path, None)
        print(f"✅ Project '{self.name}' saved and patched.")
        return {"status": "SUCCESS", "draft_path": draft_path}

    def _mirror_draft_content(self, draft_path: str) -> None:
        """[本地补丁 · 适配剪映 10.5]

        剪映 10.x 的草稿索引（`draft_json_file` / root_meta_info.json）指向
        `draft_content.json`，而本 Skill 生成的是 `draft_info.json`。
        实测剪映能兜底识别，但多一层镜像可避免依赖对方的自愈逻辑。
        同时刷新 tm_draft_modified，防止剪映把草稿判为陈旧。
        """
        info = os.path.join(draft_path, "draft_info.json")
        mirror = os.path.join(draft_path, "draft_content.json")
        try:
            if os.path.exists(info):
                shutil.copy2(info, mirror)

            meta_p = os.path.join(draft_path, "draft_meta_info.json")
            if os.path.exists(meta_p):
                with open(meta_p, "r", encoding="utf-8") as fp:
                    meta = json.load(fp)
                meta["tm_draft_modified"] = int(time.time() * 1000)
                with open(meta_p, "w", encoding="utf-8") as fp:
                    json.dump(meta, fp, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[warn] draft mirror skipped: {e}")

# 导出工具函数以便向下兼容
__all__ = ["JyProject", "get_default_drafts_root", "get_all_drafts", "safe_tim", "format_srt_time"]

if __name__ == "__main__":
    # 测试代码
    try:
        project = JyProject("Refactor_Test_Project", overwrite=True)
        print("🚀 Refactored JyProject initialized successfully.")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
