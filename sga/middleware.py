"""
Custom middleware
"""

from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.utils.dateparse import parse_datetime

from sga.models import Course, Assignment, Student, Grader
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
        if not hasattr(request.session, "course_rolls"):
            request.session.course_rolls = {}

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

            # On the initial request, we have potentially gotten new information
            # from edX; update the database accordingly
            # request.LTI["lis_outcome_service_url"]
            course, _ = Course.objects.get_or_create(edx_id=request.LTI["context_id"])
            due_date = request.POST.get("custom_component_due_date")
            if due_date:
                due_date = parse_datetime(due_date)
            defaults = {"course": course, "due_date": due_date,
                        "name": request.POST.get("custom_component_display_name")}
            Assignment.objects.update_or_create(
                edx_id=request.LTI["resource_link_id"],
                defaults=defaults
            )
            if "Instructor" in request.LTI.get("roles", []):
                course.administrators.add(request.user)
                Grader.objects.filter(user=request.user, course=course).delete()
                Student.objects.filter(user=request.user, course=course).delete()
            else:
                course.administrators.remove(request.user)
                # Ensure the student object exists; graders also should have a
                # student object, since they are promoted from students and
                # if they are ever demoted, their student data should still exist
                Student.objects.get_or_create(course=course, user=request.user)
            # We only check for roll on the initial LTI request since the user's session
            # in our tool is expected to be short-lived enough to not warrant
            # checking on every request
            request.session.course_rolls[course.id] = get_roll(request.user, course)


def get_roll(user, course):
    """ Returns the roll a user has in a course given the course id """
    if user.administrator_courses.filter(id=course.id).count():
        return Roles.admin
    elif user.grader_courses.filter(id=course.id).count():
        return Roles.grader
    else:
        return Roles.student
