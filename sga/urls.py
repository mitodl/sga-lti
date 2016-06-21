from django.conf.urls import url
from django.conf.urls.static import static

from sga.views import index, dev_start, view_submission_as_student, view_student_list, \
    view_assignment, view_submission_as_staff, view_assignment_list, view_student, \
    view_grader_list, view_grader, unsubmit_submission, change_student_to_grader, \
    change_grader_to_student, download_all_submissions, download_not_graded_submissions, unassign_grader, \
    unassign_student
from sga_lti import settings


urlpatterns = [
    url(r'^$', index, name='sga-index'),
    url(r'^dev-start/(?P<username>[a-zA-Z0-9-_]{0,50})$', dev_start, name="dev_start"),
    url(r'^view-student-list/(?P<course_id>\w{0,50})$', view_student_list, name="view_student_list"),
    url(r'^view-grader-list/(?P<course_id>\w{0,50})$', view_grader_list, name="view_grader_list"),
    url(r'^view-assignment-list/(?P<course_id>\w{0,50})$', view_assignment_list, name="view_assignment_list"),
    url(r'^view-submission-as-student/(?P<assignment_id>\w{0,50})$', view_submission_as_student, name="view_submission_as_student"),
    url(r'^view-submission-as-staff/(?P<assignment_id>\w{0,50})/(?P<student_user_id>[a-zA-Z0-9-_]{0,50})$', view_submission_as_staff, name="view_submission_as_staff"),
]

if settings.DEVELOPMENT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
