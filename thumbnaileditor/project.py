import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass
class ProjectConfig:
    title: str
    background_card: str
    foreground_cards: list[str]
    # Optional per-project overrides
    output_resolution: str | None = None
    card_scale: float | None = None
    card_overlap: float | None = None
    title_font_size: int | None = None
    title_bar_opacity: float | None = None
    title_bar_position: str | None = None


def load_project(project_path: str | Path) -> tuple[Path, ProjectConfig]:
    """Load and validate a project folder, returning (project_dir, config)."""
    path = Path(project_path).resolve()

    if not path.is_dir():
        raise ValueError(f"Project path is not a directory: {path}")

    config_file = path / "config.toml"
    if not config_file.exists():
        raise FileNotFoundError(f"Missing config.toml in {path}")

    with open(config_file, "rb") as f:
        raw = tomllib.load(f)

    _validate(raw, config_file)

    cards = raw["foreground_cards"]
    if not (1 <= len(cards) <= 5):
        raise ValueError(f"foreground_cards must have 1–5 entries, got {len(cards)}")

    return path, ProjectConfig(
        title=raw["title"],
        background_card=raw["background_card"],
        foreground_cards=cards,
        output_resolution=raw.get("output_resolution"),
        card_scale=raw.get("card_scale"),
        card_overlap=raw.get("card_overlap"),
        title_font_size=raw.get("title_font_size"),
        title_bar_opacity=raw.get("title_bar_opacity"),
        title_bar_position=raw.get("title_bar_position"),
    )


def discover_projects(projects_folder: str | Path) -> list[Path]:
    """Return all subdirectories containing a config.toml, sorted by name."""
    root = Path(projects_folder)
    return sorted(p.parent for p in root.glob("*/config.toml"))


def _validate(raw: dict, config_file: Path) -> None:
    required = ("title", "background_card", "foreground_cards")
    missing = [k for k in required if k not in raw]
    if missing:
        raise ValueError(f"config.toml missing required keys {missing}: {config_file}")
