from django.contrib import admin

from pictures.models import PictureField
from pictures.widgets import AdminPictureWidget

from . import models


@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    formfield_overrides = {PictureField: {"widget": AdminPictureWidget}}
