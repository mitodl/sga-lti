from django.contrib.auth.models import User
from django.db import models

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
    max_students = models.IntegerField()
    user = models.ForeignKey(User)
    course = models.ForeignKey("Course")


class Student(models.Model):
    grader = models.ForeignKey(Grader, null=True, related_name="students", on_delete=models.SET_NULL)
    user = models.ForeignKey(User)

  
class Course(TimeStampedModel):
    edx_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    administrators = models.ManyToManyField(User, related_name="administrated_courses")
    graders = models.ManyToManyField(User, through=Grader, related_name="graded_courses")
    students = models.ManyToManyField(User, through=Student)


class Assignment(TimeStampedModel):
    edx_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=128)
    due_date = models.DateTimeField()
    grace_period = models.IntegerField()
    course = models.ForeignKey(Course, related_name="assignments")


class Submission(TimeStampedModel):
    assignment = models.ForeignKey(Assignment, related_name="submissions")
    student = models.ForeignKey(User, related_name="submitted_assignments")
    graded_by = models.ForeignKey(User, related_name="graded_assignments")
    
    description = models.TextField()
    feedback = models.TextField()
    grade = models.IntegerField()  # 0-100
    submitted_at = models.DateTimeField(auto_now_add=True)  # UTC
    graded_at = models.DateTimeField()  # UTC
    submitted = models.BooleanField(default=True)
    
    student_document = models.FileField()
    grader_document = models.FileField(null=True)
    
    class Meta:
        unique_together = (("assignment", "student"),)