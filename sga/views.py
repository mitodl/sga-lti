"""
View definitions
"""

from datetime import datetime
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from sga.backend.authentication import allowed_roles, get_role
from sga.backend.constants import (
    Roles,
    GRADER_TO_STUDENT_CONFIRM,
    STUDENT_TO_GRADER_CONFIRM,
    UNASSIGN_GRADER_CONFIRM,
    UNASSIGN_STUDENT_CONFIRM,
    UNSUBMIT_CONFIRM)
from sga.backend.files import serve_zip_file
from sga.forms import (
    StudentAssignmentSubmissionForm,
    GraderAssignmentSubmissionForm,
    GraderMaxStudentsForm,
    AssignGraderToStudentForm,
    AssignStudentToGraderForm
)
from sga.models import Assignment, Submission, Course, Grader, Student


@csrf_exempt
def index(request):
    """
    View for redirecting EdX launch to the appropriate page
    """
    if not request.initial_lti_request:
        return render(request, "sga/index.html")
    course_edx_id = request.LTI.get("context_id")
    assignment_edx_id = request.LTI.get("resource_link_id")
    course = Course.objects.get(edx_id=course_edx_id)
    assignment = Assignment.objects.get(edx_id=assignment_edx_id)
    user_role = get_role(request.user, course.id)
    if user_role == Roles.student:
        return redirect("view_submission_as_student", course_id=course.id, assignment_id=assignment.id)
    if user_role in [Roles.admin, Roles.grader]:
        return redirect("view_assignment", course_id=course.id, assignment_id=assignment.id)
    raise Exception("Bad role %s" % user_role)


@allowed_roles([Roles.admin, Roles.grader, Roles.student])  # TODO: Change
def staff_index(request, course_id):
    """
    Staff index
    """
    return render(request, "sga/staff_index.html")


@allowed_roles([Roles.student, Roles.grader, Roles.admin])
def view_submission_as_student(request, course_id, assignment_id):
    """
    View submission (for student)
    """
    assignment = Assignment.get_or_404_check_course(course_id, id=assignment_id)
    submission, _ = Submission.objects.get_or_create(student=request.user, assignment=assignment)
    if request.method == "POST":
        submission_form = StudentAssignmentSubmissionForm(request.POST, request.FILES, instance=submission)
        if submission_form.is_valid():
            submission_form.save()
            submission.submitted = True
            submission.submitted_at = datetime.utcnow()
            submission.save()
            redirect("view_submission_as_student", course_id=course_id, assignment_id=assignment_id)
    else:
        submission_form = StudentAssignmentSubmissionForm(instance=submission)
    return render(request, "sga/view_submission_as_student.html", context={
        "course_id": course_id,
        "submission_form": submission_form,
        "submission": submission,
        "assignment": assignment,
    })


@allowed_roles([Roles.grader, Roles.admin])
def view_submission_as_staff(request, course_id, assignment_id, student_user_id):
    """
    View submission (for staff)
    """
    assignment = Assignment.get_or_404_check_course(course_id, id=assignment_id)
    student = Student.get_or_404_check_course(course_id, user_id=student_user_id)
    submission, _ = Submission.objects.get_or_create(student=student.user, assignment=assignment)
    next_not_graded_submission = Submission.objects.filter(
        assignment=assignment,
        submitted=True,
        graded_at=None
    ).exclude(pk=submission.pk).first()
    if next_not_graded_submission:
        kwargs = {
            "course_id": course_id,
            "assignment_id": assignment_id,
            "student_user_id": next_not_graded_submission.student.id
        }
        next_not_graded_submission_url = reverse("view_submission_as_staff", kwargs=kwargs)
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
            redirect(
                "view_submission_as_staff",
                course_id=course_id,
                assignment_id=assignment_id,
                student_user_id=student.user.id
            )
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
        "UNSUBMIT_CONFIRM": UNSUBMIT_CONFIRM
    })


@allowed_roles([Roles.admin])
def view_grader_list(request, course_id):
    """
    View grader list
    """
    course = get_object_or_404(Course, id=course_id)
    graders = course.grader_set.all()
    # for grader_user in grader_users:
    #     grader_user.not_graded_submissions = course.not_graded_submissions_by_user(grader_user)
    return render(request, "sga/view_grader_list.html", context={
        "course": course,
        "graders": graders
    })


@allowed_roles([Roles.grader, Roles.admin])
def view_student_list(request, course_id):
    """
    View student list
    """
    course = get_object_or_404(Course, id=course_id)
    if request.role == Roles.grader:
        students = Student.objects.filter(course=course, grader__user=request.user)
        grader_user = request.user
    if request.role == Roles.admin:
        students = Student.objects.filter(course=course)
        grader_user = None
    for student in students:
        student.not_graded_submissions_count = course.not_graded_submissions_count_by_student(student)
    return render(request, "sga/view_student_list.html", context={
        "course": course,
        "students": students,
        "grader_user": grader_user
    })


