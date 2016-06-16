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

from sga.backend.authentication import student_view, grader_view
from sga.forms import StudentAssignmentSubmissionForm, GraderAssignmentSubmissionForm
from sga.models import Assignment, Submission, Course, Grader


def index(request):
    """
    The index view. Display available programs
    """
    return render(request, "sga/index.html")


@student_view
def view_submission_student(request, assignment_id):
    """
    Submission view for students
    """
    try:
        assignment = Assignment.objects.get(edx_id=assignment_id)
        submission, created = Submission.objects.get_or_create(student=request.user, assignment=assignment)
    except:
        raise Http404()
    if request.method == "POST":
        submission_form = StudentAssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if submission_form.is_valid():
            submission_form.save()
            submission.submitted = True
            submission.submitted_at = datetime.utcnow()
            submission.save()
            redirect("view_submission_student", assignment_id=assignment_id)
    else:
        submission_form = StudentAssignmentSubmissionForm(instance=submission)
    return render(request, "sga/view_submission_student.html", context={
        "submission_form": submission_form,
        "submission": submission,
        "assignment": assignment
    })


@grader_view
def view_submission_grader(request, assignment_id, student_user_id):
    """
    Submission view for graders
    """
    try:
        assignment = Assignment.objects.get(edx_id=assignment_id)
        grader = Grader.objects.get(user=request.user, course=assignment.course)
        student_user = grader.students.get(user__username=student_user_id).user
        submission, created = Submission.objects.get_or_create(student=student_user, assignment=assignment)
    except:
        raise Http404()
    if request.method == "POST":
        print(submission.__dict__)
        submission_form = GraderAssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if submission_form.is_valid():
            submission_form.save()
            submission.graded_at = datetime.utcnow()
            submission.graded_by = grader.user
            submission.save()
            redirect("view_submission_grader", assignment_id=assignment_id, student_user_id=student_user.username)
        else:
            # Clear changes made to submission instance since form is invalid (form field values are untouched)
            submission = Submission.objects.get(pk=submission.pk)
    else:
        submission_form = GraderAssignmentSubmissionForm(instance=submission)
    return render(request, "sga/view_submission_grader.html", context={
        "submission_form": submission_form,
        "submission": submission,
        "assignment": assignment,
        "student_user": student_user
    })


@grader_view
def view_assignment_grader(request, assignment_id):
    """
    Assignment view for graders
    """
    try:
        assignment = Assignment.objects.get(edx_id=assignment_id)
        course = assignment.course
    except:
        raise Http404()
    student_users = course.students.all()
    for student_user in student_users:
        submission, created = Submission.objects.get_or_create(student=student_user, assignment=assignment)
        student_user.submitted = "Yes" if submission.submitted else "No"
        student_user.graded = "Yes" if submission.graded() else "No"
    return render(request, "sga/view_assignment_grader.html", context={
        "student_users": student_users,
        "course": course,
        "assignment": assignment
    })


@grader_view
def view_student_list(request, course_id):
    try:
        course = Course.objects.get(edx_id=course_id)
    except:
        raise Http404()
    student_users = course.students.all()
    for student_user in student_users:
        student_user.ungraded_submissions_by_user = course.ungraded_submissions_by_user(student_user)
    return render(request, "sga/view_students_list.html", context={
        "course": course,
        "student_users": student_users
    })


@grader_view
def view_assignment_list(request, course_id):
    try:
        course = Course.objects.get(edx_id=course_id)
    except:
        raise Http404()
    assignments = course.assignments.all()
    return render(request, "sga/view_assignment_list_grader.html", context={
        "course": course,
        "assignments": assignments
    })


def dev_start(request, username):
    """
    For local development only - sets session variables
    """
    if settings.DEVELOPMENT:
        user = authenticate(username=username, password=" ")
        login(request, user)
        SESSION = {
            "user_id": username,  # Edx user id
            "resource_link_title": "Assignment Title",  # Assignment title
            "resource_link_id": "assignment1id",  # Assignment Edx id
            "context_label": "Course Title",  # Course title
            "context_id": "courseid",  # Course Edx id
            "roles": "student",  # User role
        }
        for var, val in SESSION.items():
            request.session[var] = val
    return redirect("sga-index")
