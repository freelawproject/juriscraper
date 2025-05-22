import unittest
from unittest import mock

from juriscraper.pacer import CaseQuery, PacerSession
from tests.network import get_pacer_session


class PacerSessionTest(unittest.TestCase):
    """Test the PacerSession wrapper class"""

    def setUp(self):
        self.session = get_pacer_session()

    def test_data_transformation(self):
        """Test our data transformation routine for building out PACER-compliant
        multi-part form data
        """
        data = {"case_id": 123, "case_type": "something"}
        expected = {"case_id": (None, 123), "case_type": (None, "something")}
        output = self.session._prepare_multipart_form_data(data)
        self.assertEqual(output, expected)

    @mock.patch("juriscraper.pacer.http.requests.Session.post")
    def test_ignores_non_data_posts(self, mock_post):
        """Test that POSTs without a data parameter just pass through as normal.

        :param mock_post: mocked Session.post method
        """
        data = {"name": ("filename", "junk")}

        self.session.post("https://free.law", files=data, auto_login=False)

        self.assertTrue(
            mock_post.called, "request.Session.post should be called"
        )
        self.assertEqual(
            data,
            mock_post.call_args[1]["files"],
            "the data should not be changed if using a files call",
        )

    @mock.patch("juriscraper.pacer.http.requests.Session.post")
    def test_transforms_data_on_post(self, mock_post):
        """Test that POSTs using the data parameter get transformed into PACER's
        delightfully odd multi-part form data.

        :param mock_post: mocked Session.post method
        """
        data = {"name": "dave", "age": 33}
        expected = {"name": (None, "dave"), "age": (None, 33)}

        self.session.post("https://free.law", data=data, auto_login=False)

        self.assertTrue(
            mock_post.called, "request.Session.post should be called"
        )
        self.assertNotIn(
            "data",
            mock_post.call_args[1],
            "we should intercept data arguments",
        )
        self.assertEqual(
            expected,
            mock_post.call_args[1]["files"],
            "we should transform and populate the files argument",
        )

    @mock.patch("juriscraper.pacer.http.requests.Session.post")
    def test_sets_default_timeout(self, mock_post):
        self.session.post("https://free.law", data={}, auto_login=False)

        self.assertTrue(
            mock_post.called, "request.Session.post should be called"
        )
        self.assertIn(
            "timeout",
            mock_post.call_args[1],
            "we should add a default timeout automatically",
        )
        self.assertEqual(
            300, mock_post.call_args[1]["timeout"], "default should be 300"
        )

    def test_scraper_has_session_attribute(self):
        report = CaseQuery("cand", PacerSession())
        try:
            report.session  # noqa: B018
        except AttributeError:
            self.fail("Did not have session attribute on CaseQuery object.")
