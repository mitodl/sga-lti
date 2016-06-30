"""
View definitions
"""

from datetime import datetime
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from sga.backend.authentication import allowed_roles
from sga.backend.constants import (
    Roles,
    GRADER_TO_STUDENT_CONFIRM,
    STUDENT_TO_GRADER_CONFIRM,
    UNASSIGN_GRADER_CONFIRM,
    UNASSIGN_STUDENT_CONFIRM,
    UNSUBMIT_CONFIRM)
from sga.backend.files import serve_zip_file
from sga.backend.send_grades import send_grade
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
    View for SGA-LTI installation instructions
    """
    return render(request, "sga/index.html")


def not_graded_block_error_page(request):
    """
    View for error message if tool is embedded in a not graded block
    """
    return render(request, "sga/not_graded_block_error_page.html")


def studio_message_page(request):
    """
    View for error message if tool is embedded in a not graded block
    """
    return render(request, "sga/studio_message_page.html")


@allowed_roles([Roles.admin, Roles.grader])
def staff_index(request, course_id):  # pylint: disable=unused-argument
    """
    Staff index
    """
    # course_id sets request.course in allowed_roles()
    return render(request, "sga/staff_index.html")


@allowed_roles([Roles.student])
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
    student = Student.get_or_404_check_course(course_id, user_id=student_user_id, deleted=False)
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
            # Update database object
            submission_form.save()
            submission.graded_at = datetime.utcnow()
            submission.graded_by = request.user
            submission.graded = True
            submission.save()
            # Send grade back to edX
            send_grade(submission.consumer_key, submission.edx_url, submission.result_id, submission.edx_grade())
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
    if request.role == Roles.admin:
        students = Student.objects.filter(course=course, deleted=False)
        grader_user = None
    else:
        students = Student.objects.filter(course=course, grader__user=request.user, deleted=False)
        grader_user = request.user
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
    student = Student.get_or_404_check_course(course_id, user_id=student_user_id, deleted=False)
    if request.method == "POST" and request.role == Roles.admin:
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
    if request.method == "POST" and request.role == Roles.admin:
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
    students = grader.students.filter(deleted=False)
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
        student_users = assignment.course.students.filter(student__deleted=False)
    else:
        grader = Grader.objects.get(user_id=request.user.id, course_id=course_id)
        student_users = grader.students.filter(deleted=False)
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
def download_all_submissions(request, course_id, assignment_id, not_graded_only=False, zipname="All Submissions"):
    """
    Generate and serve zip file with submission files
    """
    assignment = Assignment.get_or_404_check_course(course_id, id=assignment_id)
    # Filter out submissions - we can chain QuerySets because they are lazy
    submissions = Submission.objects.filter(
        assignment=assignment,
        student__student__deleted=False
    ).exclude(
        student_document=""
    )
    if request.role == Roles.grader:
        grader = Grader.objects.get(user=request.user, course=assignment.course)
        student_users = [s.user for s in grader.students.filter(deleted=False)]
        submissions = submissions.filter(student__in=student_users)
    if not_graded_only:
        submissions = submissions.exclude(graded=True)
    course = Course.objects.get(id=course_id)
    full_zipname = "{course_edx_id} - {zipname}".format(course_edx_id=course.edx_id, zipname=zipname)
    return serve_zip_file(submissions, full_zipname)


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
        zipname="Not Graded Submissions"
    )


@allowed_roles([Roles.admin])
@require_http_methods(["POST"])
def change_grader_to_student(request, course_id, grader_user_id):  # pylint: disable=unused-argument
    """
    Change grader to student
    """
    grader = Grader.get_or_404_check_course(course_id, user_id=grader_user_id)
    student, _ = Student.objects.update_or_create(
        course_id=course_id,
        user_id=grader_user_id,
        defaults={"deleted": False}
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
    student.update(grader=None, deleted=True)
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
    return redirect("view_grader", course_id=course_id, grader_user_id=grader_user_id)


def dev_start(request):  # pragma: no cover
    """
    For local development only - sets session variables and authenticates user
    """
    if settings.DEVELOPMENT:
        request.role = Roles.admin
        request.course = Course.objects.get(id=1)
        request.session["course_roles"]["1"] = Roles.admin
        request.session.save()
    return redirect("sga_index")
