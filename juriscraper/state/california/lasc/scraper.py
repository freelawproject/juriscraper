"""Scraper for the three free Los Angeles Superior Court sites.

The court publishes three things without charge, each on its own site and
each behind its own session: the civil case summary, which answers one case
number at a time; the tentative rulings its civil courtrooms publish and take
down once the hearing has passed; and the public civil calendar, which is the
only place the court names cases in bulk.

The parsers in this package turn one of those pages into data and build the
posts the sites need. `LASCScraper` holds the session each site requires and
makes those posts in the order the site insists on:

- The case summary takes one GET, for the search form's anti-forgery token,
  and one POST per case number. The court redirects a number it knows to the
  summary and answers one it doesn't with the search page and a message, so a
  lookup either returns a case or raises.
- The tentative rulings search page lists every courtroom currently
  publishing, and posting one of its options back returns that courtroom's
  rulings. The rulings page does not carry the courtroom list, so each
  courtroom is fetched from a freshly loaded search page rather than from the
  page the last one returned.
- The calendar gates its search behind a disclaimer and fills its department
  list from the chosen courthouse by postback, so a search is the fourth
  request of a session rather than the first. Its result page does carry the
  whole search form, so one courthouse's departments are swept from each
  result in turn.

Nothing here is authenticated: all of it is what the court shows the public.
The Media Access Portal, which needs credentials and covers far more, is a
separate client in `juriscraper.lasc`.
"""

from collections.abc import Generator
from datetime import date
from typing import Final
from urllib.parse import urljoin

import requests
from typing_extensions import override

from juriscraper.abstract_parser import ParserValidationError
from juriscraper.lib.exceptions import JuriscraperException
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.state.BaseStateScraper import (
    BaseStateScraper,
    HasCaseUrl,
    ScraperRequestManager,
)
from juriscraper.state.california.lasc.calendar import (
    CIVIL_CALENDAR_URL,
    CalendarDepartmentsParser,
    CalendarEvent,
    CalendarLocation,
    CalendarLocationsParser,
    CalendarParser,
    build_calendar_form_data,
    build_department_list_form_data,
    build_disclaimer_form_data,
)
from juriscraper.state.california.lasc.case_summary import (
    CASE_SUMMARY_SEARCH_URL,
    CaseSummaryParser,
    LASCCaseSummary,
    Refusal,
    build_case_search_form_data,
    search_refusal,
)
from juriscraper.state.california.lasc.tentative_rulings import (
    TENTATIVE_RULINGS_URL,
    TentativeRuling,
    TentativeRulingOption,
    TentativeRulingOptionsParser,
    TentativeRulingsParser,
    build_department_form_data,
)

logger = make_default_logger()

COURT_ID: Final[str] = "lasc"

# The calendar's own page for a case, which its rows link to. The court has no
# addressable case summary: that is reached by posting a case number from a
# session of its own, so this is the only URL a calendar row yields.
CALENDAR_CASE_URL: Final[str] = (
    "https://www.lacourt.ca.gov/CivilCalendar/ui/CalendarCase.aspx"
)

# How often a request that times out or is refused is made again. The
# court's sites are quick when they answer at all, so a request that hangs
# for the full timeout has gone wrong rather than gotten slow, and repeating
# it usually works.
MAX_ATTEMPTS: Final[int] = 3

# Seconds to leave between requests. Sweeping the calendar is one request per
# courtroom across some forty courthouses, and this is a county court's own
# website rather than a state API built for bulk access, so it is swept at
# walking pace. A caller who has agreed something else with the court passes
# its own request manager.
MIN_REQUEST_INTERVAL: Final[float] = 0.5


class LASCCaseNotFound(JuriscraperException):
    """Raised when the case summary has no case with the number looked up.

    :ivar case_number: The number that was looked up.
    :ivar message: The court's own message, e.g. ``No match found for case
        number 25STCV99998.``
    """

    def __init__(self, case_number: str, message: str) -> None:
        self.case_number = case_number
        self.message = message
        super().__init__(f"No case summary for {case_number}: {message}")


