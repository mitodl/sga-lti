"""
Backend logic for file uploads and downloads
"""

import os
import re
from io import BytesIO
from zipfile import ZipFile

from django.http import HttpResponse

from sga.backend.constants import INVALID_S3_CHARACTERS_REGEX


def convert_illegal_S3_chars(path, replace_with="_"):
    """
    Converts illegal S3 characters to replace_with
    """
    return re.sub(INVALID_S3_CHARACTERS_REGEX, replace_with, path)


def serve_zip_file(filepaths, zipname="zipfile"):
    """
    Takes a list of filepaths and serves a zipfile of those files
    """
    # Create zip file in memory StringIO()
    s = BytesIO()
    with ZipFile(s, "w") as z:
        for filepath in filepaths:
            _, filename = os.path.split(filepath)
            z.write(filepath, arcname=os.path.join(zipname, filename))
    # Serve zip file in response
    resp = HttpResponse(s.getvalue(), content_type="application/zip")
    resp["Content-Disposition"] = "attachment; filename={zipname}.zip".format(zipname=zipname)
    return resp


def student_submission_file_path(instance, filename):
    """
    Returns the upload destination path (including filename) for a student submission
    """
    path = "{course_id}/student-uploads/{username}-{assignment_name}{extension}".format(
        course_id=instance.assignment.course.edx_id,
        username=instance.student.username,
        assignment_name=instance.assignment.name,
        extension=os.path.splitext(filename)[1]
    )
    return convert_illegal_S3_chars(path)


def grader_submission_file_path(instance, filename):
    """
    Returns the upload destination path (including filename) for a grader submission
    """
    path = "{course_id}/grader-uploads/{username}-{assignment_name}{extension}".format(
        course_id=instance.assignment.course.edx_id,
        username=instance.student.username,
        assignment_name=instance.assignment.name,
        extension=os.path.splitext(filename)[1]
    )
    return convert_illegal_S3_chars(path)
