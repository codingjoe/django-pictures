import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from pictures import validators
from tests.testapp.models import ValidatorModel


class TestBaseSizeValidator:
    def test_init__none(self):
        assert validators.MinSizeValidator(None, None).limit_value == (
            float("inf"),
            float("inf"),
        )

    def test_compare(self):
        assert validators.BaseSizeValidator(None, None).compare(None) == NotImplemented


class TestMaxSizeValidator:
    def test_compare__inf(self):
        limit_value = float("inf"), float("inf")
        instance = validators.MaxSizeValidator(*limit_value)
        assert not instance.compare((300, 200), limit_value)

    def test_compare__eq(self):
        assert not validators.MaxSizeValidator(300, 200).compare((300, 200), (300, 200))

    def test_compare__gt(self):
        limit_value = 300, 200
        instance = validators.MaxSizeValidator(*limit_value)
        assert instance.compare((600, 400), limit_value)
        assert instance.compare((600, 200), limit_value)
        assert instance.compare((300, 400), limit_value)
        assert instance.compare((600, 100), limit_value)
        assert instance.compare((150, 400), limit_value)

    def test_compare__lt(self):
        limit_value = 300, 200
        instance = validators.MaxSizeValidator(*limit_value)
        assert not instance.compare((150, 100), (300, 200))
        assert not instance.compare((300, 100), (300, 200))
        assert not instance.compare((150, 200), (300, 200))

    @pytest.mark.django_db
    def test_integration(self):
        img = Image.new("RGB", (800, 800), (255, 55, 255))

        with io.BytesIO() as output:
            img.save(output, format="JPEG")
            file = SimpleUploadedFile("image.jpg", output.getvalue())

        obj = ValidatorModel(picture=file)
        with pytest.raises(ValidationError) as e:
            obj.full_clean()

        assert "The required maximum resolution is: 800x600 px." in str(
            e.value.error_dict["picture"][0]
        )


class TestMinSizeValidator:
    def test_compare__inf(self):
        limit_value = float("inf"), float("inf")
        instance = validators.MinSizeValidator(*limit_value)
        assert instance.compare((300, 200), limit_value)

    def test_compare__eq(self):
        assert not validators.MinSizeValidator(300, 200).compare((300, 200), (300, 200))

    def test_compare__gt(self):
        limit_value = 300, 200
        instance = validators.MinSizeValidator(*limit_value)
        assert not instance.compare((600, 400), limit_value)
        assert not instance.compare((600, 200), limit_value)
        assert not instance.compare((300, 400), limit_value)
        assert instance.compare((600, 100), limit_value)
        assert instance.compare((150, 400), limit_value)

    def test_compare__lt(self):
        limit_value = 300, 200
        instance = validators.MinSizeValidator(*limit_value)
        assert instance.compare((150, 100), (300, 200))
        assert instance.compare((300, 100), (300, 200))
        assert instance.compare((150, 200), (300, 200))

    @pytest.mark.django_db
    def test_integration(self):
        img = Image.new("RGB", (300, 200), (255, 55, 255))

        with io.BytesIO() as output:
            img.save(output, format="JPEG")
            file = SimpleUploadedFile("image.jpg", output.getvalue())

        obj = ValidatorModel(picture=file)
        with pytest.raises(ValidationError) as e:
            obj.full_clean()

        assert "The required minimum resolution is: 400x300 px." in str(
            e.value.error_dict["picture"][0]
        )
