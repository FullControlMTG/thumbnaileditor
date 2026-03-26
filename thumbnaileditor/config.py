import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    projects_folder: str = field(default_factory=lambda: os.getenv("PROJECTS_FOLDER", "./projects"))
    output_folder: str = field(default_factory=lambda: os.getenv("OUTPUT_FOLDER", "./output"))
    cache_folder: str = field(default_factory=lambda: os.getenv("CACHE_FOLDER", "./cache"))
    output_resolution: tuple[int, int] = field(default_factory=lambda: _parse_resolution(
        os.getenv("OUTPUT_RESOLUTION", "1920x1080")
    ))
    card_scale: float = field(default_factory=lambda: float(os.getenv("CARD_SCALE", "0.72")))
    card_overlap: float = field(default_factory=lambda: float(os.getenv("CARD_OVERLAP", "0.12")))
    title_font_size: int = field(default_factory=lambda: int(os.getenv("TITLE_FONT_SIZE", "90")))
    title_bar_opacity: float = field(default_factory=lambda: float(os.getenv("TITLE_BAR_OPACITY", "0.55")))
    title_bar_position: str = field(default_factory=lambda: os.getenv("TITLE_BAR_POSITION", "bottom"))


def _parse_resolution(value: str) -> tuple[int, int]:
    w, h = value.lower().split("x")
    return int(w), int(h)


config = Config()