class LASCRestrictedCase(JuriscraperException):
    """Raised when a case may only be viewed by its parties.

    Some cases, such as confidential unlawful detainers, need a court-issued
    access code even though their case number's litigation type is civil.

    :ivar case_number: The number that was looked up.
    :ivar message: The court's explanation, e.g. ``Case Number 26STCV00002 is
        a confidential Unlawful Detainer case.``
    """

    def __init__(self, case_number: str, message: str) -> None:
        self.case_number = case_number
        self.message = message
        super().__init__(
            f"Case summary for {case_number} is restricted: {message}"
        )


class LASCCalendarRow(HasCaseUrl):
    """One scheduled event, with the courtroom it was found in.

    This is `CalendarEvent` as `LASCScraper.backfill` yields it: the event's
    own fields, the courtroom whose calendar named it, and a URL for the case.

    :ivar case_url: The calendar's page for the case. The case summary has no
        URL of its own, so `LASCScraper.case_summary` takes `case_number`
        instead.
    :ivar case_number: The case number, e.g. ``23STCV04845``.
    :ivar case_name: The case name as the calendar prints it.
    :ivar hearing_date: The date the event is scheduled for.
    :ivar hearing_time: The time as the calendar prints it, e.g. ``8:30 AM``.
    :ivar event: What the event is, e.g. ``Jury Trial``.
    :ivar date_filed: The date the case was filed, when the row gives it.
    :ivar location_code: The court's code for the courthouse, e.g. ``LAM``.
    :ivar courthouse: The courthouse name.
    :ivar department: The department whose calendar named the case.
    """

    case_number: str
    case_name: str
    hearing_date: date
    hearing_time: str
    event: str
    date_filed: date | None
    location_code: str
    courthouse: str
    department: str


class _CalendarSession:
    """The calendar pages a courthouse's departments are searched from.

    The site gates its search behind a disclaimer and fills its department
    list from the chosen courthouse by postback, so reaching a courtroom's
    calendar takes three posts before the search itself. Those pages are what
    this holds: the search form once the disclaimer is accepted, and, once a
    courthouse is chosen, that courthouse's page with its departments loaded.

    Every department is then searched from that one page, rather than from
    the calendar the last department returned. Both work — the result pages
    carry the whole form too — but a result page runs to hundreds of rows and
    re-reading one to build the next post costs more than the search does,
    and searching from a fixed page leaves each department independent of the
    one before it.

    :ivar form: The search page, with the disclaimer accepted.
    :ivar courthouse: The courthouse whose departments `form` has loaded, or
        `None` before one is chosen.
    """

    def __init__(self, form: str) -> None:
        self.form = form
        self.courthouse: str | None = None


