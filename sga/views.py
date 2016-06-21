from datetime import datetime
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from sga.backend.authentication import allowed_roles
from sga.backend.downloads import serve_zip_file
from sga.backend.constants import Roles, GRADER_TO_STUDENT_CONFIRM, STUDENT_TO_GRADER_CONFIRM, UNASSIGN_GRADER_CONFIRM, \
    UNASSIGN_STUDENT_CONFIRM
from sga.forms import StudentAssignmentSubmissionForm, GraderAssignmentSubmissionForm, GraderMaxStudentsForm, \
    AssignGraderToStudentForm, AssignStudentToGraderForm
from sga.models import Assignment, Submission, Course, Grader, Student, User


@csrf_exempt
def index(request):
    """
    The index view. Display available programs
    """
    course = Course.objects.first()
    assignments = course.assignments.all()
    users = User.objects.all()
    students = Student.objects.all()
    graders = Grader.objects.all()
    admins = course.administrators.all()
    if "role" not in request:
        request.role = None
    return render(request, "sga/index.html", context={
        "course": course,
        "assignments": assignments,
        "users": users,
        "students": students,
        "graders": graders,
        "admins": admins
    })


@allowed_roles([Roles.student])
def view_submission_as_student(request, assignment_id):
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
            redirect("view_submission_as_student", assignment_id=assignment_id)
    else:
        submission_form = StudentAssignmentSubmissionForm(instance=submission)
    return render(request, "sga/view_submission_as_student.html", context={
        "submission_form": submission_form,
        "submission": submission,
        "assignment": assignment,
    })


@allowed_roles([Roles.grader, Roles.admin])
def view_submission_as_staff(request, assignment_id, student_user_id):
    """
    Submission view for staff
    """
    try:
        assignment = Assignment.objects.get(edx_id=assignment_id)
        student = Student.objects.get(user__username=student_user_id)
        submission, created = Submission.objects.get_or_create(student=student.user, assignment=assignment)
    except:
        raise Http404()
    next_not_graded_submission = Submission.objects.filter(assignment=assignment, submitted=True,
                                                           graded_at=None).exclude(pk=submission.pk).first()
    if next_not_graded_submission:
        next_not_graded_submission_url = reverse("view_submission_as_staff", kwargs={
            "assignment_id": assignment_id,
            "student_user_id": next_not_graded_submission.student.username
        })
    else:
        next_not_graded_submission_url = None
    if request.method == "POST":
        submission_form = GraderAssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if submission_form.is_valid():
            submission_form.save()
            submission.graded_at = datetime.utcnow()
            submission.graded_by = request.user
            submission.graded = True
            submission.save()
            redirect("view_submission_as_staff", assignment_id=assignment_id, student_user_id=student.user.username)
        else:
            # Clear changes made to submission instance since form is invalid (form field values are untouched)
            submission = Submission.objects.get(pk=submission.pk)
    else:
        submission_form = GraderAssignmentSubmissionForm(instance=submission)
    return render(request, "sga/view_submission_as_staff.html", context={
        "submission_form": submission_form,
        "next_not_graded_submission_url": next_not_graded_submission_url,
        "submission": submission,
        "assignment": assignment,
        "student_user": student.user,
    })


@allowed_roles([Roles.admin])
def unsubmit_submission(request, assignment_id, student_user_id):
    try:
        assignment = Assignment.objects.get(edx_id=assignment_id)
        student = Student.objects.get(user__username=student_user_id)
        submission, created = Submission.objects.get_or_create(student=student.user, assignment=assignment)
    except:
        raise Http404()
    submission.submitted = False
    submission.graded = False
    submission.save()
    return redirect("view_submission_as_staff", assignment_id=assignment_id, student_user_id=student_user_id)


