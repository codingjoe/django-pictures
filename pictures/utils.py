import math
import random
import sys
from fractions import Fraction
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from . import conf

__all__ = ["sizes", "source_set", "placeholder"]


def _grid(*, _columns=12, **breakpoint_sizes):
    settings = conf.get_settings()
    for key in breakpoint_sizes.keys() - settings.BREAKPOINTS.keys():
        raise KeyError(
            f"Invalid breakpoint: {key}. Choices are: {', '.join(settings.BREAKPOINTS.keys())}"
        )
    prev_size = _columns
    for key, value in settings.BREAKPOINTS.items():
        prev_size = breakpoint_sizes.get(key, prev_size)
        yield key, prev_size / _columns


def _media_query(*, container_width: int = None, **breakpoints: {str: int}):
    settings = conf.get_settings()
    prev_ratio = None
    prev_width = 0
    for key, ratio in breakpoints.items():
        width = settings.BREAKPOINTS[key]
        if container_width and width >= container_width:
            yield f"(min-width: {prev_width}px) and (max-width: {container_width - 1}px) {math.floor(ratio * 100)}vw"
            break
        if prev_ratio and prev_ratio != ratio:
            yield f"(min-width: {prev_width}px) and (max-width: {width - 1}px) {math.floor(prev_ratio * 100)}vw"
            prev_width = width
        prev_ratio = ratio
    yield f"{math.floor(prev_ratio * container_width)}px" if container_width else f"{math.floor(prev_ratio * 100)}vw"


def sizes(*, cols=12, container_width: int = None, **breakpoints: {str: int}) -> str:
    breakpoints = dict(_grid(_columns=cols, **breakpoints))
    return ", ".join(_media_query(container_width=container_width, **breakpoints))


def source_set(
    size: (int, int), *, ratio: str | Fraction | None, max_width: int, cols: int
) -> set:
    ratio = Fraction(ratio) if ratio else None
    img_width, img_height = size
    ratio = ratio or (img_width / img_height)
    settings = conf.get_settings()
    # calc all widths at 1X resolution
    widths = (max_width * (w + 1) / cols for w in range(cols))
    # exclude widths above the max width
    widths = (w for w in widths if w <= max_width)
    # sizes for all screen resolutions
    widths = (w * res for w in widths for res in settings.PIXEL_DENSITIES)
    # exclude sizes above the original image width or height
    return {math.floor(w) for w in widths if w <= img_width and w / ratio <= img_height}


@lru_cache
def placeholder(width: int, height: int, alt):
    hue = random.randint(0, 360)  # nosec
    img = Image.new("RGB", (width, height), color=f"hsl({hue}, 40%, 80%)")
    draw = ImageDraw.Draw(img)
    draw.line(((0, 0, width, height)), width=3, fill=f"hsl({hue}, 60%, 20%)")
    draw.line(((0, height, width, 0)), width=3, fill=f"hsl({hue}, 60%, 20%)")
    draw.rectangle(
        (width / 4, height / 4, width * 3 / 4, height * 3 / 4),
        fill=f"hsl({hue}, 40%, 80%)",
    )

    fontsize = 32
    if sys.platform == "win32":
        font_name = "Arial"
    elif sys.platform in ["linux", "linux2"]:
        font_name = "DejaVuSans-Bold"
    elif sys.platform == "darwin":
        font_name = "Helvetica"
    font = ImageFont.truetype(font_name, fontsize)
    text = f"{alt}\n<{width}x{height}>"
    while font.getsize(text)[0] < width / 2:
        # iterate until the text size is just larger than the criteria
        fontsize += 1
        font = ImageFont.truetype(font_name, fontsize)

    draw.text(
        (width / 2, height / 2),
        text,
        font=font,
        fill=f"hsl({hue}, 60%, 20%)",
        align="center",
        anchor="mm",
    )
    return img
