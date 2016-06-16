from django.conf.urls import url
from django.conf.urls.static import static

from sga.views import index, dev_start, view_submission_as_student, view_student_list_as_grader, \
    view_assignment_as_grader, view_submission_as_grader, view_assignment_list_as_grader, view_student_as_grader, \
    view_grader_list_as_admin
from sga_lti import settings


urlpatterns = [
    url(r'^$', index, name='sga-index'),
    url(r'^dev-start/(?P<username>\w{0,50})$', dev_start, name="dev_start"),
    url(r'^view-student-list-as-grader/(?P<course_id>\w{0,50})$', view_student_list_as_grader, name="view_student_list_as_grader"),
    url(r'^view-grader-list-as-admin/(?P<course_id>\w{0,50})$', view_grader_list_as_admin, name="view_grader_list_as_admin"),
    url(r'^view-assignment-list-as-grader/(?P<course_id>\w{0,50})$', view_assignment_list_as_grader, name="view_assignment_list_as_grader"),
    url(r'^view-submission-as-student/(?P<assignment_id>\w{0,50})$', view_submission_as_student, name="view_submission_as_student"),
    url(r'^view-submission-as-grader/(?P<assignment_id>\w{0,50})/(?P<student_user_id>\w{0,50})$', view_submission_as_grader, name="view_submission_as_grader"),
    url(r'^view-assignment-as-grader/(?P<assignment_id>\w{0,50})$', view_assignment_as_grader, name="view_assignment_as_grader"),
    url(r'^view-student-as-grader/(?P<course_id>\w{0,50})/(?P<student_user_id>\w{0,50})$', view_student_as_grader, name="view_student_as_grader"),
]

if settings.DEVELOPMENT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
