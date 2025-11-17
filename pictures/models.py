from __future__ import annotations

import abc
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
from django.urls import reverse
from django.utils.module_loading import import_string
from PIL import Image, ImageOps

from pictures import conf, utils

__all__ = ["PictureField", "PictureFieldFile", "Picture"]

RGB_FORMATS = ["JPEG"]


@dataclasses.dataclass
class Picture(abc.ABC):
    """
    An abstract picture class similar to Django's image class.

    Subclasses will need to implement the `url` property.
    """

    parent_name: str
    file_type: str
    aspect_ratio: str | Fraction | None
    storage: Storage
    width: int

    def __post_init__(self):
        self.aspect_ratio = Fraction(self.aspect_ratio) if self.aspect_ratio else None

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.deconstruct() == other.deconstruct()

    def deconstruct(self):
        return (
            f"{self.__class__.__module__}.{self.__class__.__qualname__}",
            (
                self.parent_name,
                self.file_type,
                str(self.aspect_ratio) if self.aspect_ratio else None,
                self.storage.deconstruct(),
                self.width,
            ),
            {},
        )

    @property
    @abc.abstractmethod
    def url(self) -> str:
        """Return the URL of the picture."""


class PillowPicture(Picture):
    """Use the Pillow library to process images."""

    @property
    def url(self) -> str:
        if conf.get_settings().USE_PLACEHOLDERS:
            return reverse(
                "pictures:placeholder",
                kwargs={
                    "alt": Path(self.parent_name).stem,
                    "width": self.width,
                    "ratio": (
                        f"{self.aspect_ratio.numerator}x{self.aspect_ratio.denominator}"
                        if self.aspect_ratio
                        else None
                    ),
                    "file_type": self.file_type,
                },
            )
        return self.storage.url(self.name)

    @property
    def height(self) -> int | None:
        if self.aspect_ratio:
            return math.floor(self.width / self.aspect_ratio)
        return None

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
        image = ImageOps.exif_transpose(image)  # crates a copy
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
            if (self.file_type in RGB_FORMATS) and (img.mode != "RGB"):
                img = img.convert("RGB")
            img.save(file_buffer, format=self.file_type)
            self.storage.delete(self.name)  # avoid any filename collisions
            self.storage.save(self.name, ContentFile(file_buffer.getvalue()))

    def delete(self):
        self.storage.delete(self.name)


class PictureFieldFile(ImageFieldFile):
    def __xor__(self, other) -> tuple[set[Picture], set[Picture]]:
        """Return the new and obsolete :class:`Picture` instances."""
        if not isinstance(other, PictureFieldFile):
            return NotImplemented
        new = self.get_picture_files_list() - other.get_picture_files_list()
        obsolete = other.get_picture_files_list() - self.get_picture_files_list()

        return new, obsolete

    def save(self, name, content, save=True):
        super().save(name, content, save)
        self.save_all()

    def save_all(self):
        self.update_all()

    def delete(self, save=True):
        self.delete_all()
        super().delete(save=save)

    def delete_all(self):
        if self:
            import_string(conf.get_settings().PROCESSOR)(
                self.storage.deconstruct(),
                self.name,
                [],
                [i.deconstruct() for i in self.get_picture_files_list()],
                self.instance_name,
            )

    def update_all(self, other: PictureFieldFile | None = None):
        if self:
            if not other:
                new = self.get_picture_files_list()
                old = []
            else:
                new, old = self ^ other
            import_string(conf.get_settings().PROCESSOR)(
                self.storage.deconstruct(),
                self.name,
                [i.deconstruct() for i in new],
                [i.deconstruct() for i in old],
                self.instance_name,
            )

    @property
    def instance_name(self):
        return f"{self.instance._meta.app_label}.{self.instance._meta.model_name}.{self.field.name}"

    @property
    def width(self):
        self._require_file()
        if self._committed and self.field.width_field:  # NoQA SIM102
            if width := getattr(self.instance, self.field.width_field, None):
                # get width from width field, to avoid loading image
                return width
        return self._get_image_dimensions()[0]

    @property
    def height(self):
        self._require_file()
        if self._committed and self.field.height_field:  # NoQA SIM102
            if height := getattr(self.instance, self.field.height_field, None):
                # get height from height field, to avoid loading image
                return height
        return self._get_image_dimensions()[1]

    @property
    def aspect_ratios(self) -> {Fraction | None: {str: {int: Picture}}}:
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
    ) -> {Fraction | None: {str: {int: Picture}}}:
        PictureClass = import_string(conf.get_settings().PICTURE_CLASS)
        return {
            ratio: {
                file_type: {
                    width: PictureClass(file_name, file_type, ratio, storage, width)
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

    def get_picture_files_list(self) -> set[Picture]:
        return {
            picture
            for sources in self.aspect_ratios.values()
            for srcset in sources.values()
            for picture in srcset.values()
        }


class PictureField(ImageField):
    attr_class = PictureFieldFile

    def __init__(
        self,
        verbose_name=None,
        name=None,
        aspect_ratios: list[str | Fraction | None] = None,
        container_width: int = None,
        file_types: list[str] = None,
        pixel_densities: list[int] = None,
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
                    hint=f"Please add two positive integer fields to '{self.model._meta.app_label}.{self.model.__name__}' and add their field names as the 'width_field' and 'height_field' attribute for your picture field. Otherwise Django will not be able to cache the image aspect size causing disk IO and potential response time increases.",
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
