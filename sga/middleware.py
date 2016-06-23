"""
Custom middleware
"""

from django.core.exceptions import ImproperlyConfigured
from django.utils.dateparse import parse_datetime

from sga.models import Course, Assignment
from sga.backend.constants import Roles


class SGAMiddleware(object):
    """
    Middleware for processing incoming LTI requests
    """
    def process_request(self, request):  # pylint: disable=no-self-use
        """
        Processes incoming LTI requests
        """
        if not hasattr(request, "LTI"):
            raise ImproperlyConfigured("LTI middleware not installed")
        if "context_id" in request.LTI:
            # Get course
            course, _ = Course.objects.get_or_create(edx_id=request.LTI["context_id"])
            request.course = course
        else:
            request.course = None

        initial_request = (request.method == "POST" and
                           request.POST.get("lti_message_type") == "basic-lti-launch-request")
        if (initial_request and request.user.is_authenticated() and
                request.course and "resource_link_id" in request.LTI):
            # On the initial request, we have potentially gotten new information
            # from edX; update the database accordingly
            # request.LTI["lis_outcome_service_url"]
            due_date = request.POST.get("custom_component_due_date")
            if due_date:
                due_date = parse_datetime(due_date)
            defaults = {"course": request.course, "due_date": due_date,
                        "name": request.POST.get("custom_component_display_name")}
            Assignment.objects.update_or_create(edx_id=request.LTI["resource_link_id"],
                                                defaults=defaults)
            if "Instructor" in request.LTI.get("roles", []):
                course.administrators.add(request.user)
            else:
                course.administrators.remove(request.user)
                course.students.add(request.user)

        # Determine roll of user based on database state; this should be accurate
        # because we update the database state on the initial LTI request
        if not request.user.is_authenticated() or not request.course:
            request.role = None
        elif course.has_admin(request.user):
            request.role = Roles.admin
        elif course.has_grader(request.user):
            request.role = Roles.grader
        else:
            request.role = Roles.student
