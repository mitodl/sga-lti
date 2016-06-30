"""
Test backend functions
"""
from io import BytesIO
from zipfile import is_zipfile

from django.core.exceptions import ValidationError
from django.test import override_settings
from mock import MagicMock, patch

from sga.backend.authentication import get_role
from sga.backend.constants import VALID_FILE_UPLOAD_EXTENSIONS, Roles
from sga.backend.files import convert_illegal_S3_chars, submissions_zip_generator
from sga.backend.send_grades import send_grade, SendGradeFailure
from sga.backend.validators import validate_file_extension
from sga.tests.common import SGATestCase


class TestBackend(SGATestCase):
    """
    Test that the backend functions work as expected
    """

    def test_validate_file_extension(self):
        """
        Verify that validators.validate_file_extension() works correctly
        """
        INVALID_FILE_UPLOAD_EXTENSIONS = [".ppt", ".txt", ".docx", ".jpg"]
        for ext in VALID_FILE_UPLOAD_EXTENSIONS:
            file = self.get_test_file("file{ext}".format(ext=ext))
            self.assertTrue(validate_file_extension, file)
        for ext in INVALID_FILE_UPLOAD_EXTENSIONS:
            file = self.get_test_file("file{ext}".format(ext=ext))
            self.assertRaises(ValidationError, validate_file_extension, file)

    def test_get_role(self):
        """
        Verify that authentication.get_role() returns the correct roles
        """
        course = self.get_test_course()
        admin_user = self.get_test_admin_user()
        student_user = self.get_test_student_user()
        grader_user = self.get_test_grader_user()
        user = self.get_test_user()
        self.assertEqual(get_role(admin_user, course.id), Roles.admin)
        self.assertEqual(get_role(student_user, course.id), Roles.student)
        self.assertEqual(get_role(grader_user, course.id), Roles.grader)
        self.assertEqual(get_role(user, course.id), Roles.none)

    def test_convert_illegal_S3_chars(self):
        """
        Verify that convert_illegal_S3_chars returns the correct conversions
        """
        CONVERSIONS = {
            "abc'defg/_(12.345)-AB*CD!": "abc'defg/_(12.345)-AB*CD!",
            "abc@#$123": "abc___123",
            "abc+<>?_": "abc_____"
        }
        for unconverted, converted in CONVERSIONS.items():
            self.assertEqual(convert_illegal_S3_chars(unconverted), converted)

    @patch(
        "oauth2.Client.request",
        MagicMock(return_value=("", "<imsx_codeMajor>success</imsx_codeMajor>"))
    )
    @override_settings(LTI_OAUTH_CREDENTIALS={"key": "secret"})
    def test_send_grade(self):  # pylint: disable=no-self-use
        """
        Tests the send_grade() function
        """
        self.assertRaises(SendGradeFailure, send_grade, "not_key", "url", "result_id", 1)
        # Call this to assert that it does NOT raise Exception
        send_grade("key", "url", "result_id", 1)

    @patch("oauth2.Client.request", MagicMock(return_value=(MagicMock(status="Bad"), "")))
    @override_settings(LTI_OAUTH_CREDENTIALS={"key": "secret"})
    def test_bad_send_grade(self):  # pylint: disable=no-self-use
        """
        Tests the failure of send_grade() function
        """
        self.assertRaises(SendGradeFailure, send_grade, "key", "url", "result_id", None)

    def test_submissions_zip_generator(self):
        """
        Tests submissions_zip_generator()
        """
        submissions = [MagicMock(student_document=self.get_test_file()) for _ in range(10)]
        # Since we're getting a stream, unpack streamed response
        zipfile = bytearray("", encoding="utf8").join(submissions_zip_generator(submissions))
        self.assertTrue(is_zipfile(BytesIO(zipfile)))
