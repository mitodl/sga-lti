"""
Test end to end django views.
"""
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model

from sga.backend.constants import Roles
from sga.models import Assignment, Course, Submission, Student, Grader


class TestViews(TestCase):  # pylint: disable=too-many-public-methods
    """
    Test that the views work as expected.
    """

    ###
    # Setup
    ###
    def setUp(self):
        """
        Common test setup
        """
        super(TestViews, self).setUp()
        self.client = Client()
        self.user_model = get_user_model()

    ###
    # Helper functions
    ###
    def setup_lti_params(self):
        """
        Initializes LTI parameters in session
        """
        lti_params = {
            "context_id": "test_course",
            "resource_link_id": "test_assignment",
            "user_id": "test_user_id",
        }
        session = self.client.session
        session["LTI_LAUNCH"] = lti_params
        session.save()

    def log_in_as(self, role):
        """
        Logs in as the role provided
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
        user, _ = self.user_model.objects.get_or_create(username="test_admin_id")
        course = self.get_test_course()
        course.administrators.add(user)
        self.client.force_login(user)
        self.setup_lti_params()

    def log_in_as_grader(self):
        """
        Logs in as a grader in the test course
        """
        grader = self.get_test_grader()
        self.client.force_login(grader.user)
        self.setup_lti_params()

    def log_in_as_student(self):
        """
        Logs in as a grader in the test course
        """
        student_user = self.get_test_student_user()
        self.client.force_login(student_user)
        self.setup_lti_params()

    def log_in_as_non_role_user(self):
        """
        Logs in as user with no role
        """
        user = self.get_test_user()
        self.client.force_login(user)
        self.setup_lti_params()

    def get_test_course(self):  # pylint: disable=no-self-use
        """
        Creates or retrieves a course object for testing. Returns the Course object.
        """
        return Course.objects.get_or_create(edx_id="test_course")[0]

    def get_test_assignment(self):
        """
        Creates or retrieves an assignment object for testing. Returns the Assignment object.
        Returns the Assignment object.
        """
        return Assignment.objects.get_or_create(
            edx_id="test_assignment",
            course=self.get_test_course()
        )[0]

    def get_test_user(self):  # pylint: disable=no-self-use
        """
        Creates or retrieves test user (with no role). Returns the User object.
        """
        return self.user_model.objects.get_or_create(username="test_user_id")[0]

    def get_test_student(self):
        """
        Creates or retrieves a user object for testing and attaches it to a course as a student.
        Returns the Student object.
        """
        student_user, _ = self.user_model.objects.get_or_create(username="test_student_id")
        course = self.get_test_course()
        student, _ = Student.objects.get_or_create(course=course, user=student_user)
        return student

    def get_test_student_user(self):
        """
        Returns the User object attached to the Student from get_test_student()
        """
        student = self.get_test_student()
        return student.user

    def get_test_grader(self):
        """
        Creates or retrieves a user object for testing and attaches it to a course as a grader.
        Returns the Grader object
        """
        grader_user, _ = self.user_model.objects.get_or_create(username="test_grader_id")
        course = self.get_test_course()
        grader, _ = Grader.objects.get_or_create(course=course, user=grader_user)
        return grader

    def get_test_grader_user(self):
        """
        Returns the User object attached to the Grader from get_test_grader()
        """
        grader = self.get_test_grader()
        return grader.user

    def get_test_submission(self):
        """
        Creates or retrieves a submission object for testing. Returns the Submission object.
        """
        return Submission.objects.get_or_create(
            student=self.get_test_student_user(),
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
        @param template: (str) template path
        @param context_keys: (list) keys expected to be in context
        @param contains: (str) str expected to occur in html of view
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

    ###
    # Tests
    ###
    def test_index_view(self):
        """ Verify the index view is as expected """
        self.do_test_successful_view(
            reverse('sga-index'),
            None,
            template="sga/index.html",
            contains="Logged In As",
            context_keys=[
                "course",
                "assignments",
                "users",
                "students",
                "graders",
                "admins"
            ]
        )

    def test_unsubmit_submission(self):
        """
        Verify that unset_submission returns 200 and updates the submission object
        """
        self.log_in_as_admin()
        assignment = self.get_test_assignment()
        student_user = self.get_test_student_user()
        submission = self.get_test_submission()
        submission.update(submitted=True, graded=True)
        kwargs = {"student_user_id": student_user.id, "assignment_id": assignment.id}
        response = self.client.post(reverse("unsubmit_submission", kwargs=kwargs), follow=True)
        self.assertEqual(response.status_code, 200)
        submission = self.get_test_submission()
        self.assertFalse(submission.graded)
        self.assertFalse(submission.submitted)

    def test_unsubmit_submission_admin_only(self):
        """
        Verify that unset_submission is not allowed for graders or students
        """
        assignment = self.get_test_assignment()
        student_user = self.get_test_student_user()
        submission = self.get_test_submission()
        submission.update(submitted=True, graded=True)
        kwargs = {"student_user_id": student_user.id, "assignment_id": assignment.id}
        url = reverse("unsubmit_submission", kwargs=kwargs)
        for role in [Roles.grader, Roles.student]:
            self.do_test_forbidden_view(url, role)
            submission = self.get_test_submission()
            self.assertTrue(submission.graded)
            self.assertTrue(submission.submitted)

    def test_view_submission_as_student(self):
        """
        Verify view submission page is as expected
        """
        assignment = self.get_test_assignment()
        url = reverse("view_submission_as_student", kwargs={"assignment_id": assignment.id})
        self.do_test_successful_view(
            url,
            Roles.student,
            template="sga/view_submission_as_student.html",
            context_keys=["submission_form", "submission", "assignment"]
        )

    def test_view_submission_as_staff(self):
        """
        Verify view submission page is as expected
        """
        student_user = self.get_test_student_user()
        assignment = self.get_test_assignment()
        kwargs = {"assignment_id": assignment.id, "student_user_id": student_user.id}
        url = reverse("view_submission_as_staff", kwargs=kwargs)
        for role in [Roles.grader, Roles.admin]:
            self.do_test_successful_view(
                url,
                role,
                template="sga/view_submission_as_staff.html",
                context_keys=[
                    "submission_form",
                    "submission",
                    "assignment",
                    "student_user",
                    "next_not_graded_submission_url"
                ]
            )

    def test_view_student_list(self):
        """
        Verify view student list page is as expected
        """
        course = self.get_test_course()
        url = reverse("view_student_list", kwargs={"course_id": course.id})
        for role in [Roles.grader, Roles.admin]:
            self.do_test_successful_view(
                url,
                role,
                template="sga/view_student_list.html",
                context_keys=["course", "students", "grader_user"]
            )

    def test_view_assignment_list(self):
        """
        Verify view assignment list page is as expected
        """
        course = self.get_test_course()
        url = reverse("view_assignment_list", kwargs={"course_id": course.id})
        for role in [Roles.grader, Roles.admin]:
            self.do_test_successful_view(
                url,
                role,
                template="sga/view_assignment_list.html",
                context_keys=["course", "assignments", "grader_user"]
            )

    def test_view_student(self):
        """
        Verify view student page is as expected
        """
        student_user = self.get_test_student_user()
        course = self.get_test_course()
        url = reverse("view_student", kwargs={"course_id": course.id, "student_user_id": student_user.id})
        self.do_test_successful_view(
            url,
            Roles.student,
            template="sga/view_student.html",
            context_keys=[
                "course",
                "student",
                "assignments",
                "STUDENT_TO_GRADER_CONFIRM",
                "UNASSIGN_GRADER_CONFIRM",
                "assign_grader_form"
            ]
        )

    def test_view_grader(self):
        """
        Verify view grader page is as expected
        """
        grader_user = self.get_test_grader_user()
        course = self.get_test_course()
        url = reverse("view_grader", kwargs={"course_id": course.id, "grader_user_id": grader_user.id})
        for role in [Roles.grader, Roles.admin]:
            self.do_test_successful_view(
                url,
                role,
                template="sga/view_grader.html",
                context_keys=[
                    "course",
                    "grader",
                    "graded_submissions",
                    "max_students_form",
                    "assign_student_form",
                    "students",
                    "GRADER_TO_STUDENT_CONFIRM",
                    "UNASSIGN_STUDENT_CONFIRM"
                ]
            )