@allowed_roles([Roles.grader, Roles.admin])
def view_assignment_list(request, course_id):
    """
    View assignment list
    """
    course = get_object_or_404(Course, id=course_id)
    if request.role == Roles.grader:
        grader_user = request.user
    else:
        grader_user = None
    assignments = course.assignments.all()
    for assgnmnt in assignments:
        if grader_user:
            assgnmnt.not_submitted_count = assgnmnt.not_submitted_submissions_count_by_grader(grader_user=grader_user)
            assgnmnt.not_graded_count = assgnmnt.not_graded_submissions_count_by_grader(grader_user=grader_user)
            assgnmnt.graded_count = assgnmnt.graded_submissions_count_by_grader(grader_user=grader_user)
        else:
            assgnmnt.not_submitted_count = assgnmnt.not_submitted_submissions_count()
            assgnmnt.not_graded_count = assgnmnt.not_graded_submissions_count()
            assgnmnt.graded_count = assgnmnt.graded_submissions_count()
    return render(request, "sga/view_assignment_list.html", context={
        "course": course,
        "assignments": assignments,
        "grader_user": grader_user
    })


@allowed_roles([Roles.student, Roles.grader, Roles.admin])
def view_student(request, course_id, student_user_id):
    """
    View student
    """
    course = get_object_or_404(Course, id=course_id)
    student = Student.get_or_404_check_course(course_id, user_id=student_user_id)
    if request.method == "POST":
        assign_grader_form = AssignGraderToStudentForm(request.POST, instance=student)
        if assign_grader_form.is_valid():
            assign_grader_form.save()
    else:
        assign_grader_form = AssignGraderToStudentForm(instance=student)
    assignments = course.assignments.all()
    for assignment in assignments:
        assignment.submission, _ = assignment.submissions.get_or_create(student=student.user)
    return render(request, "sga/view_student.html", context={
        "course": course,
        "student": student,
        "assignments": assignments,
        "STUDENT_TO_GRADER_CONFIRM": STUDENT_TO_GRADER_CONFIRM,
        "UNASSIGN_GRADER_CONFIRM": UNASSIGN_GRADER_CONFIRM,
        "assign_grader_form": assign_grader_form
    })


@allowed_roles([Roles.grader, Roles.admin])
def view_grader(request, course_id, grader_user_id):
    """
    View grader
    """
    course = get_object_or_404(Course, id=course_id)
    grader = Grader.get_or_404_check_course(course_id, user_id=grader_user_id)
    # Disallow if current user is not admin or this grader
    if request.role == Roles.grader and grader.user != request.user:
        return HttpResponseForbidden()
    # Load forms and handle form submission
    max_students_form = GraderMaxStudentsForm(instance=grader)
    assign_student_form = AssignStudentToGraderForm(instance=grader)
    if request.method == "POST":
        if "max_students_submit" in request.POST:
            max_students_form = GraderMaxStudentsForm(request.POST, instance=grader)
            if max_students_form.is_valid():
                max_students_form.save()
        if "assign_student_submit" in request.POST:
            assign_student_form = AssignStudentToGraderForm(request.POST, instance=grader)
            if assign_student_form.is_valid():
                assign_student_form.save(grader)
    # Get other data for page
    graded_submissions = grader.user.graded_submissions.all()
    students = grader.students.all()
    for student in students:
        student.not_graded_submissions_count = course.not_graded_submissions_count_by_student(student)
    # Render page
    return render(request, "sga/view_grader.html", context={
        "course": course,
        "grader": grader,
        "graded_submissions": graded_submissions,
        "max_students_form": max_students_form,
        "assign_student_form": assign_student_form,
        "students": students,
        "GRADER_TO_STUDENT_CONFIRM": GRADER_TO_STUDENT_CONFIRM,
        "UNASSIGN_STUDENT_CONFIRM": UNASSIGN_STUDENT_CONFIRM
    })


@allowed_roles([Roles.grader, Roles.admin])
def view_assignment(request, course_id, assignment_id):
    """
    View assignment
    """
    assignment = Assignment.get_or_404_check_course(course_id, id=assignment_id)
    if request.role == Roles.admin:
        student_users = assignment.course.students.all()
    if request.role == Roles.grader:
        grader = Grader.objects.get(user_id=request.user.id, course_id=course_id)
        student_users = grader.students.all()
    for student_user in student_users:
        submission, _ = Submission.objects.get_or_create(student=student_user, assignment=assignment)
        student_user.submitted = "Yes" if submission.submitted else "No"
        student_user.graded = "Yes" if submission.graded else "No"
    return render(request, "sga/view_assignment.html", context={
        "student_users": student_users,
        "course": assignment.course,
        "assignment": assignment
    })


