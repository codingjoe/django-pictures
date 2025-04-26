import pytest
from django.http import Http404

from pictures.views import placeholder


def test_placeholder(rf):
    response = placeholder(rf.get("/"), 400, "4x3", "avif", "amazing_img")
    assert response.status_code == 200
    assert response["Content-Type"] == "image/avif"
    assert response["Cache-Control"] == "public, max-age=31536000"


def test_placeholder__invalid_ratio(rf):
    with pytest.raises(Http404):
        placeholder(rf.get("/"), 400, "not-a-fraction", "avif", "amazing_img")


def test_placeholder__invalid_file_type(rf):
    with pytest.raises(Http404) as e:
        placeholder(rf.get("/"), 400, "4x3", "gif", "amazing_img")
    assert "File type not allowed" in str(e.value)
