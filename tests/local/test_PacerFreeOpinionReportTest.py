import os

from juriscraper.lib.exceptions import ParsingException
from juriscraper.lib.html_utils import get_html_parsed_text
from juriscraper.pacer.free_documents import FreeOpinionReport
from tests import TESTS_ROOT_EXAMPLES_PACER
from tests.local.PacerParseTestCase import PacerParseTestCase

TESTS_ROOT_EXAMPLES_PACER_FREE_OPINION_REPORT = os.path.join(
    TESTS_ROOT_EXAMPLES_PACER, "free_opinion_report"
)


class PacerFreeOpinionReportTest(PacerParseTestCase):
    def setUp(self):
        self.maxDiff = 200000

    def test_free_opinion_report(self):
        self.parse_files(
            TESTS_ROOT_EXAMPLES_PACER_FREE_OPINION_REPORT,
            "*.html",
            FreeOpinionReport,
        )

    def test_reported_opinion_count(self):
        """reported_opinion_count returns PACER's own "Total number of
        opinions reported", which is independent of how many rows we parse.

        cand_2 is a real example where PACER reports 52 opinions but only 12
        rows are parsable: exactly the silent gap this count exists to expose.
        """
        # (fixture, expected reported count, expected parsed rows)
        cases = [
            ("areb_1", 1, 1),
            ("cacd_1", 2, 2),
            ("cand_2", 52, 12),
            # insb_1: a complete four-column page whose single opinion row has
            # an unlinked Doc. # cell. It must parse (pacer_doc_id=None) rather
            # than aborting the whole report. See issue #2053.
            ("insb_1", 1, 1),
        ]
        for fixture, reported, parsed in cases:
            with self.subTest(fixture=fixture):
                court = fixture.rsplit("_", 1)[0]
                report = FreeOpinionReport(court)
                path = os.path.join(
                    TESTS_ROOT_EXAMPLES_PACER_FREE_OPINION_REPORT,
                    f"{fixture}.html",
                )
                with open(path, encoding="utf-8") as f:
                    report._parse_text(f.read())
                self.assertEqual(report.reported_opinion_count, reported)
                self.assertEqual(len(report.data), parsed)

    def test_missing_banner_raises_parsing_exception(self):
        """A page missing the "Total number of opinions reported" banner
        (truncation / unknown layout) raises a dedicated ParsingException
        instead of a bare IndexError, so it stops sharing a Sentry fingerprint
        with real parse bugs. See issue #2053.
        """
        tree = get_html_parsed_text(
            "<html><body><p>No banner here.</p></body></html>"
        )
        with self.assertRaises(ParsingException):
            FreeOpinionReport._get_reported_opinion_count(tree)

    def test_unparsable_row_is_skipped_not_fatal(self):
        """A single malformed row must not abort the whole report: it is
        skipped and logged loudly, while the other rows still parse. See
        issue #2053.
        """
        html = """
        <html><body>
        <b>Total number of opinions reported:</b> 2<br>
        <table>
          <tr><th>Case</th><th>Date</th><th>Doc</th><th>Description</th></tr>
          <tr valign=top>
            <td><a href='/cgi-bin/DktRpt.pl?500739'>08-50533 French Design Jewelry, Inc. v. Downey</a></td>
            <td>08/20/2009</td>
            <td align=center>40</td>
            <td>Findings of Fact (re: Doc # <a href='https://ecf.insb.uscourts.gov/doc1/072012916914'>25</a>)</td>
          </tr>
          <tr><td>malformed row with no date cell</td></tr>
        </table>
        </body></html>
        """
        report = FreeOpinionReport("insb")
        report._parse_text(html)
        with self.assertLogs("juriscraper.lib.log_tools", level="ERROR") as cm:
            data = report.data
        # The good row survives; the malformed row is dropped.
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["docket_number"], "08-50533")
        # The skip was logged loudly, naming the offending row.
        log_text = "\n".join(cm.output)
        self.assertIn("Skipping unparsable row", log_text)
        self.assertIn("malformed row with no date cell", log_text)
