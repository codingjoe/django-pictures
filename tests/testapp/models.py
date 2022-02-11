from django.db import models
from django.urls import reverse

from pictures.models import PictureField


class SimpleModel(models.Model):
    picture_width = models.PositiveIntegerField(null=True)
    picture_height = models.PositiveIntegerField(null=True)
    picture = PictureField(
        upload_to="testapp/simplemodel/",
        aspect_ratios=[None, "3/2", "16/9"],
        width_field="picture_width",
        height_field="picture_height",
        blank=True,
        null=True,
    )


class Profile(models.Model):
    name = models.CharField(max_length=100)
    picture = PictureField(
        upload_to="testapp/profile/", aspect_ratios=[None, "1/1", "3/2", "16/9"]
    )

    def get_absolute_url(self):
        return reverse("profile_detail", kwargs={"pk": self.pk})
