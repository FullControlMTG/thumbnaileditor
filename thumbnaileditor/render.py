import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import Config
from .project import ProjectConfig
from .scryfall import fetch_image, resolve_image_url


def render_thumbnail(project_config: ProjectConfig, env_config: Config) -> Image.Image:
    """Compose and return the final thumbnail as a PIL Image."""
    # Resolve effective settings (project overrides env defaults)
    width, height = _resolve_resolution(project_config, env_config)
    card_scale = project_config.card_scale or env_config.card_scale
    card_overlap = project_config.card_overlap or env_config.card_overlap
    card_rotation = project_config.card_rotation if project_config.card_rotation is not None else env_config.card_rotation
    font_size = project_config.title_font_size or env_config.title_font_size
    bar_opacity = project_config.title_bar_opacity or env_config.title_bar_opacity
    bar_position = project_config.title_bar_position  # pixel y, or None for default

    canvas = Image.new("RGBA", (width, height))

    # 1. Background
    bg = fetch_image(resolve_image_url(project_config.background_card), env_config.cache_folder)
    bg = _make_mirrored_background(bg, width, height)
    canvas.paste(bg, (0, 0))

    # 2. Foreground cards
    card_height = int(height * card_scale)
    cards = [
        fetch_image(url, env_config.cache_folder)
        for url in project_config.foreground_cards
    ]
    cards = [_scale_to_height(img, card_height) for img in cards]
    cards = [_round_card_corners(img) for img in cards]
    _paste_foreground_cards(canvas, cards, width, height, card_overlap, card_rotation)

    # 3. Title bar + text
    pip_radius = (project_config.pip_radius if project_config.pip_radius is not None else env_config.pip_radius) if project_config.color_identity else 0
    text_shadow_offset = project_config.title_text_dropshadow_offset if project_config.title_text_dropshadow_offset is not None else env_config.title_text_dropshadow_offset
    bar_y, bar_h = _draw_title(canvas, project_config.title, width, height, font_size, bar_opacity, bar_position, project_config.title_bar_height, pip_radius, text_shadow_offset)

    # 4. Color identity pips (drawn over the bar)
    if project_config.color_identity:
        _draw_color_identity(canvas, project_config.color_identity, width, bar_y, bar_h, pip_radius, project_config.pip_position, env_config.assets_folder)

    return canvas.convert("RGB")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_resolution(project_config: ProjectConfig, env_config: Config) -> tuple[int, int]:
    if project_config.output_resolution:
        w, h = project_config.output_resolution.lower().split("x")
        return int(w), int(h)
    return env_config.output_resolution


def _make_mirrored_background(img: Image.Image, width: int, height: int) -> Image.Image:
    """Resize image to output height, then tile it as a mirrored pair.

    The left half of the canvas shows the center-cropped image; the right half
    shows a horizontally flipped copy of the same crop.
    """
    half_w = width // 2

    # Resize to output height, preserving aspect ratio
    ratio = height / img.height
    scaled_w = int(img.width * ratio)
    img = img.resize((scaled_w, height), Image.LANCZOS)

    # Center-crop to half the canvas width
    left = max(0, (scaled_w - half_w) // 2)
    tile = img.crop((left, 0, left + half_w, height))

    canvas = Image.new("RGBA", (width, height))
    canvas.paste(tile, (0, 0))
    canvas.paste(tile.transpose(Image.FLIP_LEFT_RIGHT), (half_w, 0))
    return canvas


_MTG_CORNER_RATIO = 3 / 63  # 3mm radius on a 63mm-wide card


def _round_card_corners(img: Image.Image) -> Image.Image:
    radius = int(img.width * _MTG_CORNER_RATIO)
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (img.width - 1, img.height - 1)], radius=radius, fill=255)
    result = img.copy().convert("RGBA")
    result.putalpha(mask)
    return result


def _scale_to_height(img: Image.Image, target_height: int) -> Image.Image:
    ratio = target_height / img.height
    new_w = int(img.width * ratio)
    return img.resize((new_w, target_height), Image.LANCZOS)


