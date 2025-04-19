#!/usr/bin/env python

import datetime
import os
import unittest

from juriscraper.lib.test_utils import MockResponse
from juriscraper.dockets.united_states.federal_appellate.scotus import (
    docket_search as ds,
)
from tests import TESTS_ROOT_EXAMPLES_SCOTUS


class YAMockResponse(MockResponse):
    """Mock a Request Response"""

    def __init__(
        self,
        status_code,
        content=None,
        headers=None,
        request=None,
        url=None,
        reason: bytes = None,
    ):
        self.status_code = status_code
        self._content = content
        self.headers = headers
        self.request = request
        self.encoding = "utf-8"
        self.reason = reason
        self.url = url


class ScotusOrdersTest(unittest.TestCase):
    """Test the SCOTUS Orders of the Court manager and parser."""

    def setUp(self):
        with open(
            os.path.join(TESTS_ROOT_EXAMPLES_SCOTUS, "scotus_orders_home.html"),
            "rb",
        ) as _hp:
            self.orders_home = _hp.read()

        with open(
            os.path.join(TESTS_ROOT_EXAMPLES_SCOTUS, "orders_list_20240220.pdf"),
            "rb",
        ) as _ol:
            self.orders_list_pdf = _ol.read()

        with open(
            os.path.join(TESTS_ROOT_EXAMPLES_SCOTUS, "misc_order_20240222.pdf"),
            "rb",
        ) as _mo:
            self.misc_order_pdf = _mo.read()

        self.pdf_links = (
            "https://www.supremecourt.gov/orders/courtorders/032024zr1_olp1.pdf",
            "https://www.supremecourt.gov/orders/courtorders/032524zor_4h25.pdf",
        )

    def test_instance(self):
        """Instantiate SCOTUSOrders"""
        test_instance = ds.SCOTUSOrders(2023)
        self.assertIsInstance(test_instance, ds.SCOTUSOrders)

    def test_order_url_regex(self):
        """Extracts the date an order was published from its URI."""
        expected = (("03", "20", "24", "zr"), ("03", "25", "24", "zor"))

        for i, uri in enumerate(self.pdf_links):
            with self.subTest(uri=uri):
                match_obj = ds.order_url_date_regex.search(uri)
                self.assertTrue(match_obj)
                self.assertTrue(len(match_obj.groups()) == 4)
                self.assertTupleEqual(expected[i], match_obj.groups())

    def test_order_url_regex_fed_rules(self):
        """Identify URI of federal judicial rules orders that we don't want."""
        URIs = (
            "https://www.supremecourt.gov/orders/courtorders/frap23_qol1.pdf",
            "https://www.supremecourt.gov/orders/courtorders/frbk23_4315.pdf",
            "https://www.supremecourt.gov/orders/courtorders/frcv23_3eah.pdf",
            "https://www.supremecourt.gov/orders/courtorders/frcr23_d1pf.pdf",
            "https://www.supremecourt.gov/orders/courtorders/frev23_5468.pdf",
        )
        for uri in URIs:
            with self.subTest(uri=uri):
                match_obj = ds.fedrules_regex.search(uri)
                self.assertTrue(match_obj)

    def test_orders_link_parser(self):
        """Take an HTML string from the Orders page and return a list of Order URLs."""
        instance = ds.SCOTUSOrders(2023)
        result = instance.orders_link_parser(self.orders_home)
        self.assertIsInstance(result, list)
        for uri in self.pdf_links:
            # these URIs were taken from the 2023 term Orders home page
            with self.subTest(uri=uri):
                self.assertIn(uri, result)

    def test_parse_orders_page(self):
        """Extract URLs for individual order documents."""
        expected_url = (
            "https://www.supremecourt.gov/orders/courtorders/032524zor_4h25.pdf"
        )
        instance = ds.SCOTUSOrders(2023)
        response = YAMockResponse(status_code=200, headers={}, content=self.orders_home)
        # patch instance attribute
        instance.homepage_response = response
        self.assertIsInstance(instance.homepage_response.text, str)
        # run parser
        instance.parse_orders_page()
        self.assertNotEqual(instance.order_meta, [])
        self.assertEqual(instance.order_meta[0]["url"], expected_url)
        self.assertEqual(len(instance.order_meta), 69)

    def test_order_pdf_parser(self):
        """Extract docket numbers from an Orders PDF."""
        instance = ds.SCOTUSOrders(2023)
        expected1 = ("23-467", "23M49", "22-7860", "22-7871")

        result_misc = instance.order_pdf_parser(self.misc_order_pdf)
        self.assertTrue(result_misc == {"23A741"})
        result_list = instance.order_pdf_parser(self.orders_list_pdf)
        for docketnum in expected1:
            with self.subTest(docketnum=docketnum):
                self.assertIn(docketnum, result_list)

    def test_term_constraints(self):
        """Allows fine-tuning of which Order dates to download from."""
        test_terms = (2023, 2023, 2022)
        test_dates = (
            dict(earliest=None, latest=None),
            dict(earliest="2024-02-28", latest="2023-11-30"),
            dict(earliest="2022-09-28", latest="2023-11-30"),
        )
        expected = (
            {"earliest": None, "latest": None},
            {
                "earliest": datetime.date(2023, 11, 30),
                "latest": datetime.date(2024, 2, 28),
            },
            {
                "earliest": datetime.date(2022, 10, 3),
                "latest": datetime.date(2023, 10, 1),
            },
        )
        for t, exp, kargs in zip(test_terms, expected, test_dates):
            with self.subTest(t=t, exp=exp, kargs=kargs):
                instance = ds.SCOTUSOrders(t)
                result = instance._term_constraints(**kargs)
                self.assertDictEqual(exp, result)


