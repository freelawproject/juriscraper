"""Parsers for the Los Angeles Superior Court public civil case calendar.

The court publishes the civil calendar of every courtroom at
`CIVIL_CALENDAR_URL`. A courtroom's calendar is fetched by posting a
courthouse, a department and a date range, and the page that comes back
lists one row per scheduled event: its date and time, what the event is,
and the number, name and filing date of the case it belongs to.

That makes the calendar the court's only free bulk source of case numbers.
The case summary answers one exact case number at a time, so a case there
has to be known before it can be looked up, while a single calendar page
names every case a courtroom has scheduled for as far ahead as it has
scheduled anything.

Two limits shape how this can be used:

- The calendar is forward-looking. A department returns "there is no
  calendar" for any range that ends before today, so the calendar cannot be
  used to enumerate cases that were filed in the past and have nothing
  scheduled ahead. It names the cases that are *active*, whenever they were
  filed, and each row carries the case's filing date, so a caller wanting
  recent filings should sweep forward and filter on that.
- A case with no future hearing is invisible here, so a sweep of the
  calendar is not a census of the court's cases.

Posting requires an ASP.NET WebForms session: the site gates the search
behind a disclaimer, fills the department list from the courthouse by
postback, and echoes hidden state fields on every request. The
``build_*_form_data`` helpers below build each of those posts from the
previous page, so a caller keeps one session and walks them in order:
disclaimer, courthouse, then search.
"""

import re
from datetime import date, datetime

from lxml import html as lxml_html
from pydantic import BaseModel
from typing_extensions import override

from juriscraper.abstract_parser import LegacyParser
from juriscraper.lib.log_tools import make_default_logger

logger = make_default_logger()

CIVIL_CALENDAR_URL = (
    "https://www.lacourt.ca.gov/CivilCalendar/ui/mainpanel.aspx"
    "?CaseType=general"
)

# The site's controls carry an ASP.NET naming-container prefix that the court
# has changed before, so each one is found by the stable tail of its `id` and
# posted back under whatever `name` it currently has.
DISCLAIMER_XPATH = "//input[contains(@id, 'butDisclaimer')]"
LOCATION_SELECT_XPATH = "//select[contains(@id, 'ddlLocation2')]"
DEPARTMENT_SELECT_XPATH = "//select[contains(@id, 'ddlDept')]"
DATE_FROM_XPATH = "//input[contains(@id, 'dateFrom')]"
DATE_TO_XPATH = "//input[contains(@id, 'dateTo')]"
RESULTS_TABLE_XPATH = "//table[contains(@id, 'tblResults')]"

# The hidden input the page's own Javascript sets to say which of the
# searches the form is being posted for. It is named plainly, not through a
# naming container.
SEARCH_TYPE_FIELD = "hdnType"
DEPARTMENT_SEARCH = "TYPE"

# A courthouse option's value packs the court's codes and address into one
# semicolon-separated string, e.g.
# "LAM;LA;Stanley Mosk Courthouse;111 North Hill Street, Los Angeles, CA".
LOCATION_VALUE_PARTS = 4

DATE_FORMAT = "%m/%d/%Y"
CASE_NUMBER_RE = re.compile(r"caseNumber=(?P<case_number>[^&\"']+)")


class CalendarLocation(BaseModel):
    """A courthouse whose calendars the site publishes.

    :ivar value: The option's value, to post back when fetching the
        courthouse's department list or one of its calendars.
    :ivar location_code: The court's code for the courthouse, e.g. ``LAM``.
        The court pads these to three characters, e.g. ``BH ``; the padding
        is stripped here.
    :ivar courthouse: The courthouse name, e.g. ``Stanley Mosk Courthouse``.
    """

    value: str
    location_code: str
    courthouse: str


class CalendarEvent(BaseModel):
    """One scheduled event on a courtroom's calendar.

    A case appears once per event, so a calendar names a case as many times
    as the courtroom has matters scheduled in it.

    :ivar case_number: The case number, e.g. ``23STCV04845``.
    :ivar case_name: The case name as the calendar prints it, e.g.
        ``LLOYD MOSLEY VS LA MONARCA BAKERY IV, LLC``.
    :ivar hearing_date: The date the event is scheduled for.
    :ivar hearing_time: The time as the calendar prints it, e.g. ``8:30 AM``.
        Empty when the courtroom gives no time.
    :ivar event: What the event is, e.g. ``Jury Trial``.
    :ivar date_filed: The date the case was filed.
    """

    case_number: str
    case_name: str
    hearing_date: date
    hearing_time: str
    event: str
    date_filed: date | None


