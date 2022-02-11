from django.conf import settings


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
            "FILE_TYPES": ["WEBP"],
            "PIXEL_DENSITIES": [1, 2],
            "USE_PLACEHOLDERS": settings.DEBUG,
        }
        | getattr(settings, "PICTURES", {}),
    )
