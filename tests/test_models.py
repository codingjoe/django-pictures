import contextlib
import copy
import io
from fractions import Fraction
from pathlib import Path
from unittest.mock import Mock

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageDraw

from pictures.models import PictureField, SimplePicture
from tests.testapp.models import JPEGModel, Profile, SimpleModel


@contextlib.contextmanager
def override_field_aspect_ratios(field, aspect_ratios):
    old_ratios = copy.deepcopy(field.aspect_ratios)
    field.aspect_ratios = aspect_ratios
    try:
        yield
    finally:
        field.aspect_ratios = old_ratios


class TestSimplePicture:
    picture_with_ratio = SimplePicture(
        parent_name="testapp/simplemodel/image.png",
        file_type="WEBP",
        aspect_ratio=Fraction("4/3"),
        storage=default_storage,
        width=800,
    )

    picture_without_ratio = SimplePicture(
        parent_name="testapp/simplemodel/image.png",
        file_type="WEBP",
        aspect_ratio=None,
        storage=default_storage,
        width=800,
    )

    def test_hash(self):
        assert hash(self.picture_with_ratio) != hash(self.picture_without_ratio)
        assert hash(self.picture_with_ratio) == hash(self.picture_with_ratio)

    def test_eq(self):
        assert self.picture_with_ratio != self.picture_without_ratio
        assert self.picture_with_ratio == self.picture_with_ratio
        assert self.picture_with_ratio != "not a picture"

    def test_url(self, settings):
        settings.PICTURES["USE_PLACEHOLDERS"] = False
        assert (
            self.picture_with_ratio.url
            == "/media/testapp/simplemodel/image/4_3/800w.webp"
        )

    def test_url__placeholder(self, settings):
        settings.PICTURES["USE_PLACEHOLDERS"] = True
        assert self.picture_with_ratio.url == "/_pictures/image/4x3/800w.WEBP"

    def test_height(self):
        assert self.picture_with_ratio.height == 600
        assert not self.picture_without_ratio.height

    def test_name(self):
        assert Path(self.picture_without_ratio.name) == Path(
            "testapp/simplemodel/image/800w.webp"
        )
        assert Path(self.picture_with_ratio.name) == Path(
            "testapp/simplemodel/image/4_3/800w.webp"
        )

    def test_path(self):
        assert self.picture_with_ratio.path.is_absolute()

    def test_save(self):
        assert not self.picture_with_ratio.path.exists()
        self.picture_with_ratio.save(Image.new("RGB", (800, 800), (255, 55, 255)))
        assert self.picture_with_ratio.path.exists()

    def test_delete(self):
        self.picture_with_ratio.save(Image.new("RGB", (800, 800), (255, 55, 255)))
        assert self.picture_with_ratio.path.exists()
        self.picture_with_ratio.delete()
        assert not self.picture_with_ratio.path.exists()

    def test_process__copy(self):
        """Do not mutate input image."""
        image = Image.new("RGB", (800, 800), (255, 55, 255))
        assert SimplePicture(
            parent_name="testapp/simplemodel/image.png",
            file_type="WEBP",
            aspect_ratio=None,
            storage=default_storage,
            width=100,
        ).process(image).size == (100, 100)

        assert image.size == (800, 800), "Image was mutated."

        assert SimplePicture(
            parent_name="testapp/simplemodel/image.png",
            file_type="WEBP",
            aspect_ratio="4/3",
            storage=default_storage,
            width=400,
        ).process(image).size == (400, 300)

        assert image.size == (800, 800), "Image was mutated."


