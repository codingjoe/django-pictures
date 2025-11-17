from unittest.mock import Mock

import pytest
from django.apps import apps
from django.dispatch import receiver

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
        field="",
    )


@pytest.mark.django_db
def test_process_picture_sends_process_picture_done_on_create(image_upload_file):
    handler = Mock()
    signals.process_picture_done.connect(handler)

    obj = SimpleModel.objects.create(picture=image_upload_file)

    handler.assert_called_once_with(
        signal=signals.process_picture_done,
        sender=SimpleModel,
        storage=obj.picture.storage.deconstruct(),
        file_name=obj.picture.name,
        new=[i.deconstruct() for i in obj.picture.get_picture_files_list()],
        old=[],
        field="testapp.simplemodel.picture",
    )


@pytest.mark.django_db
def test_processed_object_found(image_upload_file):
    obj = SimpleModel.objects.create()

    found_object = None

    @receiver(signals.process_picture_done, sender=SimpleModel)
    def handler(*, file_name, field, **__):
        nonlocal found_object
        app_label, model_name, field_name = field.split(".")
        model = apps.get_model(app_label=app_label, model_name=model_name)

        # Users can now modify the object that process_picture_done
        # corresponds to
        found_object = model.objects.get(**{field_name: file_name})

    obj.picture.save("image.png", image_upload_file)

    assert obj == found_object
