from __future__ import annotations

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
class SimplePicture:
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
            image = image.copy()
            image.thumbnail(size)
        return image

    def save(self, image):
        with io.BytesIO() as file_buffer:
            img = self.process(image)
            img.save(file_buffer, format=self.file_type)
            self.storage.delete(self.name)  # avoid any filename collisions
            self.storage.save(self.name, ContentFile(file_buffer.getvalue()))

    def delete(self):
        self.storage.delete(self.name)


class PictureFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        super().save(name, content, save)
        self.save_all()

    def save_all(self):
        if self:
            from . import tasks

            tasks.process_picture(self)

    def delete(self, save=True):
        self.delete_all()
        super().delete(save=save)

    def delete_all(self, aspect_ratios=None):
        aspect_ratios = aspect_ratios or self.aspect_ratios
        for sources in aspect_ratios.values():
            for srcset in sources.values():
                for picture in srcset.values():
                    picture.delete()

    def update_all(self, from_aspect_ratios):
        self.delete_all(from_aspect_ratios)
        self.save_all()

    @property
    def width(self):
        self._require_file()
        if (
            self._committed
            and self.field.width_field
            and hasattr(self.instance, self.field.width_field)
        ):
            # get width from width field, to avoid loading image
            return getattr(self.instance, self.field.width_field)
        return self._get_image_dimensions()[0]

    @property
    def height(self):
        self._require_file()
        if (
            self._committed
            and self.field.height_field
            and hasattr(self.instance, self.field.height_field)
        ):
            # get height from height field, to avoid loading image
            return getattr(self.instance, self.field.height_field)
        return self._get_image_dimensions()[1]

    @property
    def aspect_ratios(self):
        self._require_file()
        return self.get_picture_files(
            file_name=self.name,
            img_width=self.width,
            img_height=self.height,
            storage=self.storage,
            field=self.field,
        )

    @staticmethod
    def get_picture_files(
        *,
        file_name: str,
        img_width: int,
        img_height: int,
        storage: Storage,
        field: PictureField,
    ):
        return {
            ratio: {
                file_type: {
                    width: SimplePicture(file_name, file_type, ratio, storage, width)
                    for width in utils.source_set(
                        (img_width, img_height),
                        ratio=ratio,
                        max_width=field.container_width,
                        cols=field.grid_columns,
                    )
                }
                for file_type in field.file_types
            }
            for ratio in field.aspect_ratios
        }


class PictureField(ImageField):
    attr_class = PictureFieldFile

    def __init__(
        self,
        verbose_name=None,
        name=None,
        aspect_ratios: [str] = None,
        container_width: int = None,
        file_types: [str] = None,
        pixel_densities: [int] = None,
        grid_columns: int = None,
        breakpoints: {str: int} = None,
        **kwargs,
    ):
        settings = conf.get_settings()
        self.aspect_ratios = aspect_ratios or [None]
        self.container_width = container_width or settings.CONTAINER_WIDTH
        self.file_types = file_types or settings.FILE_TYPES
        self.pixel_densities = pixel_densities or settings.PIXEL_DENSITIES
        self.grid_columns = grid_columns or settings.GRID_COLUMNS
        self.breakpoints = breakpoints or settings.BREAKPOINTS
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
        return (
            name,
            path,
            args,
            {
                **kwargs,
                "aspect_ratios": self.aspect_ratios,
                "container_width": self.container_width,
                "file_types": self.file_types,
                "pixel_densities": self.pixel_densities,
                "grid_columns": self.grid_columns,
                "breakpoints": self.breakpoints,
            },
        )
