"""Tests for the Los Angeles Superior Court tentative rulings parsers."""

import unittest
from datetime import date

from juriscraper.abstract_parser import ParserValidationError
from juriscraper.state.california.lasc.tentative_rulings import (
    TentativeRuling,
    TentativeRulingOptionsParser,
    TentativeRulingsParser,
    build_department_form_data,
)
from tests import TESTS_ROOT_EXAMPLES_STATES
from tests.local.lasc_pages import (
    CASE_NAME_STYLE,
    ruling_header,
    rulings_page,
)
from tests.local.PacerParseTestCase import PacerParseTestCase

EXAMPLES = (
    TESTS_ROOT_EXAMPLES_STATES / "california" / "lasc" / "tentative_rulings"
)


class LASCTentativeRulingsExampleTest(PacerParseTestCase):
    """Parse the pages captured from the court's site."""

    def setUp(self) -> None:
        self.maxDiff = 200000

    def test_rulings_pages(self) -> None:
        self.parse_files(EXAMPLES, "department_*.html", TentativeRulingsParser)

    def test_search_page(self) -> None:
        self.parse_files(
            EXAMPLES, "search_form*.html", TentativeRulingOptionsParser
        )


class LASCTentativeRulingsParserTest(unittest.TestCase):
    """Edge cases of splitting a rulings page."""

    def parse(self, page: str) -> list[TentativeRuling]:
        parser = TentativeRulingsParser("lasc")
        parser._parse_text(page)
        return parser.data

    def test_header_fields(self) -> None:
        [ruling] = self.parse(
            rulings_page(
                ruling_header("24nncv01819", "September  4, 2026", "309")
                + "Ruling."
            )
        )
        self.assertEqual(ruling.case_number, "24NNCV01819")
        self.assertEqual(ruling.hearing_date, date(2026, 9, 4))
        self.assertEqual(ruling.department, "309")

    def test_case_name_variants(self) -> None:
        cases: dict[str, tuple[str | None, str]] = {
            f"<span {CASE_NAME_STYLE}>#4 - HERNANDEZ vs GM LLC</span>": (
                "4",
                "HERNANDEZ vs GM LLC",
            ),
            f"<span {CASE_NAME_STYLE}>#11 -&nbsp;KELEDJIAN vs KOKCHYAN</span>": (
                "11",
                "KELEDJIAN vs KOKCHYAN",
            ),
            f"<span {CASE_NAME_STYLE}>POWELL vs WONG<br></span>": (
                None,
                "POWELL vs WONG",
            ),
            # The calendar number and name underlined as separate spans, the
            # name nested in a plain span that also wraps the ruling.
            (
                f"<span {CASE_NAME_STYLE}>#10 -&nbsp;</span>"
                f'<span style="white-space: normal;">'
                f"<span {CASE_NAME_STYLE}>AMEX vs YONG<br></span>"
            ): ("10", "AMEX vs YONG"),
            f"<span {CASE_NAME_STYLE}>24VECV02388 ADEL V MALIBU</span>": (
                None,
                "ADEL V MALIBU",
            ),
            "<span>Not a case name.</span>": (None, ""),
            "": (None, ""),
        }
        for opening, (calendar_number, case_name) in cases.items():
            with self.subTest(opening=opening):
                [ruling] = self.parse(
                    rulings_page(ruling_header() + opening + "<br><br>Ruling.")
                )
                self.assertEqual(ruling.calendar_number, calendar_number)
                self.assertEqual(ruling.case_name, case_name)

    def test_a_label_with_nothing_after_it(self) -> None:
        """A heading that ends on the bare label has no name to read, and
        failing to read one mustn't cost the page every ruling on it."""
        [ruling] = self.parse(rulings_page(ruling_header() + "Case Name"))

        self.assertEqual(ruling.case_name, "")
        self.assertEqual(ruling.case_number, "24NNCV01819")

    def test_typed_case_name_variants(self) -> None:
        """Courtrooms that don't underline the name type it into the ruling
        in their own layouts."""
        cases: dict[str, tuple[str | None, str]] = {
            "<p>CASE NAME: Chavez v. City of Rosemead, et al.</p>": (
                None,
                "Chavez v. City of Rosemead, et al.",
            ),
            "<p>CASE NAME: Cowell v. Corepower Yoga COMP. FILED: 04-27-26</p>": (
                None,
                "Cowell v. Corepower Yoga",
            ),
            # Word processors wrap their source mid-sentence.
            "<p>CASE\nNAME: Ara\nBekmezian v. General Motors LLC</p>": (
                None,
                "Ara Bekmezian v. General Motors LLC",
            ),
            (
                "<p>SUPERIOR COURT OF CALIFORNIA</p>"
                "<p>MIKHAIL SIRETSKIY, an individual,</p><p>Plaintiff,</p>"
                "<p>vs.</p><p>ALLA KUTZ, an individual; IGOR KUTZ, an "
                "individual and DOES 1 through 20, inclusive,</p>"
                "<p>Defendants.</p>"
            ): (None, "MIKHAIL SIRETSKIY v. ALLA KUTZ, et al."),
            (
                "<p>SHERRIE GOLDEN</p><p>Plaintiff,</p><p>Case No.:</p>"
                "<p>25TRCV04402</p><p>vs.</p><p>[Tentative] Granted</p>"
                "<p>TURO, INC.; and</p><p>DOES 1 through 50, inclusive,</p>"
                "<p>Defendant.</p>"
            ): (None, "SHERRIE GOLDEN v. TURO, INC., et al."),
            "<p>No. 8 - Artyom Harutyunyan v. Volvo Cars, LLC</p>": (
                "8",
                "Artyom Harutyunyan v. Volvo Cars, LLC",
            ),
            "<p>25STCV15519 Jae Ho Son v. Cenocore, Inc., et al</p>": (
                None,
                "Jae Ho Son v. Cenocore, Inc., et al",
            ),
            "<p>LAKE HUGHES v. COUNTY OF LOS ANGELES [25STCV05368]</p>": (
                None,
                "LAKE HUGHES v. COUNTY OF LOS ANGELES",
            ),
            "<p>Gomez v. Horiguchi, Case no.</p><p>26VECV02944</p>": (
                None,
                "Gomez v. Horiguchi",
            ),
            (
                "<p>The Court tenders the following tentative decision in "
                "the matter Robert Reed, et al. v. EQR-Vantage, LP, Los "
                "Angeles County Superior Court case number 26STCV15490.</p>"
            ): (None, "Robert Reed, et al. v. EQR-Vantage, LP"),
            # A middle initial is not a "v.".
            "<p>Defendants: Ray Vargas aka Ray V Vargas</p>": (None, ""),
            # Nor is a citation a caption.
            "<p>Smith v. Jones (2010) 50 Cal.4th 1.</p>": (None, ""),
        }
        for opening, (calendar_number, case_name) in cases.items():
            with self.subTest(opening=opening):
                [ruling] = self.parse(
                    rulings_page(ruling_header() + opening + "<p>Ruling.</p>")
                )
                self.assertEqual(ruling.calendar_number, calendar_number)
                self.assertEqual(ruling.case_name, case_name)

    def test_header_case_numbers(self) -> None:
        """The header's number is kept unless it is malformed and the ruling
        labels a Los Angeles case number."""
        cases = {
            # Cases transferred in keep their original county's number.
            ("30-2026-01564595", "<p>Ruling.</p>"): "30-2026-01564595",
            (
                "25STCV1892624STC",
                "<p>Case No.:</p><p>24STCV30415</p><p>Ruling.</p>",
            ): "24STCV30415",
            ("25STCV1892624STC", "<p>Ruling.</p>"): "25STCV1892624STC",
            (
                "24STCV09259",
                "<p>Consolidated with Case No.: 24STCV19183</p>",
            ): "24STCV09259",
        }
        for (header_number, ruling), case_number in cases.items():
            with self.subTest(header_number=header_number, ruling=ruling):
                [parsed] = self.parse(
                    rulings_page(ruling_header(header_number) + ruling)
                )
                self.assertEqual(parsed.case_number, case_number)

    def test_ruling_html_is_bounded(self) -> None:
        """A ruling ends at the site's separator, not at a rule inside it."""
        footnotes = '<hr align="left" size="1" width="33%"><p>[1] Note.</p>'
        first, last = self.parse(
            rulings_page(
                ruling_header("24NNCV01819")
                + f"<span {CASE_NAME_STYLE}>#1 - A vs B</span><br><br>First."
                + footnotes,
                ruling_header("26NNCV05273") + "<p>Last.</p>",
            )
        )
        self.assertEqual(first.ruling_html, f"First.{footnotes}")
        self.assertEqual(last.ruling_html, "<p>Last.</p>")

    def test_page_without_rulings(self) -> None:
        self.assertEqual(self.parse(rulings_page()), [])

    def test_empty_ruling_fails_validation(self) -> None:
        page = rulings_page(
            ruling_header() + f"<span {CASE_NAME_STYLE}>#1 - A vs B</span><br>"
        )
        with self.assertRaises(ParserValidationError):
            self.parse(page)


