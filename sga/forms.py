"""
Django form definitions
"""

from django import forms
from django.db.models import Count, F

from sga.models import Submission, Grader, Student


class StudentAssignmentSubmissionForm(forms.ModelForm):
    """
    Form for student submissions
    """
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
    """
    Form for grader submissions
    """
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
    """
    Form for changing max_students on Grader
    """
    class Meta:
        model = Grader
        fields = [
            "max_students"
        ]
        labels = {
            "max_students": "Max Students"
        }


class AssignStudentToGraderForm(forms.ModelForm):
    """
    Form for assigning a student to a grader
    """
    students = forms.ModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        """
        Filters graders for only ones that are available for assigning students to
        """
        super().__init__(*args, **kwargs)
        self.fields["students"].queryset = Student.objects.filter(
            grader=None,
            course=self.instance.course
        ).order_by(
            "user__username"
        )

    def is_valid(self):
        """
        Overrides the default is_valid for custom validation
        """
        print(self.cleaned_data["students"])
        raise Exception()

    def save(self, grader=None):
        """
        Save student-grader foreign key relationship
        """
        student = self.cleaned_data["students"]
        student.grader = grader
        student.save()

    class Meta:
        model = Grader
        fields = [
            "students"
        ]


class AssignGraderToStudentForm(forms.ModelForm):
    """
    Form for assigning a grader to a student
    """
    def __init__(self, *args, **kwargs):
        """
        Filters graders for only ones that are available for assigning students to
        """
        super().__init__(*args, **kwargs)
        self.fields["grader"].queryset = self.fields["grader"].queryset.annotate(
            Count("students")
        ).filter(
            max_students__gt=F("students__count"),
            course=self.instance.course
        ).order_by(
            "user__username"
        )

    class Meta:
        model = Student
        fields = [
            "grader"
        ]
