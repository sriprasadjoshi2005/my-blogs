import os
import random

from django.conf import settings
from django.templatetags.static import static

from .models import SiteProfile

IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}


def _background_urls():
    """Every picture you drop into static/backgrounds/ is picked up automatically."""
    folder = settings.BASE_DIR / "static" / "backgrounds"
    try:
        names = sorted(n for n in os.listdir(folder) if os.path.splitext(n)[1].lower() in IMAGE_TYPES)
    except FileNotFoundError:
        names = []
    return [static(f"backgrounds/{name}") for name in names]


def site_wide(request):
    urls = _background_urls()
    mode = settings.BACKGROUND_MODE
    if mode == "random" and urls:
        urls = [random.choice(urls)]
    return {
        "SITE_NAME": settings.SITE_NAME,
        "profile": SiteProfile.load(),
        "background_urls": urls,
        "background_rotate": mode != "random" and len(urls) > 1,
    }
