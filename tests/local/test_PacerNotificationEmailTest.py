import os

from juriscraper.pacer.email import NotificationEmail
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase

TESTS_ROOT_EXAMPLES_PACER_NEF = os.path.join(TESTS_ROOT_EXAMPLES_PACER, "nef")


class PacerNotificationEmailTest(PacerParseTestCase):
    def setUp(self):
        self.maxDiff = 200000

    def test_notification_emails(self):
        self.parse_files(
            TESTS_ROOT_EXAMPLES_PACER_NEF, "*.html", NotificationEmail
        )
