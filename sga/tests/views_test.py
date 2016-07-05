"""
Test end to end django views.
"""
from django.core.urlresolvers import reverse
from mock import patch, MagicMock

from sga.backend.constants import Roles
from sga.forms import (
    AssignGraderToStudentForm,
    GraderMaxStudentsForm,
    GraderAssignmentSubmissionForm,
    StudentAssignmentSubmissionForm,
    AssignStudentToGraderForm)
from sga.tests.common import SGATestCase


class TestViews(SGATestCase):
    """
    Test that the views work as expected
    """
    # pylint: disable=too-many-public-methods

    def test_index_view(self):
        """
        Verify the index view is as expected
        """
        self.do_test_successful_view(
            reverse("sga_index"),
            Roles.none,
            template="sga/index.html"
        )

    def test_not_graded_block_error_page_view(self):
        """
        Verify the not_graded_block_error_page view is as expected
        """
        self.do_test_successful_view(
            reverse("not_graded_block_error_page"),
            Roles.none,
            template="sga/not_graded_block_error_page.html"
        )

    def test_studio_message_page_view(self):
        """
        Verify the studio_message_page view is as expected
        """
        self.do_test_successful_view(
            reverse("studio_message_page"),
            Roles.none,
            template="sga/studio_message_page.html"
        )

    def test_staff_index_view(self):
        """
        Verify the staff_index view is as expected
        """
        course = self.get_test_course()
        for role in [Roles.admin, Roles.grader]:
            self.do_test_successful_view(
                reverse("staff_index", kwargs={"course_id": course.id}),
                role,
                template="sga/staff_index.html"
            )

    def test_staff_index_view_staff_only(self):
        """
        Verify the staff_index view is not allowed for students
        """
        course = self.get_test_course()
        self.do_test_forbidden_view(
            reverse("staff_index", kwargs={"course_id": course.id}),
            Roles.student
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
        kwargs = {
            "course_id": self.default_course.id,
            "student_user_id": student_user.id,
            "assignment_id": assignment.id
        }
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
        Verify view submission page (as student) is as expected
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

    def test_view_submission_as_student_student_only(self):
        """
        Verify view submission page (as student) is only accessible to the student
        """
        assignment = self.get_test_assignment()
        kwargs = {
            "course_id": self.default_course.id,
            "assignment_id": assignment.id
        }
        url = reverse("view_submission_as_student", kwargs=kwargs)
        for role in [Roles.admin, Roles.grader]:
            self.do_test_forbidden_view(
                url,
                role
            )

    def test_submit_student_assignment(self):
        """
        Verify successful student submission via view_submission_as_student
        """
        self.log_in_as_student()
        submission = self.get_test_submission()
        self.assertIsNone(submission.student_document.name)
        self.assertIsNone(submission.description)
        self.assertFalse(submission.submitted)
        test_file = self.get_test_file()
        form_data = {
            "description": "file description"
        }
        form_files = {
            "student_document": test_file
        }
        form = StudentAssignmentSubmissionForm(data=form_data, files=form_files, instance=submission)
        self.assertTrue(form.is_valid())
        kwargs = {
            "course_id": submission.assignment.course_id,
            "assignment_id": submission.assignment_id
        }
        form_data.update(form_files)
        response = self.client.post(reverse("view_submission_as_student", kwargs=kwargs), data=form_data)
        submission = self.get_test_submission()
        # Submission should now be submitted
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(submission.student_document.name)
        self.assertIsNotNone(submission.description)
        self.assertTrue(submission.submitted)

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

    @patch("sga.views.send_grade", MagicMock(return_value=None))
    def test_submit_grader_document(self):
        """
        Verify successful grader submission via view_submission_as_staff
        """
        self.log_in_as_grader()
        submission = self.get_test_submission()
        student_user = self.get_test_student_user()
        self.assertIsNone(submission.grader_document.name)
        self.assertIsNone(submission.feedback)
        self.assertFalse(submission.graded)
        test_file = self.get_test_file()
        form_data = {
            "feedback": "file feedback",
            "grade": 75
        }
        form_files = {
            "grader_document": test_file
        }
        form = GraderAssignmentSubmissionForm(data=form_data, files=form_files, instance=submission)
        self.assertTrue(form.is_valid())
        kwargs = {
            "course_id": submission.assignment.course_id,
            "assignment_id": submission.assignment_id,
            "student_user_id": student_user.id
        }
        form_data.update(form_files)
        response = self.client.post(reverse("view_submission_as_staff", kwargs=kwargs), data=form_data)
        submission = self.get_test_submission()
        # Submission should now be submitted
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(submission.grader_document.name)
        self.assertIsNotNone(submission.feedback)
        self.assertTrue(submission.graded)

    def test_view_submission_as_staff_staff_only(self):
        """
        Verify view submission page (as staff) is only accessible to staff
        """
        assignment = self.get_test_assignment()
        student_user = self.get_test_student_user()
        kwargs = {
            "course_id": self.default_course.id,
            "assignment_id": assignment.id,
            "student_user_id": student_user.id
        }
        url = reverse("view_submission_as_staff", kwargs=kwargs)
        self.do_test_forbidden_view(
            url,
            Roles.student
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

    def test_assign_grader(self):
        """
        Verify that AssignGraderToStudentForm correctly assigns a grader to a student
        (POST to view_student)
        """
        self.log_in_as_admin()
        grader = self.get_test_grader()
        student = self.get_test_student()
        course = self.get_test_course()
        # Grader should have available slots
        self.assertGreater(grader.available_student_slots_count(), 0)
        # Grader should not be assigned to student
        self.assertNotEqual(student.grader, grader)
        form_data = {"grader": grader.id}
        form = AssignGraderToStudentForm(data=form_data, instance=student)
        self.assertTrue(form.is_valid())
        kwargs = {
            "course_id": course.id,
            "student_user_id": student.user_id
        }
        response = self.client.post(reverse("view_student", kwargs=kwargs), data=form_data)
        student = self.get_test_student()
        # Grader should now be assigned
        self.assertEqual(response.status_code, 200)
        self.assertEqual(student.grader, grader)

    def test_assign_grader_admin_only(self):
        """
        Verify assigning grader via view_student is only allowed for admins
        """
        grader = self.get_test_grader()
        student = self.get_test_student()
        course = self.get_test_course()
        # Grader should have available slots
        self.assertGreater(grader.available_student_slots_count(), 0)
        # Grader should not be assigned to student
        self.assertNotEqual(student.grader, grader)
        form_data = {"grader": grader.id}
        form = AssignGraderToStudentForm(data=form_data, instance=student)
        self.assertTrue(form.is_valid())
        url = reverse("view_student", kwargs={"course_id": course.id, "student_user_id": student.user_id})
        # Roles.grader and Roles.student is allowed on the page, but shouldn't be able to assign graders
        for log_in_func in [self.log_in_as_grader, self.log_in_as_student]:
            log_in_func()
            response = self.client.post(url, data=form_data)
            student = self.get_test_student()
            # Grader should still not be assigned
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(student.grader, grader)

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
            "grader_user_id": grader.user_id
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
            "grader_user_id": grader_2.user_id
        }
        url = reverse("view_grader", kwargs=kwargs)
        for role in [Roles.grader, Roles.student]:
            self.do_test_forbidden_view(url, role)

    def test_change_grader_max_students(self):
        """
        Verify that GraderMaxStudentsForm correctly changes a graders max number of students
        (POST to view_grader)
        """
        NEW_MAX_STUDENTS = 123
        self.log_in_as_admin()
        grader = self.get_test_grader()
        course = self.get_test_course()
        current_max_students = grader.max_students
        # Current max_students should be different than our new number
        self.assertNotEqual(current_max_students, NEW_MAX_STUDENTS)
        form_data = {"max_students": NEW_MAX_STUDENTS}
        form = GraderMaxStudentsForm(data=form_data, instance=grader)
        self.assertTrue(form.is_valid())
        kwargs = {
            "course_id": course.id,
            "grader_user_id": grader.user_id
        }
        form_data.update({"max_students_submit": True})
        response = self.client.post(reverse("view_grader", kwargs=kwargs), data=form_data)
        # Grader should now have NEW_MAX_STUDENTS number of max_students
        grader = self.get_test_grader()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(grader.max_students, NEW_MAX_STUDENTS)

    def test_change_grader_max_students_admin_only(self):
        """
        Verify changing grader max_students via view_student is only allowed for admins
        """
        NEW_MAX_STUDENTS = 123
        self.log_in_as_grader()
        grader = self.get_test_grader()
        course = self.get_test_course()
        current_max_students = grader.max_students
        # Current max_students should be different than our new number
        self.assertNotEqual(current_max_students, NEW_MAX_STUDENTS)
        form_data = {"max_students": NEW_MAX_STUDENTS}
        form = GraderMaxStudentsForm(data=form_data, instance=grader)
        self.assertTrue(form.is_valid())
        kwargs = {
            "course_id": course.id,
            "grader_user_id": grader.user_id
        }
        form_data.update({"max_students_submit": True})
        response = self.client.post(reverse("view_grader", kwargs=kwargs), data=form_data)
        # Grader should not have changed to NEW_MAX_STUDENTS number of max_students
        grader = self.get_test_grader()
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(grader.max_students, NEW_MAX_STUDENTS)
        self.assertEqual(grader.max_students, current_max_students)

    def test_assign_student(self):
        """
        Verify that AssignStudentToGraderForm correctly assigns a student to a grader
        (POST to view_grader)
        """
        student = self.get_test_student()
        grader = self.get_test_grader()
        course = self.get_test_course()
        # Grader should have available slots
        self.assertGreater(grader.available_student_slots_count(), 0)
        # Grader should not be assigned to student
        self.assertNotEqual(student.grader, grader)
        # First have to initialize form to retrieve the choices the form provides. There's an issue
        # with Travis builds where self.get_test_student() apparently returns a different object
        # than the form's queryset, even though the only object that should exist in the test
        # database is the object from self.get_test_student()
        form = AssignStudentToGraderForm(instance=grader)
        # We only want one student_user_id, but we have to iterate because form.fields["students"].choices
        # is a ModelChoiceIterator, so we must iterate
        for choice in form.fields["students"].choices:
            student_user_id = choice[0]  # (user_id, label)
            if student_user_id:
                break
        # Now we set form_data using the student_user_id we got from above. If there were no choices and
        # we get a referenced before assignment error, it's probably not a test logic issue and it should
        # rightfully break
        print(student_user_id)
        for choice in form.fields["students"].choices:
            print(choice)
        form_data = {"students": student_user_id}
        form = AssignStudentToGraderForm(data=form_data, instance=grader)
        self.assertTrue(form.is_valid())
        kwargs = {
            "course_id": course.id,
            "grader_user_id": grader.user_id
        }
        form_data.update({"assign_student_submit": True})
        self.log_in_as_admin()
        response = self.client.post(reverse("view_grader", kwargs=kwargs), data=form_data)
        # Grader should now be assigned
        self.assertEqual(response.status_code, 200)
        student = self.get_test_student()
        self.assertEqual(student.grader, grader)

    def test_assign_student_admin_only(self):
        """
        Verify that AssignStudentToGraderForm correctly assigns a student to a grader
        (POST to view_grader)
        """
        student = self.get_test_student()
        grader = self.get_test_grader()
        course = self.get_test_course()
        # Grader should have available slots
        self.assertGreater(grader.available_student_slots_count(), 0)
        # Grader should not be assigned to student
        self.assertNotEqual(student.grader, grader)
        # See comment from test_assign_student() about why the next 4 lines are necessary with Travis
        form = AssignStudentToGraderForm(instance=grader)
        for choice in form.fields["students"].choices:
            student_user_id = choice[0]  # (user_id, label)
            if student_user_id:
                break
        form_data = {"students": student_user_id}
        form = AssignStudentToGraderForm(data=form_data, instance=grader)
        self.assertTrue(form.is_valid())
        kwargs = {
            "course_id": course.id,
            "grader_user_id": grader.user_id
        }
        form_data.update({"assign_student_submit": True})
        url = reverse("view_grader", kwargs=kwargs)
        # As grader
        self.log_in_as_grader()
        response = self.client.post(url, data=form_data)
        # Grader should still not be assigned
        self.assertEqual(response.status_code, 200)
        student = self.get_test_student()
        self.assertNotEqual(student.grader, grader)

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
        kwargs = {"course_id": self.default_course.id, "student_user_id": student.user_id}
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
        kwargs = {"course_id": self.default_course.id, "student_user_id": student.user_id}
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
            "student_user_id": student.user_id,
            "grader_user_id": grader.user_id
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
            "student_user_id": student.user_id,
            "grader_user_id": grader.user_id
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

    def test_download_all_submissions(self):
        """
        Verify download_all_submissions returns a .zip file
        """
        # Get zip file
        assignment = self.get_test_assignment()
        kwargs = {
            "course_id": self.default_course.id,
            "assignment_id": assignment.id
        }
        for log_in_func in [self.log_in_as_admin, self.log_in_as_grader]:
            log_in_func()
            response = self.client.get(reverse("download_all_submissions", kwargs=kwargs), follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.get("Content-Disposition").startswith("attachment; filename="))

    def test_download_all_submissions_staff_only(self):
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

    def test_download_not_graded_submissions(self):
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
            self.assertTrue(response.get("Content-Disposition").startswith("attachment; filename="))

    def test_download_not_graded_submissions_staff_only(self):
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
