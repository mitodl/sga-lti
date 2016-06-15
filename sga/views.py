"""
sga views
"""
import json

from datetime import datetime
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import Http404
from django.shortcuts import render, redirect

from sga.backend.authentication import is_student
from sga.forms import AssignmentSubmissionForm
from sga.models import Assignment, Submission, Course


def get_bundle_url(request, bundle_name):
    """
    Create a URL for the webpack bundle.
    """
    if settings.DEBUG and settings.USE_WEBPACK_DEV_SERVER:
        host = request.get_host().split(":")[0]

        return "{host_url}/{bundle}".format(
            host_url=settings.WEBPACK_SERVER_URL.format(host=host),
            bundle=bundle_name
        )
    else:
        return static("bundles/{bundle}".format(bundle=bundle_name))


def index(request):
    """
    The index view. Display available programs
    """
    return render(request, "sga/index.html")


def view_assignment(request, assignment_id):
    if is_student(request.user):
        return redirect("view_assignment_student", assignment_id=assignment_id)

def view_assignment_student(request, assignment_id):
    """
    Assignment view for students
    """
    try:
        assignment = Assignment.objects.get(edx_id=assignment_id)
        submission, created = Submission.objects.get_or_create(student=request.user, assignment=assignment)
    except:
        raise Http404()
    if request.method == "POST":
        submission_form = AssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if submission_form.is_valid():
            submission_form.save()
            submission.submitted = True
            submission.submitted_at = datetime.utcnow()
            submission.save()
            redirect("view_assignment", assignment_id=assignment_id)
    else:
        submission_form = AssignmentSubmissionForm(instance=submission)
    return render(request, "sga/view_assignment_student.html", context={
        "submission_form": submission_form,
        "submission": submission,
        "assignment_id": assignment_id,
        "assignment_name": "PLACEHOLDER"
    })


def view_student_list(request, course_id):
    try:
        course = Course.objects.get(edx_id=course_id)
    except:
        raise Http404()
    students = course.students.all()
    return render(request, "sga/view_students_list.html", context={
        "course_name": course.name,
        "students": students
    })


def dev_start(request, username):
    """
    For local development only - sets session variables
    """
    if settings.DEVELOPMENT:
        print(username)
        SESSION = {
            "user_id": "user_id1234",  # Edx user id
            "resource_link_title": "Assignment Title",  # Assignment title
            "resource_link_id": "assignment_id1234",  # Assignment Edx id
            "context_label": "Course Title",  # Course title
            "context_id": "course_id1234",  # Course Edx id
            "roles": "student",  # User role
        }
        for var, val in SESSION.items():
            request.session[var] = val
        user = authenticate(username=username, password=" ")
        login(request, user)
    return redirect("sga-index")
