from django.contrib.admin.widgets import AdminFileWidget

__all__ = ["AdminPictureWidget"]


class AdminPictureWidget(AdminFileWidget):
    """Admin file input with a preview of every aspect ratio of a picture."""

    template_name = "pictures/widgets/admin_picture.html"

    class Media:
        css = {"all": ["pictures/admin.css"]}
