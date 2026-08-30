"""Signals sent by django-pictures."""

import django.dispatch

# Sent after image processing completed successfully.
picture_processed = django.dispatch.Signal()
