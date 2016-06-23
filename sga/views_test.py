"""
Test end to end django views.
"""
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model


class TestViews(TestCase):
    """
    Test that the views work as expected.
    """
    def setUp(self):
        """Common test setup"""
        super(TestViews, self).setUp()
        self.client = Client()
        UserModel = get_user_model()
        user, _ = UserModel.objects.get_or_create(username="test_user_id")
        lti_params = {
            "context_id": "test_course",
            "resource_link_id": "test_assignment",
            "user_id": "test_user_id",
        }
        session = self.client.session
        session["LTI_LAUNCH"] = lti_params
        session.save()
        self.client.force_login(user)

    def test_index_view(self):
        """Verify the index view is as expected"""
        response = self.client.get(reverse('sga-index'))
        self.assertContains(
            response,
            "Logged In As",
            status_code=200
        )
