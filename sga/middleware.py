from django.core.exceptions import ImproperlyConfigured

from sga.models import Course


class SGAMiddleware(object):
    def process_request(self, request):
        # Validate LTI request
        if not hasattr(request, "LTI"):
            raise ImproperlyConfigured()
        # Get course
        course, created = Course.objects.get_or_create(edx_id=request.LTI["context_id"])
        # Get role
        if request.method == "POST" and request.POST.get("lti_message_type") == "basic-lti-launch-request":
            # This is an initial request
            setattr(request.LTI, "initial_request", True)
        else:
            setattr(request.LTI, "initial_request", False)
            