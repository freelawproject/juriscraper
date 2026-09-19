"""Tests for the Los Angeles Superior Court civil calendar parsers."""

import unittest
from datetime import date

from juriscraper.state.california.lasc.calendar import (
    CalendarDepartmentsParser,
    CalendarEvent,
    CalendarLocationsParser,
    CalendarParser,
    build_calendar_form_data,
    build_department_list_form_data,
    build_disclaimer_form_data,
)
from tests import TESTS_ROOT_EXAMPLES_STATES
from tests.local.PacerParseTestCase import PacerParseTestCase

EXAMPLES = TESTS_ROOT_EXAMPLES_STATES / "california" / "lasc" / "calendar"

LOCATION = "LAM;LA;Stanley Mosk Courthouse;111 North Hill Street"


def _row(
    case_number: str = "23STCV04845",
    case_name: str = "MOSLEY VS LA MONARCA BAKERY",
    hearing_date: str = "09/21/2026",
    hearing_time: str = "8:30 AM",
    event: str = "Jury Trial",
    date_filed: str = "03/06/2023",
) -> str:
    """Build a calendar row the way the court prints one."""
    return (
        f'<tr><td valign="top">{hearing_date}</td>'
        f'<td valign="top">{hearing_time}</td>'
        f'<td valign="top">{event}</td>'
        f'<td valign="top"><a href="CalendarCase.aspx?caseNumber='
        f'{case_number}" >{case_number}</a></td>'
        f'<td valign="top">{case_name}</td>'
        f'<td valign="top">{date_filed}</td></tr>'
    )


def _page(*rows: str, departments: tuple[str, ...] = ("310",)) -> str:
    """Wrap rows in the markup of a calendar result page."""
    options = "".join(f'<option value="{d}">{d}</option>' for d in departments)
    return f"""
    <html><body><form id="lascwebform">
      <input type="hidden" name="__VIEWSTATE" value="state">
      <input type="hidden" name="Loc" value="LAM">
      <input type="hidden" name="hdnType" value="">
      <select name="ctl00$body$ddlLocation2" id="body_ddlLocation2">
        <option value="">Select</option>
        <option value="{LOCATION}">Stanley Mosk Courthouse</option>
      </select>
      <select name="ctl00$body$ddlDept" id="body_ddlDept">{options}</select>
      <input name="ctl00$body$dateFrom" id="body_dateFrom" value="">
      <input name="ctl00$body$dateTo" id="body_dateTo" value="">
      <input type="submit" name="ctl00$body$butDisclaimer"
             id="body_butDisclaimer" value="I Agree">
      <table id="body_calendarDeptDate_tblResults">
        <tr><th>Date</th><th>Time</th><th>Event</th><th>Case</th>
            <th>Title</th><th>File Date</th></tr>
        {"".join(rows)}
      </table>
    </form></body></html>
    """


class LASCCalendarExampleTest(PacerParseTestCase):
    """Parse the pages captured from the court's site."""

    def setUp(self) -> None:
        self.maxDiff = 200000

    def test_calendar_pages(self) -> None:
        self.parse_files(EXAMPLES, "calendar_*.html", CalendarParser)

    def test_search_page(self) -> None:
        self.parse_files(EXAMPLES, "search_form*.html", CalendarLocationsParser)


