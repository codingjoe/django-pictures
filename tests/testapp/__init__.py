try:
    from .celery_app import app as celery_app
except ImportError:  # celery is not installed
    __all__ = []
else:
    __all__ = ["celery_app"]
