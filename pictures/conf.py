from __future__ import annotations

from django.conf import settings as django_settings
from django.core.signals import setting_changed
from django.utils.functional import SimpleLazyObject, empty

__all__ = ["app_settings"]


def get_settings():
    return type(
        "Settings",
        (),
        {
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
            "USE_PLACEHOLDERS": django_settings.DEBUG,
            "QUEUE_NAME": "pictures",
            "BACKEND": "default",
            "PICTURE_CLASS": "pictures.models.PillowPicture",
            "PROCESSOR": "pictures.tasks.process_picture",
            **getattr(django_settings, "PICTURES", {}),
        },
    )


class LazySettings(SimpleLazyObject):
    def _reset(self, *, setting="PICTURES", **kwargs):
        if setting in {"PICTURES", "DEBUG"}:
            self._wrapped = empty


app_settings = LazySettings(get_settings)

setting_changed.connect(app_settings._reset)
