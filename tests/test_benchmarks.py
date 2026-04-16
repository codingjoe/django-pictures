"""Benchmark tests for image processing to detect performance regressions."""

from __future__ import annotations

import io

import django
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from PIL import Image

from pictures import migrations
from pictures.models import PictureField
from pictures.tasks import _process_picture
from tests.testapp.models import Profile, SimpleModel

try:
    import celery
except ImportError:
    celery = None

try:
    import django_rq
except ImportError:
    django_rq = None

try:
    import dramatiq
except ImportError:
    dramatiq = None

skip_dramatiq = pytest.mark.skipif(
    not all(x is None for x in [dramatiq, celery, django_rq]),
    reason="dramatiq, celery and django-rq are installed",
)

requires_django_tasks = pytest.mark.skipif(
    django.VERSION < (6, 0),
    reason="Django tasks require Django 6.0+",
)


def _make_upload_file() -> SimpleUploadedFile:
    """Return a fresh in-memory PNG upload file."""
    img = Image.new("RGBA", (800, 800), (255, 55, 255, 1))
    with io.BytesIO() as output:
        img.save(output, format="PNG")
        return SimpleUploadedFile("image.png", output.getvalue())


@pytest.mark.benchmark
@skip_dramatiq
@requires_django_tasks
@pytest.mark.django_db
class TestProcessPicture:
    """Benchmark the end-to-end image processing pipeline."""

    def test_process_picture(self, benchmark, large_image_upload_file):
        """Benchmark processing all picture sizes through the full pipeline."""
        obj = SimpleModel.objects.create(picture=large_image_upload_file)
        pictures = [i.deconstruct() for i in obj.picture.get_picture_files_list()]
        benchmark(
            _process_picture,
            obj.picture.storage.deconstruct(),
            obj.picture.name,
            pictures,
        )


@pytest.mark.benchmark
@skip_dramatiq
@requires_django_tasks
@pytest.mark.django_db
class TestAlterPictureField:
    """Benchmark the AlterPictureField migration operation."""

    def test_update_pictures(self, request, benchmark):
        """Benchmark update_pictures migration operation across multiple objects."""

        class ToModel(models.Model):
            name = models.CharField(max_length=100)
            picture = PictureField(
                upload_to="testapp/profile/", aspect_ratios=[None, "21/9"]
            )

            class Meta:
                app_label = request.node.name
                db_table = "testapp_profile"

        for index in range(3):
            Profile.objects.create(name=f"Profile {index}", picture=_make_upload_file())

        migration = migrations.AlterPictureField("profile", "picture", PictureField())
        from_field = Profile._meta.get_field("picture")
        benchmark(migration.update_pictures, from_field, ToModel)
