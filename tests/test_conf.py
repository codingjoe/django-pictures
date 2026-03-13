import pytest

from pictures import conf
from pictures.conf import get_settings


def test_get_settings__returns_singleton():
    """Return the same Settings instance on every call."""
    assert get_settings() is conf.settings


def test_settings__defaults():
    """Return default values when PICTURES is not configured."""
    assert conf.settings.PIXEL_DENSITIES == [1, 2]
    assert conf.settings.FILE_TYPES == ["AVIF"]
    assert conf.settings.GRID_COLUMNS == 12


def test_settings__override(settings):
    """Reflect overridden PICTURES settings."""
    settings.PICTURES = {**settings.PICTURES, "GRID_COLUMNS": 6}
    assert get_settings().GRID_COLUMNS == 6


def test_settings__invalid_attribute():
    """Raise AttributeError for unknown setting names."""
    with pytest.raises(AttributeError, match="Invalid setting: 'DOES_NOT_EXIST'"):
        _ = conf.settings.DOES_NOT_EXIST


def test_settings__reload(settings):
    """Reload updated Django settings after explicit reload."""
    settings.PICTURES = {**settings.PICTURES, "GRID_COLUMNS": 6}
    assert get_settings().GRID_COLUMNS == 6
    settings.PICTURES = {**settings.PICTURES, "GRID_COLUMNS": 8}
    conf.settings.reload()
    assert get_settings().GRID_COLUMNS == 8


def test_settings__use_placeholders_default(settings):
    """Default USE_PLACEHOLDERS to settings.DEBUG."""
    settings.DEBUG = True
    assert get_settings().USE_PLACEHOLDERS is True
    settings.DEBUG = False
    assert get_settings().USE_PLACEHOLDERS is False