class ScotusDocketFullTextSearchTest(unittest.TestCase):
    """Test the SCOTUS Docket Search manager and parser."""

    def setUp(self):
        with open(
            os.path.join(
                TESTS_ROOT_EXAMPLES_SCOTUS,
                "scotus_docket_search_home.aspx",
            ),
            "r",
        ) as _f:
            self.homepage = _f.read()

        with open(
            os.path.join(
                TESTS_ROOT_EXAMPLES_SCOTUS,
                "scotus_docket_search_results_page1.aspx",
            ),
            "r",
        ) as _f:
            self.page1 = _f.read()

        with open(
            os.path.join(
                TESTS_ROOT_EXAMPLES_SCOTUS,
                "scotus_docket_search_results_page2.aspx",
            ),
            "r",
        ) as _f:
            self.page2 = _f.read()

        self.test_instance = ds.DocketFullTextSearch("")

    def test_instance(self):
        """Instantiate DocketFullTextSearch"""
        self.assertIsInstance(self.test_instance, ds.DocketFullTextSearch)

    def test_classmethod_instantiation(self):
        """Instantiate DocketFullTextSearch using the `date_query` classmethod.
        This is the preferred method of instantiation."""
        instance = ds.DocketFullTextSearch.date_query("2024-04-01")
        self.assertIsInstance(instance, ds.DocketFullTextSearch)
        self.assertEqual(instance.search_string, "Apr 01, 2024")

    def test_search_page_metadata_parser(self):
        """Parses hidden fields from Docket Search page."""
        expected = {
            "ctl00_ctl00_RadScriptManager1_TSM": "",
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": "jkF4BYmzedCwenqv/sgNCVMXPauykip5wr1PKLEeK6c+FmoDUAqrCoqJc0jApuDzRjFl/iDlmwlcFBsgh165V+fwuqfo5fgTp3J/0Iy/0+e/ovzd1kt2jh0YAL6J6qA+",
            "__VIEWSTATEGENERATOR": "71826567",
        }
        meta_elements = self.test_instance.search_page_metadata_parser(self.homepage)
        self.assertDictEqual(meta_elements, expected)

    def test_page_count_parser1(self):
        """Take an HTML string from the docket search results."""
        expected = {"items": 499, "cur_pg": 1, "max_pg": 100}
        meta_elements = self.test_instance.page_count_parser(self.page1)
        self.assertDictEqual(meta_elements, expected)

    def test_page_count_parser2(self):
        """Take an HTML string from the docket search results."""
        expected = {"items": 499, "cur_pg": 2, "max_pg": 100}
        meta_elements = self.test_instance.page_count_parser(self.page2)
        self.assertDictEqual(meta_elements, expected)

    def test_docket_number_parser(self):
        """Take an HTML string from the docket search results and return
        a list of docket numbers."""
        expected1 = {"23-779", "23-726", "23-156", "23A769", "23-367"}
        expected2 = {"23-6803", "23A481", "22O141", "23-250", "23-463"}
        docket_numbers1 = self.test_instance.docket_number_parser(self.page1)
        docket_numbers2 = self.test_instance.docket_number_parser(self.page2)
        self.assertSetEqual(docket_numbers1, expected1)
        self.assertSetEqual(docket_numbers2, expected2)
