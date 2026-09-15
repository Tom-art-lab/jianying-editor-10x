---
name: tiktok-commerce-video-editor
description: Create localized short-form commerce videos from a user-supplied project profile, preserving source audio, using content-aware motion graphics, music excerpts, captions, transitions, and publish-safe QA. Use for TikTok, Reels, Shorts, and similar vertical selling videos.
---

# TikTok Commerce Video Editor

Use this skill when a user asks to turn product footage, creator footage, voiceover, music, or reference videos into publishable short-form commerce edits.

## Product and order are always project data

Never assume the product, language, market, feature names, shot roles, or shot order from this skill. Read the project profile first. If a profile is missing, infer only what the supplied footage proves and ask for the missing order when changing it could alter the edit. A project may define any number of roles and any valid order; N1 is an example profile, not a default.

Profile fields and the validation contract are documented in [references/project-profile.md](references/project-profile.md). Validate a profile before rendering:

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
- Music may begin at a selected excerpt or phrase rather than time zero. Choose a passage that suits the footage, record the start offset and evidence, align natural cuts to beats only when native clip durations allow, and duck music below creator audio, source sound, and narration.
- Keep originals and previous deliveries. Render a new batch into its own delivery directory containing only final MP4 files. Delete intermediate renders only after count, decode, specification, audio, safe-area, ending, and uniqueness checks pass.

## Model-neutral operation

The skill is prompt-and-contract driven. Claude, Codex, Gemini, Grok, Hunyuan, DeepSeek, GLM, Kimi, and other models can use it when their host can read the skill and invoke the local media tools. The model supplies decisions and structured project data; FFmpeg or the host editor performs deterministic media work. Provider-specific TTS, lip-sync, or cloud APIs belong in adapters and must never be required by the core profile.

Do not claim that every model has the same tool access. If a host lacks video rendering, browser control, or a speech API, keep the profile and edit decision list portable and report the missing adapter instead of silently changing the creative contract.

## Required delivery record

Record the project profile version, source paths, order, caption timings, audio-retention flags, music title/artist/source/license evidence, music excerpt offset, motion-graphic style, output hash, and QA results. Never place API keys, cookies, private source files, or account credentials in the skill or repository.

Use [references/qa-checklist.md](references/qa-checklist.md) for the final review and [examples/project-profile.example.json](../../examples/project-profile.example.json) as a product-agnostic starting point.
