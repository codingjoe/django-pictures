from __future__ import annotations

import importlib

from django.apps import apps
from django.core.files.storage import Storage
from django.db import transaction
from PIL import Image

from pictures import conf
from pictures.models import PictureFieldFile


def _process_picture(field_file: PictureFieldFile) -> None:
    # field_file.file may already be closed and can't be reopened.
    # Therefore, we always open it from storage.
    with field_file.storage.open(field_file.name) as fs:
        with Image.open(fs) as img:
            for ratio, sources in field_file.aspect_ratios.items():
                for file_type, srcset in sources.items():
                    for width, picture in srcset.items():
                        picture.save(img)


process_picture = _process_picture


def construct_storage(
    storage_cls: str, storage_args: tuple, storage_kwargs: dict
) -> Storage:
    storage_module, storage_class = storage_cls.rsplit(".", 1)
    storage_cls = getattr(importlib.import_module(storage_module), storage_class)
    return storage_cls(*storage_args, **storage_kwargs)


def process_picture_async(
    app_name: str, model_name: str, field_name: str, file_name: str, storage_construct
) -> None:
    model = apps.get_model(f"{app_name}.{model_name}")
    field = model._meta.get_field(field_name)
    storage = construct_storage(*storage_construct)

    with storage.open(file_name) as file:
        with Image.open(file) as img:
            for ratio, sources in PictureFieldFile.get_picture_files(
                file_name=file_name,
                img_width=img.width,
                img_height=img.height,
                storage=storage,
                field=field,
            ).items():
                for file_type, srcset in sources.items():
                    for width, picture in srcset.items():
                        picture.save(img)


try:
    import dramatiq
except ImportError:
    pass
else:

    @dramatiq.actor(queue_name=conf.get_settings().QUEUE_NAME)
    def process_picture_with_dramatiq(
        app_name, model_name, field_name, file_name, storage_construct
    ) -> None:
        process_picture_async(
            app_name, model_name, field_name, file_name, storage_construct
        )

    def process_picture(field_file: PictureFieldFile) -> None:  # noqa: F811
        opts = field_file.instance._meta
        transaction.on_commit(
            lambda: process_picture_with_dramatiq.send(
                app_name=opts.app_label,
                model_name=opts.model_name,
                field_name=field_file.field.name,
                file_name=field_file.name,
                storage_construct=field_file.storage.deconstruct(),
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
        app_name, model_name, field_name, file_name, storage_construct
    ) -> None:
        process_picture_async(
            app_name, model_name, field_name, file_name, storage_construct
        )

    def process_picture(field_file: PictureFieldFile) -> None:  # noqa: F811
        opts = field_file.instance._meta
        transaction.on_commit(
            lambda: process_picture_with_celery.apply_async(
                kwargs=dict(
                    app_name=opts.app_label,
                    model_name=opts.model_name,
                    field_name=field_file.field.name,
                    file_name=field_file.name,
                    storage_construct=field_file.storage.deconstruct(),
                ),
                queue=conf.get_settings().QUEUE_NAME,
            )
        )
