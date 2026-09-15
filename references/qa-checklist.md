# QA checklist

- [ ] Output dimensions, frame rate, codec, audio codec, and duration match the profile.
- [ ] Every source is present, at native speed, and used only in an allowed order.
- [ ] Creator speech and every available source-audio stream remain audible.
- [ ] Narration is complete and natural; no sentence or action is cut off.
- [ ] Captions are in the project language, stable in size, at most two lines, and disappear exactly with their own speech.
- [ ] Caption and every graphic are inside the publish-safe region and do not overlap.
- [ ] Motion graphics describe the shot, contain no opaque black blocks or rejected low-quality stickers, and vary across the batch.
- [ ] If music is enabled, it comes from the project's supplied music folder, uses the recorded excerpt offset, has platform/region evidence, stays clearly below speech/source audio, and leaves every spoken word intelligible on phone speakers.
- [ ] If music is skipped or optional music was not supplied, the decision is recorded and no unrelated default track is added.
- [ ] CTA arrow, when enabled, has a thick shaft and triangular head, points at the actual target, stays visible at publish size, and has no faint rectangle, translucent box, panel, or rectangular background.
- [ ] First, middle, final, and publish-size frames have been inspected.
- [ ] Full audio/video decode succeeds and true peak stays below clipping.
- [ ] Output count, captions, source combinations, music, and file hashes are unique where the batch requests variation.
- [ ] Delivery directory contains only final MP4s; originals and prior deliveries remain intact.
