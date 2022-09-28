from django.apps import AppConfig


class PicturesAppConfig(AppConfig):
    name = "pictures"

    def ready(self):
        import pictures.checks  # noqa
