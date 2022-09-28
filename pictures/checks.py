from django.core.checks import Error, Tags, register
from django.urls import NoReverseMatch, reverse

from . import conf

__all__ = ["placeholder_url_check"]


@register(Tags.urls)
def placeholder_url_check(app_configs, **kwargs):
    errors = []
    if conf.get_settings().USE_PLACEHOLDERS:
        try:
            reverse(
                "pictures:placeholder",
                kwargs={
                    "alt": "test",
                    "width": 100,
                    "ratio": "1x1",
                    "file_type": "jpg",
                },
            )
        except NoReverseMatch:
            errors.append(
                Error(
                    "Placeholder URLs are not configured correctly.",
                    hint=(
                        'PICTURES["USE_PLACEHOLDERS"] is True,'
                        ' but include("pictures.urls") is missing for your URL config.'
                    ),
                    id="pictures.E001",
                )
            )
    return errors
