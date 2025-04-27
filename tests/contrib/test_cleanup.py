import pytest
from django.core.files.storage import default_storage
from django.db import router, transaction

from tests.testapp.models import SimpleModel

pytest.importorskip("django_cleanup")


def get_using(instance):
    return router.db_for_write(instance.__class__, instance=instance)


class TestCleanCase:
    @pytest.mark.django_db(transaction=True)
    def test_delete(self, stub_worker, image_upload_file):
        obj = SimpleModel(picture=image_upload_file)
        obj.save()
        stub_worker.join()

        name = obj.picture.name
        path = obj.picture.aspect_ratios["16/9"]["AVIF"][100].path
        assert default_storage.exists(name)
        assert path.exists()
        with transaction.atomic(get_using(obj)):
            obj.delete()
        assert not default_storage.exists(name)
        assert not path.exists()
