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
