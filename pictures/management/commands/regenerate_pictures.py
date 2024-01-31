from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Q

from pictures.models import PictureField, PictureFieldFile


def regenerate_pictures(model_name: str):
    app_label, model_name = model_name.split(".")
    model = apps.get_model(app_label, model_name)
    for field in model._meta.get_fields():
        if isinstance(field, PictureField):
            for obj in model._default_manager.exclude(
                Q(**{field.name: ""}) | Q(**{field.name: None})
            ).iterator():
                field_file = getattr(obj, field.name)
                field_file.update_all(
                    from_aspect_ratios=PictureFieldFile.get_picture_files(
                        file_name=field_file.name,
                        img_width=field_file.width,
                        img_height=field_file.height,
                        storage=field_file.storage,
                        field=field,
                    )
                )


class Command(BaseCommand):
    """Regenerate pictures for a given model or a list of models."""

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("model", nargs="+", type=str)

    def handle(self, *args, **options):
        for model_name in options["model"]:
            regenerate_pictures(model_name)
