"""
Test management commands
"""
from io import StringIO

from sga.management.commands.createmockdata import CreateMockDataCommand
from sga.tests.common import SGATestCase


class ManagementTest(SGATestCase):
    """
    Class for management tests
    """
    def test_create_mock_data(self):
        """
        Test create_mock_data command
        """
        out = StringIO()
        command = CreateMockDataCommand()
        command.execute(stdout=out)
        self.assertIn("Successfully created mock data.", out.getvalue())
