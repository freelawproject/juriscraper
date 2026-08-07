#!/usr/bin/env python3
"""
Unit tests for PACER docket description column detection.

Tests the _detect_description_column_index() methods in DocketReport
and DocketHistoryReport to ensure they correctly identify the description
column in various table layouts (2-column, 3-column, etc.).
"""

import unittest

from lxml import html

from juriscraper.pacer.docket_history_report import DocketHistoryReport
from juriscraper.pacer.docket_report import DocketReport
from juriscraper.pacer.http import PacerSession


class TestDocketReportColumnDetection(unittest.TestCase):
    """Test column detection in DocketReport."""

    def setUp(self):
        """Set up test fixtures."""
        self.session = PacerSession(username="test", password="test")

    def test_3_column_layout_standard(self):
        """Test detection with standard 3-column layout (Doc No, Date, Description)."""
        html_content = """
        <html>
        <body>
        <center><font size="+1">3:17-cr-00168-SLG-DMS</font> USA v. Salazar-Cardenas<br>
        <b>Date filed:</b> 12/07/2017<br>
        <b>Date of last filing:</b> 12/07/2017</center>
        <table>
        <tbody>
        <tr><th>No.</th><th>Date Filed</th><th>Docket Text</th></tr>
        <tr>
        <td>1</td>
        <td>11/16/2017</td>
        <td>Complaint filed by USA</td>
        </tr>
        <tr>
        <td>2</td>
        <td>11/17/2017</td>
        <td>Order granting motion</td>
        </tr>
        </tbody>
        </table>
        </body>
        </html>
        """
        report = DocketReport("akd", self.session)
        report.tree = html.fromstring(html_content)

        idx = report._detect_description_column_index()
        self.assertEqual(
            idx,
            2,
            "Expected description column at index 2 for 3-column layout",
        )

    def test_2_column_layout(self):
        """Test detection with 2-column layout (Date, Description)."""
        html_content = """
        <html>
        <body>
        <center><font size="+1">3:17-cr-00168-SLG-DMS</font> USA v. Salazar-Cardenas<br>
        <b>Date filed:</b> 12/07/2017<br>
        <b>Date of last filing:</b> 12/07/2017</center>
        <table>
        <tbody>
        <tr><th>Date Filed</th><th>Description</th></tr>
        <tr>
        <td>11/16/2017</td>
        <td>Complaint filed by USA</td>
        </tr>
        <tr>
        <td>11/17/2017</td>
        <td>Order granting motion</td>
        </tr>
        </tbody>
        </table>
        </body>
        </html>
        """
        report = DocketReport("test", self.session)
        report.tree = html.fromstring(html_content)

        idx = report._detect_description_column_index()
        self.assertEqual(
            idx,
            1,
            "Expected description column at index 1 for 2-column layout",
        )

    def test_description_header_variant(self):
        """Test detection with 'Description' header instead of 'Docket Text'."""
        html_content = """
        <html>
        <body>
        <table>
        <tbody>
        <tr><th>No.</th><th>Date</th><th>Description</th></tr>
        <tr>
        <td>1</td>
        <td>11/16/2017</td>
        <td>Motion to dismiss</td>
        </tr>
        </tbody>
        </table>
        </body>
        </html>
        """
        report = DocketReport("test", self.session)
        report.tree = html.fromstring(html_content)

        idx = report._detect_description_column_index()
        self.assertEqual(
            idx,
            2,
            "Expected description column at index 2 with 'Description' header",
        )

    def test_fallback_when_no_header(self):
        """Test fallback to index 2 when no description header is found."""
        html_content = """
        <html>
        <body>
        <table>
        <tbody>
        <tr><th>Column1</th><th>Column2</th><th>Column3</th></tr>
        <tr>
        <td>1</td>
        <td>11/16/2017</td>
        <td>Some text</td>
        </tr>
        </tbody>
        </table>
        </body>
        </html>
        """
        report = DocketReport("test", self.session)
        report.tree = html.fromstring(html_content)

        idx = report._detect_description_column_index()
        self.assertEqual(
            idx,
            2,
            "Expected fallback to index 2 when no description header found",
        )

    def test_caching_of_detected_index(self):
        """Test that the detected column index is cached."""
        html_content = """
        <html>
        <body>
        <table>
        <tbody>
        <tr><th>Date</th><th>Description</th></tr>
        <tr>
        <td>11/16/2017</td>
        <td>Test entry</td>
        </tr>
        </tbody>
        </table>
        </body>
        </html>
        """
        report = DocketReport("test", self.session)
        report.tree = html.fromstring(html_content)

        # First call should detect and cache
        idx1 = report._detect_description_column_index()
        # Second call should return cached value
        idx2 = report._detect_description_column_index()

        self.assertEqual(
            idx1, idx2, "Cached index should match initial detection"
        )
        self.assertEqual(idx1, 1, "Expected description at index 1")

    def test_case_insensitive_header_matching(self):
        """Test that header matching is case-insensitive."""
        html_content = """
        <html>
        <body>
        <table>
        <tbody>
        <tr><th>No.</th><th>Date</th><th>DOCKET TEXT</th></tr>
        <tr>
        <td>1</td>
        <td>11/16/2017</td>
        <td>Entry text</td>
        </tr>
        </tbody>
        </table>
        </body>
        </html>
        """
        report = DocketReport("test", self.session)
        report.tree = html.fromstring(html_content)

        idx = report._detect_description_column_index()
        self.assertEqual(
            idx, 2, "Expected case-insensitive matching of 'DOCKET TEXT'"
        )


