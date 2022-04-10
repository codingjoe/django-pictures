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


def test_default():
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
    def test_to_representation(self, image_upload_file):

        profile = models.Profile.objects.create(picture=image_upload_file)
        serializer = ProfileSerializer(profile)
        assert serializer.data["picture"] == {
            "null": {
                "WEBP": {
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
            "1/1": {
                "WEBP": {
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
            "3/2": {
                "WEBP": {
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
            "16/9": {
                "WEBP": {
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
        }
