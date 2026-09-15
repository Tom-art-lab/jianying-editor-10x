# QA checklist

- [ ] Output dimensions, frame rate, codec, audio codec, and duration match the profile.
- [ ] Every source is present, at native speed, and used only in an allowed order.
- [ ] Creator speech and every available source-audio stream remain audible.
- [ ] Narration is complete and natural; no sentence or action is cut off.
- [ ] Captions are in the project language, stable in size, at most two lines, and disappear exactly with their own speech.
- [ ] Caption and every graphic are inside the publish-safe region and do not overlap.
- [ ] Motion graphics describe the shot, contain no opaque black blocks or rejected low-quality stickers, and vary across the batch.
- [ ] Music exists, uses the recorded excerpt offset, is licensed/evidenced for the target platform and region, and ducks under speech/source audio.
- [ ] CTA arrow, when enabled, has a thick shaft and triangular head, points at the actual target, and stays visible at publish size.
- [ ] First, middle, final, and publish-size frames have been inspected.
- [ ] Full audio/video decode succeeds and true peak stays below clipping.
- [ ] Output count, captions, source combinations, music, and file hashes are unique where the batch requests variation.
- [ ] Delivery directory contains only final MP4s; originals and prior deliveries remain intact.
