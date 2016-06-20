from django import forms
from django.db.models import Count, F

from sga.models import Submission, Grader, Student


class StudentAssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = [
            "student_document",
            "description"
        ]
        labels = {
            "student_document": "File Submission",
            "description": "File Description"
        }


class GraderAssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = [
            "grader_document",
            "feedback",
            "grade"
        ]
        labels = {
            "grader_document": "Annotated File Submission",
            "feedback": "Feedback",
            "grade": "Grade (0-100)"
        }


class GraderMaxStudentsForm(forms.ModelForm):
    class Meta:
        model = Grader
        fields = [
            "max_students"
        ]
        labels = {
            "max_students": "Max Students"
        }


class AssignGraderToStudentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        """ Filters graders for only ones that are available for assigning students to"""
        super().__init__(*args, **kwargs)
        self.fields["grader"].queryset = self.fields["grader"].queryset.annotate(Count("students")).filter(max_students__gt=F("students__count"))
    
    class Meta:
        model = Student
        fields = [
            "grader"
        ]