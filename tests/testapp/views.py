from django.views import generic

from . import models


class TestView(generic.TemplateView):
    template_name = "testapp/test.html"


class ProfileDetailView(generic.DetailView):
    model = models.Profile
