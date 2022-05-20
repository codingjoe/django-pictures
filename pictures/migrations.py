from typing import Type

from django.db import models
from django.db.migrations import AlterField

from pictures.models import PictureField, PictureFieldFile

__all__ = ["AlterPictureField"]


class AlterPictureField(AlterField):
    """Alter field schema and render or remove picture sizes."""

    reduces_to_sql = False
    reversible = True

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        super().database_forwards(app_label, schema_editor, from_state, to_state)
        from_model = from_state.apps.get_model(app_label, self.model_name)
        to_model = to_state.apps.get_model(app_label, self.model_name)
        self.alter_picture_field(from_model, to_model)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        super().database_backwards(app_label, schema_editor, from_state, to_state)
        from_model = from_state.apps.get_model(app_label, self.model_name)
        to_model = to_state.apps.get_model(app_label, self.model_name)
        self.alter_picture_field(from_model, to_model)

    def alter_picture_field(
        self, from_model: Type[models.Model], to_model: Type[models.Model]
    ):
        from_field = from_model._meta.get_field(self.name)
        to_field = to_model._meta.get_field(self.name)

        if not isinstance(from_field, PictureField) and isinstance(
            to_field, PictureField
        ):
            self.to_picture_field(from_model, to_model)
        elif isinstance(from_field, PictureField) and not isinstance(
            to_field, PictureField
        ):
            self.from_picture_field(from_model)
        elif isinstance(from_field, PictureField) and isinstance(
            to_field, PictureField
        ):
            self.update_pictures(from_field, to_model)

    def update_pictures(self, from_field: PictureField, to_model: Type[models.Model]):
        for obj in to_model._default_manager.all().iterator():
            field_file = getattr(obj, self.name)
            field_file.update_all(
                from_aspect_ratios=PictureFieldFile.get_picture_files(
                    file_name=field_file.name,
                    img_width=field_file.width,
                    img_height=field_file.height,
                    storage=field_file.storage,
                    field=from_field,
                )
            )

    def from_picture_field(self, from_model: Type[models.Model]):
        for obj in from_model._default_manager.all().iterator():
            field_file = getattr(obj, self.name)
            field_file.delete_all()

    def to_picture_field(
        self, from_model: Type[models.Model], to_model: Type[models.Model]
    ):
        from_field = from_model._meta.get_field(self.name)
        if hasattr(from_field.attr_class, "delete_variations"):
            # remove obsolete django-stdimage variations
            for obj in from_model._default_manager.all().iterator():
                field_file = getattr(obj, self.name)
                field_file.delete_variations()
        for obj in to_model._default_manager.all().iterator():
            field_file = getattr(obj, self.name)
            field_file.save_all()
