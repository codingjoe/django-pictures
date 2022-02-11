import math
from fractions import Fraction

from django.http import Http404, HttpResponse

from . import conf, utils


def placeholder(request, width, ratio, file_type, alt):
    try:
        ratio = Fraction(ratio.replace("x", "/"))
    except ValueError:
        raise Http404()
    settings = conf.get_settings()
    height = math.floor(width * ratio)
    if file_type.upper() not in settings.FILE_TYPES:
        raise Http404("File type not allowed")
    img = utils.placeholder(width, height, alt=alt)
    response = HttpResponse(
        content_type=f"image/{file_type.lower()}",
        headers={"Cache-Control": f"max-age={60*60*24*365}"},
    )
    img.save(response, file_type.upper())
    return response