def _hidden_state(tree: lxml_html.HtmlElement) -> dict[str, str]:
    """Collect the hidden fields a post has to echo back.

    Every hidden input is echoed, not just ASP.NET's ``__``-prefixed state:
    the site keeps the chosen courthouse in hidden fields of its own
    (``Loc``, ``LocName``, ``DivCode`` and companions) and answers "Missing
    search criteria or session expired" to a post that drops them.

    The site also nests its forms improperly, so a control can parse into a
    different form than the one holding the state, which is why these are
    gathered from the whole page rather than from one form.

    :param tree: The parsed page the post is being built from.
    :return: The hidden fields to post back.
    """
    return {
        name: field.get("value", "")
        for field in tree.xpath("//input[@type='hidden']")
        if (name := field.get("name", ""))
    }


def _control_name(tree: lxml_html.HtmlElement, xpath: str, label: str) -> str:
    """Find the posted name of one of the search form's controls.

    :param tree: The parsed page the post is being built from.
    :param xpath: The xpath locating the control.
    :param label: What the control is, for the error message.
    :return: The control's `name`.
    :raises ValueError: If the page has no such control.
    """
    controls = tree.xpath(xpath)
    if not controls:
        raise ValueError(f"The calendar page has no {label}.")
    return controls[0].get("name", "")


def build_disclaimer_form_data(page_html: str) -> dict[str, str]:
    """Build the post that accepts the calendar's disclaimer.

    The site shows the search form only after its disclaimer is accepted, so
    this is the first post of a session.

    :param page_html: The calendar page, as first fetched.
    :return: The form fields to post to `CIVIL_CALENDAR_URL`.
    :raises ValueError: If the page has no disclaimer button.
    """
    tree = lxml_html.fromstring(page_html)
    button = tree.xpath(DISCLAIMER_XPATH)
    if not button:
        raise ValueError("The calendar page has no disclaimer button.")
    data = _hidden_state(tree)
    data[button[0].get("name", "")] = button[0].get("value", "I Agree")
    return data


def build_department_list_form_data(
    page_html: str, location_value: str
) -> dict[str, str]:
    """Build the post that fills the department list for a courthouse.

    The site leaves the department list empty until a courthouse is chosen,
    and fills it by posting the choice back, so a caller MUST make this post
    before it can search a department.

    :param page_html: The search page, fetched in the same session this will
        be posted from.
    :param location_value: The `CalendarLocation.value` to choose.
    :return: The form fields to post to `CIVIL_CALENDAR_URL`.
    :raises ValueError: If the page has no courthouse list.
    """
    tree = lxml_html.fromstring(page_html)
    location_field = _control_name(
        tree, LOCATION_SELECT_XPATH, "courthouse list"
    )
    data = _hidden_state(tree)
    data["__EVENTTARGET"] = location_field
    data["__EVENTARGUMENT"] = ""
    data[location_field] = location_value
    return data


def build_calendar_form_data(
    page_html: str,
    location_value: str,
    department: str,
    date_from: date,
    date_to: date,
) -> dict[str, str]:
    """Build the post that fetches one courtroom's calendar.

    :param page_html: The search page with this courthouse's departments
        loaded, fetched in the same session this will be posted from.
    :param location_value: The `CalendarLocation.value` to search.
    :param department: The department to search, as the department list
        gives it, e.g. ``310``.
    :param date_from: The first day to include. The court returns nothing
        for a range that ends before today.
    :param date_to: The last day to include.
    :return: The form fields to post to `CIVIL_CALENDAR_URL`.
    :raises ValueError: If the page is missing one of the search controls.
    """
    tree = lxml_html.fromstring(page_html)
    data = _hidden_state(tree)
    data[_control_name(tree, LOCATION_SELECT_XPATH, "courthouse list")] = (
        location_value
    )
    data[_control_name(tree, DEPARTMENT_SELECT_XPATH, "department list")] = (
        department
    )
    data[_control_name(tree, DATE_FROM_XPATH, "start date")] = (
        date_from.strftime(DATE_FORMAT)
    )
    data[_control_name(tree, DATE_TO_XPATH, "end date")] = date_to.strftime(
        DATE_FORMAT
    )
    data[SEARCH_TYPE_FIELD] = DEPARTMENT_SEARCH
    return data


