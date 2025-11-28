from __future__ import annotations

from typing import Protocol

from django.apps import apps
from django.db import transaction
from PIL import Image

from pictures import conf, signals, utils


def noop(*args, **kwargs) -> None:
    """Do nothing. You will need to set up your own image processing (like a CDN)."""


class PictureProcessor(Protocol):
    def __call__(
        self,
        storage: tuple[str, list, dict],
        file_name: str,
        sender: tuple[str, str, str],
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None: ...


def _process_picture(
    storage: tuple[str, list, dict],
    file_name: str,
    sender: tuple[str, str, str],
    new: list[tuple[str, list, dict]] | None = None,
    old: list[tuple[str, list, dict]] | None = None,
) -> None:
    new = new or []
    old = old or []
    storage = utils.reconstruct(*storage)
    if new:
        with storage.open(file_name) as fs, Image.open(fs) as img:
            for picture in new:
                picture = utils.reconstruct(*picture)
                picture.save(img)

    for picture in old:
        picture = utils.reconstruct(*picture)
        picture.delete()

    app_label, model_name, field_name = sender
    model = apps.get_model(app_label=app_label, model_name=model_name)
    field = model._meta.get_field(field_name)

    signals.picture_processed.send(
        sender=field,
        file_name=file_name,
        new=new,
        old=old,
    )


process_picture: PictureProcessor = _process_picture


try:
    import dramatiq
except ImportError:
    pass
else:

    @dramatiq.actor(queue_name=conf.get_settings().QUEUE_NAME)
    def process_picture_with_dramatiq(
        storage: tuple[str, list, dict],
        file_name: str,
        sender: tuple[str, str, str],
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None:
        _process_picture(storage, file_name, sender, new, old)

    def process_picture(  # noqa: F811
        storage: tuple[str, list, dict],
        file_name: str,
        sender: tuple[str, str, str],
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None:
        transaction.on_commit(
            lambda: process_picture_with_dramatiq.send(
                storage=storage,
                file_name=file_name,
                sender=sender,
                new=new,
                old=old,
            )
        )


try:
    from celery import shared_task
except ImportError:
    pass
else:

    @shared_task(
        ignore_results=True,
        retry_backoff=True,
    )
    def process_picture_with_celery(
        storage: tuple[str, list, dict],
        file_name: str,
        sender: tuple[str, str, str],
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None:
        _process_picture(storage, file_name, sender, new, old)

    def process_picture(  # noqa: F811
        storage: tuple[str, list, dict],
        file_name: str,
        sender: tuple[str, str, str],
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None:
        transaction.on_commit(
            lambda: process_picture_with_celery.apply_async(
                kwargs=dict(
                    storage=storage,
                    file_name=file_name,
                    sender=sender,
                    new=new,
                    old=old,
                ),
                queue=conf.get_settings().QUEUE_NAME,
            )
        )


try:
    from django_rq import job
except ImportError:
    pass
else:

    @job(conf.get_settings().QUEUE_NAME)
    def process_picture_with_django_rq(
        storage: tuple[str, list, dict],
        file_name: str,
        sender: tuple[str, str, str],
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None:
        _process_picture(storage, file_name, sender, new, old)

    def process_picture(  # noqa: F811
        storage: tuple[str, list, dict],
        file_name: str,
        sender: tuple[str, str, str],
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None:
        transaction.on_commit(
            lambda: process_picture_with_django_rq.delay(
                storage=storage,
                file_name=file_name,
                sender=sender,
                new=new,
                old=old,
            )
        )
