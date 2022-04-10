import json

from rest_framework import serializers

__all__ = ["PictureField"]

from pictures.models import PictureFieldFile, SimplePicture


def default(obj):
    if isinstance(obj, SimplePicture):
        return obj.url
    raise TypeError(f"Type '{type(obj).__name__}' not serializable")


class PictureField(serializers.ReadOnlyField):
    """Read-only field for all aspect ratios and sizes of the image."""

    def to_representation(self, obj: PictureFieldFile):
        return json.loads(json.dumps(obj.aspect_ratios, default=default))
