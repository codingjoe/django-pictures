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

    def __init__(self, **kwargs):
        self.aspect_ratios = kwargs.pop("aspect_ratios", None)
        super().__init__(**kwargs)

    def to_representation(self, obj: PictureFieldFile):
        if self.aspect_ratios is None:
            return json.loads(json.dumps(obj.aspect_ratios, default=default))

        for ratio in self.aspect_ratios:
            if ratio not in obj.aspect_ratios:
                raise ValueError(
                    f"Invalid ratio: {ratio}. Choices are: {', '.join(filter(None, obj.aspect_ratios.keys()))}"
                )
        return json.loads(
            json.dumps(
                {ratio: obj.aspect_ratios[ratio] for ratio in self.aspect_ratios},
                default=default,
            )
        )
