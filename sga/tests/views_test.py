"""
Test end to end django views.
"""
from io import BytesIO
from zipfile import ZipFile

from django.core.urlresolvers import reverse

from sga.backend.constants import Roles
from sga.tests.common import SGATestCase


class TestViews(SGATestCase):  # pylint: disable=too-many-public-methods
    """
    Test that the views work as expected
    """

    # def test_index_view(self):
    #     """ Verify the index view is as expected """
    #     self.do_test_successful_view(
    #         reverse("sga_index"),
    #         None,
    #         template="sga/index.html"
    #     )

    def test_unsubmit_submission(self):
        """
        Verify that unset_submission returns 200 and updates the submission object
        """
        self.log_in_as_admin()
        assignment = self.get_test_assignment()
        student_user = self.get_test_student_user()
        submission = self.get_test_submission()
        submission.update(submitted=True, graded=True)
        kwargs = {
            "course_id": self.default_course.id,
            "student_user_id": student_user.id,
            "assignment_id": assignment.id
        }
        print(kwargs)
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
        kwargs = {
            "course_id": self.default_course.id,
            "student_user_id": student_user.id,
            "assignment_id": assignment.id
        }
        url = reverse("unsubmit_submission", kwargs=kwargs)
        for role in [Roles.grader, Roles.student]:
            self.do_test_forbidden_view(url, role, method="post")
            submission = self.get_test_submission()
            self.assertTrue(submission.graded)
            self.assertTrue(submission.submitted)

    def test_view_submission_as_student(self):
        """
        Verify view submission page is as expected
        """
        assignment = self.get_test_assignment()
        kwargs = {
            "course_id": self.default_course.id,
            "assignment_id": assignment.id
        }
        url = reverse("view_submission_as_student", kwargs=kwargs)
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
        kwargs = {
            "course_id": self.default_course.id,
            "assignment_id": assignment.id,
            "student_user_id": student_user.id
        }
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
                    "next_not_graded_submission_url",
                    "UNSUBMIT_CONFIRM"
                ]
            )

    def test_view_assignment(self):
        """
        Verify view assignment is as expected
        """
        assignment = self.get_test_assignment()
        self.get_test_student()  # Create a student for testing view
        kwargs = {
            "course_id": self.default_course.id,
            "assignment_id": assignment.id
        }
        url = reverse("view_assignment", kwargs=kwargs)
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
        kwargs = {
            "course_id": self.default_course.id,
            "assignment_id": assignment.id
        }
        url = reverse("view_assignment", kwargs=kwargs)
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
        kwargs = {
            "course_id": course.id,
            "student_user_id": student_user.id
        }
        url = reverse("view_student", kwargs=kwargs)
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
        grader = self.get_test_grader()
        course = self.get_test_course()
        # Create student assigned to this grader for testing view
        student = self.get_test_student()
        student.grader = grader
        student.save()
        kwargs = {
            "course_id": course.id,
            "grader_user_id": grader.user.id
        }
        url = reverse("view_grader", kwargs=kwargs)
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
        kwargs = {
            "course_id": course.id,
            "grader_user_id": grader_2.user.id
        }
        url = reverse("view_grader", kwargs=kwargs)
        for role in [Roles.grader, Roles.student]:
            self.do_test_forbidden_view(url, role)

    def test_unassign_grader(self):
        """
        Verify unassignment of grader from student
        """
        self.log_in_as_admin()
        grader = self.get_test_grader()
        student = self.get_test_student()
        student.grader = grader
        student.save()
        # Verify that this grader is assigned to this student
        self.assertTrue(student in grader.students.all())
        kwargs = {"course_id": self.default_course.id, "student_user_id": student.user.id}
        response = self.client.post(reverse("unassign_grader", kwargs=kwargs), follow=True)
        self.assertEqual(response.status_code, 200)
        grader = self.get_test_grader()
        student = self.get_test_student()
        # Verify that the grader is no longer assigned to the student
        self.assertFalse(student in grader.students.all())
        # Verify student isn't assigned to another grader
        self.assertIsNone(student.grader)

    def test_unassign_grader_admin_only(self):
        """
        Verify unassign_grader view is only accessible for admins
        """
        student = self.get_test_student()
        kwargs = {"course_id": self.default_course.id, "student_user_id": student.user.id}
        url = reverse("unassign_grader", kwargs=kwargs)
        for role in [Roles.grader, Roles.student]:
            self.do_test_forbidden_view(url, role, method="post")

    def test_unassign_student(self):
        """
        Verify unassignment of student from grader
        """
        self.log_in_as_admin()
        grader = self.get_test_grader()
        student = self.get_test_student()
        student.grader = grader
        student.save()
        # Verify that this grader is assigned to this student
        self.assertTrue(student in grader.students.all())
        kwargs = {
            "course_id": self.default_course.id,
            "student_user_id": student.user.id,
            "grader_user_id": grader.user.id
        }
        response = self.client.post(reverse("unassign_student", kwargs=kwargs), follow=True)
        self.assertEqual(response.status_code, 200)
        grader = self.get_test_grader()
        student = self.get_test_student()
        # Verify that the grader is no longer assigned to the student
        self.assertFalse(student in grader.students.all())
        # Verify student isn't assigned to another grader
        self.assertIsNone(student.grader)

    def test_unassign_student_admin_only(self):
        """
        Verify unassign_student view is only accessible for admins
        """
        student = self.get_test_student()
        grader = self.get_test_grader()
        kwargs = {
            "course_id": self.default_course.id,
            "student_user_id": student.user.id,
            "grader_user_id": grader.user.id
        }
        url = reverse("unassign_student", kwargs=kwargs)
        for role in [Roles.grader, Roles.student]:
            self.do_test_forbidden_view(url, role, method="post")

    def test_change_student_to_grader(self):
        """
        Verify changing student status to grader status
        """
        self.log_in_as_admin()
        course = self.get_test_course()
        user = self.get_test_student_user()
        # Verify user is a student, not a grader, in course
        self.assertTrue(course.has_student(user))
        self.assertFalse(course.has_grader(user))
        kwargs = {"course_id": self.default_course.id, "student_user_id": user.id}
        response = self.client.post(reverse("change_student_to_grader", kwargs=kwargs), follow=True)
        self.assertEqual(response.status_code, 200)
        # Verify user is no longer a student in course
        self.assertFalse(course.has_student(user))
        self.assertTrue(course.has_grader(user))

    def test_change_student_to_grader_admin_only(self):
        """
        Verify change_student_to_grader is only accessible for admins
        """
        student_user = self.get_test_student_user()
        kwargs = {
            "course_id": self.default_course.id,
            "student_user_id": student_user.id
        }
        url = reverse("change_student_to_grader", kwargs=kwargs)
        for role in [Roles.grader, Roles.student]:
            self.do_test_forbidden_view(url, role, method="post")

    def test_change_grader_to_student(self):
        """
        Verify changing grader status to student status
        """
        self.log_in_as_admin()
        course = self.get_test_course()
        user = self.get_test_grader_user()
        # Verify user is a grader, not a student, in course
        self.assertFalse(course.has_student(user))
        self.assertTrue(course.has_grader(user))
        kwargs = {
            "course_id": self.default_course.id,
            "grader_user_id": user.id
        }
        response = self.client.post(reverse("change_grader_to_student", kwargs=kwargs), follow=True)
        self.assertEqual(response.status_code, 200)
        # Verify user is no longer a grader in course
        self.assertTrue(course.has_student(user))
        self.assertFalse(course.has_grader(user))

    def test_change_grader_to_student_admin_only(self):
        """
        Verify change_grader_to_student is only accessible for admins
        """
        grader_user = self.get_test_grader_user()
        kwargs = {
            "course_id": self.default_course.id,
            "grader_user_id": grader_user.id
        }
        url = reverse("change_grader_to_student", kwargs=kwargs)
        for role in [Roles.grader, Roles.student]:
            self.do_test_forbidden_view(url, role, method="post")

    def test_download_all_submissions_view(self):
        """
        Verify download_all_submissions returns a .zip file
        """
        assignment = self.get_test_assignment()
        kwargs = {
            "course_id": self.default_course.id,
            "assignment_id": assignment.id
        }
        for log_in_func in [self.log_in_as_admin, self.log_in_as_grader]:
            log_in_func()
            response = self.client.get(reverse("download_all_submissions", kwargs=kwargs), follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get("Content-Disposition"), "attachment; filename=all_submissions.zip")
            self.assertIsNone(ZipFile(BytesIO(response.content), "r").testzip())

    def test_download_all_submissions_view_staff_only(self):
        """
        Verify download_all_submissions is not accessible for students
        """
        self.log_in_as_student()
        assignment = self.get_test_assignment()
        kwargs = {
            "course_id": self.default_course.id,
            "assignment_id": assignment.id
        }
        url = reverse("download_all_submissions", kwargs=kwargs)
        self.do_test_forbidden_view(url, Roles.student)

    def test_download_not_graded_submissions_view(self):
        """
        Verify download_not_graded_submissions returns a .zip file
        """
        assignment = self.get_test_assignment()
        kwargs = {
            "course_id": self.default_course.id,
            "assignment_id": assignment.id
        }
        for log_in_func in [self.log_in_as_admin, self.log_in_as_grader]:
            log_in_func()
            response = self.client.get(reverse("download_not_graded_submissions", kwargs=kwargs), follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get("Content-Disposition"), "attachment; filename=not_graded_submissions.zip")
            self.assertIsNone(ZipFile(BytesIO(response.content), "r").testzip())

    def test_download_not_graded_submissions_view_staff_only(self):
        """
        Verify download_not_graded_submissionss is not accessible for students
        """
        self.log_in_as_student()
        assignment = self.get_test_assignment()
        kwargs = {
            "course_id": self.default_course.id,
            "assignment_id": assignment.id
        }
        url = reverse("download_all_submissions", kwargs=kwargs)
        self.do_test_forbidden_view(url, Roles.student)
