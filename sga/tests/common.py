"""
Has parent test class for test cases
"""
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth import get_user_model

from sga.backend.authentication import get_role
from sga.backend.constants import Roles
from sga.models import Assignment, Course, Submission, Student, Grader


DEFAULT_STUDENT_USERNAME = "test_student"
DEFAULT_GRADER_USERNAME = "test_grader"
DEFAULT_ADMIN_USERNAME = "test_admin"
DEFAULT_USER_USERNAME = "test_user_id"
DEFAULT_ASSIGNMENT_EDX_ID = "test_assignment"
DEFAULT_TEST_COURSE_ID = "test_course"


class SGATestCase(TestCase):
    """
    Parent test class for test cases
    """

    ###
    # Setup
    ###
    def setUp(self):
        """
        Common test setup
        """
        super(SGATestCase, self).setUp()
        self.client = Client()
        self.user_model = get_user_model()
        self.default_course = self.get_test_course()

    ###
    # Helper functions
    ###
    def setup_session_params(self, user):
        """
        Initializes session parameters (assumes test course)
        """
        # LTI params
        lti_params = {
            "context_id": DEFAULT_TEST_COURSE_ID,
            "resource_link_id": DEFAULT_ASSIGNMENT_EDX_ID,
            "user_id": DEFAULT_USER_USERNAME,
        }
        session = self.client.session
        session["LTI_LAUNCH"] = lti_params
        # Role params
        course = self.get_test_course()
        session.course_roles = {}
        session.course_roles[str(course.id)] = get_role(user, course.id)
        session.save()

    def log_in_as(self, role):
        """
        Logs in as the role provided
        @param role: (str) role
        """
        if role == Roles.student:
            self.log_in_as_student()
        elif role == Roles.grader:
            self.log_in_as_grader()
        elif role == Roles.admin:
            self.log_in_as_admin()
        else:
            # Assume anonymous, but logged in, user
            self.log_in_as_non_role_user()

    def log_in_as_admin(self):
        """
        Logs in as an admin in the test course
        """
        admin_user = self.get_test_admin_user()
        self.client.force_login(admin_user)
        self.setup_session_params(admin_user)

    def log_in_as_grader(self):
        """
        Logs in as a grader in the test course
        """
        grader_user = self.get_test_grader_user()
        self.client.force_login(grader_user)
        self.setup_session_params(grader_user)

    def log_in_as_student(self):
        """
        Logs in as a grader in the test course
        """
        student_user = self.get_test_student_user()
        self.client.force_login(student_user)
        self.setup_session_params(student_user)

    def log_in_as_non_role_user(self):
        """
        Logs in as user with no role
        """
        user = self.get_test_user()
        self.client.force_login(user)
        self.setup_session_params(user)

    def get_test_course(self):  # pylint: disable=no-self-use
        """
        Creates or retrieves a course object for testing. Returns the Course object.
        """
        return Course.objects.get_or_create(edx_id=DEFAULT_TEST_COURSE_ID)[0]

    def get_test_assignment(self, edx_id=DEFAULT_ASSIGNMENT_EDX_ID):
        """
        Creates or retrieves an assignment object for testing. Returns the Assignment object.
        Returns the Assignment object.

        @param edx_id: (optional[str]) edx_id for Assignment to be created/retrieved
        """
        return Assignment.objects.get_or_create(
            edx_id=edx_id,
            course=self.get_test_course()
        )[0]

    def get_test_user(self):  # pylint: disable=no-self-use
        """
        Creates or retrieves test user (with no role). Returns the User object.
        """
        return self.user_model.objects.get_or_create(username=DEFAULT_USER_USERNAME)[0]

    def get_test_student(self, username=DEFAULT_STUDENT_USERNAME):
        """
        Creates or retrieves a user object for testing and attaches it to a course as a student.
        Returns the Student object.
        @param username: (optional[str]) username for User
        """
        student_user, _ = self.user_model.objects.get_or_create(username=username)
        course = self.get_test_course()
        student, _ = Student.objects.get_or_create(course=course, user=student_user)
        return student

    def get_test_student_user(self, username=DEFAULT_STUDENT_USERNAME):
        """
        Returns the User object attached to the Student from get_test_student()
        @param username: (optional[str]) username for User
        """
        student = self.get_test_student(username=username)
        return student.user

    def get_test_grader(self, username=DEFAULT_GRADER_USERNAME):
        """
        Creates or retrieves a user object for testing and attaches it to a course as a grader.
        Returns the Grader object.
        @param username: (optional[str]) username for User
        """
        grader_user, _ = self.user_model.objects.get_or_create(username=username)
        course = self.get_test_course()
        grader, _ = Grader.objects.get_or_create(course=course, user=grader_user)
        return grader

    def get_test_grader_user(self):
        """
        Returns the User object attached to the Grader from get_test_grader()
        """
        grader = self.get_test_grader()
        return grader.user

    def get_test_admin_user(self):
        """
        Creates or retrieves a user object for testing and attaches it to a course as an admin.
        Returns the User object.
        """
        admin_user, _ = self.user_model.objects.get_or_create(username=DEFAULT_ADMIN_USERNAME)
        course = self.get_test_course()
        course.administrators.add(admin_user)
        return admin_user

    def get_test_submission(self, student_username=DEFAULT_STUDENT_USERNAME):
        """
        Creates or retrieves a submission object for testing. Returns the Submission object.
        @param username: (optional[str]) username for student User attached to Submission
        """
        return Submission.objects.get_or_create(
            student=self.get_test_student_user(username=student_username),
            assignment=self.get_test_assignment()
        )[0]

    def do_test_forbidden_view(self, url_path, role):
        """
        Runs general tests for view functions to ensure the view is forbidden for the role provided

        @param url_path: (str) url path for self.client.get()
        @param role: (st) role to log in as; must be in of [Roles.student, Roles.grader, Roles.admin]
        """
        self.log_in_as(role)
        response = self.client.get(url_path, follow=True)
        self.assertEqual(response.status_code, 403)
        return response

    def do_test_successful_view(self, url_path, role, template=None, contains=None, context_keys=None):
        # pylint: disable-msg=too-many-arguments
        """
        Runs general tests for view functions to ensure 200 status code, template used, context variables

        @param url_path: (str) url path for self.client.get()
        @param role: (str) role to log in as; must be in of [Roles.student, Roles.grader, Roles.admin]
        @param template: (optional[str]) template path
        @param context_keys: (optional[list]) keys expected to be in context
        @param contains: (optional[str]) str expected to occur in html of view
        """
        self.log_in_as(role)
        response = self.client.get(url_path, follow=True)
        self.assertEqual(response.status_code, 200)
        if template:
            self.assertTemplateUsed(response, template)
        if context_keys:
            for key in context_keys:
                self.assertTrue(key in response.context, msg="{key} not in context".format(key=key))
        if contains:
            self.assertContains(response, contains)
        return response
