# thumbnaileditor

An automated thumbnail editor for FullControlMTG video thumbnails.

Generates professional 1920x1080 thumbnails by compositing Magic: The Gathering card images with a blurred background, foreground cards, and a title overlay.

---

## Features

- **Multi-card layout**: Display 1–5 foreground cards with alternating tilt rotation
- **Blurred background**: Uses a full-art card scaled to fill the frame with a Gaussian blur effect
- **Title bar overlay**: Semi-transparent black bar with white outlined text, configurable at top or bottom
- **Scryfall image caching**: Card images are downloaded once and cached locally to avoid redundant requests
- **Per-project config**: Each project has its own `config.toml` with optional overrides for every global setting
- **Batch rendering**: Process all projects in a single command
- **Dry-run validation**: Validate project configs without producing output

---

## Requirements

- Python 3.10+
- pip

---

## Installation

```bash
git clone https://github.com/FullControlMTG/thumbnaileditor
cd thumbnaileditor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Configuration

### Global settings (`.env`)

Copy `.env.example` to `.env` and adjust as needed:

```env
PROJECTS_FOLDER=./projects
OUTPUT_FOLDER=./output
CACHE_FOLDER=./cache
OUTPUT_RESOLUTION=1920x1080
CARD_SCALE=0.72
CARD_OVERLAP=0.12
TITLE_FONT_SIZE=90
TITLE_BAR_OPACITY=0.55
TITLE_BAR_POSITION=bottom
```

### Project config (`projects/<project_name>/config.toml`)

Each project lives in its own subdirectory under `PROJECTS_FOLDER`:

```toml
title = "My Video Title"
background_card = "https://cards.scryfall.io/..."   # Full-art card used as background
foreground_cards = [
    "https://cards.scryfall.io/...",                # 1–5 cards to display in the foreground
    "https://cards.scryfall.io/...",
]

# Optional per-project overrides (all global settings can be overridden here)
card_scale = 0.72
card_overlap = 0.12
title_font_size = 90
title_bar_opacity = 0.55
title_bar_position = "bottom"   # "top" or "bottom"
output_resolution = "1920x1080"
```

An example project is provided at `projects/example/config.toml`.

---

## Usage

### Render a single project

```bash
python main.py render projects/example
```

Output is saved to `{OUTPUT_FOLDER}/{project_name}.png` by default.

**Options:**

| Flag | Description |
|------|-------------|
| `--dry-run` | Validate the config without rendering |
| `-o, --output <path>` | Write output to a custom file path |

```bash
python main.py render projects/example --dry-run
python main.py render projects/example -o ~/Desktop/my_thumbnail.png
```

### Render all projects

```bash
python main.py batch
```

Discovers all subdirectories in `PROJECTS_FOLDER`, renders each one, and continues on errors (errors are printed to stderr).

```bash
python main.py batch --dry-run   # Validate all configs without rendering
```

---

## Directory structure

```
thumbnaileditor/
├── main.py                  # Entry point
├── requirements.txt
├── .env.example             # Environment variable template
├── thumbnaileditor/
│   ├── cli.py               # CLI commands
│   ├── config.py            # Global config loader
│   ├── project.py           # Project config loader & discovery
│   ├── render.py            # Image composition logic
│   └── scryfall.py          # Image download & caching
├── projects/
│   └── example/
│       └── config.toml
├── cache/                   # Downloaded card images (auto-created)
└── output/                  # Rendered thumbnails (auto-created)
```

---

## Runbook

### Clearing the image cache

Card images are cached indefinitely in `CACHE_FOLDER` using SHA256-based filenames. To force a re-download of all images:

```bash
rm -rf ./cache/*
```

To clear a single cached image, delete the corresponding file from `./cache/`.

### Adding a new project

1. Create a new subdirectory under `projects/`:
   ```bash
   mkdir projects/my-new-video
   ```
2. Add a `config.toml` with at minimum `title`, `background_card`, and `foreground_cards`.
3. Validate the config before rendering:
   ```bash
   python main.py render projects/my-new-video --dry-run
   ```
4. Render:
   ```bash
   python main.py render projects/my-new-video
   ```

### Batch rendering all projects

```bash
source .venv/bin/activate
python main.py batch
```

Failed projects are skipped and reported to stderr. Successfully rendered thumbnails land in `./output/`.

### Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Activate the virtual environment: `source .venv/bin/activate` |
| Image download timeout | Default timeout is 15 seconds. Check your internet connection or the Scryfall URL. |
| Font renders as default/ugly | Install a system font: `sudo apt install fonts-liberation` (Debian/Ubuntu) |
| Wrong output resolution | Set `OUTPUT_RESOLUTION` in `.env` or `output_resolution` in the project's `config.toml` |
| Batch skips a project | Run `python main.py render projects/<name>` directly to see the full error |
