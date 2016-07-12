"""
Model definitions
"""
from datetime import datetime

import pytz
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from sga.backend.files import student_submission_file_path, grader_submission_file_path
from sga.backend.validators import validate_file_extension, validate_file_size


class TimeStampedModel(models.Model):
    """
    Base model for create/update timestamps
    """
    created_on = models.DateTimeField(auto_now_add=True)  # UTC
    updated_on = models.DateTimeField(auto_now=True)  # UTC

    def update(self, **kwargs):
        """
        Automatically update updated_on timestamp
        """
        update_fields = {"updated_on"}
        for k, v in kwargs.items():
            setattr(self, k, v)
            update_fields.add(k)
        self.save(update_fields=update_fields)

    class Meta:
        abstract = True


class Grader(TimeStampedModel):
    """
    Grader model (intermediate between Course and User)
    """
    max_students = models.IntegerField(default=10)
    user = models.ForeignKey(User)
    course = models.ForeignKey("Course")

    def __str__(self):
        return self.user.username

    def get_number_of_students(self):
        """ Gets the number of students assigned to the grader """
        return self.students.filter(deleted=False).count()

    def graded_submissions_count(self):
        """
        Returns a count of submission that are graded by this grader
        """
        return Submission.objects.filter(
            graded_by=self.user,
            student__student__deleted=False,
            assignment__course=self.course,
            submitted=True,
            graded=True
        ).count()

    def not_graded_submissions_count(self):
        """
        Returns a count of submission that are submitted but not graded by this grader
        """
        student_users = [s.user for s in self.students.filter(deleted=False)]
        return Submission.objects.filter(
            student__in=student_users,
            assignment__course=self.course,
            submitted=True,
            graded=False
        ).count()

    def available_student_slots_count(self):
        """
        Returns a count of the number of students this grader can still accept
        """
        return self.max_students - self.students.filter(deleted=False).count()

    class Meta():
        unique_together = (("user", "course"),)


class Student(TimeStampedModel):
    """
    Student model (intermediate between Course and User)
    """
    grader = models.ForeignKey(Grader, null=True, related_name="students", on_delete=models.SET_NULL)
    user = models.ForeignKey(User)
    course = models.ForeignKey("Course")
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta():
        unique_together = (("user", "course"),)


class Course(TimeStampedModel):
    """
    Course model
    """
    edx_id = models.CharField(max_length=128, unique=True)
    administrators = models.ManyToManyField(User, related_name="administrator_courses")
    graders = models.ManyToManyField(User, through=Grader, related_name="grader_courses")
    students = models.ManyToManyField(User, through=Student, related_name="student_courses")

    def has_student(self, user):
        """
        Returns a boolean of whether or not user is a Student in this course
        """
        return self.students.filter(pk=user.pk, student__deleted=False).exists()

    def has_grader(self, user):
        """
        Returns a boolean of whether or not user is a Grader in this course
        """
        return self.graders.filter(pk=user.pk).exists()

    def has_admin(self, user):
        """
        Returns a boolean of whether or not user is an administrator in this course
        """
        return self.administrators.filter(pk=user.pk).exists()

    def not_graded_submissions_count_by_student(self, student):
        """
        Returns a count of submissions by this student that are submitted but not graded
        """
        if student.deleted:
            return "N/A"
        return Submission.objects.filter(
            assignment__course=self,
            student=student.user,
            submitted=True,
            graded=False
        ).count()


class Assignment(TimeStampedModel):
    """
    Assignment model
    """
    edx_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    due_date = models.DateTimeField(null=True)
    grace_period = models.IntegerField(default=0)
    course = models.ForeignKey(Course, related_name="assignments")

    def graded_submissions_count(self):
        """
        Returns a count of submissions for this assignment that are graded
        """
        return self.submissions.filter(submitted=True, graded=True, student__student__deleted=False).count()

    def graded_submissions_count_by_grader(self, grader=None, grader_user=None):
        """
        Returns a count of submissions for this assignment for this grader that are graded
        """
        if not grader_user:
            grader_user = grader.user
        return Submission.objects.filter(
            graded_by=grader_user,
            student__student__deleted=False,
            assignment=self,
            submitted=True,
            graded=True
        ).count()

    def not_graded_submissions_count(self):
        """
        Returns a count of submissions for this assignment that are submitted but not graded
        """
        return self.submissions.filter(submitted=True, graded=False, student__student__deleted=False).count()

    def not_graded_submissions_count_by_grader(self, grader=None, grader_user=None):
        """
        Returns a count of submissions for this assignment for this grader that are submitted but not graded
        """
        if not grader:
            grader = Grader.objects.get(user=grader_user, course=self.course)
        student_users = [s.user for s in grader.students.filter(deleted=False)]
        return Submission.objects.filter(
            student__in=student_users,
            assignment=self,
            submitted=True,
            graded=False
        ).count()

    def not_submitted_submissions_count(self):
        """
        Returns a count of submissions for this assignment that are not submitted
        """
        # Graders all have student objects
        students_in_course = self.course.students.filter(student__deleted=False).count()
        return students_in_course - self.graded_submissions_count() - self.not_graded_submissions_count()

    def not_submitted_submissions_count_by_grader(self, grader=None, grader_user=None):
        """
        Returns a count of submissions for this assignment for this grader that are not submitted
        """
        if not grader:
            grader = Grader.objects.get(user=grader_user, course=self.course)
        return (grader.get_number_of_students()
                - self.graded_submissions_count_by_grader(grader_user=grader.user)
                - self.not_graded_submissions_count_by_grader(grader=grader))

    def is_past_due_date(self, now=datetime.utcnow().replace(tzinfo=pytz.UTC)):
        """
        Returns a boolean of whether or not the assignment is past its due date
        """
        if not self.due_date:
            return None
        return now >= self.due_date


class Submission(TimeStampedModel):
    """
    Submission model
    """
    assignment = models.ForeignKey(Assignment, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submitted_submissions")
    graded_by = models.ForeignKey(User, null=True, related_name="graded_submissions")

    student_document = models.FileField(
        upload_to=student_submission_file_path,
        null=True,
        max_length=512,
        validators=[validate_file_extension, validate_file_size]
    )
    description = models.TextField(null=True)
    submitted_at = models.DateTimeField(null=True)  # UTC
    submitted = models.BooleanField(default=False)

    grader_document = models.FileField(
        upload_to=grader_submission_file_path,
        null=True,
        max_length=512,
        validators=[validate_file_extension, validate_file_size]
    )
    feedback = models.TextField(null=True)
    grade = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True)  # 0-100
    graded_at = models.DateTimeField(null=True)  # UTC
    graded = models.BooleanField(default=False)

    edx_url = models.CharField(max_length=256, null=True)  # lis_outcome_service_url
    result_id = models.CharField(max_length=256, null=True)  # lis_result_sourcedid
    consumer_key = models.CharField(max_length=256, null=True)  # oauth_consumer_key

    def grade_display(self):
        """
        Human-readable display of this submission's grade
        """
        if self.grade:
            return "{grade}/100 ({percent}%)".format(grade=self.grade, percent=self.grade)
        else:
            return "(Not Graded)"

    def edx_grade(self):
        """
        Returns grade converted to edX format (0.00 - 1.00)
        """
        return self.grade / 100

    class Meta:
        unique_together = (("assignment", "student"),)
