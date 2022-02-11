import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


@pytest.fixture
def imagedata():
    img = Image.new("RGB", (800, 800), (255, 55, 255))

    output = io.BytesIO()
    img.save(output, format="JPEG")

    return output


@pytest.fixture
def image_upload_file(imagedata):
    return SimpleUploadedFile("image.jpg", imagedata.getvalue())


@pytest.fixture(autouse=True, scope="function")
def media_root(settings, tmpdir_factory):
    settings.MEDIA_ROOT = tmpdir_factory.mktemp("media", numbered=True)
