# Generated by Django 4.1 on 2023-04-17 15:42

from django.db import migrations, models

import pictures.models


class Migration(migrations.Migration):
    dependencies = [
        ("testapp", "0003_validatormodel"),
    ]

    operations = [
        migrations.CreateModel(
            name="JPEGModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("picture_width", models.PositiveIntegerField(null=True)),
                ("picture_height", models.PositiveIntegerField(null=True)),
                (
                    "picture",
                    pictures.models.PictureField(
                        aspect_ratios=[None, "3/2", "16/9"],
                        blank=True,
                        breakpoints={
                            "l": 1200,
                            "m": 992,
                            "s": 768,
                            "xl": 1400,
                            "xs": 576,
                        },
                        container_width=1200,
                        file_types=["WEBP", "JPEG"],
                        grid_columns=12,
                        height_field="picture_height",
                        null=True,
                        pixel_densities=[1, 2],
                        upload_to="testapp/simplemodel/",
                        width_field="picture_width",
                    ),
                ),
            ],
        ),
    ]
