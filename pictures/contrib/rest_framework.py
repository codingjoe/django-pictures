import json

from django.http import QueryDict
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

    def __init__(self, aspect_ratio=None, image_source=None, **kwargs):
        self.aspect_ratio = aspect_ratio
        self.image_source = image_source
        super().__init__(**kwargs)

    def to_representation(self, obj: PictureFieldFile):
        if not obj:
            return None

        base_payload = {
            "url": obj.url,
            "width": obj.width,
            "height": obj.height,
        }

        # if aspect_ratio is set, only return that aspect ratio to reduce payload size
        if self.aspect_ratio and self.image_source:
            try:
                sizes = obj.aspect_ratios[self.aspect_ratio][self.image_source]
            except KeyError as e:
                raise ValueError(
                    f"Invalid ratio {self.aspect_ratio} or image source {self.image_source}. Choices are: {', '.join(filter(None, obj.aspect_ratios.keys()))}"
                ) from e
            payload = {
                **base_payload,
                "ratios": {
                    self.aspect_ratio: {
                        "sources": {f"image/{self.image_source.lower()}": sizes}
                    }
                },
            }
        else:
            payload = {
                **base_payload,
                "ratios": {
                    ratio: {
                        "sources": {
                            f"image/{file_type.lower()}": sizes
                            for file_type, sizes in sources.items()
                        },
                    }
                    for ratio, sources in obj.aspect_ratios.items()
                },
            }

        # if the request has query parameters, filter the payload
        try:
            query_params: QueryDict = self.context["request"].GET
        except KeyError:
            pass
        else:
            ratio = query_params.get(f"{self.field_name}_ratio")
            container = query_params.get(f"{self.field_name}_container")
            try:
                container = int(container)
            except TypeError:
                container = None
            except ValueError as e:
                raise ValueError(f"Container width is not a number: {container}") from e
            breakpoints = {
                bp: int(query_params.get(f"{self.field_name}_{bp}"))
                for bp in get_settings().BREAKPOINTS
                if f"{self.field_name}_{bp}" in query_params
            }
            if ratio is not None:
                try:
                    payload["ratios"] = {ratio: payload["ratios"][ratio]}
                except KeyError as e:
                    raise ValueError(
                        f"Invalid ratio: {ratio}. Choices are: {', '.join(filter(None, obj.aspect_ratios.keys()))}"
                    ) from e
                else:
                    payload["ratios"][ratio]["media"] = utils.sizes(
                        container_width=container, **breakpoints
                    )

        return json.loads(json.dumps(payload, default=default))