class LASCScraper(BaseStateScraper):
    """Reads the Los Angeles Superior Court's three free sites.

    Each site keeps its own session, and this holds all of them, so one
    scraper can be used for every kind of request. The calendar's session is
    the only one with state worth keeping between calls, and it is built on
    the first calendar request rather than in the constructor, so a scraper
    that is only ever asked for a case summary never loads the calendar.
    """

    COURT_IDS: list[str] = [COURT_ID]

    # The calendar names what is scheduled ahead, so there is no reaching
    # back through it. See `backfill`.
    BACKFILLS_HISTORY: bool = False

    def __init__(
        self,
        request_manager: ScraperRequestManager | None = None,
        **kwargs,
    ) -> None:
        """Initialize the scraper.

        :param request_manager: Optional `ScraperRequestManager` instance.
            One is built paced and retrying if this is left out.
        :param kwargs: Additional arguments passed to the parent.
        """
        super().__init__(
            request_manager=request_manager
            or ScraperRequestManager(
                min_request_interval=MIN_REQUEST_INTERVAL,
                max_attempts=MAX_ATTEMPTS,
            ),
            **kwargs,
        )
        # Each site's session, built on the first request that needs it so
        # that a scraper only ever asked for a case summary never loads the
        # calendar.
        self._case_search: str | None = None
        self._rulings_search: str | None = None
        self._calendar: _CalendarSession | None = None

    # -- Requests ---------------------------------------------------------

    @staticmethod
    def _decode(response: requests.Response) -> str:
        """Read a response's body as text.

        Requests falls back to ISO-8859-1 for an HTML response that declares
        no charset, which mangles the court's non-ASCII characters. The
        court's sites do declare one, but the tentative rulings are pasted in
        from word processors and occasionally arrive without it, so an
        undeclared charset is sniffed rather than assumed.

        :param response: The response to read.
        :return: The body as text.
        """
        content_type = response.headers.get("Content-Type", "")
        if "charset" not in content_type.lower():
            response.encoding = response.apparent_encoding
        return response.text

    def _request(
        self, method: str, url: str, data: dict[str, str] | None = None
    ) -> str:
        """Make one request and read the page it answers with.

        Pacing the request and repeating one the court doesn't answer are the
        request manager's business; what is left here is reading the body.

        :param method: The HTTP method.
        :param url: The URL to request.
        :param data: The form fields to post, if any.
        :return: The page the court answered with.
        :raises requests.HTTPError: If the court answers with an error status.
        :raises requests.Timeout: If it never answers.
        :raises requests.ConnectionError: If the connection can't be made.
        """
        response = self.request_manager.request(method, url, data=data)
        response.raise_for_status()
        return self._decode(response)

    def _get(self, url: str) -> str:
        """Fetch a page.

        :param url: The URL to fetch.
        :return: The page.
        """
        return self._request("GET", url)

    def _post(self, url: str, data: dict[str, str]) -> str:
        """Post a form and return the page it answers with.

        :param url: The URL to post to.
        :param data: The form fields, as one of the parsers' `build_*` helpers
            built them.
        :return: The page the court answered with.
        """
        return self._request("POST", url, data)

    # -- Case summary -----------------------------------------------------

    def case_summary(self, case_number: str) -> LASCCaseSummary:
        """Look up one case.

        :param case_number: The case number to look up, e.g. ``25STCV20242``.
        :return: The case as the summary shows it.
        :raises LASCCaseNotFound: If the court has no such case, or won't
            answer for it, e.g. because the number's litigation type isn't one
            the civil summary covers.
        :raises LASCRestrictedCase: If the case may only be viewed by its
            parties.
        """
        try:
            page = self._search_for_case(case_number)
        except (requests.HTTPError, ValueError):
            # The form's token outlives many searches but not the session it
            # belongs to, and a page kept from a session the court has since
            # forgotten is refused rather than answered.
            logger.info("Renewing the case summary's search form.")
            self._case_search = None
            page = self._search_for_case(case_number)
        if refusal := search_refusal(page):
            reason, message = refusal
            if reason is Refusal.RESTRICTED:
                raise LASCRestrictedCase(case_number, message)
            raise LASCCaseNotFound(case_number, message)
        return CaseSummaryParser(COURT_ID).parse(page)

    def _search_for_case(self, case_number: str) -> str:
        """Post one case number to the search form.

        The form carries an anti-forgery token, which the court checks against
        the session it was served to. One token covers as many searches as the
        session lasts, so the page it came on is kept rather than fetched
        again for every case.

        :param case_number: The case number to look up.
        :return: The page the search ended at.
        """
        if self._case_search is None:
            self._case_search = self._get(CASE_SUMMARY_SEARCH_URL)
        return self._post(
            CASE_SUMMARY_SEARCH_URL,
            build_case_search_form_data(self._case_search, case_number),
        )

    # -- Tentative rulings ------------------------------------------------

    def tentative_ruling_options(self) -> list[TentativeRulingOption]:
        """List the courtrooms publishing rulings, and for which dates.

        A ruling is taken down once its hearing has passed, so this is only
        ever current and upcoming dates and has to be asked at least daily to
        catch every ruling the court publishes.

        :return: One option per courtroom and hearing date.
        """
        # Always fresh: which courtrooms are publishing is the thing being
        # asked, and it changes through the day.
        self._rulings_search = self._get(TENTATIVE_RULINGS_URL)
        return TentativeRulingOptionsParser(COURT_ID).parse(
            self._rulings_search
        )

    def tentative_rulings(
        self, option: TentativeRulingOption
    ) -> list[TentativeRuling]:
        """Fetch the rulings one courtroom published for one hearing date.

        A rulings page carries ASP.NET's state but not the courtroom list, so
        the next courtroom can't be asked for from the page this one returned.
        The search page can, though: the court answers a postback built from
        it for as long as the session lasts, so it is kept and posted from
        again rather than fetched once per courtroom.

        :param option: The option to fetch, from `tentative_ruling_options`.
        :return: The courtroom's rulings for that date, in the order it
            published them. Empty when it published none.
        """
        try:
            return self._fetch_rulings(option)
        except (requests.HTTPError, ValueError):
            logger.info("Renewing the tentative rulings search page.")
            self._rulings_search = None
            return self._fetch_rulings(option)

    def _fetch_rulings(
        self, option: TentativeRulingOption
    ) -> list[TentativeRuling]:
        """Post one courtroom's option back to the search page.

        :param option: The option to fetch.
        :return: The courtroom's rulings for that date.
        """
        if self._rulings_search is None:
            self._rulings_search = self._get(TENTATIVE_RULINGS_URL)
        page = self._post(
            TENTATIVE_RULINGS_URL,
            build_department_form_data(self._rulings_search, option.value),
        )
        return TentativeRulingsParser(COURT_ID).parse(page)

    def all_tentative_rulings(
        self,
    ) -> Generator[
        tuple[TentativeRulingOption, list[TentativeRuling]], None, None
    ]:
        """Fetch every ruling the court is currently publishing.

        A courtroom whose page can't be read is logged and skipped: one
        courtroom's malformed rulings shouldn't cost a sweep the hundred
        others. A page that no longer holds the controls the posts are built
        from is not skipped, because that means the site changed and the whole
        sweep is worthless.

        :return: Each courtroom and date, with the rulings it published.
        :raises ValueError: If the search page no longer holds the courtroom
            list.
        """
        for option in self.tentative_ruling_options():
            try:
                rulings = self.tentative_rulings(option)
            except (ParserValidationError, requests.RequestException):
                logger.warning(
                    "Skipping tentative rulings for %s department %s on %s",
                    option.location_code,
                    option.department,
                    option.hearing_date,
                    exc_info=True,
                )
                continue
            logger.info(
                "Found %s tentative rulings in %s department %s for %s",
                len(rulings),
                option.location_code,
                option.department,
                option.hearing_date,
            )
            yield option, rulings

    # -- Calendar ---------------------------------------------------------

    def _calendar_session(self) -> _CalendarSession:
        """Open the calendar's search form, accepting its disclaimer.

        The site shows the form only once the disclaimer is accepted.

        :return: The session, ready for a courthouse to be chosen.
        """
        if self._calendar is not None:
            return self._calendar
        page = self._get(CIVIL_CALENDAR_URL)
        try:
            disclaimer = build_disclaimer_form_data(page)
        except ValueError:
            # A session that has already accepted it is served the form
            # directly.
            logger.debug("The calendar was served without its disclaimer.")
        else:
            page = self._post(CIVIL_CALENDAR_URL, disclaimer)
        self._calendar = _CalendarSession(page)
        return self._calendar

    def _select_courthouse(self, location: CalendarLocation) -> str:
        """Choose a courthouse, which is what fills its department list.

        :param location: The courthouse to choose.
        :return: The search page, with the courthouse's departments loaded.
        """
        session = self._calendar_session()
        if session.courthouse != location.value:
            session.form = self._post(
                CIVIL_CALENDAR_URL,
                build_department_list_form_data(session.form, location.value),
            )
            session.courthouse = location.value
        return session.form

    def calendar_locations(self) -> list[CalendarLocation]:
        """List the courthouses whose calendars the site publishes.

        :return: One entry per courthouse.
        :raises ParserValidationError: If the page lists no courthouse, which
            means the disclaimer wasn't accepted or the site changed.
        """
        return CalendarLocationsParser(COURT_ID).parse(
            self._calendar_session().form
        )

    def calendar_departments(self, location: CalendarLocation) -> list[str]:
        """List the departments a courthouse's calendar can be searched by.

        :param location: The courthouse to list, from `calendar_locations`.
        :return: The departments, as the site gives them, e.g. ``310``.
        """
        return CalendarDepartmentsParser(COURT_ID).parse(
            self._select_courthouse(location)
        )

    def calendar(
        self,
        location: CalendarLocation,
        department: str,
        date_from: date,
        date_to: date,
    ) -> list[CalendarEvent]:
        """Fetch one courtroom's calendar.

        The calendar is forward-looking: the court answers a range that ends
        before today with "there is no calendar", whatever the courtroom has
        heard in the past.

        :param location: The courthouse to search, from `calendar_locations`.
        :param department: The department to search, from
            `calendar_departments`.
        :param date_from: The first day to include.
        :param date_to: The last day to include.
        :return: One entry per scheduled event, in the order the calendar
            lists them. Empty when the courtroom has nothing scheduled in the
            range.
        """
        result = self._post(
            CIVIL_CALENDAR_URL,
            build_calendar_form_data(
                self._select_courthouse(location),
                location.value,
                department,
                date_from,
                date_to,
            ),
        )
        return CalendarParser(COURT_ID).parse(result)

    @override
    def backfill(
        self,
        courts: list[str],
        date_range: tuple[date, date],
        courthouses: list[str] | None = None,
    ) -> Generator[LASCCalendarRow, None, None]:
        """Name every case the court has scheduled, courtroom by courtroom.

        This sweeps the calendar, which is the court's only free source of
        case numbers in bulk, and is a backfill only in a limited sense. The
        calendar is forward-looking, so a range that ends before today names
        nothing, and a case with no hearing ahead of it is invisible however
        recently it was filed: this enumerates the court's *active* cases,
        whenever they were filed, not its filings. Each row carries the case's
        filing date, so a caller after recent filings sweeps a range ahead and
        filters on that.

        A case is named once per scheduled event, and a case in more than one
        courtroom is named in each, so rows are yielded for the first event
        that names a case and its later events are dropped. A department whose
        calendar can't be read is logged and skipped.

        :param courts: The court ids to sweep, as the base class means them.
            This court is one court, `COURT_ID`, sitting in many courthouses,
            so the only useful values are that id and an empty list, both of
            which sweep the whole county. Pass `courthouses` to narrow it.
        :param date_range: The first and last day of hearings to include.
        :param courthouses: The courthouses to sweep, by the court's code,
            e.g. ``LAM``. `None` sweeps every courthouse the calendar
            publishes.
        :return: One row per case.
        :raises ValueError: If the calendar no longer holds the controls its
            posts are built from.
        """
        date_from, date_to = date_range
        if date_to < date.today():
            logger.warning(
                "The calendar has nothing for a range ending %s: it only "
                "covers hearings from today on.",
                date_to,
            )

        if courts and COURT_ID not in {
            court.strip().lower() for court in courts
        }:
            logger.warning(
                "Not sweeping: %s is the only court here, and %s was asked "
                "for.",
                COURT_ID,
                ", ".join(courts),
            )
            return

        wanted = {
            courthouse.strip().upper()
            for courthouse in courthouses or []
            if courthouse.strip()
        }
        locations = [
            location
            for location in self.calendar_locations()
            if not wanted or location.location_code.upper() in wanted
        ]
        if missing := wanted - {
            location.location_code.upper() for location in locations
        }:
            logger.warning(
                "The calendar publishes no courthouse for %s",
                ", ".join(sorted(missing)),
            )

        seen: set[str] = set()
        for location in locations:
            for department in self.calendar_departments(location):
                try:
                    events = self.calendar(
                        location, department, date_from, date_to
                    )
                except (ParserValidationError, requests.RequestException):
                    logger.warning(
                        "Skipping the calendar of %s department %s",
                        location.location_code,
                        department,
                        exc_info=True,
                    )
                    continue
                logger.info(
                    "Found %s events in %s department %s from %s to %s",
                    len(events),
                    location.location_code,
                    department,
                    date_from,
                    date_to,
                )
                for event in events:
                    if event.case_number in seen:
                        continue
                    seen.add(event.case_number)
                    yield LASCCalendarRow(
                        **event.model_dump(),
                        case_url=urljoin(
                            CALENDAR_CASE_URL,
                            f"?caseNumber={event.case_number}",
                        ),
                        location_code=location.location_code,
                        courthouse=location.courthouse,
                        department=department,
                    )
