from unittest.mock import Mock

import pytest
from django.core.management import call_command
from django.db import models
from django.db.models.fields.files import ImageFieldFile

from pictures import migrations
from pictures.models import PictureField
from tests.testapp.models import Profile

try:
    import dramatiq
except ImportError:
    dramatiq = None

try:
    import celery
except ImportError:
    celery = None


skip_dramatiq = pytest.mark.skipif(
    not all(x is None for x in [dramatiq, celery]),
    reason="dramatiq and celery are installed",
)


@skip_dramatiq
class TestAlterPictureField:
    def test_alter_picture_field__image_to_image(self, request, monkeypatch):
        class FromModel(models.Model):
            picture = models.ImageField()

            class Meta:
                app_label = request.node.name

        class ToModel(models.Model):
            picture = models.ImageField()

            class Meta:
                app_label = request.node.name

        migration = migrations.AlterPictureField("profile", "picture", PictureField())
        monkeypatch.setattr(migration, "update_pictures", Mock())
        monkeypatch.setattr(migration, "from_picture_field", Mock())
        monkeypatch.setattr(migration, "to_picture_field", Mock())
        migration.alter_picture_field(FromModel, ToModel)

        assert not migration.update_pictures.called
        assert not migration.from_picture_field.called
        assert not migration.to_picture_field.called

    def test_alter_picture_field__image_to_picture(self, request, monkeypatch):
        class FromModel(models.Model):
            picture = models.ImageField()

            class Meta:
                app_label = request.node.name

        class ToModel(models.Model):
            picture = PictureField()

            class Meta:
                app_label = request.node.name

        migration = migrations.AlterPictureField("profile", "picture", PictureField())
        monkeypatch.setattr(migration, "to_picture_field", Mock())
        migration.alter_picture_field(FromModel, ToModel)

        migration.to_picture_field.assert_called_once_with(FromModel, ToModel)

    def test_alter_picture_field__picture_to_image(self, request, monkeypatch):
        class FromModel(models.Model):
            picture = PictureField()

            class Meta:
                app_label = request.node.name

        class ToModel(models.Model):
            picture = models.ImageField()

            class Meta:
                app_label = request.node.name

        migration = migrations.AlterPictureField("profile", "picture", PictureField())
        monkeypatch.setattr(migration, "from_picture_field", Mock())
        migration.alter_picture_field(FromModel, ToModel)

        migration.from_picture_field.assert_called_once_with(FromModel)

    def test_alter_picture_field__picture_to_picture(self, request, monkeypatch):
        class FromModel(models.Model):
            picture = PictureField()

            class Meta:
                app_label = request.node.name

        class ToModel(models.Model):
            picture = PictureField()

            class Meta:
                app_label = request.node.name

        migration = migrations.AlterPictureField("profile", "picture", PictureField())
        monkeypatch.setattr(migration, "update_pictures", Mock())
        monkeypatch.setattr(migration, "from_picture_field", Mock())
        monkeypatch.setattr(migration, "to_picture_field", Mock())
        migration.alter_picture_field(FromModel, ToModel)
        from_field = FromModel._meta.get_field("picture")
        migration.update_pictures.assert_called_once_with(from_field, ToModel)
        assert not migration.from_picture_field.called
        assert not migration.to_picture_field.called

    @pytest.mark.django_db
    def test_update_pictures(self, request, stub_worker, image_upload_file):
        class ToModel(models.Model):
            name = models.CharField(max_length=100)
            picture = PictureField(
                upload_to="testapp/profile/", aspect_ratios=[None, "21/9"]
            )

            class Meta:
                app_label = request.node.name
                db_table = "testapp_profile"

        luke = Profile.objects.create(name="Luke", picture=image_upload_file)
        stub_worker.join()
        migration = migrations.AlterPictureField("profile", "picture", PictureField())
        from_field = Profile._meta.get_field("picture")

        path = luke.picture.aspect_ratios["16/9"]["WEBP"][100].path
        assert path.exists()

        migration.update_pictures(from_field, ToModel)
        stub_worker.join()

        assert not path.exists()
        luke.refresh_from_db()
        path = (
            ToModel.objects.get(pk=luke.pk)
            .picture.aspect_ratios["21/9"]["WEBP"][100]
            .path
        )
        assert path.exists()

    @pytest.mark.django_db
    def test_update_pictures__without_picture(self, request, stub_worker):
        class ToModel(models.Model):
            name = models.CharField(max_length=100)
            picture = PictureField(
                upload_to="testapp/profile/", aspect_ratios=[None, "21/9"], blank=True
            )

            class Meta:
                app_label = request.node.name
                db_table = "testapp_profile"

        luke = Profile.objects.create(name="Luke")
        stub_worker.join()
        migration = migrations.AlterPictureField("profile", "picture", PictureField())
        from_field = Profile._meta.get_field("picture")

        migration.update_pictures(from_field, ToModel)
        stub_worker.join()
        luke.refresh_from_db()

        assert not luke.picture

    @pytest.mark.django_db
    def test_from_picture_field(self, stub_worker, image_upload_file):
        luke = Profile.objects.create(name="Luke", picture=image_upload_file)
        stub_worker.join()
        path = luke.picture.aspect_ratios["16/9"]["WEBP"][100].path
        assert path.exists()
        migration = migrations.AlterPictureField("profile", "picture", PictureField())
        migration.from_picture_field(Profile)
        stub_worker.join()
        assert not path.exists()

    @pytest.mark.django_db
    def test_to_picture_field(self, request, stub_worker, image_upload_file):
        class FromModel(models.Model):
            picture = models.ImageField()

            class Meta:
                app_label = request.node.name
                db_table = "testapp_profile"

        class ToModel(models.Model):
            name = models.CharField(max_length=100)
            picture = models.ImageField(upload_to="testapp/profile/")

            class Meta:
                app_label = request.node.name
                db_table = "testapp_profile"

        luke = ToModel.objects.create(name="Luke", picture=image_upload_file)
        stub_worker.join()
        migration = migrations.AlterPictureField("profile", "picture", PictureField())
        migration.to_picture_field(FromModel, Profile)
        stub_worker.join()
        luke.refresh_from_db()
        path = (
            Profile.objects.get(pk=luke.pk)
            .picture.aspect_ratios["16/9"]["WEBP"][100]
            .path
        )
        assert path.exists()

    @pytest.mark.django_db
    def test_to_picture_field_blank(self, request, stub_worker):
        class FromModel(models.Model):
            picture = models.ImageField(blank=True)

            class Meta:
                app_label = request.node.name
                db_table = "testapp_profile"

        class ToModel(models.Model):
            name = models.CharField(max_length=100)
            picture = models.ImageField(upload_to="testapp/profile/", blank=True)

            class Meta:
                app_label = request.node.name
                db_table = "testapp_profile"

        ToModel.objects.create(name="Luke")
        stub_worker.join()
        migration = migrations.AlterPictureField("profile", "picture", PictureField())
        migration.to_picture_field(FromModel, Profile)

    @pytest.mark.django_db
    def test_to_picture_field__from_stdimage(
        self, request, stub_worker, image_upload_file
    ):
        class StdImageFieldFile(ImageFieldFile):
            delete_variations = Mock()

        class StdImageField(models.ImageField):
            attr_class = StdImageFieldFile

        class FromModel(models.Model):
            picture = StdImageField()

            class Meta:
                app_label = request.node.name
                db_table = "testapp_profile"

        class ToModel(models.Model):
            name = models.CharField(max_length=100)
            picture = models.ImageField(upload_to="testapp/profile/")

            class Meta:
                app_label = request.node.name
                db_table = "testapp_profile"

        luke = ToModel.objects.create(name="Luke", picture=image_upload_file)
        stub_worker.join()
        migration = migrations.AlterPictureField("profile", "picture", PictureField())
        migration.to_picture_field(FromModel, Profile)
        stub_worker.join()
        luke.refresh_from_db()
        path = (
            Profile.objects.get(pk=luke.pk)
            .picture.aspect_ratios["16/9"]["WEBP"][100]
            .path
        )
        assert path.exists()
        assert StdImageFieldFile.delete_variations.called

    @pytest.mark.django_db(transaction=True)
    def test_database_backwards_forwards(self):
        call_command("migrate", "testapp", "0001")
        call_command("migrate", "testapp", "0002")
