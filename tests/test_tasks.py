import importlib
from unittest.mock import Mock

import pytest
from django.core.exceptions import ImproperlyConfigured

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
    tasks._process_picture(
        obj.picture.storage.deconstruct(),
        obj.picture.name,
        new=[i.deconstruct() for i in obj.picture.get_picture_files_list()],
    )


def test_noop():
    tasks.noop()  # does nothing


def test_django_tasks_misconfiguration(settings):
    pytest.importorskip(
        "django", minversion="6.0", reason="Django tasks introduced in 6.0"
    )
    settings.TASKS = {
        "default": {
            "BACKEND": "django.tasks.backends.immediate.ImmediateBackend",
            "QUEUES": ["default"],
        }
    }
    with pytest.raises(ImproperlyConfigured) as e:
        importlib.reload(tasks)
    assert str(e.value) == (
        "Pictures are processed on a separate queue by default,"
        " please update the 'TASKS' setting in accordance with Django-Pictures documentation."
    )
