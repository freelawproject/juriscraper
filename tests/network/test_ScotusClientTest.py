#!/usr/bin/env python

import datetime
import unittest

from juriscraper.lib.test_utils import MockResponse
from juriscraper.dockets.united_states.federal_appellate.scotus import (
    clients,
    scotus_docket,
    docket_search as ds,
)


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


@unittest.skip("All URIs passed on 2024-03-28")
class ScotusClientTest(unittest.TestCase):
    """Test the download client shared by SCOTUS modules."""

    def test_valid_uri_downloads(self):
        """Known good URIs as of 2024-03-28."""
        URIs = (
            "https://www.supremecourt.gov/",
            "https://www.supremecourt.gov/RSS/Cases/JSON/23-181.json",
            "https://www.supremecourt.gov/DocketPDF/23/23-181/276036/20230823151847724_Word%20Count%20Petition%20for%20Writ%20Harrison.pdf",
            "https://www.supremecourt.gov/docket/docket.aspx",
            "https://www.supremecourt.gov/orders/ordersofthecourt/",
        )
        for uri in URIs:
            with self.subTest(uri=uri):
                response = clients.download_client(uri)
                self.assertTrue(response.ok)


@unittest.skip("All URIs passed on 2024-03-29")
class ScotusDownloadManagerTest(unittest.TestCase):
    """Test the download managers."""

    def setUp(self):
        self.test_docket_numbers = [
            "23-175",  # Grant's Pass; lots of entries
            "23A1",  # Simple application docket
            "23M1",  # Motion denied on first day of term
            "22O141",  # An 'Orig.' case; not many of these
            "22-6592",  # JSON missing final docket entry 2023-02-21
        ]

    def test_valid_docket_downloads(self):
        """Known good docket numbers as of 2024-03-29."""
        responses = scotus_docket.linear_download(self.test_docket_numbers)
        for i, r in enumerate(responses):
            with self.subTest(r=r):
                response = r
                self.assertTrue(response.ok)
                docket = response.json()
                case_number = docket.get("CaseNumber")
                self.assertEqual(
                    self.test_docket_numbers[i], case_number.rstrip()
                )


@unittest.skip("All passed on 2024-03-29")
class ScotusOrdersDownloadTest(unittest.TestCase):
    """Test the Orders of the Court download managers."""

    def setUp(self):
        self.sample_order_pdfs = (
            "https://www.supremecourt.gov/orders/courtorders/032024zr1_olp1.pdf",
            "https://www.supremecourt.gov/orders/courtorders/032524zor_4h25.pdf",
        )

    def test_orders_page_download(self):
        """Download https://www.supremecourt.gov/orders/ordersofthecourt/"""
        instance = ds.SCOTUSOrders(2023, cache_pdfs=False)
        instance.orders_page_download()
        self.assertIsNotNone(instance.homepage_response)
        self.assertIsInstance(
            instance.homepage_response, clients.requests.Response
        )

    def test_orders_page_download_304(self):
        """Try the Orders home page with the 'If-Modified-Since' header set."""
        instance = ds.SCOTUSOrders(2023, cache_pdfs=False)
        instance.orders_page_download(
            since_timestamp=datetime.datetime.now(tz=datetime.timezone.utc)
        )
        self.assertIsNotNone(instance.homepage_response)
        self.assertIsInstance(
            instance.homepage_response, clients.requests.Response
        )
        # this should only fail if page is updated as query executes
        self.assertTrue(instance.homepage_response.status_code == 304)

    def test_order_pdf_download(self):
        """Download individual PDFs."""
        instance = ds.SCOTUSOrders(2023, cache_pdfs=False)
        for uri in self.sample_order_pdfs:
            with self.subTest(uri=uri):
                response = instance.order_pdf_download(uri)
                self.assertTrue(response.content[:4] == b"%PDF")

    def test_get_orders(self):
        """Orders scraping manager."""
        instance = ds.SCOTUSOrders(2023, cache_pdfs=True)
        kargs = dict(
            earliest="2024-03-06",
            latest="2024-03-06",
            include_misc=True,
            delay=0.25,
        )
        # run manager method
        instance._get_orders(**kargs)
        # check side effects
        self.assertIsNotNone(instance.homepage_response)
        self.assertNotEqual(instance.order_meta, [])
        self.assertIsNotNone(instance._pdf_cache)
        self.assertTrue(tuple(instance._pdf_cache)[0].content[:4] == b"%PDF")
        self.assertEqual(instance._docket_numbers, set(["23-411"]))
        self.assertEqual(instance.docket_numbers(), ["23-411"])


class ScotusFullTextSearchDownloadTest(unittest.TestCase):
    """Test the Docket Search download managers."""

    def setUp(self):
        self.test_instance = ds.DocketFullTextSearch.date_query("2024-04-01")

    @unittest.skip("Passed on 2024-03-30")
    def test_full_text_search_page(self):
        """Download https://www.supremecourt.gov/docket/docket.aspx"""
        response = self.test_instance.full_text_search_page()
        self.assertIsInstance(response, clients.requests.Response)
        self.assertTrue("Docket Search" in response.text)

    def test_search_query(self):
        """Send POST full text search query. Use 2024-02-29 because there were
        relatively few matches for the search term."""
        instance = ds.DocketFullTextSearch.date_query("2024-02-29")
        instance.search_query()
        self.assertIsNot(instance.query_responses, [])
        self.assertIsInstance(
            instance.query_responses[0], ds.requests.Response
        )
        self.assertTrue("Docket Search" in instance.query_responses[0].text)

    # TODO: figure out mocking
    def test_pager(self):
        """Download 2,...,n pages of search results"""
        pass

    def test_scrape(self):
        """Scraping manager for Docket Search."""
        instance = ds.DocketFullTextSearch.date_query("2024-02-29")
        instance.scrape()
        for r in instance.query_responses:
            with self.subTest(r=r):
                self.assertIsInstance(r, ds.requests.Response)
                self.assertTrue(r.ok)
                self.assertTrue("Docket Search" in r.text)
