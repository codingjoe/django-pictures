from django.views import generic

from . import models


class ProfileDetailView(generic.DetailView):
    model = models.Profile
