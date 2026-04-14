import contextlib
import copy
import io
from fractions import Fraction
from pathlib import Path

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageCms, ImageDraw

from pictures.models import PictureField, PillowPicture
from tests.testapp.models import JPEGModel, Profile, SimpleModel


@contextlib.contextmanager
def override_field_aspect_ratios(field, aspect_ratios):
    old_ratios = copy.deepcopy(field.aspect_ratios)
    field.aspect_ratios = aspect_ratios
    try:
        yield
    finally:
        field.aspect_ratios = old_ratios


def profile_name_from_bytes(profile_bytes):
    if not profile_bytes:
        return None

    profile = ImageCms.ImageCmsProfile(io.BytesIO(profile_bytes))
    return ImageCms.getProfileName(profile).strip()


def get_cmyk_profile_bytes():
    return Path(__file__).with_name("assets").joinpath("ps_cmyk.icc").read_bytes()


def get_rgb_profile_bytes():
    return Path(__file__).with_name("assets").joinpath("ps_rgb.icc").read_bytes()


class TestPillowPicture:
    picture_with_ratio = PillowPicture(
        parent_name="testapp/simplemodel/image.png",
        file_type="AVIF",
        aspect_ratio=Fraction("4/3"),
        storage=default_storage,
        width=800,
    )

    picture_without_ratio = PillowPicture(
        parent_name="testapp/simplemodel/image.png",
        file_type="AVIF",
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
        settings.PICTURES = settings.PICTURES | {"USE_PLACEHOLDERS": False}
        assert (
            self.picture_with_ratio.url
            == "/media/testapp/simplemodel/image/4_3/800w.avif"
        )

    def test_url__placeholder(self, settings):
        settings.PICTURES["USE_PLACEHOLDERS"] = True
        assert self.picture_with_ratio.url == "/_pictures/image/4x3/800w.AVIF"

    def test_height(self):
        assert self.picture_with_ratio.height == 600
        assert not self.picture_without_ratio.height

    def test_name(self):
        assert Path(self.picture_without_ratio.name) == Path(
            "testapp/simplemodel/image/800w.avif"
        )
        assert Path(self.picture_with_ratio.name) == Path(
            "testapp/simplemodel/image/4_3/800w.avif"
        )

    def test_path(self):
        assert self.picture_with_ratio.path.is_absolute()

    def test_save(self):
        assert not self.picture_with_ratio.path.exists()
        self.picture_with_ratio.save(Image.new("RGB", (800, 800), (255, 55, 255)))
        assert self.picture_with_ratio.path.exists()

    def test_process__copy(self):
        """Do not mutate input image."""
        image = Image.new("RGB", (800, 800), (255, 55, 255))
        assert PillowPicture(
            parent_name="testapp/simplemodel/image.png",
            file_type="AVIF",
            aspect_ratio=None,
            storage=default_storage,
            width=100,
        ).resize(image).size == (100, 100)

        assert image.size == (800, 800), "Image was mutated."

        assert PillowPicture(
            parent_name="testapp/simplemodel/image.png",
            file_type="AVIF",
            aspect_ratio="4/3",
            storage=default_storage,
            width=400,
        ).resize(image).size == (400, 300)

        assert image.size == (800, 800), "Image was mutated."

    @pytest.mark.parametrize("file_type", ["AVIF", "WEBP", "PNG", "GIF", "JPEG"])
    def test_save__web_formats_strip_exif_and_keep_only_srgb_icc(self, file_type):
        image = Image.new("CMYK", (20, 20), (0, 128, 255, 0))
        exif = Image.Exif()
        exif[0x010E] = "django-pictures test image"
        image.info["exif"] = exif.tobytes()
        image.info["icc_profile"] = get_cmyk_profile_bytes()
        picture = PillowPicture(
            parent_name="testapp/simplemodel/image.png",
            file_type=file_type,
            aspect_ratio=None,
            storage=default_storage,
            width=20,
        )

        image = picture.pre_process(image)
        picture.save(image)

        with Image.open(picture.path) as saved_image:
            assert saved_image.mode in ["RGB", "RGBA", "P"]
            assert not saved_image.info.get("exif")
            assert len(saved_image.getexif()) == 0

            profile_name = profile_name_from_bytes(saved_image.info.get("icc_profile"))
            assert profile_name is None

    def test_save__strip_exif(self):
        image = Image.new("RGB", (20, 20), (255, 0, 0))
        exif = image.getexif()
        exif[0x010E] = "reproduction"
        picture = PillowPicture(
            parent_name="testapp/simplemodel/image.png",
            file_type="JPEG",
            aspect_ratio=None,
            storage=default_storage,
            width=20,
        )
        picture.save(image)
        with Image.open(picture.path) as saved_image:
            assert not saved_image.getexif()

    def test_save__strip_icc_profile(self):
        image = Image.new("RGB", (20, 20), (255, 0, 0))
        image.info["icc_profile"] = get_rgb_profile_bytes()
        picture = PillowPicture(
            parent_name="testapp/simplemodel/image.png",
            file_type="PNG",
            aspect_ratio=None,
            storage=default_storage,
            width=20,
        )
        picture.save(image)
        with Image.open(picture.path) as saved_image:
            assert not saved_image.info.get("icc_profile")

    def test_save__png_applies_non_srgb_rgb_profile_transform(self):
        # Use a lossless format here so exact pixel comparisons remain stable.
        image = Image.new("RGB", (1, 1), (255, 128, 0))
        image.info["icc_profile"] = get_rgb_profile_bytes()
        source_pixel = image.getpixel((0, 0))

        source_profile = ImageCms.ImageCmsProfile(io.BytesIO(image.info["icc_profile"]))
        srgb_profile = ImageCms.createProfile("sRGB")
        expected = ImageCms.profileToProfile(
            image,
            source_profile,
            srgb_profile,
            outputMode="RGB",
        )
        expected_pixel = expected.getpixel((0, 0))
        picture = PillowPicture(
            parent_name="testapp/simplemodel/image.png",
            file_type="PNG",
            aspect_ratio=None,
            storage=default_storage,
            width=1,
        )

        assert expected_pixel != source_pixel

        image = picture.pre_process(image)
        picture.save(image)

        with Image.open(picture.path) as saved_image:
            saved_pixel = saved_image.getpixel((0, 0))
            if saved_image.mode == "RGBA":
                saved_pixel = saved_pixel[:3]
            assert saved_pixel == expected_pixel
            assert saved_pixel != source_pixel

    def test_delete(self):
        self.picture_with_ratio.save(Image.new("RGB", (800, 800), (255, 55, 255)))
        assert self.picture_with_ratio.path.exists()
        self.picture_with_ratio.delete()
        assert not self.picture_with_ratio.path.exists()

    @pytest.mark.parametrize(
        ("file_type", "image_mode", "expected_mode"),
        [
            ("AVIF", "RGB", "RGBA"),
            ("WEBP", "RGBA", "RGBA"),
            ("WEBP", "RGB", "RGBA"),
            ("PNG", "RGBA", "RGBA"),
            ("TIFF", "CMYK", "RGBA"),
            ("JPEG", "RGBA", "RGB"),
        ],
    )
    def test_process__convert_to_expected_mode(
        self, file_type, image_mode, expected_mode
    ):
        image = Image.new(image_mode, (10, 10))
        picture = PillowPicture(
            parent_name="testapp/simplemodel/image.png",
            file_type=file_type,
            aspect_ratio=None,
            storage=default_storage,
            width=10,
        )

        image = picture.pre_process(image)
        # resize() might call convert() depending on file_type
        result = picture.resize(image)

        assert result.mode == expected_mode

    def test_process__normalize_color_profile__preserve_alpha(self):
        image = Image.new("RGBA", (10, 10))
        image.info["icc_profile"] = get_rgb_profile_bytes()
        picture = PillowPicture(
            parent_name="testapp/simplemodel/image.png",
            file_type="WEBP",
            aspect_ratio=Fraction("4/3"),
            storage=default_storage,
            width=10,
        )

        image = picture.pre_process(image)
        result = picture.resize(image)

        assert result.mode == "RGBA"
        assert "A" in result.getbands(), "Alpha channel was not preserved."

    def test_process__raise_os_error_on_broken_color_profile(self):
        image = Image.new("CMYK", (10, 10))
        image.info["icc_profile"] = b"broken profile"

        with pytest.raises(OSError):
            self.picture_with_ratio.pre_process(image)


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
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=300,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=600,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=500,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=500,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=300,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=700,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=800,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=200,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=300,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=700,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=100,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=400,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=800,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=100,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=700,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=200,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=600,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=500,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=800,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=200,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=100,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=400,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=600,
                ),
                PillowPicture(
                    parent_name="testapp/simplemodel/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=400,
                ),
            },
            {
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=600,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=300,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=800,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=500,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=700,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=100,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=500,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=700,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=800,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=200,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=100,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=600,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=100,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=700,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=800,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=200,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=500,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=800,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=300,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=300,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=600,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=700,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(1, 1),
                    storage=default_storage,
                    width=400,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=400,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=400,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=200,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=300,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=600,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(3, 2),
                    storage=default_storage,
                    width=100,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=Fraction(16, 9),
                    storage=default_storage,
                    width=200,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
                    aspect_ratio=None,
                    storage=default_storage,
                    width=400,
                ),
                PillowPicture(
                    parent_name="testapp/profile/image.png",
                    file_type="AVIF",
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
        assert obj.picture.aspect_ratios["16/9"]["AVIF"][100].path.exists()

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
        assert obj.picture.aspect_ratios["16/9"]["AVIF"][100].path.exists()
        with Image.open(
            obj.picture.aspect_ratios["16/9"]["AVIF"][100].path
        ) as img_small:
            assert img_small.size == (100, 56)
            pixels = img_small.load()
            assert pixels[0, 0][1] == 0  # blue is on the top, always blue!

    @pytest.mark.django_db
    def test_save__is_blank(self):
        obj = SimpleModel()
        obj.save()
        assert not obj.picture

    @pytest.mark.django_db
    def test_delete(self, stub_worker, image_upload_file):
        obj = SimpleModel(picture=image_upload_file)
        obj.save()
        stub_worker.join()

        name = obj.picture.name
        path = obj.picture.aspect_ratios["16/9"]["AVIF"][100].path
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
        path = obj.picture.aspect_ratios["16/9"]["AVIF"][100].path
        assert default_storage.exists(name)
        assert path.exists()

        old = copy.deepcopy(obj.picture)
        with override_field_aspect_ratios(obj.picture.field, ["1/1"]):
            obj.picture.update_all(old)
            stub_worker.join()
            assert default_storage.exists(name)
            assert obj.picture.aspect_ratios["1/1"]["AVIF"][100].path.exists()
            assert not path.exists()

    @pytest.mark.django_db
    def test_width(self, stub_worker, image_upload_file):
        obj = SimpleModel(picture=image_upload_file)
        obj.save()
        obj.picture_width = None

        assert obj.picture.width == 800

    @pytest.mark.django_db
    def test_height(self, stub_worker, image_upload_file):
        obj = SimpleModel(picture=image_upload_file)
        obj.save()
        obj.picture_height = None

        assert obj.picture.height == 800

    @pytest.mark.django_db
    def test_update_all__empty(self, stub_worker, image_upload_file):
        obj = SimpleModel()
        obj.save()

        obj.picture.update_all(obj.picture)

    def test_delete_all__empty(self):
        obj = SimpleModel()
        obj.picture.delete_all()


class TestPictureField:
    @pytest.mark.django_db
    def test_integration(self, image_upload_file):
        obj = SimpleModel.objects.create(picture=image_upload_file)
        assert obj.picture.aspect_ratios == {
            None: {
                "AVIF": {
                    800: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=800,
                    ),
                    100: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=100,
                    ),
                    200: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=200,
                    ),
                    300: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=300,
                    ),
                    400: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=400,
                    ),
                    500: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=500,
                    ),
                    600: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=600,
                    ),
                    700: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=None,
                        storage=default_storage,
                        width=700,
                    ),
                }
            },
            "3/2": {
                "AVIF": {
                    800: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=800,
                    ),
                    100: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=100,
                    ),
                    200: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=200,
                    ),
                    300: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=300,
                    ),
                    400: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=400,
                    ),
                    500: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=500,
                    ),
                    600: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=600,
                    ),
                    700: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(3, 2),
                        storage=default_storage,
                        width=700,
                    ),
                }
            },
            "16/9": {
                "AVIF": {
                    800: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=800,
                    ),
                    100: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=100,
                    ),
                    200: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=200,
                    ),
                    300: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=300,
                    ),
                    400: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=400,
                    ),
                    500: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=500,
                    ),
                    600: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
                        aspect_ratio=Fraction(16, 9),
                        storage=default_storage,
                        width=600,
                    ),
                    700: PillowPicture(
                        parent_name="testapp/simplemodel/image.png",
                        file_type="AVIF",
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

    @pytest.mark.parametrize(
        "aspect_ratios",
        [
            ("3/2",),
            (None,),
            (
                "3/2",
                None,
            ),
        ],
    )
    def test_check_width_height_field(self, aspect_ratios):
        with override_field_aspect_ratios(Profile.picture.field, aspect_ratios):
            errors = Profile.picture.field._check_width_height_field()
        assert errors
        assert errors[0].id == "fields.E101"
        assert errors[0].hint.startswith(
            "Please add two positive integer fields to 'testapp.Profile'"
        )

    def test_check(self):
        assert not SimpleModel._meta.get_field("picture").check()
        assert Profile._meta.get_field("picture").check()
