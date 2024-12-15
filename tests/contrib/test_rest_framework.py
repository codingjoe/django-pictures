from fractions import Fraction

import pytest
from django.core.files.storage import default_storage

from pictures.models import Picture
from tests.testapp import models

serializers = pytest.importorskip("rest_framework.serializers")
rest_framework = pytest.importorskip("pictures.contrib.rest_framework")


class ProfileSerializer(serializers.ModelSerializer):
    image = rest_framework.PictureField(source="picture")
    image_mobile = rest_framework.PictureField(
        source="picture", aspect_ratios=["3/2"], file_types=["WEBP"]
    )

    class Meta:
        model = models.Profile
        fields = ["image", "image_mobile"]


class ProfileSerializerWithInvalidData(serializers.ModelSerializer):
    image_invalid = rest_framework.PictureField(
        source="picture", aspect_ratios=["21/11"], file_types=["GIF"]
    )

    class Meta:
        model = models.Profile
        fields = ["image_invalid"]


class TestPicture(Picture):
    @property
    def url(self):
        return f"/media/{self.parent_name}"


def test_default(settings):
    settings.PICTURES["USE_PLACEHOLDERS"] = False
    assert (
        rest_framework.default(
            obj=TestPicture(
                parent_name="testapp/simplemodel/image.jpg",
                file_type="WEBP",
                aspect_ratio=Fraction("4/3"),
                storage=default_storage,
                width=800,
            )
        )
        == "/media/testapp/simplemodel/image.jpg"
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

        assert serializer.data["image"] == {
            "url": "/media/testapp/profile/image.png",
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
                    },
                    "media": "(min-width: 0px) and (max-width: 1199px) 100vw, 1200px",
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
                    },
                    "media": "(min-width: 0px) and (max-width: 1199px) 100vw, 1200px",
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
                    },
                    "media": "(min-width: 0px) and (max-width: 1199px) 100vw, 1200px",
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
                    },
                    "media": "(min-width: 0px) and (max-width: 1199px) 100vw, 1200px",
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
        request.GET["image_ratio"] = "1/1"
        request.GET["image_l"] = "3"
        request.GET["image_m"] = "4"
        serializer = ProfileSerializer(profile, context={"request": request})

        assert serializer.data["image"] == {
            "url": "/media/testapp/profile/image.png",
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
                    "media": "(min-width: 0px) and (max-width: 991px) 100vw, (min-width: 992px) and (max-width: 1199px) 25vw, 400px",
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
        request.GET["image_ratio"] = "21/11"
        request.GET["image_l"] = "3"
        request.GET["image_m"] = "4"
        serializer = ProfileSerializer(profile, context={"request": request})

        with pytest.raises(ValueError) as e:
            serializer.data["image"]

        assert str(e.value) == "Invalid ratios: 21/11. Choices are: 1/1, 3/2, 16/9"

    @pytest.mark.django_db
    def test_to_representation__blank(self, rf, image_upload_file, settings):
        settings.PICTURES["USE_PLACEHOLDERS"] = False

        profile = models.Profile.objects.create()
        request = rf.get("/")
        request.GET._mutable = True
        request.GET["image_ratio"] = "21/11"
        request.GET["image_l"] = "3"
        request.GET["image_m"] = "4"
        serializer = ProfileSerializer(profile, context={"request": request})

        assert serializer.data["image"] is None

    @pytest.mark.django_db
    def test_to_representation__no_get_params(self, rf, image_upload_file, settings):
        settings.PICTURES["USE_PLACEHOLDERS"] = False

        profile = models.Profile.objects.create(picture=image_upload_file)
        request = rf.get("/")
        request.GET._mutable = True
        request.GET["foo"] = "bar"
        serializer = ProfileSerializer(profile, context={"request": request})
        assert serializer.data["image_mobile"] == {
            "url": "/media/testapp/profile/image.png",
            "width": 800,
            "height": 800,
            "ratios": {
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
                    },
                    "media": "(min-width: 0px) and (max-width: 1199px) 100vw, 1200px",
                }
            },
        }

    @pytest.mark.django_db
    def test_to_representation__multiple_ratios(self, rf, image_upload_file, settings):
        settings.PICTURES["USE_PLACEHOLDERS"] = False

        profile = models.Profile.objects.create(picture=image_upload_file)
        request = rf.get("/")
        request.GET._mutable = True
        request.GET.setlist("image_ratio", ["3/2", "16/9"])
        serializer = ProfileSerializer(profile, context={"request": request})
        print(serializer.data["image"])
        assert serializer.data["image"] == {
            "url": "/media/testapp/profile/image.png",
            "width": 800,
            "height": 800,
            "ratios": {
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
                    },
                    "media": "(min-width: 0px) and (max-width: 1199px) 100vw, 1200px",
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
                    },
                    "media": "(min-width: 0px) and (max-width: 1199px) 100vw, 1200px",
                },
            },
        }

    @pytest.mark.django_db
    def test_to_representation__with_container(self, rf, image_upload_file, settings):
        settings.PICTURES["USE_PLACEHOLDERS"] = False

        profile = models.Profile.objects.create(picture=image_upload_file)
        request = rf.get("/")
        request.GET._mutable = True
        request.GET["image_ratio"] = "16/9"
        request.GET["image_container"] = "1200"
        serializer = ProfileSerializer(profile, context={"request": request})
        assert serializer.data["image"] == {
            "url": "/media/testapp/profile/image.png",
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
    def test_to_representation__without_container(
        self, rf, image_upload_file, settings
    ):
        settings.PICTURES["USE_PLACEHOLDERS"] = False

        profile = models.Profile.objects.create(picture=image_upload_file)
        request = rf.get("/")
        request.GET._mutable = True
        request.GET["image_ratio"] = "16/9"
        serializer = ProfileSerializer(profile, context={"request": request})
        assert serializer.data["image"] == {
            "url": "/media/testapp/profile/image.png",
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
    def test_to_representation__with_false_str_container(
        self, rf, image_upload_file, settings
    ):
        settings.PICTURES["USE_PLACEHOLDERS"] = False

        profile = models.Profile.objects.create(picture=image_upload_file)
        request = rf.get("/")
        request.GET._mutable = True
        request.GET["image_ratio"] = "16/9"
        request.GET["image_container"] = "not_a_number"
        serializer = ProfileSerializer(profile, context={"request": request})
        with pytest.raises(ValueError) as e:
            serializer.data["image"]
        assert str(e.value) == "Container width is not a number: not_a_number"

    @pytest.mark.django_db
    def test_to_representation__with_prefiltered_aspect_ratio_and_source(
        self, image_upload_file, settings
    ):
        settings.PICTURES["USE_PLACEHOLDERS"] = False

        profile = models.Profile.objects.create(picture=image_upload_file)
        serializer = ProfileSerializer(profile)

        assert serializer.data["image_mobile"] == {
            "url": "/media/testapp/profile/image.png",
            "width": 800,
            "height": 800,
            "ratios": {
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
                    },
                    "media": "(min-width: 0px) and (max-width: 1199px) 100vw, 1200px",
                }
            },
        }
