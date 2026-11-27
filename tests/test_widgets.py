import pytest

from pictures.widgets import AdminPictureWidget
from tests.testapp.models import Profile


class TestAdminPictureWidget:
    @pytest.mark.django_db
    def test_render(self, image_upload_file, settings):
        """Render a preview for every aspect ratio of the picture."""
        settings.PICTURES = settings.PICTURES | {"USE_PLACEHOLDERS": False}
        profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
        html = AdminPictureWidget().render("picture", profile.picture)
        assert html.count("<figure>") == 4
        assert "<figcaption>800×800</figcaption>" in html
        assert "<figcaption>1/1</figcaption>" in html
        assert "<figcaption>16/9</figcaption>" in html
        assert "/media/testapp/profile/image/16_9/800w.avif 800w" in html
        assert "/media/testapp/profile/image/800w.avif 800w" in html

    def test_render__empty(self):
        """Render the file input without previews."""
        html = AdminPictureWidget().render("picture", None)
        assert 'type="file"' in html
        assert "picture-previews" not in html

    def test_media(self):
        """Include the preview stylesheet."""
        assert "pictures/admin.css" in str(AdminPictureWidget().media)

    @pytest.mark.django_db
    def test_admin_change_view(self, admin_client, image_upload_file):
        """Use the widget in the admin change form."""
        profile = Profile.objects.create(name="Spiderman", picture=image_upload_file)
        response = admin_client.get(f"/admin/testapp/profile/{profile.pk}/change/")
        assert response.status_code == 200
        assert b"picture-previews" in response.content
