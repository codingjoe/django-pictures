import json
from unittest.mock import Mock

import pytest

from pictures import signals, tasks
from tests.conftest import skip_dramatiq
from tests.testapp.models import SimpleModel


@pytest.mark.django_db
@skip_dramatiq
def test_process_picture__send_picture_processed(image_upload_file):
    obj = SimpleModel.objects.create(picture=image_upload_file)
    pictures = [i.deconstruct() for i in obj.picture.get_picture_files_list()]

    handler = Mock()
    signals.picture_processed.connect(handler)
    try:
        tasks._process_picture(
            storage=obj.picture.storage.deconstruct(),
            file_name=obj.picture.name,
            sender=obj.picture.sender,
            new=pictures,
        )
    finally:
        signals.picture_processed.disconnect(handler)

    handler.assert_called_once_with(
        signal=signals.picture_processed,
        sender=SimpleModel._meta.get_field("picture"),
        file_name=obj.picture.name,
        new=pictures,
        old=[],
    )


@pytest.mark.django_db
@skip_dramatiq
def test_process_picture__send_picture_processed_on_create(image_upload_file):
    handler = Mock()
    signals.picture_processed.connect(handler)
    try:
        obj = SimpleModel.objects.create(picture=image_upload_file)
    finally:
        signals.picture_processed.disconnect(handler)

    handler.assert_called_once()
    kwargs = handler.call_args.kwargs
    assert kwargs["signal"] == signals.picture_processed
    assert kwargs["sender"] == SimpleModel._meta.get_field("picture")
    assert kwargs["file_name"] == obj.picture.name
    assert kwargs["old"] == []
    # task backends JSON-serialize the arguments, thus tuples become lists
    assert json.dumps(kwargs["new"]) == json.dumps([
        i.deconstruct() for i in obj.picture.get_picture_files_list()
    ])


@pytest.mark.django_db
@skip_dramatiq
def test_process_picture__send_picture_processed_on_delete(image_upload_file):
    obj = SimpleModel.objects.create(picture=image_upload_file)
    name = obj.picture.name
    pictures = [i.deconstruct() for i in obj.picture.get_picture_files_list()]

    handler = Mock()
    signals.picture_processed.connect(handler)
    try:
        obj.picture.delete()
    finally:
        signals.picture_processed.disconnect(handler)

    handler.assert_called_once()
    kwargs = handler.call_args.kwargs
    assert kwargs["signal"] == signals.picture_processed
    assert kwargs["sender"] == SimpleModel._meta.get_field("picture")
    assert kwargs["file_name"] == name
    assert kwargs["new"] == []
    # task backends JSON-serialize the arguments, thus tuples become lists
    assert json.dumps(kwargs["old"]) == json.dumps(pictures)


@pytest.mark.django_db
@skip_dramatiq
def test_process_picture__get_processed_object(image_upload_file):
    obj = SimpleModel.objects.create()

    found_object = None

    def handler(*, sender, file_name, **kwargs):
        nonlocal found_object
        found_object = sender.model.objects.get(**{sender.name: file_name})

    field = SimpleModel._meta.get_field("picture")
    signals.picture_processed.connect(handler, sender=field)
    try:
        obj.picture.save("image.png", image_upload_file)
    finally:
        signals.picture_processed.disconnect(handler, sender=field)

    assert obj == found_object


@pytest.mark.django_db
@skip_dramatiq
def test_process_picture__without_sender(image_upload_file):
    """Process pictures of queued tasks that predate the sender argument."""
    obj = SimpleModel.objects.create(picture=image_upload_file)
    pictures = [i.deconstruct() for i in obj.picture.get_picture_files_list()]
    path = obj.picture.aspect_ratios["16/9"]["AVIF"][100].path
    path.unlink()
    assert not path.exists()

    handler = Mock()
    signals.picture_processed.connect(handler)
    try:
        tasks._process_picture(
            storage=obj.picture.storage.deconstruct(),
            file_name=obj.picture.name,
            sender=None,
            new=pictures,
        )
    finally:
        signals.picture_processed.disconnect(handler)

    assert path.exists()
    assert not handler.called


@pytest.mark.django_db
@skip_dramatiq
def test_process_picture__without_registered_model(image_upload_file):
    """Send no signal for models that only exist in a historical migration state."""
    obj = SimpleModel.objects.create(picture=image_upload_file)
    pictures = [i.deconstruct() for i in obj.picture.get_picture_files_list()]

    handler = Mock()
    signals.picture_processed.connect(handler)
    try:
        tasks._process_picture(
            storage=obj.picture.storage.deconstruct(),
            file_name=obj.picture.name,
            sender=("testapp", "unknown_model", "picture"),
            new=pictures,
        )
    finally:
        signals.picture_processed.disconnect(handler)

    # pictures are still processed, no error is raised
    assert obj.picture.aspect_ratios["16/9"]["AVIF"][100].path.exists()
    assert not handler.called
