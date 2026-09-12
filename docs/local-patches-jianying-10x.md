# 本地补丁记录 · 适配剪映 10.x（Windows）

> 本文件记录在本机（剪映 10.5.0.13988 / Windows 11）上为让本 Skill 正常工作所做的修改。
> **若后续执行 `git pull` 升级 Skill，这些补丁会被覆盖，需按本文件重新打一遍。**

## 一、参考环境（实测于本机，其他机器按实际填）

| 项 | 值 |
| --- | --- |
| 剪映版本 | 10.5.0.13988 |
| 剪映安装路径 | `<剪映安装目录>\JianyingPro.exe`，例如 `D:\JianyingPro\JianyingPro.exe` |
| 草稿目录 | Windows: `%LOCALAPPDATA%\JianyingPro\User Data\Projects\com.lveditor.draft`<br>macOS: `~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft` |
| ffmpeg / ffprobe | 装在 PATH 里即可，或用 `JY_FFMPEG` 指定 |
| Python 环境 | 任意 Python 3.9+ 虚拟环境（本机用的是 WorkBuddy 自带的 venv） |

> **不用手填路径**：`scripts/utils/jy_paths.py` 会自动探测以上所有位置。
> 想确认本机探测结果，跑：
> ```bash
> python <SKILL_ROOT>/scripts/utils/jy_paths.py
> ```

## 二、实测结论（关键）

**能用的**：草稿生成/编辑链路全部可用。
已验证：Skill 生成的草稿会被剪映 10.5 识别并列出，点击可正常打开，
预览画面、视频轨、音频波形、文字轨均正常，分辨率 1920x1080 @ 30fps。

**不能用的**：自动导出。
剪映 10.x 前端为 QML，**不对外暴露 accessibility 树**：

| 探测方式 | 结果 |
| --- | --- |
| UIA 遍历（对照：微信 17 个控件、记事本 35 个） | 剪映 **0** 个有效节点 |
| 原生 MSAA `AccessibleObjectFromWindow` → `accChildCount` | **0** |
| 管理员权限运行 Python | 仍为 0（排除 UIA 权限隔离） |

> 注意：编辑页窗口（`MainWindow_QMLTYPE_*`）会返回 **1 个**残留子控件，
> 所以判断标准不能用"有没有子控件"，必须统计整棵树的有效节点数。

因此原实现依赖的 `HomePageDraftTitle:`、`MainWindowTitleBarExportBtn`、
`ExportOkBtn` 等控件描述符在 10.x 上永远找不到。**这是剪映版本层面的限制，改控件名无法绕过。**

## 三、补丁清单

| # | 文件 | 改动 |
| --- | --- | --- |
| 1 | `scripts/vendor/pyJianYingDraft/draft_folder.py` | `create_draft()` 里写入真实草稿元数据（`draft_id` 随机 UUID、`draft_name`、`draft_fold_path`、`draft_root_path`、`draft_json_file`、`tm_draft_create/modified` 等）。原模板这些字段全为空、`draft_id` 还是所有草稿共用的固定值，完全依赖剪映启动时"自愈"补全。 |
| 2 | `scripts/jy_wrapper.py` | 新增 `_mirror_draft_content()`：保存时把 `draft_info.json` 镜像一份为 `draft_content.json`，并刷新 `tm_draft_modified`。剪映 10.x 的草稿索引 `draft_json_file` 指向 `draft_content.json`。 |
| 3 | `scripts/vendor/pyJianYingDraft/jianying_controller.py` | 新增 `ui_automation_available()`（统计整棵树有效节点数 ≥10 才算可用），并在 `export_draft()` 开头预检，不可用时立即抛明确错误，而不是让调用方干等 20 分钟超时。 |
| 4 | `scripts/auto_exporter.py` | 识别上述情况，返回独立错误码 `ui_automation_unavailable` + `manual_export_required: true`。 |
| 5 | `scripts/env_doctor.py` | **新增**：环境自检。报告剪映版本、草稿目录、ffmpeg、依赖缺失，并直接给出"自动生成草稿 / 自动导出"两项能力的可用结论。 |
| 6 | `SKILL.md`、`rules/core.md` | 新增版本兼容矩阵与 10.x 导出限制说明。 |

## 四、验证

```bash
# 1) 环境自检
python <SKILL_ROOT>/scripts/env_doctor.py

# 2) 端到端：生成草稿后，在剪映首页确认能列出、点击能打开
```

## 五、升级后重打补丁

```bash
cd <SKILL_ROOT> && git pull
```

然后按本文件第三节逐条重新应用。补丁代码全部以 `[本地补丁 · 适配剪映 10.x]`
注释标记，`grep -rn "本地补丁" <SKILL_ROOT>` 可快速定位。

---

