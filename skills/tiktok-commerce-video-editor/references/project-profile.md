# Project profile

The profile is project data, not a global rule. Replace every example value before production.

Required shape:

```json
{
  "schema_version": 1,
  "project_name": "example",
  "market": "id-ID",
  "canvas": {"width": 1080, "height": 1920, "fps": 60},
  "product": {"name": "replace me", "facts": ["replace me"]},
  "roles": [
    {"id": "intro", "label": "creator intro", "required": false},
    {"id": "feature_a", "label": "feature A", "required": true}
  ],
  "allowed_orders": [["intro", "feature_a"]],
  "caption": {"language": "id-ID", "max_lines": 2, "font_px": 50,
    "safe_rect": {"x": 200, "y": 1050, "w": 680, "h": 230},
    "style": "white fill, black outline", "composite_last": true},
  "audio": {"retain_source_audio": true, "creator_gain": 1.0,
    "footage_gain": 0.78, "music_policy": "prompt_user_folder",
    "music_dir": "./music", "music_duck_under_speech": true,
    "allow_music_excerpt": true},
  "cta_arrow": {"enabled": true, "shape": "thick shaft and triangular head",
    "target": "platform cart icon", "avoid_rects": ["caption.safe_rect"]},
  "delivery": {"output_dir": "./delivery", "mp4_only": true,
    "preserve_originals": true, "clean_intermediates_after_qa": true}
}
```

`allowed_orders` is intentionally a list: one project can support several valid editorial structures without forcing the structure of another product. Roles can be renamed, added, or removed. Do not add claims to `product.facts` that are not supported by the supplied material.

`audio.music_policy` must be one of:

- `prompt_user_folder`: ask the creator to put the chosen tracks in `music_dir`, then read only that folder.
- `skip`: render without background music and record the explicit skip decision.
- `optional`: use tracks from `music_dir` only when present; otherwise continue without music and record that no music was supplied.

Never assume that a track in another user's folder is suitable for this project. Keep title, artist, source, region, license evidence, SHA-256, and excerpt start offset in the delivery record when music is used.

For a different platform, replace `caption.safe_rect`, `cta_arrow.target`, and the platform-control exclusions after inspecting its actual publish UI. Keep the coordinate system in output pixels.
