from django.conf.urls import url
from django.conf.urls.static import static

from sga.views import index, dev_start, view_assignment
from sga_lti import settings

urlpatterns = [
    url(r'^$', index, name='sga-index'),
    url(r'^dev-start$', dev_start),
    url(r'^view-assignment/(?P<assignment_id>\w{0,50})$', view_assignment, name="view-assignment")
]

if settings.DEVELOPMENT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
