from django import template
from django.template import loader

from .. import utils
from ..conf import get_settings

register = template.Library()


@register.simple_tag()
def picture(field_file, alt=None, ratio=None, container=None, **kwargs):
    settings = get_settings()
    container = container or settings.CONTAINER_WIDTH
    tmpl = loader.get_template("pictures/picture.html")
    breakpoints = {}
    attrs = {}
    try:
        sources = field_file.aspect_ratios[ratio]
    except KeyError as e:
        raise ValueError(
            f"Invalid ratio: {ratio}. Choices are: {', '.join(filter(None, field_file.aspect_ratios.keys()))}"
        ) from e
    for key, value in kwargs.items():
        if key in settings.BREAKPOINTS:
            breakpoints[key] = value
        else:
            attrs[key] = value
    return tmpl.render(
        {
            "field_file": field_file,
            "alt": alt,
            "ratio": (ratio or "3/2").replace("/", "x"),
            "sources": sources,
            "media": utils.sizes(container_width=container, **breakpoints),
            "attrs": attrs,
            "use_placeholders": settings.USE_PLACEHOLDERS,
        }
    )


@register.simple_tag()
def img_url(field_file, file_type, width, ratio=None) -> str:
    """
    Return the URL for a specific image file.

    This may be useful for use-cases like emails, where you can't use a picture tag.
    """
    try:
        file_types = field_file.aspect_ratios[ratio]
    except KeyError as e:
        raise ValueError(
            f"Invalid ratio: {ratio}. Choices are: {', '.join(filter(None, field_file.aspect_ratios.keys()))}"
        ) from e
    try:
        sizes = file_types[file_type.upper()]
    except KeyError as e:
        raise ValueError(
            f"Invalid file type: {file_type}. Choices are: {', '.join(file_types.keys())}"
        ) from e
    for w, img in sorted(sizes.items()):
        url = img.url
        if w >= width:
            break
    return url
