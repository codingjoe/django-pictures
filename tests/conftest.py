import io
from unittest.mock import Mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from pictures import conf


@pytest.fixture
def image_upload_file():
    img = Image.new("RGB", (800, 800), (255, 55, 255))

    with io.BytesIO() as output:
        img.save(output, format="JPEG")
        return SimpleUploadedFile("image.jpg", output.getvalue())


@pytest.fixture(autouse=True, scope="function")
def media_root(settings, tmpdir_factory):
    settings.MEDIA_ROOT = tmpdir_factory.mktemp("media", numbered=True)


@pytest.fixture(autouse=True)
def instant_commit(monkeypatch):
    monkeypatch.setattr("django.db.transaction.on_commit", lambda f: f())


@pytest.fixture()
def stub_worker():
    try:
        import dramatiq
    except ImportError:
        yield Mock()
    else:
        broker = dramatiq.get_broker()
        broker.emit_after("process_boot")
        broker.flush_all()
        worker = dramatiq.Worker(broker, worker_timeout=100)
        worker.start()

        class Meta:
            @staticmethod
            def join():
                broker.join(conf.get_settings().QUEUE_NAME, timeout=60000)
                worker.join()

        yield Meta
        worker.stop()
