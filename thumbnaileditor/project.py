import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass
class ProjectConfig:
    # [metadata]
    title: str
    # [cards]
    background_card: str
    foreground_cards: list[str]
    # [title] — all optional per-project overrides
    title_bar_position: int | None = None   # pixel y coordinate for top of bar
    title_bar_height: int | None = None     # explicit bar height in pixels
    title_bar_opacity: float | None = None
    title_font_size: int | None = None
    card_scale: float | None = None
    card_overlap: float | None = None
    card_rotation: float | None = None
    color_identity: list[str] = field(default_factory=list)
    pip_radius: int | None = None
    pip_position: int | None = None         # explicit pixel y for top of pips
    output_resolution: str | None = None


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

    cards = raw["cards"]["foreground_cards"]
    if not (1 <= len(cards) <= 5):
        raise ValueError(f"foreground_cards must have 1–5 entries, got {len(cards)}")

    title_section = raw.get("title", {})
    shadow_section = title_section.get("shadow", {})
    cards_section = raw["cards"]
    metadata_section = raw["metadata"]

    return path, ProjectConfig(
        title=metadata_section["title"],
        background_card=cards_section["background_card"],
        foreground_cards=cards,
        output_resolution=title_section.get("output_resolution"),
        title_bar_position=shadow_section.get("position"),
        title_bar_height=shadow_section.get("height"),
        title_bar_opacity=shadow_section.get("opacity"),
        title_font_size=title_section.get("font_size"),
        card_scale=cards_section.get("card_scale"),
        card_overlap=cards_section.get("card_overlap"),
        card_rotation=cards_section.get("card_rotation"),
        color_identity=metadata_section.get("color_identity", []),
        pip_radius=title_section.get("pip_radius"),
        pip_position=title_section.get("pip_position"),
    )


def discover_projects(projects_folder: str | Path) -> list[Path]:
    """Return all subdirectories containing a config.toml, sorted by name."""
    root = Path(projects_folder)
    return sorted(p.parent for p in root.glob("*/config.toml"))


def _validate(raw: dict, config_file: Path) -> None:
    if "metadata" not in raw or "title" not in raw.get("metadata", {}):
        raise ValueError(f"config.toml missing [metadata] section with 'title': {config_file}")
    if "cards" not in raw:
        raise ValueError(f"config.toml missing [cards] section: {config_file}")
    missing = [k for k in ("background_card", "foreground_cards") if k not in raw["cards"]]
    if missing:
        raise ValueError(f"[cards] section missing required keys {missing}: {config_file}")
