"""
URLs for sga
"""
from django.conf.urls import include, url
from sga.views import index


urlpatterns = [
    url(r'^$', index, name='sga-index'),
    url(r'^status/', include('server_status.urls')),
]