def _paste_foreground_cards(
    canvas: Image.Image,
    cards: list[Image.Image],
    width: int,
    height: int,
    overlap: float,
    rotation: float,
) -> None:
    n = len(cards)
    # Total visual width = sum of card widths minus overlapping portions
    card_w = cards[0].width  # all scaled to same height so widths are similar
    total_w = sum(c.width for c in cards) - int(card_w * overlap) * (n - 1)

    x = (width - total_w) // 2
    y = (height - cards[0].height) // 2 + int(height * 0.04)  # slightly below center

    for i, card in enumerate(cards):
        angle = (i - (n - 1) / 2) * rotation
        rotated = card.rotate(angle, expand=True, resample=Image.BICUBIC)

        # Re-center after rotation expansion
        paste_x = x - (rotated.width - card.width) // 2
        paste_y = y - (rotated.height - card.height) // 2

        if rotated.mode == "RGBA":
            canvas.paste(rotated, (paste_x, paste_y), rotated)
        else:
            canvas.paste(rotated, (paste_x, paste_y))

        x += card.width - int(card_w * overlap)


def _draw_title(
    canvas: Image.Image,
    title: str,
    width: int,
    height: int,
    font_size: int,
    bar_opacity: float,
    bar_position: int | None,
    bar_height: int | None,
    pip_radius: int = 0,
    text_shadow_offset: int = 0,
) -> tuple[int, int]:
    font = _load_font(font_size)

    # Measure text to size the bar
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bbox = dummy.textbbox((0, 0), title, font=font)
    text_h = bbox[3] - bbox[1]

    if bar_height is not None:
        bar_h = bar_height
        text_y_offset = bar_h // 2
        pip_overhang = 0  # user positions pips explicitly
    else:
        pip_size = pip_radius * 2
        pip_overlap = pip_size // 3
        pip_overhang = pip_size - pip_overlap
        text_padding = int(font_size * 0.3)
        text_section_h = text_h + text_padding * 2
        bar_h = text_section_h + pip_overlap
        text_y_offset = text_section_h // 2

    if bar_position is not None:
        bar_y = bar_position
    else:  # default: near bottom with 5% padding
        bar_y = height - bar_h - pip_overhang - int(height * 0.05)

    # Semi-transparent black bar
    bar = Image.new("RGBA", (width, bar_h), (0, 0, 0, int(255 * bar_opacity)))
    canvas.paste(bar, (0, bar_y), bar)

    # White text centered in the bar
    draw = ImageDraw.Draw(canvas)
    text_x = width // 2
    text_y = bar_y + text_y_offset

    if text_shadow_offset:
        draw.text(
            (text_x + text_shadow_offset, text_y + text_shadow_offset),
            title,
            font=font,
            fill=(0, 0, 0, 180),
            anchor="mm",
        )
    draw.text(
        (text_x, text_y),
        title,
        font=font,
        fill=(255, 255, 255, 255),
        anchor="mm",
    )

    return bar_y, bar_h


_PIP_ORDER = ["white", "blue", "black", "red", "green", "colorless"]
_COLOR_TO_PIP = {"W": "white", "U": "blue", "B": "black", "R": "red", "G": "green", "C": "colorless"}


def _draw_color_identity(
    canvas: Image.Image,
    color_identity: list[str],
    width: int,
    bar_y: int,
    bar_h: int,
    pip_radius: int,
    pip_position: int | None,
    assets_folder: str,
) -> None:
    pip_size = pip_radius * 2
    pip_gap = int(pip_size * 0.15)

    # Load pips in WUBRG+C order, skipping any that aren't requested or can't be found
    identity_set = {c.upper() for c in color_identity}
    pips: list[Image.Image] = []
    for color_key in _PIP_ORDER:
        short = next(k for k, v in _COLOR_TO_PIP.items() if v == color_key)
        if short not in identity_set:
            continue
        pip_path = Path(assets_folder) / f"{color_key}.png"
        if not pip_path.exists():
            continue
        pip = Image.open(pip_path).convert("RGBA")
        pip = pip.resize((pip_size, pip_size), Image.LANCZOS)
        pips.append(pip)

    if not pips:
        return

    total_w = len(pips) * pip_size + (len(pips) - 1) * pip_gap
    x = (width - total_w) // 2
    pip_y = pip_position if pip_position is not None else bar_y + bar_h - pip_size // 3

    for pip in pips:
        canvas.paste(pip, (x, pip_y), pip)
        x += pip_size + pip_gap


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    font_candidates = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for path in font_candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()
