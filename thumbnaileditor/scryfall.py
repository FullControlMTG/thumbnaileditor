import hashlib
from pathlib import Path

import requests
from PIL import Image


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
