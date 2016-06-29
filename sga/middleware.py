"""
Custom middleware
"""

from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.shortcuts import redirect
from django.utils.dateparse import parse_datetime

from sga.models import Course, Assignment, Student, Grader
from sga.backend.authentication import get_role


class SGAMiddleware(object):
    """
    Middleware for processing incoming LTI requests
    """
    ADMIN_ROLES = ["Administrator", "Instructor"]

    def process_request(self, request):  # pylint: disable=no-self-use
        """
        Processes incoming LTI requests
        """
        if not hasattr(request, "LTI"):
            raise ImproperlyConfigured("LTI middleware not installed")
        if "course_roles" not in request.session:
            request.session["course_roles"] = {}

        initial_lti_request = (request.method == "POST" and
                               request.POST.get("lti_message_type") == "basic-lti-launch-request")
        request.initial_lti_request = initial_lti_request
        if initial_lti_request:
            if not request.user.is_authenticated():
                # Raise 400; user is using bad LTI credentials
                raise SuspiciousOperation("Bad LTI credentials")
            if not request.LTI.get("context_id"):
                # Raise a 400 error
                raise SuspiciousOperation("No context_id in LTI parameters")
            if not request.LTI.get("resource_link_id"):
                # Raise a 400 error
                raise SuspiciousOperation("No resource_link_id in LTI parameters")
            if not request.LTI.get("lis_outcome_service_url"):
                return redirect("not_graded_block_error_page")
            # On the initial request, we have potentially gotten new information
            # from edX; update the database accordingly
            # request.LTI["lis_outcome_service_url"]
            course, _ = Course.objects.get_or_create(edx_id=request.LTI["context_id"])
            due_date = request.POST.get("custom_component_due_date")
            if due_date:
                due_date = parse_datetime(due_date)
            name = request.POST.get("custom_component_display_name", request.LTI["resource_link_id"])
            defaults = {"course": course, "due_date": due_date, "name": name}
            Assignment.objects.update_or_create(
                edx_id=request.LTI["resource_link_id"],
                defaults=defaults
            )
            if any([r for r in self.ADMIN_ROLES if r in request.LTI.get("roles", [])]):
                course.administrators.add(request.user)
                Grader.objects.filter(user=request.user, course=course).delete()
                Student.objects.filter(user=request.user, course=course).delete()
            else:
                course.administrators.remove(request.user)
                # Ensure the student object exists; graders also should have a
                # student object, since they are promoted from students and
                # if they are ever demoted, their student data should still exist
                Student.objects.get_or_create(course=course, user=request.user)
            # We only check for role on the initial LTI request since the user's session in our tool
            # is expected to be short-lived enough to not warrant checking on every request.
            # We also need to cast str on course.id because the url parameters are passed as string
            # to the decorator and views.
            request.session["course_roles"][str(course.id)] = get_role(request.user, course.id)
