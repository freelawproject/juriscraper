from pathlib import Path
from unittest import IsolatedAsyncioTestCase, mock

from httpx import HTTPError, Request, Response

from juriscraper.scotus import SCOTUSEmail
from tests import TESTS_ROOT_EXAMPLES_SCOTUS


class SCOTUSFollowupTest(IsolatedAsyncioTestCase):
    """Ensure the handle_email method works as expected."""

    def setUp(self):
        self.test_root = Path(TESTS_ROOT_EXAMPLES_SCOTUS) / "email"

    async def run_test_on_email(self, email_path: Path):
        with open(email_path) as f:
            scotus_email_scraper = SCOTUSEmail()
            scotus_email_scraper._parse_text(f.read())
            try:
                await scotus_email_scraper.handle_email()
            except HTTPError:
                # We expect an exception to be raised because we gave the scraper a 404
                pass

    @mock.patch(
        "juriscraper.scotus.scotus_email.httpx.AsyncClient.get",
        new_callable=mock.AsyncMock,
    )
    async def test_handle_email(self, mock_get):
        mock_get.side_effect = lambda url, **kwargs: Response(
            404, request=Request("GET", url)
        )

        await self.run_test_on_email(self.test_root / "25-250.eml")
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(
            mock_get.call_args_list[-1].args[0],
            "https://www.supremecourt.gov/search.aspx?filename=/docket/DocketFiles/html/Public/25-250.html",
        )

        await self.run_test_on_email(self.test_root / "25-261.eml")
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(
            mock_get.call_args_list[-1].args[0],
            "https://www.supremecourt.gov/search.aspx?filename=/docket/DocketFiles/html/Public/25-261.html",
        )

        await self.run_test_on_email(
            self.test_root / "25a561-confirmation.eml"
        )
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(
            mock_get.call_args_list[-1].args[0],
            "http://file.supremecourt.gov/casenotification/update?verify=CfDJ8LWjh78o-U5EigyPTWy9BmekjhR9plnZeYQHVl3uPceov95hvtFvqNhiJMMqHBzJV2ghZqBPHNh5RsKiWpg5xIivNeMJY6khyqOvoh-hr-GWniqjbqooFYeevAFYHzSBQhlX_vMY2mIJORl9dYZAaLJvbk-JFWLANLnh3vaPhtAknU6xszMVXJwPqQNU2onUC7VoP-YN_pV3k6UXmQvUziwuPaKuwgWOogpRaNQt1lapNhv6zXvL8zIJnH-nCnZeom2o2g7odXotLrdvau4p1xtZ6lOzboGltJGV0LTuxQFT",
        )
