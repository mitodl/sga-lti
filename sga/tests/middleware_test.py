"""
Tests for the SGAMiddleware
"""
from django.core.exceptions import ImproperlyConfigured
from mock import MagicMock

from sga.middleware import SGAMiddleware
from sga.tests.common import SGATestCase


class MiddlewareTest(SGATestCase):
    """
    Tests for the SGAMiddleware
    """

    def get_test_request(self):
        """ Sets up a mock request object """
        request = MagicMock()
        request.LTI = {
            "context_id": "test_course",
            "resource_link_id": "test_assignment",
            "user_id": "test_user_id",
        }
        request.method = "POST"
        request.POST = {"lti_message_type": "basic-lti-launch-request"}
        request.user = self.get_test_user()
        return request

    def test_middleware_configuration_check(self):
        """ Test that the middleware doesn't work without and LTI parameter on request """
        request = self.client.request()
        middleware = SGAMiddleware()
        self.assertRaises(ImproperlyConfigured, middleware.process_request, request)

    def test_middleware(self):
        """ Test that the middleware sets request params """
        request = self.get_test_request()
        middleware = SGAMiddleware()
        middleware.process_request(request)
        self.assertTrue(request.initial_lti_request)
        self.assertTrue(self.get_test_course().has_student(self.get_test_user()))
