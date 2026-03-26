# Architecture

## Module overview

| Module | Responsibility |
|--------|---------------|
| `main.py` | Entry point — delegates to `cli()` |
| `thumbnaileditor/cli.py` | Click CLI (`render`, `batch` commands) |
| `thumbnaileditor/config.py` | Global config from `.env` via `python-dotenv`; exposes singleton `config` |
| `thumbnaileditor/project.py` | Per-project `config.toml` loader and project discovery |
| `thumbnaileditor/scryfall.py` | Image download with SHA256-based disk cache |
| `thumbnaileditor/render.py` | Image composition pipeline |

## Rendering pipeline

`render_thumbnail(project_config, env_config)` runs three stages in order:

1. **Background** — `_make_mirrored_background`: fetches the background card, resizes to output height, center-crops to half the canvas width, pastes on the left half, pastes a horizontally flipped copy on the right half. No blur.
2. **Foreground cards** — scaled to `card_scale * height`, fanned with alternating tilt rotation and overlap controlled by `card_overlap`.
3. **Title bar** — semi-transparent black bar at top or bottom with white outlined text.

## Config layering

`ProjectConfig` fields are all optional except `title`, `background_card`, and `foreground_cards`. `render_thumbnail` resolves each setting as `project_value or env_value`, so project-level keys override globals without needing to repeat them.

## Image caching

`fetch_image` caches by `sha256(url)[:16]` as a `.png` file under `CACHE_FOLDER`. Cache is indefinite — clear manually with `rm -rf ./cache/*`.
