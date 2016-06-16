from django.conf.urls import url
from django.conf.urls.static import static

from sga.views import index, dev_start, view_submission_student, view_student_list, \
    view_assignment_grader, view_submission_grader, view_assignment_list
from sga_lti import settings

urlpatterns = [
    url(r'^$', index, name='sga-index'),
    url(r'^dev-start/(?P<username>\w{0,50})$', dev_start, name="dev_start"),
    url(r'^view-student-list/(?P<course_id>\w{0,50})$', view_student_list, name="view_student_list"),
    url(r'^view-assignment-list/(?P<course_id>\w{0,50})$', view_assignment_list, name="view_assignment_list"),
    url(r'^view-submission-student/(?P<assignment_id>\w{0,50})$', view_submission_student, name="view_submission_student"),
    url(r'^view-submission-grader/(?P<assignment_id>\w{0,50})/(?P<student_user_id>\w{0,50})$', view_submission_grader, name="view_submission_grader"),
    url(r'^view-assignment-grader/(?P<assignment_id>\w{0,50})$', view_assignment_grader, name="view_assignment_grader")
]

if settings.DEVELOPMENT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
