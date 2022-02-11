from django.urls import path

from . import views

app_name = "pictures"

urlpatterns = [
    path(
        "<alt>/<ratio>/<int:width>w.<file_type>",
        views.placeholder,
        name="placeholder",
    ),
]
