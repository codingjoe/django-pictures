import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from pictures import conf


@pytest.fixture(scope="session")
def image_upload_file():
    img = Image.new("RGBA", (800, 800), (255, 55, 255, 1))

    with io.BytesIO() as output:
        img.save(output, format="PNG")
        return SimpleUploadedFile("image.png", output.getvalue())


@pytest.fixture(scope="session")
def tiny_image_upload_file():
    img = Image.new("RGBA", (1, 1), (255, 55, 255, 1))

    with io.BytesIO() as output:
        img.save(output, format="PNG")
        return SimpleUploadedFile("image.png", output.getvalue())


@pytest.fixture(scope="session")
def large_image_upload_file():
    img = Image.new("RGB", (2000, 3000), (255, 55, 255))
    exif = img.getexif()
    exif[0x0112] = 8  # pretend to be rotated by 90 degrees

    with io.BytesIO() as output:
        img.save(output, format="JPEG", exif=exif, jpeg_quality=95)
        return SimpleUploadedFile("image.jpeg", output.getvalue())


@pytest.fixture(autouse=True)
def media_root(settings, tmpdir_factory):
    settings.MEDIA_ROOT = tmpdir_factory.mktemp("media", numbered=True)


@pytest.fixture(autouse=True)
def instant_commit(monkeypatch):
    monkeypatch.setattr("django.db.transaction.on_commit", lambda f: f())


@pytest.fixture(autouse=True)
def reset_pictures_settings():
    """Reset the pictures' settings to prevent side effects from other tests."""
    conf.app_settings._reset()
