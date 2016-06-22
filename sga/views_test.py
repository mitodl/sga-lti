"""
Test end to end django views.
"""
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from sga.models import Assignment, Course, Submission, Student, Grader


class TestViews(TestCase):
    """
    Test that the views work as expected.
    """
    def setUp(self):
        """ Common test setup """
        super(TestViews, self).setUp()
        self.client = Client()
        UserModel = get_user_model()
        user, _ = UserModel.objects.get_or_create(username="test_user_id")
        lti_params = {
            "context_id": "test_course",
            "resource_link_id": "test_assignment",
            "user_id": "test_user_id",
        }
        session = self.client.session
        session["LTI_LAUNCH"] = lti_params
        session.save()
        self.client.force_login(user)

    def log_in_as_admin(self):
        UserModel = get_user_model()
        user, _ = UserModel.objects.get_or_create(username="test_admin_id")
        course = self.get_test_course()
        course.administrators.add(user)
        self.client.force_login(user)

    def log_in_as_grader(self):
        UserModel = get_user_model()
        user, _ = UserModel.objects.get_or_create(username="test_grader_id")
        course = self.get_test_course()
        Grader.objects.get_or_create(course=course, user=user)
        self.client.force_login(user)

    def get_test_course(self):  # pylint: disable=no-self-use
        """ Creates a course object for testing """
        return Course.objects.get_or_create(edx_id="test_course")[0]

    def get_test_assignment(self):
        """ Creates an assignment object for testing """
        return Assignment.objects.get_or_create(
            edx_id="test_assignment",
            course=self.get_test_course()
        )[0]

    def get_test_student_user(self):
        """ Creates a user object for testing and attaches it to a course as
            a student """
        UserModel = get_user_model()
        student_user, _ = UserModel.objects.get_or_create(username="test_student_id")
        course = self.get_test_course()
        Student.objects.get_or_create(course=course, user=student_user)
        return student_user

    def get_test_submission(self):
        """ Creates a submission object for testing """
        return Submission.objects.get_or_create(
            student=self.get_test_student_user(),
            assignment=self.get_test_assignment()
        )[0]

    def test_index_view(self):
        """ Verify the index view is as expected """
        response = self.client.get(reverse('sga-index'))
        self.assertContains(
            response,
            "Logged In As",
            status_code=200
        )

    def test_unsubmit_submission(self):
        """ Verify that unset_submission returns 200 and updates the
            submission object """
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
        """ Verify that unset_submission is not allowed for graders """
        self.log_in_as_grader()
        assignment = self.get_test_assignment()
        student_user = self.get_test_student_user()
        submission = self.get_test_submission()
        submission.update(submitted=True, graded=True)
        kwargs = {"student_user_id": student_user.id, "assignment_id": assignment.id}
        response = self.client.post(reverse("unsubmit_submission", kwargs=kwargs), follow=True)
        self.assertEqual(response.status_code, 403)
        submission = self.get_test_submission()
        self.assertTrue(submission.graded)
        self.assertTrue(submission.submitted)


#     def test_webpack_url(self):
#         """Verify that webpack bundle src shows up in production"""
#         for debug, expected_url in [
#                 (True, "foo_server/style.js"),
#                 (False, "bundles/style.js")
#         ]:
#             with self.settings(
#                 DEBUG=debug,
#                 USE_WEBPACK_DEV_SERVER=True,
#                 WEBPACK_SERVER_URL="foo_server"
#             ):
#                 response = self.client.get(reverse('sga-index'))
#                 self.assertContains(
#                     response,
#                     expected_url,
#                     status_code=200
#                 )