## 六、剪映 GUI 自动化实战姿势（10.x 必读）

因为 10.x 不暴露 accessibility，所有界面操作只能靠**坐标点击 + 截图验证**。
踩过的坑与可靠做法：

### 6.1 截图必须能真正抢到前台

只调 `SetForegroundWindow` 会被系统拒绝（前台锁定），截图会抓到自己的窗口。
可靠序列：

```python
user32.ShowWindow(hwnd, 9)                      # SW_RESTORE
fg = user32.GetForegroundWindow()
tf = user32.GetWindowThreadProcessId(fg, None)
tm = kernel32.GetCurrentThreadId()
user32.AttachThreadInput(tf, tm, True)          # 关键
user32.BringWindowToTop(hwnd)
user32.SetForegroundWindow(hwnd)
user32.AttachThreadInput(tf, tm, False)
```

校验方式：`GetForegroundWindow() == hwnd`，并对截图求像素均值（黑屏≈0，正常 >20）。

### 6.2 点击用窗口比例，不要写死像素

首页（`HomePage_QMLTYPE_*`）窗口尺寸由用户拖拽决定，点开草稿进入编辑页
（`MainWindow_QMLTYPE_*`）后会**最大化**（实测从 1168×780 跳到 1920×1032）。
一律用 `rc.left + int(W * fx)` 形式。

### 6.3 草稿卡片排序会变

每次先截一张列表图确认顺序再点，不要假定"第一个就是某某"。

### 6.4 启动 / 关闭剪映

- 关闭：`taskkill /F /IM JianyingPro.exe` + `JianyingProTray.exe`
  （**必须先关再改草稿文件**，否则文件被锁，重建时删除会失败）
- 启动：`ShellExecuteW(None, 'open', exe, None, cwd, 1)`
  用 `subprocess.Popen` 从后台脚本拉起会随父进程退出而被回收；
  `DETACHED_PROCESS` 也无效。
  启动器用**根目录那个** `D:\JianyingPro\JianyingPro.exe`（5.3MB），
  不要直接用版本子目录里的 exe。

## 七、用户收藏的贴纸 / 箭头 → 程序化接入

**结论：贴纸不能直接写进草稿。**
实测往 `materials.stickers` 写素材 + 新建 Sticker 轨，剪映 10.5 **完全不显示**；
补 `path`/`extra_info`/尺寸字段也不行。原因是草稿被剪映写成了**私有加密格式**，
无法从既有草稿反查它写入贴纸时所需的完整元数据。

**可用替代路径：把贴纸资产渲染成带 alpha 的 overlay 视频，走普通视频轨。**

1. 从 `%LOCALAPPDATA%\JianyingPro\User Data\Cache\artistEffect\<resource_id>\<hash>\` 取资产：
   - `SequenceMap.png` — sprite sheet（如 560×560 = 2×2 共 4 帧 280×280 RGBA）
   - `ani_info.json` — 每帧在 sheet 中的 `frame.x/y/w/h`
   - `heycanInfo.json` — `frameCount` / `singleWidth` / `singleHeight`
   - `infoSticker.lua` — 动画参数（如 `setFps(4)`、循环、easeIn/easeOut 缩放）
   > `<resource_id>` 就是目录名，不需要从草稿里解出来。
2. 拆帧 → 按需镜像/旋转（例：贴纸尖端朝左上，`FLIP_TOP_BOTTOM` 后朝左下）
3. 缩放到目标尺寸，摆到画布指定位置，合成帧序列
4. ffmpeg 编码：
   ```bash
   ffmpeg -framerate 60 -i f%05d.png \
          -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le -vendor apl0 \
          out.mov
   ```
   （与 `edit/animations/batch_*/arrow_*/render.mov` 的规格一致：
   ProRes 4444 / yuva444p12le / 1080×1920 / 60fps）
5. 草稿里 `add_media_safe(out.mov, fmt(t-3.0), duration=fmt(3.0), track_name="Overlay")`

参考实现：`scripts/tools/sticker_to_overlay.py`（命令行版，支持 `--list` 列出本机缓存贴纸）

## 八、草稿轨道命名约定（本项目）

`VideoTrack` / `VoiceOver` / `BGM` / `Overlay` / `Subtitles`。
注意 `Overlay` 是 `video` 类型轨道，剪映编辑页里显示在**字幕轨下方、主视频轨上方**，
前段为空属正常（只在末尾 3 秒有内容）。

## 九、重写生成脚本时的检查项

`_build_drafts3.py` 曾整段漏掉箭头代码（v2 有、v3 没带上），导致重建后 Overlay 轨消失。
重写生成脚本后，逐项核对前一版的功能清单：**开场 / 九段功能 / 转场 / 滤镜 /
关键帧 / 配音 / 字幕 / BGM / 箭头**，一项都不能少。
