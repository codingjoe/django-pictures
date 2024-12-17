import json

from django.http import QueryDict
from rest_framework import serializers

__all__ = ["PictureField"]

from pictures import utils
from pictures.models import Picture, PictureFieldFile


def default(obj):
    if isinstance(obj, Picture):
        return obj.url
    raise TypeError(f"Type '{type(obj).__name__}' not serializable")


class PictureField(serializers.ReadOnlyField):
    """Read-only field for all aspect ratios and sizes of the image."""

    def __init__(self, aspect_ratios=None, file_types=None, **kwargs):
        super().__init__(**kwargs)
        self.aspect_ratios = aspect_ratios or []
        self.file_types = file_types or []

    def to_representation(self, obj: PictureFieldFile):
        if not obj:
            return None

        base_payload = {
            "url": obj.url,
            "width": obj.width,
            "height": obj.height,
        }
        field = obj.field

        # if the request has query parameters, filter the payload
        try:
            query_params: QueryDict = self.context["request"].GET
        except KeyError:
            ratios = self.aspect_ratios
            container = field.container_width
            breakpoints = {}
        else:
            ratios = (
                query_params.getlist(f"{self.field_name}_ratio")
            ) or self.aspect_ratios
            container = query_params.get(f"{self.field_name}_container")
            try:
                container = int(container)
            except TypeError:
                container = field.container_width
            except ValueError as e:
                raise ValueError(f"Container width is not a number: {container}") from e
            breakpoints = {
                bp: int(query_params.get(f"{self.field_name}_{bp}"))
                for bp in field.breakpoints
                if f"{self.field_name}_{bp}" in query_params
            }
            if set(ratios) - set(self.aspect_ratios or obj.aspect_ratios.keys()):
                raise ValueError(
                    f"Invalid ratios: {', '.join(ratios)}. Choices are: {', '.join(filter(None, obj.aspect_ratios.keys()))}"
                )

        payload = {
            **base_payload,
            "ratios": {
                ratio: {
                    "sources": {
                        f"image/{file_type.lower()}": sizes
                        for file_type, sizes in sources.items()
                        if file_type in self.file_types or not self.file_types
                    },
                    "media": utils.sizes(
                        field=field, container_width=container, **breakpoints
                    ),
                }
                for ratio, sources in obj.aspect_ratios.items()
                if ratio in ratios or not ratios
            },
        }

        return json.loads(json.dumps(payload, default=default))
