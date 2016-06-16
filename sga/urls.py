from django.conf.urls import url
from django.conf.urls.static import static

from sga.views import index, dev_start, view_submission_as_student, view_student_list, \
    view_assignment, view_submission_as_staff, view_assignment_list, view_student, \
    view_grader_list, view_grader, unsubmit_submission
from sga_lti import settings


urlpatterns = [
    url(r'^$', index, name='sga-index'),
    url(r'^dev-start/(?P<username>\w{0,50})$', dev_start, name="dev_start"),
    url(r'^view-student-list/(?P<course_id>\w{0,50})$', view_student_list, name="view_student_list"),
    url(r'^view-grader-list/(?P<course_id>\w{0,50})$', view_grader_list, name="view_grader_list"),
    url(r'^view-assignment-list/(?P<course_id>\w{0,50})$', view_assignment_list, name="view_assignment_list"),
    url(r'^view-submission-as-student/(?P<assignment_id>\w{0,50})$', view_submission_as_student, name="view_submission_as_student"),
    url(r'^view-submission-as-staff/(?P<assignment_id>\w{0,50})/(?P<student_user_id>\w{0,50})$', view_submission_as_staff, name="view_submission_as_staff"),
    url(r'^view-assignment/(?P<assignment_id>\w{0,50})$', view_assignment, name="view_assignment"),
    url(r'^view-student/(?P<course_id>\w{0,50})/(?P<student_user_id>\w{0,50})$', view_student, name="view_student"),
    url(r'^view-grader/(?P<course_id>\w{0,50})/(?P<grader_user_id>\w{0,50})$', view_grader, name="view_grader"),
    url(r'^unsubmit-submission/(?P<assignment_id>\w{0,50})/(?P<student_user_id>\w{0,50})$', unsubmit_submission, name="unsubmit_submission"),
]

if settings.DEVELOPMENT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