def _parse_date(value: str) -> date | None:
    """Read one of the calendar's dates.

    :param value: The date as the calendar prints it, e.g. ``09/21/2026``.
    :return: The date, or `None` if the cell held something else.
    """
    try:
        return datetime.strptime(value.strip(), DATE_FORMAT).date()
    except ValueError:
        return None


class CalendarLocationsParser(LegacyParser[list[CalendarLocation]]):
    """Parse the courthouses the calendar search page lists."""

    @override
    def _parse(self, i: str) -> list[CalendarLocation]:
        """Parse the search page's courthouse list.

        :param i: The search page, after the disclaimer is accepted.
        :return: One entry per listed courthouse. The list's "Select"
            placeholder, which has no value, is skipped.
        """
        tree = lxml_html.fromstring(i)
        locations: list[CalendarLocation] = []
        for option in tree.xpath(f"{LOCATION_SELECT_XPATH}/option"):
            value = option.get("value", "")
            if not value:
                continue
            parts = value.split(";")
            if len(parts) < LOCATION_VALUE_PARTS:
                logger.warning("Skipping unreadable courthouse %r", value)
                continue
            locations.append(
                CalendarLocation(
                    value=value,
                    location_code=parts[0].strip(),
                    courthouse=parts[2].strip(),
                )
            )
        return locations

    @override
    def validate(self, _output: list[CalendarLocation]) -> bool:
        """Reject a page that lists no courthouse.

        An empty list means the disclaimer wasn't accepted or the page's
        markup no longer matches what this parser expects.

        :param _output: The parsed courthouses.
        :return: Whether any courthouse was found.
        """
        return bool(_output)


class CalendarDepartmentsParser(LegacyParser[list[str]]):
    """Parse the departments a courthouse's calendar can be searched by."""

    @override
    def _parse(self, i: str) -> list[str]:
        """Parse the search page's department list.

        :param i: The search page, with a courthouse chosen.
        :return: The departments, as the list gives them. Empty when no
            courthouse has been chosen yet.
        """
        tree = lxml_html.fromstring(i)
        return [
            value
            for option in tree.xpath(f"{DEPARTMENT_SELECT_XPATH}/option")
            if (value := option.get("value", ""))
        ]


class CalendarParser(LegacyParser[list[CalendarEvent]]):
    """Parse the events on one courtroom's calendar."""

    @override
    def _parse(self, i: str) -> list[CalendarEvent]:
        """Parse a calendar result page.

        A courtroom with nothing scheduled in the range returns a page
        saying so instead of a table, which parses to no events.

        :param i: The calendar result page.
        :return: One entry per scheduled event, in the order the calendar
            lists them. Rows whose date or case number can't be read are
            skipped and logged.
        """
        tree = lxml_html.fromstring(i)
        tables = tree.xpath(RESULTS_TABLE_XPATH)
        if not tables:
            return []
        events: list[CalendarEvent] = []
        for row in tables[0].xpath(".//tr"):
            cells = row.xpath("./td")
            # The table opens with a header row, which has no `td` cells.
            if len(cells) < 6:
                continue
            hearing_date = _parse_date(cells[0].text_content())
            links = cells[3].xpath(".//a/@href")
            number = CASE_NUMBER_RE.search(links[0]) if links else None
            if hearing_date is None or number is None:
                logger.warning(
                    "Skipping unreadable calendar row %r",
                    " ".join(row.text_content().split()),
                )
                continue
            events.append(
                CalendarEvent(
                    case_number=number.group("case_number").strip(),
                    case_name=" ".join(cells[4].text_content().split()),
                    hearing_date=hearing_date,
                    hearing_time=" ".join(cells[1].text_content().split()),
                    event=" ".join(cells[2].text_content().split()),
                    date_filed=_parse_date(cells[5].text_content()),
                )
            )
        return events
