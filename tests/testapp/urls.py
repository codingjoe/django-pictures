from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("profile/<int:pk>/", views.ProfileDetailView.as_view(), name="profile_detail"),
    path("_pictures/", include("pictures.urls")),
    path("admin/", admin.site.urls),
]
