import os

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
