import pytest

from pictures.templatetags.pictures import img_url, picture
from tests.testapp.models import Profile

picture_html = b"""
<picture>
  <source type="image/webp"
          srcset="/media/testapp/profile/image/800w.webp 800w, /media/testapp/profile/image/100w.webp 100w, /media/testapp/profile/image/200w.webp 200w, /media/testapp/profile/image/300w.webp 300w, /media/testapp/profile/image/400w.webp 400w, /media/testapp/profile/image/500w.webp 500w, /media/testapp/profile/image/600w.webp 600w, /media/testapp/profile/image/700w.webp 700w"
          sizes="(min-width: 0px) and (max-width: 991px) 100vw, (min-width: 992px) and (max-width: 1199px) 33vw, 600px">
  <img src="/media/testapp/profile/image.png" alt="Spiderman" width="800" height="800">
</picture>
"""

picture_with_placeholders_html = b"""
<picture>
  <source type="image/webp"
          srcset="/_pictures/Spiderman/3x2/800w.WEBP 800w, /_pictures/Spiderman/3x2/100w.WEBP 100w, /_pictures/Spiderman/3x2/200w.WEBP 200w, /_pictures/Spiderman/3x2/300w.WEBP 300w, /_pictures/Spiderman/3x2/400w.WEBP 400w, /_pictures/Spiderman/3x2/500w.WEBP 500w, /_pictures/Spiderman/3x2/600w.WEBP 600w, /_pictures/Spiderman/3x2/700w.WEBP 700w"
          sizes="(min-width: 0px) and (max-width: 991px) 100vw, (min-width: 992px) and (max-width: 1199px) 33vw, 600px">
  <img src="/media/testapp/profile/image.png" alt="Spiderman" width="800" height="800">
</picture>
"""


@pytest.mark.django_db
def test_picture(client, image_upload_file, settings):
    settings.PICTURES["USE_PLACEHOLDERS"] = False
    profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
    response = client.get(profile.get_absolute_url())
    assert response.status_code == 200
    assert picture_html in response.content


@pytest.mark.django_db
def test_picture__placeholder(client, image_upload_file, settings):
    settings.PICTURES["USE_PLACEHOLDERS"] = True
    profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
    response = client.get(profile.get_absolute_url())
    assert response.status_code == 200
    assert picture_with_placeholders_html in response.content


@pytest.mark.django_db
def test_picture__placeholder_with_alt(client, image_upload_file, settings):
    settings.PICTURES["USE_PLACEHOLDERS"] = True
    profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
    html = picture(
        profile.picture, img_alt="Event 2022/2023", ratio="3/2", img_loading="lazy"
    )
    assert "/_pictures/Event%25202022%252F2023/3x2/800w.WEBP" in html


@pytest.mark.django_db
def test_picture__invalid_ratio(image_upload_file):
    profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
    with pytest.raises(ValueError) as e:
        picture(profile.picture, ratio="4/3")
    assert "Invalid ratio: 4/3. Choices are: 1/1, 3/2, 16/9" in str(e.value)


@pytest.mark.django_db
def test_picture__additional_attrs_img(image_upload_file):
    profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
    html = picture(profile.picture, ratio="3/2", img_loading="lazy")
    assert ' loading="lazy"' in html


@pytest.mark.django_db
def test_picture__additional_attrs_img_size(image_upload_file):
    profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
    html = picture(profile.picture, ratio="3/2", img_width=500, img_height=500)
    assert ' width="500"' in html
    assert ' height="500"' in html


@pytest.mark.django_db
def test_picture__additional_attrs_picture(image_upload_file):
    profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
    html = picture(profile.picture, ratio="3/2", picture_class="picture-class")
    assert '<picture class="picture-class"' in html


@pytest.mark.django_db
def test_picture__additional_attrs__type_error(image_upload_file):
    profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
    with pytest.raises(TypeError) as e:
        picture(profile.picture, ratio="3/2", does_not_exist="error")
    assert "Invalid keyword argument: does_not_exist" in str(e.value)


@pytest.mark.django_db
def test_img_url(image_upload_file):
    profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
    assert (
        img_url(profile.picture, ratio="3/2", file_type="webp", width="800")
        == "/_pictures/image/3x2/800w.WEBP"
    )


@pytest.mark.django_db
def test_img_url__raise_wrong_ratio(image_upload_file):
    profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
    with pytest.raises(ValueError) as e:
        img_url(profile.picture, ratio="2/3", file_type="webp", width=800)
    assert "Invalid ratio: 2/3. Choices are: 1/1, 3/2, 16/9" in str(e.value)


@pytest.mark.django_db
def test_img_url__raise_wrong_file_type(image_upload_file):
    profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
    with pytest.raises(ValueError) as e:
        img_url(profile.picture, ratio="3/2", file_type="gif", width=800)
    assert "Invalid file type: gif. Choices are: WEBP" in str(e.value)
