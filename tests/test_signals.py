from unittest.mock import Mock

import pytest
from django.dispatch import receiver

from pictures import signals, tasks
from tests.testapp.models import SimpleModel


@pytest.mark.django_db
def test_process_picture_sends_process_picture_done(image_upload_file):
    obj = SimpleModel.objects.create(picture=image_upload_file)

    handler = Mock()
    signals.picture_processed.connect(handler)

    tasks._process_picture(
        obj.picture.storage.deconstruct(),
        obj.picture.name,
        obj.picture.sender,
        new=[i.deconstruct() for i in obj.picture.get_picture_files_list()],
    )

    handler.assert_called_once_with(
        signal=signals.picture_processed,
        sender=SimpleModel._meta.get_field("picture"),
        file_name=obj.picture.name,
        new=[i.deconstruct() for i in obj.picture.get_picture_files_list()],
        old=[],
    )


@pytest.mark.django_db
def test_process_picture_sends_process_picture_done_on_create(image_upload_file):
    handler = Mock()
    signals.picture_processed.connect(handler)

    obj = SimpleModel.objects.create(picture=image_upload_file)

    handler.assert_called_once_with(
        signal=signals.picture_processed,
        sender=SimpleModel._meta.get_field("picture"),
        file_name=obj.picture.name,
        new=[i.deconstruct() for i in obj.picture.get_picture_files_list()],
        old=[],
    )


@pytest.mark.django_db
def test_processed_object_found(image_upload_file):
    obj = SimpleModel.objects.create()

    found_object = None

    @receiver(signals.picture_processed, sender=SimpleModel._meta.get_field("picture"))
    def handler(*, sender, file_name, **__):
        nonlocal found_object

        # Users can now modify the object that picture_processed corresponds to
        found_object = sender.model.objects.get(**{sender.name: file_name})

    obj.picture.save("image.png", image_upload_file)

    assert obj == found_object
