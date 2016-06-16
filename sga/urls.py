from django.conf.urls import url
from django.conf.urls.static import static

from sga.views import index, dev_start, view_submission_as_student, view_student_list_as_grader, \
    view_assignment_as_grader, view_submission_as_grader, view_assignment_list_as_grader
from sga_lti import settings

urlpatterns = [
    url(r'^$', index, name='sga-index'),
    url(r'^dev-start/(?P<username>\w{0,50})$', dev_start, name="dev_start"),
    url(r'^view-student-list/(?P<course_id>\w{0,50})$', view_student_list_as_grader, name="view_student_list_as_grader"),
    url(r'^view-assignment-list/(?P<course_id>\w{0,50})$', view_assignment_list_as_grader, name="view_assignment_list_as_grader"),
    url(r'^view-submission-student/(?P<assignment_id>\w{0,50})$', view_submission_as_student, name="view_submission_as_student"),
    url(r'^view-submission-grader/(?P<assignment_id>\w{0,50})/(?P<student_user_id>\w{0,50})$', view_submission_as_grader, name="view_submission_as_grader"),
    url(r'^view-assignment-grader/(?P<assignment_id>\w{0,50})$', view_assignment_as_grader, name="view_assignment_as_grader")
]

if settings.DEVELOPMENT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
