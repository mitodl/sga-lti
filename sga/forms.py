from django import forms

from sga.models import Submission


class AssignmentSubmissionForm(forms.ModelForm):
    
    def clean(self):
        upload_to = '/some/path'
        if not 'file' in self.cleaned_data:
            return self.cleaned_data
        upload_to += self.cleaned_data['file'].name
    
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