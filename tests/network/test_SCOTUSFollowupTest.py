import re
from pathlib import Path
from unittest import TestCase

import responses
from requests.exceptions import HTTPError

from juriscraper.scotus import SCOTUSEmail
from tests import TESTS_ROOT_EXAMPLES_SCOTUS


class SCOTUSFollowupTest(TestCase):
    """Ensure the handle_email method works as expected."""

    def setUp(self):
        self.test_root = Path(TESTS_ROOT_EXAMPLES_SCOTUS) / "email"
        self.response = responses.add(
            method="GET", url=re.compile(r".+"), status=404
        )

    def run_test_on_email(self, email_path: Path):
        with open(email_path) as f:
            scotus_email_scraper = SCOTUSEmail()
            scotus_email_scraper._parse_text(f.read())
            try:
                scotus_email_scraper.handle_email()
            except HTTPError:
                # We expect an exception to be raised because we gave the scraper a 404
                pass

    @responses.activate
    def test_handle_email(self):
        self.run_test_on_email(self.test_root / "25-250.eml")
        self.assertEqual(self.response.call_count, 1)
        self.assertEqual(
            self.response.calls[-1].request.url,
            "https://www.supremecourt.gov/search.aspx?filename=/docket/DocketFiles/html/Public/25-250.html",
        )

        self.run_test_on_email(self.test_root / "25-261.eml")
        self.assertEqual(self.response.call_count, 2)
        self.assertEqual(
            self.response.calls[-1].request.url,
            "https://www.supremecourt.gov/search.aspx?filename=/docket/DocketFiles/html/Public/25-261.html",
        )

        self.run_test_on_email(self.test_root / "25a561-confirmation.eml")
        self.assertEqual(self.response.call_count, 3)
        self.assertEqual(
            self.response.calls[-1].request.url,
            "http://file.supremecourt.gov/casenotification/update?verify=CfDJ8LWjh78o-U5EigyPTWy9BmekjhR9plnZeYQHVl3uPceov95hvtFvqNhiJMMqHBzJV2ghZqBPHNh5RsKiWpg5xIivNeMJY6khyqOvoh-hr-GWniqjbqooFYeevAFYHzSBQhlX_vMY2mIJORl9dYZAaLJvbk-JFWLANLnh3vaPhtAknU6xszMVXJwPqQNU2onUC7VoP-YN_pV3k6UXmQvUziwuPaKuwgWOogpRaNQt1lapNhv6zXvL8zIJnH-nCnZeom2o2g7odXotLrdvau4p1xtZ6lOzboGltJGV0LTuxQFT",
        )
