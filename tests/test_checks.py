from unittest.mock import Mock

from django.urls import NoReverseMatch

from pictures import checks


def test_placeholder_url_check(settings, monkeypatch):
    """Test that the placeholder URL check works."""

    settings.PICTURES["USE_PLACEHOLDERS"] = True
    assert not checks.placeholder_url_check({})

    reverse = Mock(side_effect=NoReverseMatch)
    monkeypatch.setattr(checks, "reverse", reverse)

    assert checks.placeholder_url_check({})

    settings.PICTURES["USE_PLACEHOLDERS"] = False
    assert not checks.placeholder_url_check({})
