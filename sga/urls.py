"""
URL definitions
"""
from django.conf.urls import url
from django.conf.urls.static import static

from sga.views import (
    index,
    dev_start,
    view_submission_as_student,
    view_student_list,
    view_assignment,
    view_submission_as_staff,
    view_assignment_list,
    view_student,
    view_grader_list,
    view_grader,
    unsubmit_submission,
    change_student_to_grader,
    change_grader_to_student,
    download_all_submissions,
    download_not_graded_submissions,
    unassign_grader,
    unassign_student
)
from sga_lti import settings


urlpatterns = [
    url(r"^$", index, name="sga_index"),
    url(r"^dev-start/(?P<username>[a-zA-Z0-9-_]{0,50})$", dev_start, name="dev_start"),
    url(r"^view-student-list/(?P<course_id>\d+)$", view_student_list, name="view_student_list"),
    url(r"^view-grader-list/(?P<course_id>\d+)$", view_grader_list, name="view_grader_list"),
    url(r"^view-assignment-list/(?P<course_id>\d+)$", view_assignment_list, name="view_assignment_list"),
    url(r"^view-submission-as-student/(?P<course_id>\d+)/(?P<assignment_id>\d+)$",
        view_submission_as_student, name="view_submission_as_student"),
    url(r"^view-submission-as-staff/(?P<course_id>\d+)/(?P<assignment_id>\d+)/(?P<student_user_id>\d+)$",
        view_submission_as_staff, name="view_submission_as_staff"),
    url(r"^view-assignment/(?P<course_id>\d+)/(?P<assignment_id>\d+)$", view_assignment, name="view_assignment"),
    url(r"^view-student/(?P<course_id>\d+)/(?P<student_user_id>\d+)$", view_student, name="view_student"),
    url(r"^view-grader/(?P<course_id>\d+)/(?P<grader_user_id>\d+)$", view_grader, name="view_grader"),
    url(r"^unsubmit-submission/(?P<course_id>\d+)/(?P<assignment_id>\d+)/(?P<student_user_id>\d+)$",
        unsubmit_submission, name="unsubmit_submission"),
    url(r"^change-student-to-grader/(?P<course_id>\d+)/(?P<student_user_id>\d+)$", change_student_to_grader,
        name="change_student_to_grader"),
    url(r"^unassign-grader/(?P<course_id>\d+)/(?P<student_user_id>\d+)$", unassign_grader, name="unassign_grader"),
    url(r"^unassign-student/(?P<course_id>\d+)/(?P<grader_user_id>\d+)/(?P<student_user_id>\d+)$",
        unassign_student, name="unassign_student"),
    url(r"^change-grader-to-student/(?P<course_id>\d+)/(?P<grader_user_id>\d+)$", change_grader_to_student,
        name="change_grader_to_student"),
    url(r"^download-all-submissions/(?P<course_id>\d+)/(?P<assignment_id>\d+)$", download_all_submissions,
        name="download_all_submissions"),
    url(r"^download-not-graded-submissions/(?P<course_id>\d+)/(?P<assignment_id>\d+)$",
        download_not_graded_submissions, name="download_not_graded_submissions"),
]

if settings.DEVELOPMENT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
