import json

from rest_framework import serializers

__all__ = ["PictureField"]

from pictures import utils
from pictures.conf import get_settings
from pictures.models import PictureFieldFile, SimplePicture


def default(obj):
    if isinstance(obj, SimplePicture):
        return obj.url
    raise TypeError(f"Type '{type(obj).__name__}' not serializable")


class PictureField(serializers.ReadOnlyField):
    """Read-only field for all aspect ratios and sizes of the image."""

    def __init__(self, ratio=None, container=None, **kwargs):
        self.ratio = ratio
        self.container = container
        self.breakpoints = {
            bp: kwargs.pop(bp) for bp in get_settings().BREAKPOINTS if bp in kwargs
        }
        super().__init__(**kwargs)

    def to_representation(self, obj: PictureFieldFile):
        if self.ratio is None:
            return json.loads(json.dumps(obj.aspect_ratios, default=default))

        try:
            sources = obj.aspect_ratios[self.ratio]
        except KeyError as e:
            raise ValueError(
                f"Invalid ratio: {self.ratio}. Choices are: {', '.join(filter(None, obj.aspect_ratios.keys()))}"
            ) from e

        return json.loads(
            json.dumps(
                {
                    "sources": sources,
                    "media": utils.sizes(
                        container_width=self.container, **self.breakpoints
                    ),
                },
                default=default,
            )
        )
