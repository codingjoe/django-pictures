import dataclasses
import io
import math
from fractions import Fraction
from pathlib import Path

from django.core import checks
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.db.models import ImageField
from django.db.models.fields.files import ImageFieldFile
from PIL import Image, ImageOps

__all__ = ["PictureField", "PictureFieldFile"]

from pictures import conf, utils


@dataclasses.dataclass
class SimpelPicture:
    """A simple picture class similar to Django's image class."""

    parent_name: str
    file_type: str
    aspect_ratio: str | Fraction | None
    storage: Storage
    width: int

    def __post_init__(self):
        self.aspect_ratio = Fraction(self.aspect_ratio) if self.aspect_ratio else None

    @property
    def url(self) -> str:
        return self.storage.url(self.name)

    @property
    def height(self) -> int or None:
        if self.aspect_ratio:
            return math.floor(self.width / self.aspect_ratio)

    @property
    def name(self) -> str:
        path = Path(self.parent_name).with_suffix("")
        if self.aspect_ratio:
            path /= str(self.aspect_ratio).replace("/", "_")
        return str(path / f"{self.width}w.{self.file_type.lower()}")

    @property
    def path(self) -> Path:
        return Path(self.storage.path(self.name))

    def process(self, image) -> Image:
        height = self.height or self.width / Fraction(*image.size)
        size = math.floor(self.width), math.floor(height)

        if self.aspect_ratio:
            image = ImageOps.fit(image, size)
        else:
            image.thumbnail(size)
        return image

    def save(self, image):
        with io.BytesIO() as file_buffer:
            img = self.process(image)
            img.save(file_buffer, format=self.file_type)
            self.storage.save(self.name, ContentFile(file_buffer.getvalue()))

    def delete(self):
        self.storage.delete(self.name)


class PictureFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        super().save(name, content, save)
        self.process_all()

    def delete(self, save=True):
        for sources in self.aspect_ratios.values():
            for srcset in sources.values():
                for picture in srcset.values():
                    picture.delete()

        super().delete(save=save)

    @property
    def width(self):
        self._require_file()
        if self._committed and self.field.width_field:
            # get width from width field, to avoid loading image
            return getattr(self.instance, self.field.width_field)
        return self._get_image_dimensions()[0]

    @property
    def height(self):
        self._require_file()
        if self._committed and self.field.height_field:
            # get height from height field, to avoid loading image
            return getattr(self.instance, self.field.height_field)
        return self._get_image_dimensions()[1]

    @property
    def aspect_ratios(self):
        self._require_file()
        settings = conf.get_settings()
        return {
            ratio: {
                file_type: {
                    width: SimpelPicture(
                        self.name, file_type, ratio, self.storage, width
                    )
                    for width in utils.source_set(
                        (self.width, self.height),
                        ratio=ratio,
                        max_width=settings.CONTAINER_WIDTH,
                        cols=settings.GRID_COLUMNS,
                    )
                }
                for file_type in settings.FILE_TYPES
            }
            for ratio in self.field.aspect_ratios
        }

    def process_all(self):
        with Image.open(self.file) as img:
            for ratio, sources in self.aspect_ratios.items():
                for file_type, srcset in sources.items():
                    for width, picture in srcset.items():
                        picture.save(img)


class PictureField(ImageField):
    attr_class = PictureFieldFile

    def __init__(
        self,
        verbose_name=None,
        name=None,
        aspect_ratios: [str] = None,
        **kwargs,
    ):
        self.aspect_ratios = aspect_ratios or [None]
        super().__init__(
            verbose_name=verbose_name,
            name=name,
            **kwargs,
        )

    def check(self, **kwargs):
        return (
            super().check(**kwargs)
            + self._check_aspect_ratios()
            + self._check_width_height_field()
        )

    def _check_aspect_ratios(self):
        errors = []
        if self.aspect_ratios:
            for ratio in self.aspect_ratios:
                if ratio is not None:
                    try:
                        Fraction(ratio)
                    except ValueError:
                        errors.append(
                            checks.Error(
                                "Invalid aspect ratio",
                                obj=self,
                                id="fields.E100",
                                hint="Aspect ratio must be a fraction, e.g. '16/9'",
                            )
                        )
        return errors

    def _check_width_height_field(self):
        if None in self.aspect_ratios and not (self.width_field and self.height_field):
            return [
                checks.Warning(
                    "width_field and height_field attributes are missing",
                    obj=self,
                    id="fields.E101",
                    hint="Set both the width_field and height_field attribute to avoid storage IO",
                )
            ]
        return []

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["aspect_ratios"] = self.aspect_ratios
        return name, path, args, kwargs
