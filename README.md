# django-pictures

Responsive cross-browser image library using modern codes like AVIF &amp; WebP.

[![PyPi Version](https://img.shields.io/pypi/v/django-pictures.svg)](https://pypi.python.org/pypi/django-pictures/)
[![Test Coverage](https://codecov.io/gh/codingjoe/django-pictures/branch/master/graph/badge.svg)](https://codecov.io/gh/codingjoe/django-pictures)
[![GitHub License](https://img.shields.io/github/license/codingjoe/django-pictures)](https://raw.githubusercontent.com/codingjoe/django-pictures/master/LICENSE)

### Usage

```python
# models.py
from django.db import models
from pictures.models import PictureField

class Profile(models.Model):
    title = models.CharField(max_length=255)
    picture = PictureField(upload_to='avatars')
```

```
<!-- template.html -->
{% load pictures %}
{% picture profile.picture alt="Spiderman" m=6 l=4 %}
```

The template above will render into:
```html
<picture>
  <source type="image/webp"
          srcset="/media/testapp/profile/image/800w.webp 800w, /media/testapp/profile/image/100w.webp 100w, /media/testapp/profile/image/200w.webp 200w, /media/testapp/profile/image/300w.webp 300w, /media/testapp/profile/image/400w.webp 400w, /media/testapp/profile/image/500w.webp 500w, /media/testapp/profile/image/600w.webp 600w, /media/testapp/profile/image/700w.webp 700w"
          sizes="(min-width: 0px) and (max-width: 991px) 100vw, (min-width: 992px) and (max-width: 1199px) 33vw, 600px">
  <img src="/media/testapp/profile/image.jpg" alt="Spiderman" width="800" height="800">
</picture>
```

### Setup

```shell
python3 -m pip install django-pictures
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'django_pictures',
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
}
```

### Config

#### Breakpoints

You may define your own breakpoints, they should be identical to the ones used
in your css library. Simply override the `PICTURES["BREAKPOINTS"]` setting.

#### Grid columns

Grids are so common in web design, that they even made it into CSS.
We default to 12 columns, but you can override this setting, via the
`PICTURES["GRID_COLUMNS"]` setting.

#### Container width

Containers are commonly used to limit the maximum width of layouts,
to promote better readability on larger screens. We default to `1200px`,
but you can override this setting, via the `PICTURES["CONTAINER_WIDTH"]` setting.

You may also set it to `None`, should you not use a container.

#### File types

Unless you still services IE11 clients, you should be fine serving just
[WebP](https://caniuse.com/webp). Sadly, [AVIF](https://caniuse.com/avif)
(WebP's successor) is
[not yet supported by Pillow](https://github.com/python-pillow/Pillow/pull/5201).

#### Pixel densities

Unless you really care that your images hold of if you hold your UHD phone very
close to your eyeballs, you should be fine, serving at the default `1x` and `2x`
densities.
