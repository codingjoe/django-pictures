import pytest

from pictures.templatetags.pictures import img_url, picture
from tests.testapp.models import Profile

picture_html = b"""
<picture>
  <source type="image/avif"
          srcset="/media/testapp/profile/image/800w.avif 800w, /media/testapp/profile/image/100w.avif 100w, /media/testapp/profile/image/200w.avif 200w, /media/testapp/profile/image/300w.avif 300w, /media/testapp/profile/image/400w.avif 400w, /media/testapp/profile/image/500w.avif 500w, /media/testapp/profile/image/600w.avif 600w, /media/testapp/profile/image/700w.avif 700w"
          sizes="(min-width: 0px) and (max-width: 991px) 100vw, (min-width: 992px) and (max-width: 1199px) 33vw, 600px">
  <img src="/media/testapp/profile/image.png" alt="Spiderman" width="800" height="800">
</picture>
"""

picture_html_large = b"""
<picture>
  <source type="image/avif"
          srcset="/media/testapp/profile/image/800w.avif 800w, /media/testapp/profile/image/100w.avif 100w, /media/testapp/profile/image/900w.avif 900w, /media/testapp/profile/image/200w.avif 200w, /media/testapp/profile/image/1000w.avif 1000w, /media/testapp/profile/image/300w.avif 300w, /media/testapp/profile/image/400w.avif 400w, /media/testapp/profile/image/500w.avif 500w, /media/testapp/profile/image/600w.avif 600w, /media/testapp/profile/image/700w.avif 700w"
          sizes="(min-width: 0px) and (max-width: 991px) 100vw, (min-width: 992px) and (max-width: 1199px) 33vw, 600px">
  <img src="/media/testapp/profile/image.png" alt="Spiderman" width="1000" height="1000">
</picture>
"""

picture_with_placeholders_html = b"""
<picture>
  <source type="image/avif"
          srcset="/_pictures/Spiderman/3x2/800w.AVIF 800w, /_pictures/Spiderman/3x2/100w.AVIF 100w, /_pictures/Spiderman/3x2/200w.AVIF 200w, /_pictures/Spiderman/3x2/300w.AVIF 300w, /_pictures/Spiderman/3x2/400w.AVIF 400w, /_pictures/Spiderman/3x2/500w.AVIF 500w, /_pictures/Spiderman/3x2/600w.AVIF 600w, /_pictures/Spiderman/3x2/700w.AVIF 700w"
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
def test_picture__large(client, large_image_upload_file, settings):
    settings.PICTURES["USE_PLACEHOLDERS"] = False
    # ensure that USE_THOUSAND_SEPARATOR doesn't break srcset with widths greater than 1000px
    settings.USE_THOUSAND_SEPARATOR = True
    profile = Profile.objects.create(name="Spiderman", picture=large_image_upload_file)
    response = client.get(profile.get_absolute_url())
    assert response.status_code == 200
    print(response.content.decode())
    assert picture_html_large in response.content


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
    assert "/_pictures/Event%25202022%252F2023/3x2/800w.AVIF" in html


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
def test_picture__field_defaults(image_upload_file):
    profile = Profile.objects.create(name="Spiderman", other_picture=image_upload_file)
    html = picture(profile.other_picture, ratio="3/2", small=2, medium=3)
    assert (
        'sizes="(min-width: 0px) and (max-width: 399px) 16vw, (min-width: 400px) and (max-width: 599px) 25vw, 150px"'
        in html
    )


@pytest.mark.django_db
def test_img_url(image_upload_file):
    profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
    assert (
        img_url(profile.picture, ratio="3/2", file_type="avif", width="800")
        == "/_pictures/image/3x2/800w.AVIF"
    )


@pytest.mark.django_db
def test_img_url__raise_wrong_ratio(image_upload_file):
    profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
    with pytest.raises(ValueError) as e:
        img_url(profile.picture, ratio="2/3", file_type="avif", width=800)
    assert "Invalid ratio: 2/3. Choices are: 1/1, 3/2, 16/9" in str(e.value)


@pytest.mark.django_db
def test_img_url__raise_wrong_file_type(image_upload_file):
    profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
    with pytest.raises(ValueError) as e:
        img_url(profile.picture, ratio="3/2", file_type="gif", width=800)
    assert "Invalid file type: gif. Choices are: AVIF" in str(e.value)


@pytest.mark.django_db
def test_img_url__too_small(tiny_image_upload_file, caplog):
    profile = Profile.objects.create(name="Spiderman", picture=tiny_image_upload_file)
    with pytest.warns() as record:
        assert (
            img_url(profile.picture, ratio="3/2", file_type="avif", width="800")
            == "/media/testapp/profile/image.png"
        )
    assert len(record) == 1
    assert (
        "Image is smaller than requested size, using source file URL."
        in record[0].message.args[0]
    )
