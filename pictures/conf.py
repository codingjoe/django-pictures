from __future__ import annotations

import django.conf
from django.test.signals import setting_changed

DEFAULTS = {
    "BREAKPOINTS": {
        "xs": 576,
        "s": 768,
        "m": 992,
        "l": 1200,
        "xl": 1400,
    },
    "GRID_COLUMNS": 12,
    "CONTAINER_WIDTH": 1200,
    "FILE_TYPES": ["AVIF"],
    "PIXEL_DENSITIES": [1, 2],
    "QUEUE_NAME": "pictures",
    "BACKEND": "default",
    "PICTURE_CLASS": "pictures.models.PillowPicture",
    "PROCESSOR": "pictures.tasks.process_picture",
}


class Settings:
    """Lazy, cached settings accessor for django-pictures."""

    def __init__(self):
        self._cache = None

    def __getattr__(self, name: str):
        if self._cache is None:
            self._cache = {
                **DEFAULTS,
                "USE_PLACEHOLDERS": django.conf.settings.DEBUG,
                **getattr(django.conf.settings, "PICTURES", {}),
            }
        try:
            return self._cache[name]
        except KeyError:
            raise AttributeError(f"Invalid setting: {name!r}")

    def reload(self):
        """Reload settings, clearing the cache."""
        self._cache = None


settings = Settings()


def _reload_settings(*, setting, **kwargs):
    if setting in {"PICTURES", "DEBUG"}:
        settings.reload()


setting_changed.connect(_reload_settings)


def get_settings() -> Settings:
    """Return the current pictures settings."""
    return settings
