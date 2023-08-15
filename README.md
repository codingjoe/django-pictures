![Django Pictures Logo](https://repository-images.githubusercontent.com/455480246/daaa7870-d28c-4fce-8296-d3e3af487a64)

# Django Pictures

Responsive cross-browser image library using modern codes like AVIF & WebP.

* responsive web images using the [picture](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/picture) tag
* native grid system support
* serve files with or without a CDN
* placeholders for local development
* migration support
* async image processing for [Celery] or [Dramatiq]
* [DRF] support

[![PyPi Version](https://img.shields.io/pypi/v/django-pictures.svg)](https://pypi.python.org/pypi/django-pictures/)
[![Test Coverage](https://codecov.io/gh/codingjoe/django-pictures/branch/main/graph/badge.svg)](https://codecov.io/gh/codingjoe/django-pictures)
[![GitHub License](https://img.shields.io/github/license/codingjoe/django-pictures)](https://raw.githubusercontent.com/codingjoe/django-pictures/master/LICENSE)

## Usage

Before you start, it can be a good idea to understand the fundamentals of
[responsive images](https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images).

Once you get a feeling how complicated things can get with all device types, you'll probably find
a new appreciation for this package and are ready to adopt in you project :)

```python
# models.py
from django.db import models
from pictures.models import PictureField

class Profile(models.Model):
    title = models.CharField(max_length=255)
    picture = PictureField(upload_to="avatars")
```

```html
<!-- template.html -->
{% load pictures %}
{% picture profile.picture img_alt="Spiderman" img_loading="lazy" picture_class="my-picture" m=6 l=4 %}
```

The template above will render into:
```html
<picture class="my-picture">
  <source type="image/webp"
          srcset="/media/testapp/profile/image/800w.webp 800w, /media/testapp/profile/image/100w.webp 100w, /media/testapp/profile/image/200w.webp 200w, /media/testapp/profile/image/300w.webp 300w, /media/testapp/profile/image/400w.webp 400w, /media/testapp/profile/image/500w.webp 500w, /media/testapp/profile/image/600w.webp 600w, /media/testapp/profile/image/700w.webp 700w"
          sizes="(min-width: 0px) and (max-width: 991px) 100vw, (min-width: 992px) and (max-width: 1199px) 33vw, 600px">
  <img src="/media/testapp/profile/image.jpg" alt="Spiderman" width="800" height="800" loading="lazy">
</picture>
```

Note that arbitrary attributes can be passed
to either the `<picture>` or `<img>` element
by prefixing parameters to the `{% picture %}` tag
with `picture_` or `img_` respectively.

## Setup

### Installation

```shell
python3 -m pip install django-pictures
```

### Settings

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'pictures',
]

# the following are defaults, but you can override them
PICTURES = {
    "BREAKPOINTS": {
        "xs": 576,
        "s": 768,
        "m": 992,
        "l": 1200,
        "xl": 1400,
    },
    "GRID_COLUMNS": 12,
    "CONTAINER_WIDTH": 1200,
    "FILE_TYPES": ["WEBP"],
    "PIXEL_DENSITIES": [1, 2],
    "USE_PLACEHOLDERS": True,
    "QUEUE_NAME": "pictures",
    "PROCESSOR": "pictures.tasks.process_picture",

}
```

If you have either Dramatiq or Celery installed, we will default to async
image processing. You will need workers to listen to the `pictures` queue.

### Placeholders

This library comes with dynamically created placeholders to simplify local
development. To enable them, add the following to enable the
`PICTURES["USE_PLACEHOLDERS"]` setting and add the following URL configuration:

```python
# urls.py
from django.urls import include, path
from pictures.conf import get_settings

urlpatterns = [
    # ...
]

if get_settings().USE_PLACEHOLDERS:
    urlpatterns += [
        path("_pictures/", include("pictures.urls")),
    ]
```

### Legacy use-cases (email)

Although the `picture`-tag is [adequate for most use-cases][caniuse-picture],
some remain, where a single `img` tag is necessary. Notably in email, where
[most clients do support WebP][caniemail-webp] but not [srcset][caniemail-srcset].
The template tag `img_url` returns a single size image URL.
In addition to the ratio you will need to define the `file_type`
as well as the `width` (absolute width in pixels).


```html
{% load pictures %}
<img src="{% img_url profile.picture ratio="3/2" file_type="webp" width=800 %}" alt="profile picture">
```

[caniuse-picture]: https://caniuse.com/picture
[caniemail-webp]: https://www.caniemail.com/features/image-webp/
[caniemail-srcset]: https://www.caniemail.com/features/html-srcset/

## Config

### Aspect ratios

You can specify the aspect ratios of your images. Images will be cropped to the
specified aspect ratio. Aspect ratios are specified as a string with a slash
between the width and height. For example, `16/9` will crop the image to 16:9.

```python
# models.py
from django.db import models
from pictures.models import PictureField


class Profile(models.Model):
    title = models.CharField(max_length=255)
    picture = PictureField(
      upload_to="avatars",
      aspect_ratios=[None, "1/1", "3/2", "16/9"],
    )
```

```html
# template.html
{% load pictures %}
{% picture profile.picture img_alt="Spiderman" ratio="16/9" m=6 l=4 %}
```

If you don't specify an aspect ratio or None in your template, the image will be
served with the original aspect ratio of the file.

You may only use aspect ratios in templates, that have been defined on the model.
The model `aspect_ratios` will default to `[None]`, if other value is provided.

### Breakpoints

You may define your own breakpoints, they should be identical to the ones used
in your css library. Simply override the `PICTURES["BREAKPOINTS"]` setting.

### Grid columns

Grids are so common in web design, that they even made it into CSS.
We default to 12 columns, but you can override this setting, via the
`PICTURES["GRID_COLUMNS"]` setting.

### Container width

Containers are commonly used to limit the maximum width of layouts,
to promote better readability on larger screens. We default to `1200px`,
but you can override this setting, via the `PICTURES["CONTAINER_WIDTH"]` setting.

You may also set it to `None`, should you not use a container.

### File types

Unless you still services IE11 clients, you should be fine serving just
[WebP](https://caniuse.com/webp). Sadly, [AVIF](https://caniuse.com/avif)
(WebP's successor) is
[not yet supported by Pillow](https://github.com/python-pillow/Pillow/pull/5201).

If you are serving IE11 use add `JPEG` to the list. Beware though, that this may
drastically increase you storage needs.

### Pixel densities

Unless you really care that your images hold of if you hold your UHD phone very
close to your eyeballs, you should be fine, serving at the default `1x` and `2x`
densities.

### Async image processing

If you have either Dramatiq or Celery installed, we will default to async
image processing. You will need workers to listen to the `pictures` queue.
You can override the queue name, via the `PICTURES["QUEUE_NAME"]` setting.

You can also override the processor, via the `PICTURES["PROCESSOR"]` setting.
The default processor is `pictures.tasks.process_picture`. It takes a single
argument, the `PictureFileFile` instance. You can use this to override the
processor, should you need to do some custom processing.

## Migrations

Django doesn't support file field migrations, but we do.
You can simply auto create the migration and replace Django's
`AlterField` operation with `AlterPictureField`. That's it.

You can follow [the example][migration] in our test app, to see how it works.

[migration]: tests/testapp/migrations/0002_alter_profile_picture.py

## Contrib

### Django Rest Framework ([DRF])

We do ship with a read-only `PictureField` that can be used to include all
available picture sizes in a DRF serializer.

```python
from rest_framework import serializers
from pictures.contrib.rest_framework import PictureField

class PictureSerializer(serializers.Serializer):
    picture = PictureField()
```

You may provide optional GET parameters to the serializer, to specify the aspect
ratio and breakpoints you want to include in the response. The parameters are
prefixed with the `fieldname_` to avoid conflicts with other fields.

```bash
curl http://localhost:8000/api/path/?picture_ratio=16%2F9&picture_m=6&picture_l=4
# %2F is the url encoded slash
```

```json
{
  "other_fields": "…",
  "picture": {
    "url": "/path/to/image.jpg",
    "width": 800,
    "height": 800,
    "ratios": {
      "1/1": {
        "sources": {
          "image/webp": {
            "100": "/path/to/image/1/100w.webp",
            "200": "…"
          }
        },
        "media": "(min-width: 0px) and (max-width: 991px) 100vw, (min-width: 992px) and (max-width: 1199px) 33vw, 25vw"
      }
    }
  }
}
```

Note that the `media` keys are only included, if you have specified breakpoints.

### Django Cleanup

`PictureField` is compatible with [Django Cleanup](https://github.com/un1t/django-cleanup),
which automatically deletes its file and corresponding `SimplePicture` files.

[drf]: https://www.django-rest-framework.org/
[celery]: https://docs.celeryproject.org/en/stable/
[dramatiq]: https://dramatiq.io/
