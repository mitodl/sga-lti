"""
Django form validators
"""

import os

from django.core.exceptions import ValidationError

from sga.backend.constants import VALID_FILE_UPLOAD_EXTENSIONS


def validate_file_extension(field_file):
    """
    Validate file extension (valid file extensions are defined in VALID_FILE_UPLOAD_EXTENSIONS)
    """
    ext = os.path.splitext(field_file.name)[1]  # .splitext returns (root, ext)
    if ext.lower() not in VALID_FILE_UPLOAD_EXTENSIONS:
        message = ("Only the following file types are supported: " +
                   "{extensions}".format(extensions=",".join(VALID_FILE_UPLOAD_EXTENSIONS)))
        raise ValidationError(message)