class TestDocketHistoryReportColumnDetection(unittest.TestCase):
    """Test column detection in DocketHistoryReport."""

    def test_3_column_layout_history(self):
        """Test detection with standard 3-column layout in history report."""
        html_content = """
        <html>
        <body>
        <center><font size="+1">3:17-cr-00168-SLG-DMS</font> USA v. Salazar-Cardenas<br>
        <b>Date filed:</b> 12/07/2017<br>
        <b>Date of last filing:</b> 12/07/2017</center>
        <table>
        <tbody>
        <tr><th>Doc. No.</th><th>Dates</th><th>Description</th></tr>
        <tr>
        <td>1</td>
        <td>Filed & Entered: 11/16/2017</td>
        <td>Complaint</td>
        </tr>
        <tr>
        <td>2</td>
        <td>Filed & Entered: 11/16/2017</td>
        <td>Order</td>
        </tr>
        </tbody>
        </table>
        </body>
        </html>
        """
        report = DocketHistoryReport("akd")
        report.tree = html.fromstring(html_content)

        idx = report._detect_description_column_index_history()
        self.assertEqual(
            idx,
            2,
            "Expected description column at index 2 for 3-column history layout",
        )

    def test_2_column_layout_history(self):
        """Test detection with 2-column layout in history report."""
        html_content = """
        <html>
        <body>
        <center><font size="+1">3:17-cr-00168-SLG-DMS</font> USA v. Salazar-Cardenas<br>
        <b>Date filed:</b> 12/07/2017<br>
        <b>Date of last filing:</b> 12/07/2017</center>
        <table>
        <tbody>
        <tr><th>Dates</th><th>Description</th></tr>
        <tr>
        <td>Filed & Entered: 11/16/2017</td>
        <td>Complaint filed</td>
        </tr>
        <tr>
        <td>Filed & Entered: 11/16/2017</td>
        <td>Order issued</td>
        </tr>
        </tbody>
        </table>
        </body>
        </html>
        """
        report = DocketHistoryReport("test")
        report.tree = html.fromstring(html_content)

        idx = report._detect_description_column_index_history()
        self.assertEqual(
            idx,
            1,
            "Expected description column at index 1 for 2-column history layout",
        )

    def test_fallback_when_no_header_history(self):
        """Test fallback to index 2 when no description header is found in history report."""
        html_content = """
        <html>
        <body>
        <table>
        <tbody>
        <tr><th>Column1</th><th>Column2</th><th>Column3</th></tr>
        <tr>
        <td>1</td>
        <td>11/16/2017</td>
        <td>Some text</td>
        </tr>
        </tbody>
        </table>
        </body>
        </html>
        """
        report = DocketHistoryReport("test")
        report.tree = html.fromstring(html_content)

        idx = report._detect_description_column_index_history()
        self.assertEqual(
            idx,
            2,
            "Expected fallback to index 2 when no description header found in history",
        )


class TestColumnDetectionIntegration(unittest.TestCase):
    """Integration tests for column detection with actual docket entry parsing."""

    def setUp(self):
        """Set up test fixtures."""
        self.session = PacerSession(username="test", password="test")

    def test_docket_entries_use_detected_column_2col(self):
        """Test that docket entries correctly use detected column in 2-column layout."""
        html_content = """
        <html>
        <body>
        <center><font size="+1">1:20-cv-12345</font> Test Case<br>
        <b>Date filed:</b> 01/01/2020</center>
        <table>
        <tbody>
        <tr><th>Date Filed</th><th>Description</th></tr>
        <tr>
        <td>01/01/2020</td>
        <td>Test description text</td>
        </tr>
        </tbody>
        </table>
        </body>
        </html>
        """
        report = DocketHistoryReport("test")
        report.tree = html.fromstring(html_content)

        # Get docket entries which should use the detected column
        entries = report.docket_entries

        # Verify that the description was extracted from the correct column
        self.assertTrue(
            len(entries) > 0, "Should have at least one docket entry"
        )
        if len(entries) > 0:
            # The description should be from column index 1 (second column)
            self.assertIn(
                "Test description text",
                entries[0].get("short_description", ""),
            )

    def test_docket_entries_use_detected_column_3col(self):
        """Test that docket entries correctly use detected column in 3-column layout."""
        html_content = """
        <html>
        <body>
        <center><font size="+1">1:20-cv-12345</font> Test Case<br>
        <b>Date filed:</b> 01/01/2020</center>
        <table>
        <tbody>
        <tr><th>No.</th><th>Date Filed</th><th>Description</th></tr>
        <tr>
        <td>1</td>
        <td>01/01/2020</td>
        <td>Three column description</td>
        </tr>
        </tbody>
        </table>
        </body>
        </html>
        """
        report = DocketHistoryReport("test")
        report.tree = html.fromstring(html_content)

        # Get docket entries which should use the detected column
        entries = report.docket_entries

        # Verify that the description was extracted from the correct column
        self.assertTrue(
            len(entries) > 0, "Should have at least one docket entry"
        )
        if len(entries) > 0:
            # The description should be from column index 2 (third column)
            self.assertIn(
                "Three column description",
                entries[0].get("short_description", ""),
            )


if __name__ == "__main__":
    unittest.main()
