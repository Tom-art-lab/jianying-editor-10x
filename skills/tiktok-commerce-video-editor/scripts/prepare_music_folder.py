#!/usr/bin/env python3
"""Create a creator-facing Desktop music folder without requiring JSON editing."""
from pathlib import Path
import re, sys

def desktop():
    home=Path.home()
    candidate=home/'Desktop'
    return candidate if candidate.exists() else home

def main(project='TikTok项目'):
    safe=re.sub(r'[^\w\u4e00-\u9fff.-]+','_',project,flags=re.UNICODE).strip('._') or 'TikTok项目'
    folder=desktop()/f'{safe}_音乐素材'
    folder.mkdir(parents=True,exist_ok=True)
    print(f'请将音乐文件放入：{folder}')
    print('支持常见音频格式；Skill 将只读取此项目文件夹，不会自动使用其他用户的曲目。')
    return folder

if __name__=='__main__':
    main(sys.argv[1] if len(sys.argv)>1 else 'TikTok项目')
