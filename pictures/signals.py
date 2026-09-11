"""Signals sent by django-pictures."""

import django.dispatch

# Sent by the processor after image processing completed successfully.
# Receivers get the picture field as sender, plus the file_name, new and old
# keyword arguments.
picture_processed = django.dispatch.Signal()
