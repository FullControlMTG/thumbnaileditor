import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .config import Config
from .project import ProjectConfig
from .scryfall import fetch_image


def render_thumbnail(project_config: ProjectConfig, env_config: Config) -> Image.Image:
    """Compose and return the final thumbnail as a PIL Image."""
    # Resolve effective settings (project overrides env defaults)
    width, height = _resolve_resolution(project_config, env_config)
    card_scale = project_config.card_scale or env_config.card_scale
    card_overlap = project_config.card_overlap or env_config.card_overlap
    font_size = project_config.title_font_size or env_config.title_font_size
    bar_opacity = project_config.title_bar_opacity or env_config.title_bar_opacity
    bar_position = project_config.title_bar_position or env_config.title_bar_position

    canvas = Image.new("RGBA", (width, height))

    # 1. Background
    bg = fetch_image(project_config.background_card, env_config.cache_folder)
    bg = _fill_and_blur(bg, width, height)
    canvas.paste(bg, (0, 0))

    # 2. Foreground cards
    card_height = int(height * card_scale)
    cards = [
        fetch_image(url, env_config.cache_folder)
        for url in project_config.foreground_cards
    ]
    cards = [_scale_to_height(img, card_height) for img in cards]
    _paste_foreground_cards(canvas, cards, width, height, card_overlap)

    # 3. Title bar + text
    _draw_title(canvas, project_config.title, width, height, font_size, bar_opacity, bar_position)

    return canvas.convert("RGB")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_resolution(project_config: ProjectConfig, env_config: Config) -> tuple[int, int]:
    if project_config.output_resolution:
        w, h = project_config.output_resolution.lower().split("x")
        return int(w), int(h)
    return env_config.output_resolution


def _fill_and_blur(img: Image.Image, width: int, height: int) -> Image.Image:
    """Scale image to fill the frame (crop to fit), then blur."""
    img_ratio = img.width / img.height
    frame_ratio = width / height

    if img_ratio > frame_ratio:
        # Image is wider — match height, crop width
        new_h = height
        new_w = int(new_h * img_ratio)
    else:
        # Image is taller — match width, crop height
        new_w = width
        new_h = int(new_w / img_ratio)

    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - width) // 2
    top = (new_h - height) // 2
    img = img.crop((left, top, left + width, top + height))
    return img.filter(ImageFilter.GaussianBlur(radius=12))


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
) -> None:
    n = len(cards)
    # Total visual width = sum of card widths minus overlapping portions
    card_w = cards[0].width  # all scaled to same height so widths are similar
    total_w = sum(c.width for c in cards) - int(card_w * overlap) * (n - 1)

    x = (width - total_w) // 2
    y = (height - cards[0].height) // 2 + int(height * 0.04)  # slightly below center

    for i, card in enumerate(cards):
        # Slight alternating tilt for a dynamic look
        angle = (i - (n - 1) / 2) * 3.5
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
    bar_position: str,
) -> None:
    font = _load_font(font_size)

    # Measure text to size the bar
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bbox = dummy.textbbox((0, 0), title, font=font)
    text_h = bbox[3] - bbox[1]
    bar_h = text_h + int(font_size * 0.7)

    if bar_position == "top":
        bar_y = int(height * 0.05)
    else:  # bottom
        bar_y = height - bar_h - int(height * 0.05)

    # Semi-transparent black bar
    bar = Image.new("RGBA", (width, bar_h), (0, 0, 0, int(255 * bar_opacity)))
    canvas.paste(bar, (0, bar_y), bar)

    # White text centered on the bar
    draw = ImageDraw.Draw(canvas)
    text_x = width // 2
    text_y = bar_y + bar_h // 2

    # Stroke (outline) for legibility
    stroke_w = max(2, font_size // 20)
    draw.text(
        (text_x, text_y),
        title,
        font=font,
        fill=(255, 255, 255, 255),
        anchor="mm",
        stroke_width=stroke_w,
        stroke_fill=(0, 0, 0, 200),
    )


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