class TestPictureFieldFile:

    @pytest.mark.django_db
    def test_symmetric_difference(self, image_upload_file):
        obj = SimpleModel.objects.create(picture=image_upload_file)
        assert obj.picture ^ obj.picture == (set(), set())
        obj2 = Profile.objects.create(picture=image_upload_file)
        with pytest.raises(TypeError):
            obj.picture ^ "not a picture"
        assert obj.picture ^ obj2.picture == (
            {
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=300,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=600,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=500,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=500,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=300,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=700,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=800,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=200,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=300,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=700,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=100,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=400,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=800,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=100,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=700,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=200,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=600,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=500,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=800,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=200,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=100,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=400,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=600,
                ),
                SimplePicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=400,
                ),
            },
            {
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=600,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=300,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=800,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=500,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=700,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=100,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=500,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=700,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=800,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=200,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=100,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=600,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=100,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=700,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=800,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=200,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=500,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=800,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=300,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=300,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=600,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=700,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=400,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=400,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=400,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=200,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=300,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=600,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=100,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=200,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=400,
                ),
                SimplePicture(
                    parent_name="testapp/profile/image.png",
                    file_type="WEBP",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=500,
                ),
            },
        )

    @pytest.mark.django_db
    def test_save(self, stub_worker, image_upload_file):
        obj = SimpleModel(picture=image_upload_file)
        obj.save()
        stub_worker.join()

        assert default_storage.exists(obj.picture.name)
        assert obj.picture.aspect_ratios["16/9"]["WEBP"][100].path.exists()

    @pytest.mark.django_db
    def test_save_JPEG_RGA(self, stub_worker, image_upload_file):
        obj = JPEGModel(picture=image_upload_file)
        obj.save()
        stub_worker.join()

        assert default_storage.exists(obj.picture.name)
        assert obj.picture.aspect_ratios["16/9"]["JPEG"][100].path.exists()

    @pytest.mark.django_db
    def test_exif_transpose(self, stub_worker):
        img = Image.new("RGB", (600, 800), (255, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle((300, 0, 600, 800), fill=(0, 0, 255))  # blue is on the right
        exif = img.getexif()
        exif[0x0112] = 8  # pretend to be rotated by 90 degrees

        with io.BytesIO() as output:
            img.save(output, format="JPEG", exif=exif)
            image_file = SimpleUploadedFile("image.jpg", output.getvalue())

        obj = SimpleModel(picture=image_file)
        obj.save()
        stub_worker.join()

        assert default_storage.exists(obj.picture.name)
        assert obj.picture.aspect_ratios["16/9"]["WEBP"][100].path.exists()
        with Image.open(
            obj.picture.aspect_ratios["16/9"]["WEBP"][100].path
        ) as img_small:
            assert img_small.size == (100, 56)
            pixels = img_small.load()
            assert pixels[0, 0] == (2, 0, 255)  # blue is on the top, always blue!

    @pytest.mark.django_db
    def test_save__is_blank(self, monkeypatch):
        obj = SimpleModel()
        save_all = Mock()
        monkeypatch.setattr("pictures.models.PictureFieldFile.save_all", save_all)
        obj.save()
        assert not save_all.called

    @pytest.mark.django_db
    def test_delete(self, stub_worker, image_upload_file):
        obj = SimpleModel(picture=image_upload_file)
        obj.save()
        stub_worker.join()

        name = obj.picture.name
        path = obj.picture.aspect_ratios["16/9"]["WEBP"][100].path
        assert default_storage.exists(name)
        assert path.exists()

        obj.picture.delete()
        stub_worker.join()
        assert not default_storage.exists(name)
        assert not path.exists()

    @pytest.mark.django_db
    def test_update_all(self, stub_worker, image_upload_file):
        obj = SimpleModel(picture=image_upload_file)
        obj.save()
        stub_worker.join()

        name = obj.picture.name
        path = obj.picture.aspect_ratios["16/9"]["WEBP"][100].path
        assert default_storage.exists(name)
        assert path.exists()

        old = copy.deepcopy(obj.picture)
        with override_field_aspect_ratios(obj.picture.field, ["1/1"]):
            obj.picture.update_all(old)
            stub_worker.join()
            assert default_storage.exists(name)
            assert obj.picture.aspect_ratios["1/1"]["WEBP"][100].path.exists()
            assert not path.exists()


class TestPictureField:
    @pytest.mark.django_db
    def test_integration(self, image_upload_file):
        obj = SimpleModel.objects.create(picture=image_upload_file)
        assert obj.picture.aspect_ratios == {
            None: {
                "WEBP": {
                    800: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=800,
                    ),
                    100: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=100,
                    ),
                    200: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=200,
                    ),
                    300: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=300,
                    ),
                    400: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=400,
                    ),
                    500: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=500,
                    ),
                    600: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=600,
                    ),
                    700: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=700,
                    ),
                }
            },
            "3/2": {
                "WEBP": {
                    800: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=800,
                    ),
                    100: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=100,
                    ),
                    200: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=200,
                    ),
                    300: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=300,
                    ),
                    400: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=400,
                    ),
                    500: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=500,
                    ),
                    600: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=600,
                    ),
                    700: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=700,
                    ),
                }
            },
            "16/9": {
                "WEBP": {
                    800: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=800,
                    ),
                    100: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=100,
                    ),
                    200: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=200,
                    ),
                    300: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=300,
                    ),
                    400: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=400,
                    ),
                    500: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=500,
                    ),
                    600: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=600,
                    ),
                    700: SimplePicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="WEBP",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=700,
                    ),
                }
            },
        }

    def test_check_aspect_ratios(self):
        assert not PictureField()._check_aspect_ratios()
        errors = PictureField(aspect_ratios=["not-a-ratio"])._check_aspect_ratios()
        assert errors
        assert errors[0].id == "fields.E100"

    def test_check_width_height_field(self):
        assert not PictureField(aspect_ratios=["3/2"])._check_width_height_field()
        with override_field_aspect_ratios(Profile.picture.field, [None]):
            errors = Profile.picture.field._check_width_height_field()
        assert errors
        assert errors[0].id == "fields.E101"
        assert errors[0].hint.startswith(
            "Please add two positive integer fields to 'testapp.Profile'"
        )

    def test_check(self):
        assert not SimpleModel._meta.get_field("picture").check()
        assert Profile._meta.get_field("picture").check()
