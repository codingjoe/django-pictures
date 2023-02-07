from fractions import Fraction

import pytest
from django.core.files.storage import default_storage

from pictures.models import SimplePicture
from tests.testapp import models

serializers = pytest.importorskip("rest_framework.serializers")
rest_framework = pytest.importorskip("pictures.contrib.rest_framework")


class ProfileSerializer(serializers.ModelSerializer):
    picture = rest_framework.PictureField()

    class Meta:
        model = models.Profile
        fields = ["picture"]


def test_default(settings):
    settings.PICTURES["USE_PLACEHOLDERS"] = False
    assert (
        rest_framework.default(
            obj=SimplePicture(
                parent_name="testapp/simplemodel/image.jpg",
                file_type="WEBP",
                aspect_ratio=Fraction("4/3"),
                storage=default_storage,
                width=800,
            )
        )
        == "/media/testapp/simplemodel/image/4_3/800w.webp"
    )


def test_default__type_error():
    with pytest.raises(TypeError) as e:
        rest_framework.default("not a picture")
    assert str(e.value) == "Type 'str' not serializable"


class TestPictureField:
    @pytest.mark.django_db
    def test_to_representation(self, image_upload_file, settings):
        settings.PICTURES["USE_PLACEHOLDERS"] = False

        profile = models.Profile.objects.create(picture=image_upload_file)
        serializer = ProfileSerializer(profile)

        assert serializer.data["picture"] == {
            "url": "/media/testapp/profile/image.jpg",
            "width": 800,
            "height": 800,
            "ratios": {
                "null": {
                    "sources": {
                        "image/webp": {
                            "800": "/media/testapp/profile/image/800w.webp",
                            "100": "/media/testapp/profile/image/100w.webp",
                            "200": "/media/testapp/profile/image/200w.webp",
                            "300": "/media/testapp/profile/image/300w.webp",
                            "400": "/media/testapp/profile/image/400w.webp",
                            "500": "/media/testapp/profile/image/500w.webp",
                            "600": "/media/testapp/profile/image/600w.webp",
                            "700": "/media/testapp/profile/image/700w.webp",
                        }
                    }
                },
                "1/1": {
                    "sources": {
                        "image/webp": {
                            "800": "/media/testapp/profile/image/1/800w.webp",
                            "100": "/media/testapp/profile/image/1/100w.webp",
                            "200": "/media/testapp/profile/image/1/200w.webp",
                            "300": "/media/testapp/profile/image/1/300w.webp",
                            "400": "/media/testapp/profile/image/1/400w.webp",
                            "500": "/media/testapp/profile/image/1/500w.webp",
                            "600": "/media/testapp/profile/image/1/600w.webp",
                            "700": "/media/testapp/profile/image/1/700w.webp",
                        }
                    }
                },
                "3/2": {
                    "sources": {
                        "image/webp": {
                            "800": "/media/testapp/profile/image/3_2/800w.webp",
                            "100": "/media/testapp/profile/image/3_2/100w.webp",
                            "200": "/media/testapp/profile/image/3_2/200w.webp",
                            "300": "/media/testapp/profile/image/3_2/300w.webp",
                            "400": "/media/testapp/profile/image/3_2/400w.webp",
                            "500": "/media/testapp/profile/image/3_2/500w.webp",
                            "600": "/media/testapp/profile/image/3_2/600w.webp",
                            "700": "/media/testapp/profile/image/3_2/700w.webp",
                        }
                    }
                },
                "16/9": {
                    "sources": {
                        "image/webp": {
                            "800": "/media/testapp/profile/image/16_9/800w.webp",
                            "100": "/media/testapp/profile/image/16_9/100w.webp",
                            "200": "/media/testapp/profile/image/16_9/200w.webp",
                            "300": "/media/testapp/profile/image/16_9/300w.webp",
                            "400": "/media/testapp/profile/image/16_9/400w.webp",
                            "500": "/media/testapp/profile/image/16_9/500w.webp",
                            "600": "/media/testapp/profile/image/16_9/600w.webp",
                            "700": "/media/testapp/profile/image/16_9/700w.webp",
                        }
                    }
                },
            },
        }

    @pytest.mark.django_db
    def test_to_representation__with_aspect_ratios(
        self, rf, image_upload_file, settings
    ):
        settings.PICTURES["USE_PLACEHOLDERS"] = False

        profile = models.Profile.objects.create(picture=image_upload_file)
        request = rf.get("/")
        request.GET._mutable = True
        request.GET["picture_ratio"] = "1/1"
        request.GET["picture_l"] = "3"
        request.GET["picture_m"] = "4"
        serializer = ProfileSerializer(profile, context={"request": request})

        assert serializer.data["picture"] == {
            "url": "/media/testapp/profile/image.jpg",
            "width": 800,
            "height": 800,
            "ratios": {
                "1/1": {
                    "sources": {
                        "image/webp": {
                            "800": "/media/testapp/profile/image/1/800w.webp",
                            "100": "/media/testapp/profile/image/1/100w.webp",
                            "200": "/media/testapp/profile/image/1/200w.webp",
                            "300": "/media/testapp/profile/image/1/300w.webp",
                            "400": "/media/testapp/profile/image/1/400w.webp",
                            "500": "/media/testapp/profile/image/1/500w.webp",
                            "600": "/media/testapp/profile/image/1/600w.webp",
                            "700": "/media/testapp/profile/image/1/700w.webp",
                        }
                    },
                    "media": "(min-width: 0px) and (max-width: 991px) 100vw, (min-width: 992px) and (max-width: 1199px) 33vw, 25vw",
                }
            },
        }

    @pytest.mark.django_db
    def test_to_representation__raise_value_error(
        self, rf, image_upload_file, settings
    ):
        settings.PICTURES["USE_PLACEHOLDERS"] = False

        profile = models.Profile.objects.create(picture=image_upload_file)
        request = rf.get("/")
        request.GET._mutable = True
        request.GET["picture_ratio"] = "21/11"
        request.GET["picture_l"] = "3"
        request.GET["picture_m"] = "4"
        serializer = ProfileSerializer(profile, context={"request": request})

        with pytest.raises(ValueError) as e:
            serializer.data["picture"]

        assert str(e.value) == "Invalid ratio: 21/11. Choices are: 1/1, 3/2, 16/9"

    @pytest.mark.django_db
    def test_to_representation__with_container(self, rf, image_upload_file, settings):
        settings.PICTURES["USE_PLACEHOLDERS"] = False

        profile = models.Profile.objects.create(picture=image_upload_file)
        request = rf.get("/")
        request.GET._mutable = True
        request.GET["picture_ratio"] = "16/9"
        request.GET["picture_container"] = "1200"
        serializer = ProfileSerializer(profile, context={"request": request})
        assert serializer.data["picture"] == {
            "url": "/media/testapp/profile/image.jpg",
            "width": 800,
            "height": 800,
            "ratios": {
                "16/9": {
                    "sources": {
                        "image/webp": {
                            "800": "/media/testapp/profile/image/16_9/800w.webp",
                            "100": "/media/testapp/profile/image/16_9/100w.webp",
                            "200": "/media/testapp/profile/image/16_9/200w.webp",
                            "300": "/media/testapp/profile/image/16_9/300w.webp",
                            "400": "/media/testapp/profile/image/16_9/400w.webp",
                            "500": "/media/testapp/profile/image/16_9/500w.webp",
                            "600": "/media/testapp/profile/image/16_9/600w.webp",
                            "700": "/media/testapp/profile/image/16_9/700w.webp",
                        }
                    },
                    "media": "(min-width: 0px) and (max-width: 1199px) 100vw, 1200px",
                }
            },
        }

    @pytest.mark.django_db
    def test_to_representation__with_container_width_lt_width(
        self, rf, image_upload_file, settings
    ):
        settings.PICTURES["USE_PLACEHOLDERS"] = False

        profile = models.Profile.objects.create(picture=image_upload_file)
        request = rf.get("/")
        request.GET._mutable = True
        request.GET["picture_ratio"] = "16/9"
        request.GET["picture_container"] = "500"
        serializer = ProfileSerializer(profile, context={"request": request})
        assert serializer.data["picture"] == {
            "url": "/media/testapp/profile/image.jpg",
            "width": 800,
            "height": 800,
            "ratios": {
                "16/9": {
                    "sources": {
                        "image/webp": {
                            "800": "/media/testapp/profile/image/16_9/800w.webp",
                            "100": "/media/testapp/profile/image/16_9/100w.webp",
                            "200": "/media/testapp/profile/image/16_9/200w.webp",
                            "300": "/media/testapp/profile/image/16_9/300w.webp",
                            "400": "/media/testapp/profile/image/16_9/400w.webp",
                            "500": "/media/testapp/profile/image/16_9/500w.webp",
                            "600": "/media/testapp/profile/image/16_9/600w.webp",
                            "700": "/media/testapp/profile/image/16_9/700w.webp",
                        }
                    },
                    "media": "(min-width: 0px) and (max-width: 499px) 100vw",
                }
            },
        }

