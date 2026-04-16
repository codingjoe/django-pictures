"""Benchmark tests for image processing to prevent performance regressions."""

from __future__ import annotations

from fractions import Fraction

import pytest
from django.core.files.storage import default_storage
from PIL import Image

from pictures.models import PillowPicture
from pictures.tasks import _process_picture
from tests.testapp.models import SimpleModel


@pytest.fixture
def rgb_image_1200w():
    """Return a 1200×900 RGB test image."""
    return Image.new("RGB", (1200, 900), (128, 64, 192))


@pytest.fixture
def rgba_image_1200w():
    """Return a 1200×900 RGBA test image."""
    return Image.new("RGBA", (1200, 900), (128, 64, 192, 200))


class TestPillowPictureProcess:
    """Benchmark PillowPicture.process() for various resize and crop scenarios."""

    def bench_process__thumbnail(self, benchmark, rgb_image_1200w):
        """Benchmark thumbnail resize without aspect ratio constraint."""
        picture = PillowPicture(
            parent_name="bench/image.png",
            file_type="AVIF",
            aspect_ratio=None,
            storage=default_storage,
            width=600,
        )
        benchmark(picture.process, rgb_image_1200w)

    def bench_process__crop_16_9(self, benchmark, rgb_image_1200w):
        """Benchmark crop-and-resize to 16/9 aspect ratio."""
        picture = PillowPicture(
            parent_name="bench/image.png",
            file_type="AVIF",
            aspect_ratio=Fraction(16, 9),
            storage=default_storage,
            width=600,
        )
        benchmark(picture.process, rgb_image_1200w)

    def bench_process__crop_1_1(self, benchmark, rgb_image_1200w):
        """Benchmark crop-and-resize to square aspect ratio."""
        picture = PillowPicture(
            parent_name="bench/image.png",
            file_type="AVIF",
            aspect_ratio=Fraction(1, 1),
            storage=default_storage,
            width=600,
        )
        benchmark(picture.process, rgb_image_1200w)


class TestPillowPictureSave:
    """Benchmark PillowPicture.save() for different output file types."""

    def bench_save__avif(self, benchmark, rgb_image_1200w):
        """Benchmark AVIF encoding."""
        picture = PillowPicture(
            parent_name="bench/image.png",
            file_type="AVIF",
            aspect_ratio=None,
            storage=default_storage,
            width=600,
        )
        benchmark(picture.save, rgb_image_1200w)

    def bench_save__webp(self, benchmark, rgb_image_1200w):
        """Benchmark WebP encoding."""
        picture = PillowPicture(
            parent_name="bench/image.png",
            file_type="WEBP",
            aspect_ratio=None,
            storage=default_storage,
            width=600,
        )
        benchmark(picture.save, rgb_image_1200w)

    def bench_save__jpeg(self, benchmark, rgb_image_1200w):
        """Benchmark JPEG encoding from an RGB source image."""
        picture = PillowPicture(
            parent_name="bench/image.png",
            file_type="JPEG",
            aspect_ratio=None,
            storage=default_storage,
            width=600,
        )
        benchmark(picture.save, rgb_image_1200w)

    def bench_save__rgba_to_avif(self, benchmark, rgba_image_1200w):
        """Benchmark AVIF encoding from an RGBA source image."""
        picture = PillowPicture(
            parent_name="bench/image.png",
            file_type="AVIF",
            aspect_ratio=None,
            storage=default_storage,
            width=600,
        )
        benchmark(picture.save, rgba_image_1200w)


@pytest.mark.django_db
class TestProcessPicture:
    """Benchmark the end-to-end _process_picture() task."""

    def bench_process_picture__single_ratio(self, benchmark, large_image_upload_file):
        """Benchmark full pipeline for a single aspect ratio."""
        obj = SimpleModel.objects.create(picture=large_image_upload_file)
        pictures = [i.deconstruct() for i in obj.picture.get_picture_files_list()]
        benchmark(
            _process_picture,
            obj.picture.storage.deconstruct(),
            obj.picture.name,
            pictures,
        )

    def bench_process_picture__encode_avif(self, benchmark, large_image_upload_file):
        """Benchmark AVIF encoding in the full pipeline."""
        obj = SimpleModel.objects.create(picture=large_image_upload_file)
        avif_pictures = [
            i.deconstruct()
            for i in obj.picture.get_picture_files_list()
            if i.file_type == "AVIF"
        ]
        benchmark(
            _process_picture,
            obj.picture.storage.deconstruct(),
            obj.picture.name,
            avif_pictures,
        )
