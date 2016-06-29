"""
Definitions for custom storages (uploaded files, etc.)
"""

from django.conf import settings
from storages.backends.s3boto import S3BotoStorage


class MediaStorage(S3BotoStorage):
    """
    Class for defining settings used for S3 uploads
    """
    location = settings.MEDIAFILES_LOCATION
