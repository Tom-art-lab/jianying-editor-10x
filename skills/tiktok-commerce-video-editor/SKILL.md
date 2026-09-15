---
name: tiktok-commerce-video-editor
description: Create localized short-form commerce videos from a user-supplied project profile, preserving source audio, using content-aware motion graphics, music excerpts, captions, transitions, and publish-safe QA. Use for TikTok, Reels, Shorts, and similar vertical selling videos.
---

# TikTok Commerce Video Editor

Use this skill when a user asks to turn product footage, creator footage, voiceover, music, or reference videos into publishable short-form commerce edits.

## First run: ask in the conversation

Do not make a first-time creator edit JSON by hand. At the start of the first editing request, ask one short question:

> 背景音乐怎么处理？
> 1. 使用音乐（我会在桌面创建一个项目音乐文件夹，请把音乐放进去）
> 2. 使用我现在拖入对话框的音乐文件
> 3. 跳过配乐

If the creator chooses option 1, create a clearly named folder on the Desktop, such as `项目名_音乐素材`, tell the creator its exact path, wait for the files to be supplied, then scan only that folder. If the creator chooses option 2, use only the attached files. If the creator chooses option 3, render without background music and record `music_policy: skip`. For later edits in the same project, reuse the recorded choice unless the creator changes it. Never silently select a default library track.

The project profile and JSON validator are advanced paths for repeatable teams and automation. They are optional for ordinary creators; the conversation answers should be converted into the profile by the host.

## Product and order are always project data

Never assume the product, language, market, feature names, shot roles, or shot order from this skill. Read the project profile first. If a profile is missing, infer only what the supplied footage proves and ask for the missing order when changing it could alter the edit. A project may define any number of roles and any valid order; N1 is an example profile, not a default.

Never require a creator to edit JSON for a normal first edit. Profile fields and the validation contract are documented in [references/project-profile.md](references/project-profile.md). Validate a generated profile before rendering:

```text
python scripts/validate_profile.py path/to/project-profile.json
```

## Editing contract

- Preserve native source speed unless the project explicitly authorizes a change. Do not cut through spoken words, creator sentences, or an action that needs its completion.
- Keep every available source-audio stream on its original timeline. Creator audio has priority; retain useful operation and ambient sound underneath narration.
- Write copy and narration in the project language and make each line describe the shot it accompanies. Keep button instructions truthful and use the project's exact wording.
- Composite captions last. Use one stable readable style per video, at most two lines, and the project's publish-safe region. A caption must disappear at its own end time; never leave stale text on the next shot.
- Create motion graphics from shot semantics. Vary chapter typography, reveals, camera motion, light hits, transitions, and decorative density across a batch. Do not reuse a rejected style, opaque black panels, cheap stickers, or tiny unreadable labels.
- Keep every graphic outside faces, hands, products, important actions, captions, and platform controls. Never place a major graphic in a platform-obscured lower area unless the profile explicitly marks it safe.
- Use a normal, high-contrast shopping CTA arrow only when the profile requests one. It must have a thick shaft, a clear triangular head, an accurate target, and a visible animation without covering captions or controls.
- Music is project choice, never a default inherited from another user's project. If the profile requests music and no usable track folder is supplied, tell the creator to place tracks in the configured project music folder and then read that folder. Do not silently download, substitute, or reuse a library track. The creator may choose `skip` and deliver without music when the profile permits it.
- When music is enabled, it may begin at a selected excerpt or phrase rather than time zero. Choose a passage that suits the footage, record the start offset and evidence, align natural cuts to beats only when native clip durations allow, and duck music below creator audio, source sound, and narration. When music is skipped, record that decision in the delivery record and omit music-only QA checks.
- Keep originals and previous deliveries. Render a new batch into its own delivery directory containing only final MP4 files. Delete intermediate renders only after count, decode, specification, audio, safe-area, ending, and uniqueness checks pass.

## Model-neutral operation

The skill is prompt-and-contract driven. Claude, Codex, Gemini, Grok, Hunyuan, DeepSeek, GLM, Kimi, and other models can use it when their host can read the skill and invoke the local media tools. The model supplies decisions and structured project data; FFmpeg or the host editor performs deterministic media work. Provider-specific TTS, lip-sync, or cloud APIs belong in adapters and must never be required by the core profile.

Do not claim that every model has the same tool access. If a host lacks video rendering, browser control, or a speech API, keep the profile and edit decision list portable and report the missing adapter instead of silently changing the creative contract.

## Export backends

Use this dual-delivery contract whenever the host can access local media tools:

- **Direct deliverable:** render a verified final MP4 through local FFmpeg/FFprobe, like the Codex workflow.
- **Editable deliverable:** also create a JianYing project/draft with the same timeline, source media, captions, audio, transitions, and motion graphics, so the creator can open it in JianYing and adjust or export manually.

The MP4 and JianYing project are two outputs of the same edit decision list; do not create them with different shot orders, timings, or copy. Keep the project file in a separate work/project location and keep the delivery directory limited to publishable MP4 files unless the creator asks for the project alongside them.

Use this order for rendering:

1. Prefer a local FFmpeg/FFprobe render when the host can execute local commands. This produces the final MP4 directly and works independently of the JianYing 10.x QML export interface.
2. Create or save the matching JianYing project/draft for manual editing or export. On JianYing 10.x, do not claim that its native export was automated.
3. If local FFmpeg rendering is unavailable, do not claim that an MP4 was exported. Return the prepared JianYing project/timeline and state which local adapter is missing.

Before rendering, detect `ffmpeg` and `ffprobe`, record their paths and versions, use a temporary work directory, and write only verified final MP4 files to the delivery directory. Keep the original footage, source audio, and previous deliveries untouched. The export route is an implementation detail; it must not alter the approved shot order, native speed, captions, motion graphics, transitions, or audio mix.

## Required delivery record

Record the project profile version, source paths, order, caption timings, audio-retention flags, music title/artist/source/license evidence, music excerpt offset, motion-graphic style, output hash, and QA results. Never place API keys, cookies, private source files, or account credentials in the skill or repository.

Use [references/qa-checklist.md](references/qa-checklist.md) for the final review and [examples/project-profile.example.json](../../examples/project-profile.example.json) as a product-agnostic starting point.
