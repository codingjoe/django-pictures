from typing import Protocol

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db import transaction
from django.tasks import exceptions, task
from PIL import Image

from pictures import conf, signals, utils
from pictures.conf import app_settings
from pictures.models import PillowPicture


def noop(*args, **kwargs) -> None:
    """Do nothing. You will need to set up your own image processing (like a CDN)."""


class PictureProcessor(Protocol):
    def __call__(
        self,
        *,
        storage: tuple[str, list, dict],
        file_name: str,
        sender: tuple[str, str, str],
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None: ...


def _process_picture(
    *,
    storage: tuple[str, list, dict],
    file_name: str,
    sender: tuple[str, str, str] | None,
    new: list[tuple[str, list, dict]] | None = None,
    old: list[tuple[str, list, dict]] | None = None,
) -> None:
    new = new or []
    old = old or []
    storage = utils.reconstruct(*storage)
    if new:
        with storage.open(file_name) as fs, Image.open(fs) as img:
            img = PillowPicture.pre_process(img)
            for picture in new:
                picture = utils.reconstruct(*picture)
                picture.save(img)

    for picture in old:
        picture = utils.reconstruct(*picture)
        picture.delete()

    if sender is not None:
        try:
            app_label, model_name, field_name = sender
            field = apps.get_registered_model(app_label, model_name)._meta.get_field(
                field_name
            )
        except LookupError, FieldDoesNotExist:
            pass  # The model may only exist in a historical migration state, send no signal.
        else:
            signals.picture_processed.send(
                sender=field,
                file_name=file_name,
                new=new,
                old=old,
            )


process_picture: PictureProcessor = _process_picture


try:

    @task(
        backend=conf.app_settings.BACKEND,
        queue_name=conf.app_settings.QUEUE_NAME,
    )
    def process_picture_with_django_tasks(
        *,
        storage: tuple[str, list, dict],
        file_name: str,
        sender: tuple[str, str, str] | None = None,
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None:
        _process_picture(
            storage=storage, file_name=file_name, sender=sender, new=new, old=old
        )

    def process_picture(
        *,
        storage: tuple[str, list, dict],
        file_name: str,
        sender: tuple[str, str, str],
        new: list[tuple[str, list, dict]] | None = None,
        old: list[tuple[str, list, dict]] | None = None,
    ) -> None:
        transaction.on_commit(
            lambda: process_picture_with_django_tasks.enqueue(
                storage=storage,
                file_name=file_name,
                sender=sender,
                new=new,
                old=old,
            )
        )

except exceptions.InvalidTask as e:
    if app_settings.PROCESSOR == "pictures.tasks.process_picture":
        msg = (
            "Pictures are processed on a separate queue by default,"
            " please update the 'TASKS' setting in accordance with Django-Pictures documentation."
            " If you use a custom processor, please set the 'PROCESSOR' setting accordingly."
        )
        raise exceptions.ImproperlyConfigured(msg) from e
