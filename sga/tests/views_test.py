"""
Test end to end django views.
"""
from django.core.urlresolvers import reverse

from sga.backend.constants import Roles
from sga.tests.common import SGATestCase


class TestViews(SGATestCase):
    """
    Test that the views work as expected
    """

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
        # Create another submission to for next_not_graded_submission link in view function
        another_submission = self.get_test_submission(student_username="test_student_2_id")
        another_submission.submitted = True
        another_submission.graded = True
        another_submission.save()
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

    def test_view_assignment(self):
        """
        Verify view assignment is as expected
        """
        assignment = self.get_test_assignment()
        self.get_test_student()  # Create a student for testing view
        url = reverse("view_assignment", kwargs={"assignment_id": assignment.id})
        for role in [Roles.grader, Roles.admin]:
            self.do_test_successful_view(
                url,
                role,
                template="sga/view_assignment.html",
                context_keys=["student_users", "course", "assignment"]
            )

    def test_view_assignment_staff_only(self):
        """
        Verify view assignment page is only accessible for staff
        """
        assignment = self.get_test_assignment()
        url = reverse("view_assignment", kwargs={"assignment_id": assignment.id})
        self.do_test_forbidden_view(url, Roles.student)

    def test_view_student_list(self):
        """
        Verify view student list page is as expected
        """
        course = self.get_test_course()
        self.get_test_student()  # Create a student for testing view
        url = reverse("view_student_list", kwargs={"course_id": course.id})
        for role in [Roles.grader, Roles.admin]:
            self.do_test_successful_view(
                url,
                role,
                template="sga/view_student_list.html",
                context_keys=["course", "students", "grader_user"]
            )

    def test_view_student_list_staff_only(self):
        """
        Verify view student list page is only accessible for staff
        """
        course = self.get_test_course()
        url = reverse("view_student_list", kwargs={"course_id": course.id})
        self.do_test_forbidden_view(url, Roles.student)

    def test_view_assignment_list(self):
        """
        Verify view assignment list page is as expected
        """
        course = self.get_test_course()
        self.get_test_assignment()  # Create an assignment for testing view
        url = reverse("view_assignment_list", kwargs={"course_id": course.id})
        for role in [Roles.grader, Roles.admin]:
            self.do_test_successful_view(
                url,
                role,
                template="sga/view_assignment_list.html",
                context_keys=["course", "assignments", "grader_user"]
            )

    def test_view_assignment_list_staff_only(self):
        """
        Verify view assignment list page is only accessible for staff
        """
        course = self.get_test_course()
        url = reverse("view_assignment_list", kwargs={"course_id": course.id})
        self.do_test_forbidden_view(url, Roles.student)

    def test_view_grader_list(self):
        """
        Verify view grader list page is as expected
        """
        course = self.get_test_course()
        url = reverse("view_grader_list", kwargs={"course_id": course.id})
        self.do_test_successful_view(
            url,
            Roles.admin,
            template="sga/view_grader_list.html",
            context_keys=["course", "graders"]
        )

    def test_view_grader_list_admin_only(self):
        """
        Verify view grader list page is only accessible for admins
        """
        course = self.get_test_course()
        url = reverse("view_grader_list", kwargs={"course_id": course.id})
        for role in [Roles.grader, Roles.student]:
            self.do_test_forbidden_view(url, role)

    def test_view_student(self):
        """
        Verify view student page is as expected
        """
        student_user = self.get_test_student_user()
        course = self.get_test_course()
        self.get_test_assignment()  # Create assignment for testing view
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
        self.get_test_student()  # Create student for testing view
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

    def test_view_grader_admin_or_self_grader_only(self):
        """
        Verify view grader list page is only accessible for admins and the logged in grader if it's the
        logged in grader's own page.
        """
        # We want to try to view the grader that isn't the default grader that's logged in
        grader_2 = self.get_test_grader(username="test_grader_2_id")
        course = self.get_test_course()
        url = reverse("view_grader", kwargs={"course_id": course.id, "grader_user_id": grader_2.user.id})
        for role in [Roles.grader, Roles.student]:
            self.do_test_forbidden_view(url, role)
