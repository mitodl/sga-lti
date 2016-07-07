"""
Custom middleware
"""
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils.dateparse import parse_datetime
from django_auth_lti.backends import LTIAuthBackend

from sga.backend.constants import STUDIO_USER_USERNAME, Roles
from sga.models import Course, Assignment, Student, Grader, Submission
from sga.backend.authentication import get_role


class SGAMiddleware(object):
    """
    Middleware for processing incoming LTI requests
    """
    ADMIN_ROLES = ["Administrator", "Instructor"]
    LTI_MIDDLEWARE_NOT_INSTALLED_MESSAGE = "LTI middleware not installed"
    UNSUCCESSFUL_LTI_AUTHENTICATION_MESSAGE = "Bad or missing LTI credentials"
    NO_CONTEXT_ID_MESSAGE = "No context_id in LTI parameters"
    NO_RESOURCE_LINK_ID_MESSAGE = "No resource_link_id in LTI parameters"
    REQUEST_USERNAME_FALSE_MESSAGE = '"Request user\'s username" must be set to True on this assignment.'

    def process_request(self, request):  # pylint: disable=no-self-use
        """
        Processes incoming LTI requests
        """
        if not hasattr(request, "LTI"):
            raise ImproperlyConfigured(self.LTI_MIDDLEWARE_NOT_INSTALLED_MESSAGE)
        if "course_roles" not in request.session:
            request.session["course_roles"] = {}
        if not request.lti_initial_request:
            # Not initial request, don't process
            return
        if not request.lti_authentication_successful:
            # Raise 400; user is using bad LTI credentials
            return HttpResponseBadRequest(self.UNSUCCESSFUL_LTI_AUTHENTICATION_MESSAGE)
        if not request.LTI.get("context_id"):
            # Raise a 400 error
            raise SuspiciousOperation(self.NO_CONTEXT_ID_MESSAGE)
        if not request.LTI.get("resource_link_id"):
            # Raise a 400 error
            raise SuspiciousOperation(self.NO_RESOURCE_LINK_ID_MESSAGE)
        if not request.LTI.get("lis_outcome_service_url"):
            return redirect("not_graded_block_error_page")
        if request.user.username == STUDIO_USER_USERNAME:
            return redirect("studio_message_page")
        if request.user.username.startswith(LTIAuthBackend.unknown_user_prefix):
            request.user.delete()
            return HttpResponseBadRequest(self.REQUEST_USERNAME_FALSE_MESSAGE)
        # On the initial request, we have potentially gotten new information
        # from edX; update the database accordingly
        # Course
        course, _ = Course.objects.get_or_create(edx_id=request.LTI["context_id"])
        # Assignment
        due_date = request.POST.get("custom_component_due_date")
        if due_date:
            due_date = parse_datetime(due_date)
        name = request.POST.get("custom_component_display_name", request.LTI["resource_link_id"])
        defaults = {"course": course, "due_date": due_date, "name": name}
        assignment, _ = Assignment.objects.update_or_create(
            edx_id=request.LTI["resource_link_id"],
            defaults=defaults
        )
        if any([r for r in self.ADMIN_ROLES if r in request.LTI.get("roles", [])]):
            course.administrators.add(request.user)
            Grader.objects.filter(user=request.user, course=course).delete()
            Student.objects.filter(user=request.user, course=course).delete()
        else:
            course.administrators.remove(request.user)
            # Ensure the student object exists; graders also should have a student object, since
            # they are promoted from students and if they are ever demoted, their student data
            # should still exist
            Student.objects.get_or_create(course=course, user=request.user)
            # If this user is a student, we need to generate a Submission object and store
            # grade submission information
            submission, _ = Submission.objects.get_or_create(student=request.user, assignment=assignment)
            submission.edx_url = request.LTI["lis_outcome_service_url"]
            submission.result_id = request.POST.get("lis_result_sourcedid")
            submission.consumer_key = request.POST.get("oauth_consumer_key")
            submission.save()

        # We only check for role on the initial LTI request since the user's session in our tool
        # is expected to be short-lived enough to not warrant checking on every request.
        # We also need to cast str on course.id because the url parameters are passed as string
        # to the decorator and views.
        user_role = get_role(request.user, course.id)
        request.session["course_roles"][str(course.id)] = user_role
        # Redirect edX launch to the appropriate page
        return self.redirect_edx_launch(user_role, course, assignment)

    @staticmethod
    def redirect_edx_launch(user_role, course, assignment):
        """
        Redirects edX launch to the appropriate page
        """
        if user_role == Roles.student:
            return redirect("view_submission_as_student", course_id=course.id, assignment_id=assignment.id)
        if user_role in [Roles.admin, Roles.grader]:
            return redirect("view_assignment", course_id=course.id, assignment_id=assignment.id)
        raise Exception("Bad role %s" % user_role)
