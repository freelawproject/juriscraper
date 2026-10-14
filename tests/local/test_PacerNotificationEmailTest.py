import os

from typing_extensions import override

from juriscraper.pacer.email import NotificationEmail, S3NotificationEmail
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase

TESTS_ROOT_EXAMPLES_PACER_NEF = os.path.join(TESTS_ROOT_EXAMPLES_PACER, "nef")
TESTS_ROOT_EXAMPLES_PACER_NEF_S3 = os.path.join(
    TESTS_ROOT_EXAMPLES_PACER, "nef/s3"
)
TESTS_ROOT_EXAMPLES_PACER_NDA_S3 = os.path.join(
    TESTS_ROOT_EXAMPLES_PACER, "nda"
)


class PacerNotificationEmailTest(PacerParseTestCase):
    @override
    def setUp(self) -> None:
        self.maxDiff = 200000

    def test_notification_emails(self) -> None:
        self.parse_files(
            TESTS_ROOT_EXAMPLES_PACER_NEF, "*.html", NotificationEmail
        )


class S3PacerNotificationEmailTest(PacerParseTestCase):
    @override
    def setUp(self) -> None:
        self.maxDiff = 200000

    def test_notification_emails_s3(self) -> None:
        self.parse_files(
            TESTS_ROOT_EXAMPLES_PACER_NEF_S3, "*.txt", S3NotificationEmail
        )


class S3PacerNdaNotificationEmailTest(PacerParseTestCase):
    @override
    def setUp(self) -> None:
        self.maxDiff = 200000

    def test_notification_emails_s3(self) -> None:
        self.parse_files(
            TESTS_ROOT_EXAMPLES_PACER_NDA_S3, "*.txt", S3NotificationEmail
        )