class LASCTentativeRulingOptionsTest(unittest.TestCase):
    """Reading the courtroom list and posting an option back."""

    SEARCH_PAGE = """
    <html><body>
      <form id="unrelated"><input type="hidden" name="other" value="no"></form>
      <form method="post" id="lascwebform">
        <input type="hidden" name="__VIEWSTATE" value="state">
        <input type="hidden" name="__EVENTVALIDATION" value="valid">
        <select name="ctl00$body$List2DeptDate" id="body_List2DeptDate">
          <option value="BH ,205,09/14/2026">(Beverly Hills Courthouse:  Dept. 205) September 14, 2026</option>
          <option value="garbage">Garbage</option>
          <option value="">Blank</option>
        </select>
      </form>
    </body></html>
    """

    def test_options(self) -> None:
        parser = TentativeRulingOptionsParser("lasc")
        parser._parse_text(self.SEARCH_PAGE)
        [option] = parser.data
        self.assertEqual(option.value, "BH ,205,09/14/2026")
        self.assertEqual(option.location_code, "BH")
        self.assertEqual(option.courthouse, "Beverly Hills Courthouse")
        self.assertEqual(option.department, "205")
        self.assertEqual(option.hearing_date, date(2026, 9, 14))

    def test_form_data_echoes_the_state_fields(self) -> None:
        self.assertEqual(
            build_department_form_data(self.SEARCH_PAGE, "BH ,205,09/14/2026"),
            {
                "__VIEWSTATE": "state",
                "__EVENTVALIDATION": "valid",
                "ctl00$body$List2DeptDate": "BH ,205,09/14/2026",
            },
        )

    def test_form_data_from_the_real_search_page(self) -> None:
        """The real page nests its forms, which must not hide the state
        fields from the post."""
        with open(EXAMPLES / "search_form.html") as f:
            data = build_department_form_data(f.read(), "ALH,X,09/14/2026")
        for field in (
            "__VIEWSTATE",
            "__VIEWSTATEGENERATOR",
            "__EVENTVALIDATION",
        ):
            with self.subTest(field=field):
                self.assertTrue(data.get(field))
        self.assertEqual(
            data["ctl00$ctl00$siteMasterHolder$basicBodyHolder$List2DeptDate"],
            "ALH,X,09/14/2026",
        )

    def test_form_data_without_courtroom_list(self) -> None:
        with self.assertRaises(ValueError):
            build_department_form_data("<html><body></body></html>", "x")
