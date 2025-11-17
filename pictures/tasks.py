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
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
        field: str = "",
    ) -> None: ...


def _process_picture(
    storage: tuple[str, list, dict],
    file_name: str,
    new: list[tuple[str, list, dict]] | None = None,
    old: list[tuple[str, list, dict]] | None = None,
    field: str = "",
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

    if field:
        app_label, model_name, _ = field.split(".")
        sender = apps.get_model(app_label=app_label, model_name=model_name)
    else:
        sender = _process_picture

    signals.process_picture_done.send(
        sender=sender,
        storage=storage.deconstruct(),
        file_name=file_name,
        new=new,
        old=old,
        field=field,
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
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
        field: str = "",
    ) -> None:
        _process_picture(storage, file_name, new, old, field)

    def process_picture(  # noqa: F811
        storage: tuple[str, list, dict],
        file_name: str,
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
        field: str = "",
    ) -> None:
        transaction.on_commit(
            lambda: process_picture_with_dramatiq.send(
                storage=storage,
                file_name=file_name,
                new=new,
                old=old,
                field=field,
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
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
        field: str = "",
    ) -> None:
        _process_picture(storage, file_name, new, old, field)

    def process_picture(  # noqa: F811
        storage: tuple[str, list, dict],
        file_name: str,
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
        field: str = "",
    ) -> None:
        transaction.on_commit(
            lambda: process_picture_with_celery.apply_async(
                kwargs=dict(
                    storage=storage,
                    file_name=file_name,
                    new=new,
                    old=old,
                    field=field,
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
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
        field: str = "",
    ) -> None:
        _process_picture(storage, file_name, new, old, field)

    def process_picture(  # noqa: F811
        storage: tuple[str, list, dict],
        file_name: str,
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
        field: str = "",
    ) -> None:
        transaction.on_commit(
            lambda: process_picture_with_django_rq.delay(
                storage=storage,
                file_name=file_name,
                new=new,
                old=old,
                field=field,
            )
        )
