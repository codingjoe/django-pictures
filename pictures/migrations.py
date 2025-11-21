from django.db import models
from django.db.migrations import AlterField
from django.db.models import Q

from pictures.models import PictureField

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
        self, from_model: type[models.Model], to_model: type[models.Model]
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

    def update_pictures(self, from_field: PictureField, to_model: type[models.Model]):
        """Remove obsolete pictures and create new ones."""
        for obj in to_model._default_manager.exclude(
            Q(**{self.name: ""}) | Q(**{self.name: None})
        ).iterator():
            new_field_file = getattr(obj, self.name)
            old_field_file = from_field.attr_class(
                instance=obj, field=from_field, name=new_field_file.name
            )
            new_field_file.update_all(old_field_file)

    def from_picture_field(self, from_model: type[models.Model]):
        for obj in from_model._default_manager.all().iterator():
            field_file = getattr(obj, self.name)
            field_file.delete_all()

    def to_picture_field(
        self, from_model: type[models.Model], to_model: type[models.Model]
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
