"""
Test end to end django models.
"""
from time import sleep

from django.core.exceptions import PermissionDenied

from sga.models import Course, Submission, Grader
from sga.tests.common import SGATestCase


class TestModels(SGATestCase):
    """
    Test that methods on models work as expected
    """

    def test_timestampedmodel_update(self):
        """
        Tests the .update() method on TimeStampedModel
        """
        course = self.get_test_course()  # Course is a subclass of TimeStampedModel
        initial_updated_on = course.updated_on
        sleep(0.1)
        course.update()
        course = Course.objects.get(id=course.id)
        self.assertLess(initial_updated_on, course.updated_on)

    def test_grader_graded_submissions_count(self):
        """
        Tests the .graded_submissions_count() method on Grader
        """
        grader = self.get_test_grader()
        submission = self.get_test_submission()
        self.assertEqual(grader.graded_submissions_count(), 0)
        submission.update(submitted=True, graded=True, graded_by=grader.user)
        self.assertEqual(grader.graded_submissions_count(), 1)

    def test_grader_not_graded_submissions_count(self):
        """
        Tests the .not_graded_submissions_count() method on Grader
        """
        grader = self.get_test_grader()
        student = self.get_test_student()
        student.grader = grader
        student.save()
        self.assertEqual(grader.not_graded_submissions_count(), 0)
        submission = self.get_test_submission()  # Uses get_test_student() to set student
        submission.update(submitted=True)
        self.assertEqual(grader.not_graded_submissions_count(), 1)
        submission.update(graded=True, graded_by=grader.user)
        self.assertEqual(grader.not_graded_submissions_count(), 0)

    def test_course_has_student(self):
        """
        Tests the .has_student() method on Course
        """
        course = self.get_test_course()
        student_user = self.get_test_student_user()
        self.assertTrue(course.has_student(student_user))

    def test_course_has_grader(self):
        """
        Tests the .has_grader() method on Course
        """
        course = self.get_test_course()
        grader_user = self.get_test_grader_user()
        self.assertTrue(course.has_grader(grader_user))

    def test_course_has_admin(self):
        """
        Tests the .has_admin() method on Course
        """
        course = self.get_test_course()
        admin_user = self.get_test_admin_user()
        self.assertTrue(course.has_admin(admin_user))

    def test_course_not_graded_submissions_count_by_student(self):
        """
        Tests the .not_graded_submissions_count_by_student() method on Course
        """
        course = self.get_test_course()
        student = self.get_test_student()
        submission = self.get_test_submission(student_username=student.user.username)
        # No submission submitted yet, so count should be 0
        self.assertEqual(course.not_graded_submissions_count_by_student(student), 0)
        submission.update(submitted=True)
        # One submission submitted, so count should be 1
        self.assertEqual(course.not_graded_submissions_count_by_student(student), 1)
        student_2 = self.get_test_student(username="test_student_2")
        submission_b = self.get_test_submission(student_username=student_2.user.username)
        submission_b.update(submitted=True)
        # Submission was created for another student, so count should still be 1
        self.assertEqual(course.not_graded_submissions_count_by_student(student), 1)
        # And count for student_2 should also be 1
        self.assertEqual(course.not_graded_submissions_count_by_student(student_2), 1)
        assignment_2 = self.get_test_assignment(edx_id="test_assignment_2")
        submission_2, _ = Submission.objects.get_or_create(
            student=student.user,
            assignment=assignment_2
        )
        # Another submission for student was created, but not submitted, so count should still be 1
        self.assertEqual(course.not_graded_submissions_count_by_student(student), 1)
        submission_2.update(submitted=True)
        # This submission was submitted, so count should now be 2
        self.assertEqual(course.not_graded_submissions_count_by_student(student), 2)
        submission.update(graded=True)
        # First submission is graded, so count should be back at 1
        self.assertEqual(course.not_graded_submissions_count_by_student(student), 1)
        submission_2.update(graded=True)
        # Second submission is graded, so count should be back at 1
        self.assertEqual(course.not_graded_submissions_count_by_student(student), 0)

    def test_assignment_graded_submissions_count(self):
        """
        Tests the .graded_submissions_count() method on Assignment
        """
        assignment = self.get_test_assignment()
        submission = self.get_test_submission()  # Uses get_test_assignment() to set submission.assignment
        self.assertEqual(assignment.graded_submissions_count(), 0)
        submission.update(submitted=True)
        self.assertEqual(assignment.graded_submissions_count(), 0)
        submission.update(graded=True)
        self.assertEqual(assignment.graded_submissions_count(), 1)

    def test_assignment_graded_submissions_count_by_grader(self):
        """
        Tests the .graded_submissions_count_by_grader() method on Assignment
        """
        assignment = self.get_test_assignment()
        student = self.get_test_student()
        grader = self.get_test_grader()
        grader_2 = self.get_test_grader(username="test_grader_2")
        student.grader = grader
        student.save()
        submission = self.get_test_submission()  # Uses get_test_assignment() to set submission.assignment
        # Submission not yet graded, so count should be 0
        self.assertEqual(assignment.graded_submissions_count_by_grader(grader=grader), 0)
        self.assertEqual(assignment.graded_submissions_count_by_grader(grader_user=grader.user), 0)
        submission.update(submitted=True, graded=True, graded_by=grader.user)
        # Submission graded, so count should be 1
        self.assertEqual(assignment.graded_submissions_count_by_grader(grader=grader), 1)
        self.assertEqual(assignment.graded_submissions_count_by_grader(grader_user=grader.user), 1)
        # Earlier submission not graded by grader_2, so count should be 0
        self.assertEqual(assignment.graded_submissions_count_by_grader(grader=grader_2), 0)

    def test_assignment_not_graded_submissions_count(self):
        """
        Tests the .not_graded_submissions_count() method on Assignment
        """
        assignment = self.get_test_assignment()
        submission = self.get_test_submission()  # Uses get_test_assignment() to set submission.assignment
        self.assertEqual(assignment.not_graded_submissions_count(), 0)
        submission.update(submitted=True)
        self.assertEqual(assignment.not_graded_submissions_count(), 1)
        submission.update(graded=True)
        self.assertEqual(assignment.not_graded_submissions_count(), 0)

    def test_assignment_not_graded_submissions_count_by_grader(self):
        """
        Tests the .not_graded_submissions_count_by_grader() method on Assignment
        """
        assignment = self.get_test_assignment()
        grader = self.get_test_grader()
        grader_2 = self.get_test_grader(username="test_grader_2")
        # No student yet, so count should be 0
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader=grader), 0)
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader_user=grader.user), 0)
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader=grader_2), 0)
        student = self.get_test_student()
        # Student exists, but not assigned to either grader, so count should be 0
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader=grader), 0)
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader_user=grader.user), 0)
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader=grader_2), 0)
        student.grader = grader
        student.save()
        # Student assigned to grader now, but submission is not submitted, so count should still be 0
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader=grader), 0)
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader_user=grader.user), 0)
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader=grader_2), 0)
        submission = self.get_test_submission()  # Uses get_test_assignment() to set submission.assignment
        submission.update(submitted=True)
        # Submission submitted, so count should be 1 for grader, 0 for grader_2
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader=grader), 1)
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader_user=grader.user), 1)
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader=grader_2), 0)
        submission.update(graded=True, graded_by=grader.user)
        # Submission graded by grader, so count should be back to 0
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader=grader), 0)
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader_user=grader.user), 0)
        self.assertEqual(assignment.not_graded_submissions_count_by_grader(grader=grader_2), 0)

    def test_assignment_not_submitted_submissions_count(self):
        """
        Tests the .not_submitted_submissions_count() method on Assignment
        """
        assignment = self.get_test_assignment()
        # No students yet, so count should be 0
        self.assertEqual(assignment.not_submitted_submissions_count(), 0)
        self.get_test_student()
        # Now there is one student, so count should be 1
        self.assertEqual(assignment.not_submitted_submissions_count(), 1)
        self.get_test_student(username="test_student_2")
        # Now there are two students, so count should be 2
        self.assertEqual(assignment.not_submitted_submissions_count(), 2)
        submission = self.get_test_submission()  # Uses get_test_assignment() and get_test_student()
        submission.update(submitted=True)
        self.assertEqual(assignment.not_submitted_submissions_count(), 1)

    def test_assignment_not_submitted_submissions_count_by_grader(self):
        """
        Tests the .not_submitted_submissions_count_by_grader() method on Assignment
        """
        assignment = self.get_test_assignment()
        grader = self.get_test_grader()
        grader_2 = self.get_test_grader(username="test_grader_2")
        # No student yet, so count should be 0
        self.assertEqual(assignment.not_submitted_submissions_count_by_grader(grader=grader), 0)
        self.assertEqual(assignment.not_submitted_submissions_count_by_grader(grader_user=grader.user), 0)
        self.assertEqual(assignment.not_submitted_submissions_count_by_grader(grader=grader_2), 0)
        student = self.get_test_student()
        # Student exists, but not assigned to either grader, so count should be 0
        self.assertEqual(assignment.not_submitted_submissions_count_by_grader(grader=grader), 0)
        self.assertEqual(assignment.not_submitted_submissions_count_by_grader(grader_user=grader.user), 0)
        self.assertEqual(assignment.not_submitted_submissions_count_by_grader(grader=grader_2), 0)
        student.grader = grader
        student.save()
        # Student assigned to grader now, so count should be 1 for grader, and 0 for grader_2
        self.assertEqual(assignment.not_submitted_submissions_count_by_grader(grader=grader), 1)
        self.assertEqual(assignment.not_submitted_submissions_count_by_grader(grader_user=grader.user), 1)
        self.assertEqual(assignment.not_submitted_submissions_count_by_grader(grader=grader_2), 0)
        submission = self.get_test_submission()  # Uses get_test_assignment() to set submission.assignment
        submission.update(submitted=True)
        # Submission submitted, so count should be back to 0 for both graders
        self.assertEqual(assignment.not_submitted_submissions_count_by_grader(grader=grader), 0)
        self.assertEqual(assignment.not_submitted_submissions_count_by_grader(grader_user=grader.user), 0)
        self.assertEqual(assignment.not_submitted_submissions_count_by_grader(grader=grader_2), 0)

    def test_submission_grade_display(self):
        """
        Tests the .grade_display() method on Submission
        """
        submission = self.get_test_submission()
        self.assertEqual(submission.grade_display(), "(Not Graded)")
        submission.update(grade=70)
        self.assertEqual(submission.grade_display(), "70/100 (70%)")

    def test_course_get_or_404_check_course(self):
        """
        Tests the .get_or_404_check_course() method on CourseModel
        """
        grader = self.get_test_grader()
        self.assertEqual(Grader.get_or_404_check_course(grader.course_id, id=grader.id), grader)
        self.assertRaises(PermissionDenied, Grader.get_or_404_check_course, grader.course_id + 1, id=grader.id)
