from unittest.mock import Mock

import pytest

from pictures import tasks
from tests.testapp.models import SimpleModel


@pytest.mark.django_db
def test_process_picture__file_cannot_be_reopened(image_upload_file):
    # regression https://github.com/codingjoe/django-pictures/issues/26
    obj = SimpleModel.objects.create(picture=image_upload_file)
    setattr(
        obj.picture.file,
        "open",
        Mock(side_effect=ValueError("The file cannot be reopened.")),
    )
    tasks._process_picture(obj.picture)
