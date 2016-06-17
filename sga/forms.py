from django import forms

from sga.models import Submission, Grader


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