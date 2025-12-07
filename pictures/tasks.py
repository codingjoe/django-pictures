from __future__ import annotations

import warnings
from typing import Protocol

import django
from django.db import transaction
from PIL import Image

from pictures import conf, utils


def noop(*args, **kwargs) -> None:
    """Do nothing. You will need to set up your own image processing (like a CDN)."""


class PictureProcessor(Protocol):
    def __call__(
        self,
        storage: tuple[str, list, dict],
        file_name: str,
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None: ...


def _process_picture(
    storage: tuple[str, list, dict],
    file_name: str,
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


process_picture: PictureProcessor = _process_picture


try:
    from dramatiq import actor
except ImportError:
    pass
else:

    @actor(queue_name=conf.get_settings().QUEUE_NAME)
    def process_picture_with_dramatiq(
        storage: tuple[str, list, dict],
        file_name: str,
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None:
        _process_picture(storage, file_name, new, old)

    def dramatiq_process_picture(  # noqa: F811
        storage: tuple[str, list, dict],
        file_name: str,
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None:
        if django.VERSION >= (6, 0):
            warnings.warn(
                "The 'dramatiq_process_picture'-processor is deprecated in favor of Django's tasks framework."
                " Deletion is scheduled with Django 5.2 version support.",
                PendingDeprecationWarning,
                stacklevel=2,
            )
        transaction.on_commit(
            lambda: process_picture_with_dramatiq.send(
                storage=storage,
                file_name=file_name,
                new=new,
                old=old,
            )
        )

    process_picture = dramatiq_process_picture  # type: ignore[assignment]


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
    ) -> None:
        _process_picture(storage, file_name, new, old)

    def celery_process_picture(  # noqa: F811
        storage: tuple[str, list, dict],
        file_name: str,
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None:
        if django.VERSION >= (6, 0):
            warnings.warn(
                "The 'celery_process_picture'-processor is deprecated in favor of Django's tasks framework."
                " Deletion is scheduled with Django 5.2 version support.",
                PendingDeprecationWarning,
                stacklevel=2,
            )
        transaction.on_commit(
            lambda: process_picture_with_celery.apply_async(
                kwargs=dict(
                    storage=storage,
                    file_name=file_name,
                    new=new,
                    old=old,
                ),
                queue=conf.get_settings().QUEUE_NAME,
            )
        )

    process_picture = celery_process_picture  # type: ignore[assignment]


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
    ) -> None:
        _process_picture(storage, file_name, new, old)

    def rq_process_picture(  # noqa: F811
        storage: tuple[str, list, dict],
        file_name: str,
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None:
        if django.VERSION >= (6, 0):
            warnings.warn(
                "The 'rq_process_picture'-processor is deprecated in favor of Django's tasks framework."
                " Deletion is scheduled with Django 5.2 version support.",
                PendingDeprecationWarning,
                stacklevel=2,
            )
        transaction.on_commit(
            lambda: process_picture_with_django_rq.delay(
                storage=storage,
                file_name=file_name,
                new=new,
                old=old,
            )
        )

    process_picture = rq_process_picture  # type: ignore[assignment]


try:
    from django.tasks import exceptions, task
except ImportError:
    pass
else:
    try:

        @task(
            backend=conf.get_settings().BACKEND,
            queue_name=conf.get_settings().QUEUE_NAME,
        )
        def process_picture_with_django_tasks(
            storage: tuple[str, list, dict],
            file_name: str,
            new: list[tuple[str, list, dict]] | None = None,
            old: list[tuple[str, list, dict]] | None = None,
        ) -> None:
            _process_picture(storage, file_name, new, old)

        def process_picture(  # noqa: F811
            storage: tuple[str, list, dict],
            file_name: str,
            new: list[tuple[str, list, dict]] | None = None,
            old: list[tuple[str, list, dict]] | None = None,
        ) -> None:
            transaction.on_commit(
                lambda: process_picture_with_django_tasks.enqueue(
                    storage=storage,
                    file_name=file_name,
                    new=new,
                    old=old,
                )
            )

    except exceptions.InvalidTask as e:
        raise exceptions.ImproperlyConfigured(
            "Pictures are processed on a separate queue by default,"
            " please configure the `TASKS` settings in accordance with Django-Pictures documentation."
        ) from e
