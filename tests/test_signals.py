from unittest.mock import Mock

import pytest

from pictures import signals, tasks
from tests.testapp.models import SimpleModel


@pytest.mark.django_db
def test_process_picture_sends_process_picture_done(image_upload_file):
    obj = SimpleModel.objects.create(picture=image_upload_file)

    handler = Mock()
    signals.process_picture_done.connect(handler)

    tasks._process_picture(
        obj.picture.storage.deconstruct(),
        obj.picture.name,
        new=[i.deconstruct() for i in obj.picture.get_picture_files_list()],
    )

    handler.assert_called_once_with(
        signal=signals.process_picture_done,
        sender=tasks._process_picture,
        storage=obj.picture.storage.deconstruct(),
        file_name=obj.picture.name,
        new=[i.deconstruct() for i in obj.picture.get_picture_files_list()],
        old=[],
    )
