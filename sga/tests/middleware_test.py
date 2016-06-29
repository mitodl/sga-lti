"""
Tests for the SGAMiddleware
"""
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.urlresolvers import reverse
from mock import MagicMock

from sga.backend.constants import Roles
from sga.middleware import SGAMiddleware
from sga.tests.common import SGATestCase, DEFAULT_LTI_PARAMS


class MiddlewareTest(SGATestCase):
    """
    Tests for the SGAMiddleware
    """

    def get_test_request(self):
        """
        Sets up a mock request object
        """
        request = MagicMock()
        request.LTI = dict(DEFAULT_LTI_PARAMS)
        request.method = "POST"
        request.POST = {
            "lti_message_type": "basic-lti-launch-request",
            "custom_component_display_name": "Not Scored Assignment"
        }
        request.session = {}
        request.user = self.get_test_user()
        return request

    def test_middleware_configuration_check(self):
        """
        Test that the middleware doesn't work without and LTI parameter on request
        """
        request = self.client.request()
        middleware = SGAMiddleware()
        self.assertRaises(ImproperlyConfigured, middleware.process_request, request)

    def test_middleware(self):
        """
        Test that the middleware sets request params
        """
        request = self.get_test_request()
        middleware = SGAMiddleware()
        middleware.process_request(request)
        self.assertTrue(request.initial_lti_request)
        course = self.get_test_course()
        course_id_str = str(course.id)
        self.assertIsNotNone(request.session["course_roles"].get(course_id_str))
        self.assertTrue(self.get_test_course().has_student(self.get_test_user()))
        self.assertFalse(self.get_test_course().has_grader(self.get_test_user()))
        self.assertFalse(self.get_test_course().has_admin(self.get_test_user()))

    def test_user_not_authenticated(self):
        """
        Test that the middleware does not allow an unauthenticated user through
        """
        request = self.get_test_request()
        request.user = AnonymousUser()
        middleware = SGAMiddleware()
        self.assertRaisesMessage(
            SuspiciousOperation,
            "Bad LTI credentials",
            middleware.process_request,
            request
        )

    def test_improper_lti_configuration(self):
        """
        Test that the middleware does not allow improper LTI parameter configurations
        """
        request = self.get_test_request()
        request.LTI.pop("resource_link_id")
        middleware = SGAMiddleware()
        self.assertRaisesMessage(
            SuspiciousOperation,
            "No resource_link_id in LTI parameters",
            middleware.process_request,
            request
        )
        # We can pop "context_id" and test it here because the check for "context_id" precedes "resource_link_id"
        request.LTI.pop("context_id")
        self.assertRaisesMessage(
            SuspiciousOperation,
            "No context_id in LTI parameters",
            middleware.process_request,
            request
        )

    def test_ungraded_block_redirect(self):
        """
        Test that the middleware redirects if it's embedded in an ungraded block
        """
        # Must change the default lti_params and POST request to spoof initial_lti_request
        lti_params = DEFAULT_LTI_PARAMS
        lti_params.pop("lis_outcome_service_url")
        self.do_test_successful_view(
            reverse("sga_index"),
            Roles.none,
            template="sga/ungraded_block_error_page.html",
            lti_params=lti_params,
            method="post",
            post_params={"lti_message_type": "basic-lti-launch-request"}
        )

    def test_admin_LTI_request(self):
        """
        Test that an LTI request from an "Instructor" links the user to the course as an admin
        """
        request = self.get_test_request()
        request.LTI["roles"] = ["Instructor"]
        middleware = SGAMiddleware()
        middleware.process_request(request)
        self.assertTrue(request.initial_lti_request)
        self.assertFalse(self.get_test_course().has_student(self.get_test_user()))
        self.assertFalse(self.get_test_course().has_grader(self.get_test_user()))
        self.assertTrue(self.get_test_course().has_admin(self.get_test_user()))

    def test_due_date_parsing(self):
        """
        Test that parsing of due date from LTI POST params works
        """
        request = self.get_test_request()
        request.POST["custom_component_due_date"] = "2016-06-30 00:00:00"
        middleware = SGAMiddleware()
        middleware.process_request(request)
        self.assertTrue(request.initial_lti_request)
        self.assertTrue(self.get_test_course().has_student(self.get_test_user()))
        self.assertFalse(self.get_test_course().has_grader(self.get_test_user()))
        self.assertFalse(self.get_test_course().has_admin(self.get_test_user()))