@allowed_roles([Roles.grader, Roles.admin])
def download_all_submissions(request, course_id, assignment_id, not_graded_only=False, zipname="all_submissions"):
    """
    Generate and serve zip file with submission files
    """
    assignment = Assignment.get_or_404_check_course(course_id, id=assignment_id)
    if request.role == Roles.grader:
        grader = Grader.objects.get(user=request.user, course=assignment.course)
        student_users = [s.user for s in grader.students.all()]
        submissions = Submission.objects.filter(assignment=assignment,
                                                student__in=student_users).exclude(student_document="")
    if request.role == Roles.admin:
        submissions = Submission.objects.filter(assignment=assignment).exclude(student_document="")
    if not_graded_only:
        submissions = submissions.exclude(graded=True)
    filepaths = [s.student_document.path for s in submissions]
    return serve_zip_file(filepaths, zipname)


@allowed_roles([Roles.grader, Roles.admin])
def download_not_graded_submissions(request, course_id, assignment_id):
    """
    Generate and serve zip file with not graded submission files
    """
    return download_all_submissions(
        request,
        course_id,
        assignment_id,
        not_graded_only=True,
        zipname="not_graded_submissions"
    )


@allowed_roles([Roles.admin])
@require_http_methods(["POST"])
def change_grader_to_student(request, course_id, grader_user_id):  # pylint: disable=unused-argument
    """
    Change grader to student
    """
    grader = Grader.get_or_404_check_course(course_id, user_id=grader_user_id)
    student = Student.objects.create(
        user=grader.user,
        course=grader.course
    )
    grader.delete()
    return redirect("view_student", course_id=student.course.id, student_user_id=student.user.id)


@allowed_roles([Roles.admin])
@require_http_methods(["POST"])
def change_student_to_grader(request, course_id, student_user_id):  # pylint: disable=unused-argument
    """
    Change student to grader
    """
    student = Student.get_or_404_check_course(course_id, user_id=student_user_id)
    grader = Grader.objects.create(
        user=student.user,
        course=student.course
    )
    student.update(grader=None)
    return redirect("view_grader", course_id=grader.course.id, grader_user_id=grader.user.id)


@allowed_roles([Roles.admin])
@require_http_methods(["POST"])
def unsubmit_submission(request, course_id, assignment_id, student_user_id):  # pylint: disable=unused-argument
    """
    Unsubmits a submission
    """
    assignment = Assignment.get_or_404_check_course(course_id, id=assignment_id)
    student = Student.get_or_404_check_course(course_id, user_id=student_user_id)
    submission, _ = Submission.objects.get_or_create(student=student.user, assignment=assignment)
    submission.submitted = False
    submission.graded = False
    submission.save()
    return redirect(
        "view_submission_as_staff",
        course_id=course_id,
        assignment_id=assignment_id,
        student_user_id=student_user_id
    )


@allowed_roles([Roles.admin])
@require_http_methods(["POST"])
def unassign_grader(request, course_id, student_user_id):  # pylint: disable=unused-argument
    """
    Unassign a grader from a student
    """
    student = Student.get_or_404_check_course(course_id, user_id=student_user_id)
    student.update(grader=None)
    return redirect("view_student", course_id=student.course.id, student_user_id=student_user_id)


@allowed_roles([Roles.admin])
@require_http_methods(["POST"])
def unassign_student(request, course_id, grader_user_id, student_user_id):  # pylint: disable=unused-argument
    """
    Unassign a student from a grader
    """
    grader = Grader.get_or_404_check_course(course_id, user_id=grader_user_id)
    student = get_object_or_404(Student, user_id=student_user_id, grader=grader)
    student.update(grader=None)
    return redirect("view_grader", course_id=student.course.id, grader_user_id=grader_user_id)


def dev_start(request):  # pragma: no cover
    """
    For local development only - sets session variables and authenticates user
    """
    if settings.DEVELOPMENT:
        # user = authenticate(username=username, password=" ")
        # login(request, user)
        # SESSION = {
        #     "user_id": username,  # Edx user id
        #     "resource_link_title": "Assignment Title",  # Assignment title
        #     "resource_link_id": "assignment1id",  # Assignment Edx id
        #     "context_label": "Course Title",  # Course title
        #     "context_id": "courseid",  # Course Edx id
        #     "roles": "student",  # User role
        # }
        # for var, val in SESSION.items():
        #     request.session[var] = val
        request.role = Roles.admin
        request.course = Course.objects.get(id=1)
        request.session["course_roles"]["1"] = Roles.admin
        request.session.save()
    return redirect("sga_index")
