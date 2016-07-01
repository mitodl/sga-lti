"""
Django form validators
"""

import os

from django.core.exceptions import ValidationError
from django.conf import settings


def validate_file_extension(field_file):
    """
    Validate file extension (valid file extensions are defined in VALID_FILE_UPLOAD_EXTENSIONS)
    """
    ext = os.path.splitext(field_file.name)[1]  # .splitext returns (root, ext)
    if ext.lower() not in settings.VALID_FILE_UPLOAD_EXTENSIONS:
        message = ("Only the following file types are supported: "
                   "{extensions}".format(extensions=",".join(settings.VALID_FILE_UPLOAD_EXTENSIONS)))
        raise ValidationError(message)


def validate_file_size(field_file):
    """ Validates that files are less than the size limit """
    filesize = field_file.file.size
    if filesize > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValidationError("Files must be less than %sMB" % str(settings.MAX_FILE_SIZE_MB))
