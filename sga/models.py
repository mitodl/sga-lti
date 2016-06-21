from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from sga.backend.constants import student_submission_file_path, grader_submission_file_path
from sga.backend.validators import validate_file_extension


class TimeStampedModel(models.Model):
    """ Base model for create/update timestamps """
    created_on = models.DateTimeField(auto_now_add=True)  # UTC
    updated_on = models.DateTimeField(auto_now=True)  # UTC

    class Meta:
        abstract = True

    def update(self, **kwargs):
        """ Automatically update updated_on timestamp"""
        update_fields = {"updated_on"}
        for k, v in kwargs.iteritems():
            setattr(self, k, v)
            update_fields.add(k)
        self.save(update_fields=update_fields)


class Grader(models.Model):
    max_students = models.IntegerField(default=10)
    user = models.ForeignKey(User)
    course = models.ForeignKey("Course")
    
    def graded_submissions_count(self):
        return Submission.objects.filter(
            graded_by=self.user,
            assignment__course=self.course,
            submitted=True,
            graded=True
        ).count()
    
    def not_graded_submissions_count(self):
        return Submission.objects.filter(
            graded_by=self.user,
            assignment__course=self.course,
            submitted=True,
            graded=False
        ).count()
    
    def __str__(self):
        return self.user.get_full_name()


class Student(models.Model):
    grader = models.ForeignKey(Grader, null=True, related_name="students", on_delete=models.SET_NULL)
    user = models.ForeignKey(User)
    course = models.ForeignKey("Course")

    def __str__(self):
        return self.user.get_full_name()

  
class Course(TimeStampedModel):
    edx_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    administrators = models.ManyToManyField(User, related_name="administrator_courses")
    graders = models.ManyToManyField(User, through=Grader, related_name="grader_courses")
    students = models.ManyToManyField(User, through=Student, related_name="student_courses")

    def has_student(self, user):
        return self.students.filter(pk=user.pk).exists()
    
    def has_grader(self, user):
        return self.graders.filter(pk=user.pk).exists()
    
    def has_admin(self, user):
        return self.administrators.filter(pk=user.pk).exists()
    
    def not_graded_submissions_count_by_user(self, user):
        print(user)
        return Submission.objects.filter(assignment__course=self, student=user, submitted=True, graded_at=None).count()


class Assignment(TimeStampedModel):
    edx_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    due_date = models.DateTimeField()
    grace_period = models.IntegerField()
    course = models.ForeignKey(Course, related_name="assignments")
    
    def graded_submissions_count(self):
        return self.submissions.filter(submitted=True, graded=True).count()
    
    def graded_submissions_count_by_grader(self, grader=None, grader_user=None):
        if not grader_user:
            grader_user = grader.user
        return Submission.objects.filter(
            graded_by=grader_user,
            assignment=self,
            submitted=True,
            graded=True
        ).count()
    
    def not_graded_submissions_count(self):
        return self.submissions.filter(submitted=True, graded=False).count()
    
    def not_graded_submissions_count_by_grader(self, grader=None, grader_user=None):
        if not grader:
            grader = Grader.objects.get(user=grader_user, course=self.course)
        student_users = [s.user for s in grader.students.all()]
        return Submission.objects.filter(
            student__in=student_users,
            assignment=self,
            submitted=True,
            graded=False
        ).count()
    
    def not_submitted_submissions_count(self):
        students_in_course = self.course.students.count()
        return students_in_course - self.graded_submissions_count() - self.not_graded_submissions_count()
    
    def not_submitted_submissions_count_by_grader(self, grader=None, grader_user=None):
        if not grader:
            grader = Grader.objects.get(user=grader_user, course=self.course)
        return (grader.students.count()
                - self.graded_submissions_count_by_grader(grader_user=grader_user)
                - self.not_graded_submissions_count_by_grader(grader=grader))


class Submission(TimeStampedModel):
    assignment = models.ForeignKey(Assignment, related_name="submissions")
    student = models.ForeignKey(User, related_name="submitted_submissions")
    graded_by = models.ForeignKey(User, null=True, related_name="graded_submissions")
    
    description = models.TextField(null=True)
    feedback = models.TextField(null=True)
    grade = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], null=True)  # 0-100
    submitted_at = models.DateTimeField(null=True)  # UTC
    graded_at = models.DateTimeField(null=True)  # UTC
    submitted = models.BooleanField(default=False)
    graded = models.BooleanField(default=False)
    
    student_document = models.FileField(upload_to=student_submission_file_path, null=True, validators=[validate_file_extension])
    grader_document = models.FileField(upload_to=grader_submission_file_path, null=True, validators=[validate_file_extension])
    
    def grade_display(self):
        return "{grade}/100 ({percent}%)".format(grade=self.grade, percent=self.grade)
    
    class Meta:
        unique_together = (("assignment", "student"),)