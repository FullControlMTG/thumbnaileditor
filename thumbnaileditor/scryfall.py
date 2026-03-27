import hashlib
import re
from pathlib import Path

import requests
from PIL import Image

_SCRYFALL_CARD_URL_RE = re.compile(r"https?://scryfall\.com/card/([^/?#]+)/([^/?#]+)")


def resolve_image_url(url: str) -> str:
    """If url is a Scryfall card page URL, resolve it to an art_crop image URL via the API.
    Otherwise return the url unchanged."""
    m = _SCRYFALL_CARD_URL_RE.match(url)
    if not m:
        return url
    set_code, collector_number = m.group(1), m.group(2)
    response = requests.get(
        f"https://api.scryfall.com/cards/{set_code}/{collector_number}",
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["image_uris"]["art_crop"]


def fetch_image(url: str, cache_folder: str | Path) -> Image.Image:
    """Download a card image by URL, caching to disk. Returns a PIL Image."""
    cache_dir = Path(cache_folder)
    cache_dir.mkdir(parents=True, exist_ok=True)

    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    cached_path = cache_dir / f"{url_hash}.png"

    if not cached_path.exists():
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        with open(cached_path, "wb") as f:
            f.write(response.content)

    return Image.open(cached_path).convert("RGBA")