class LASCCalendarParserTest(unittest.TestCase):
    """Reading one courtroom's calendar."""

    def parse(self, page: str) -> list[CalendarEvent]:
        parser = CalendarParser("lasc")
        parser._parse_text(page)
        return parser.data

    def test_reads_an_event(self) -> None:
        """Each row names a case, when it is due and when it was filed."""
        [event] = self.parse(_page(_row()))

        self.assertEqual(event.case_number, "23STCV04845")
        self.assertEqual(event.case_name, "MOSLEY VS LA MONARCA BAKERY")
        self.assertEqual(event.hearing_date, date(2026, 9, 21))
        self.assertEqual(event.hearing_time, "8:30 AM")
        self.assertEqual(event.event, "Jury Trial")
        self.assertEqual(event.date_filed, date(2023, 3, 6))

    def test_a_case_appears_once_per_event(self) -> None:
        """A courtroom hearing two matters in a case lists it twice."""
        events = self.parse(
            _page(_row(event="Jury Trial"), _row(event="Status Conference"))
        )

        self.assertEqual([e.event for e in events], ["Jury Trial", "Status Conference"])
        self.assertEqual({e.case_number for e in events}, {"23STCV04845"})

    def test_a_courtroom_with_nothing_scheduled(self) -> None:
        """The court answers an empty calendar with a message, not a table."""
        page = "<html><body>There is no calendar for Department 20</body></html>"

        self.assertEqual(self.parse(page), [])

    def test_a_row_without_a_case_is_skipped(self) -> None:
        """A row the court couldn't fill is dropped rather than guessed at."""
        broken = (
            '<tr><td valign="top">09/21/2026</td><td valign="top">8:30 AM</td>'
            '<td valign="top">Jury Trial</td><td valign="top"></td>'
            '<td valign="top">A VS B</td><td valign="top">03/06/2023</td></tr>'
        )

        self.assertEqual(len(self.parse(_page(broken, _row()))), 1)

    def test_a_row_without_a_filing_date(self) -> None:
        """A case with no readable filing date still names its case."""
        [event] = self.parse(_page(_row(date_filed="&nbsp;")))

        self.assertIsNone(event.date_filed)
        self.assertEqual(event.case_number, "23STCV04845")


class LASCCalendarFormTest(unittest.TestCase):
    """Building the posts the court's search needs."""

    def test_reads_the_courthouse_list(self) -> None:
        """A courthouse option packs the court's codes into its value."""
        parser = CalendarLocationsParser("lasc")
        parser._parse_text(_page())
        [location] = parser.data

        self.assertEqual(location.location_code, "LAM")
        self.assertEqual(location.courthouse, "Stanley Mosk Courthouse")

    def test_reads_the_department_list(self) -> None:
        """The departments a chosen courthouse can be searched by."""
        parser = CalendarDepartmentsParser("lasc")
        parser._parse_text(_page(departments=("310", "311")))

        self.assertEqual(parser.data, ["310", "311"])

    def test_disclaimer_post_carries_the_hidden_fields(self) -> None:
        """The search form is shown only once the disclaimer is accepted."""
        data = build_disclaimer_form_data(_page())

        self.assertEqual(data["__VIEWSTATE"], "state")
        self.assertEqual(data["ctl00$body$butDisclaimer"], "I Agree")

    def test_department_list_post_is_a_courthouse_postback(self) -> None:
        """The court fills the department list by posting the choice back."""
        data = build_department_list_form_data(_page(), LOCATION)

        self.assertEqual(data["__EVENTTARGET"], "ctl00$body$ddlLocation2")
        self.assertEqual(data["ctl00$body$ddlLocation2"], LOCATION)

    def test_search_post_echoes_every_hidden_field(self) -> None:
        """The court answers a post that drops its own hidden fields with
        "session expired", so all of them are echoed back."""
        data = build_calendar_form_data(
            _page(), LOCATION, "310", date(2026, 9, 18), date(2027, 9, 18)
        )

        self.assertEqual(data["Loc"], "LAM")
        self.assertEqual(data["__VIEWSTATE"], "state")
        self.assertEqual(data["hdnType"], "TYPE")
        self.assertEqual(data["ctl00$body$ddlDept"], "310")
        self.assertEqual(data["ctl00$body$dateFrom"], "09/18/2026")
        self.assertEqual(data["ctl00$body$dateTo"], "09/18/2027")

    def test_a_page_without_the_search_form_is_refused(self) -> None:
        """An error page can't be used to build the next post."""
        with self.assertRaises(ValueError):
            build_calendar_form_data(
                "<html><body>An exception occurred.</body></html>",
                LOCATION,
                "310",
                date(2026, 9, 18),
                date(2027, 9, 18),
            )


if __name__ == "__main__":
    unittest.main()
