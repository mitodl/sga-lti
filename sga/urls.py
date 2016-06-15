from django.conf.urls import url
from django.conf.urls.static import static

from sga.views import index, dev_start, view_assignment, view_assignment_student, view_student_list
from sga_lti import settings

urlpatterns = [
    url(r'^$', index, name='sga-index'),
    url(r'^dev-start/(?P<username>\w{0,50})$', dev_start),
    url(r'^view-student-list/(?P<course_id>\w{0,50})$', view_student_list, name="view_student_list"),
    url(r'^view-assignment/(?P<assignment_id>\w{0,50})$', view_assignment, name="view_assignment"),
    url(r'^view-assignment-student/(?P<assignment_id>\w{0,50})$', view_assignment_student, name="view_assignment_student")
]

if settings.DEVELOPMENT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
