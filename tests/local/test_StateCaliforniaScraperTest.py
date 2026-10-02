"""Tests for the Los Angeles Superior Court scraper.

The parsers have tests of their own; what is tested here is the order the
scraper makes its requests in, which is what each of the court's sites
insists on, and what it does with the pages they answer with.
"""

import unittest
from datetime import date
from typing import Any
from unittest import mock

import requests
from typing_extensions import override

from juriscraper.state import BaseStateScraper as base_module
from juriscraper.state.BaseStateScraper import ScraperRequestManager
from juriscraper.state.california.lasc.calendar import CIVIL_CALENDAR_URL
from juriscraper.state.california.lasc.case_summary import (
    CASE_SUMMARY_SEARCH_URL,
)
from juriscraper.state.california.lasc.scraper import (
    MAX_ATTEMPTS,
    MIN_REQUEST_INTERVAL,
    LASCCaseNotFound,
    LASCRestrictedCase,
    LASCScraper,
)
from juriscraper.state.california.lasc.tentative_rulings import (
    TENTATIVE_RULINGS_URL,
)
from tests import TESTS_ROOT_EXAMPLES_STATES
from tests.local.lasc_pages import (
    DISCLAIMER_PAGE,
    LOCATION,
    calendar_page,
    calendar_row,
    ruling,
    rulings_page,
    rulings_search_page,
)

EXAMPLES = TESTS_ROOT_EXAMPLES_STATES / "california" / "lasc"


def _example(*parts: str) -> str:
    """Read one of the pages captured from the court's site."""
    return EXAMPLES.joinpath(*parts).read_text()


class FakeResponse:
    """One canned page, answering the bits of a response that are read."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.status_code = 200
        self.encoding = "utf-8"
        self.headers = {"Content-Type": "text/html; charset=utf-8"}

    def raise_for_status(self) -> None:
        """Canned pages are always the court's answer, never an error."""
        return None


class FakeRequestManager(ScraperRequestManager):
    """Answers requests from canned pages, in order, and records them.

    This replaces `_send`, the one place a request is really made, so the
    pacing and retrying the manager does around it are still in play.
    """

    def __init__(self, *pages: str) -> None:
        super().__init__(max_attempts=MAX_ATTEMPTS)
        self.pages = list(pages)
        self.calls: list[tuple[str, str, dict[str, str]]] = []
        # Exceptions to raise, one per request, before answering with a page.
        self.failures: list[Exception] = []

    @override
    def _send(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        self.calls.append((method, url, kwargs.get("data") or {}))
        if self.failures:
            raise self.failures.pop(0)
        if not self.pages:
            raise AssertionError(f"Nothing left to answer {method} {url}.")
        return FakeResponse(self.pages.pop(0))  # type: ignore[return-value]

    @property
    def sequence(self) -> list[tuple[str, str]]:
        """The method and URL of each request made, in order."""
        return [(method, url) for method, url, _ in self.calls]


def _scraper(*pages: str) -> tuple[LASCScraper, FakeRequestManager]:
    """A scraper whose court answers with `pages`, and the requests it made."""
    manager = FakeRequestManager(*pages)
    return LASCScraper(request_manager=manager), manager


class LASCRequestTest(unittest.TestCase):
    """Getting an answer out of sites that hang, without leaning on them."""

    def test_the_scraper_paces_itself_and_tries_again(self) -> None:
        """A sweep is a thousand requests to a county court's own website, so
        the scraper it builds for itself waits between them and repeats one
        the court doesn't answer."""
        manager = LASCScraper().request_manager

        self.assertEqual(manager.min_request_interval, MIN_REQUEST_INTERVAL)
        self.assertEqual(manager.max_attempts, MAX_ATTEMPTS)

    def test_a_caller_can_set_its_own_pace(self) -> None:
        """A caller who has agreed something else with the court says so by
        passing its own request manager."""
        manager = ScraperRequestManager(min_request_interval=0)

        self.assertIs(LASCScraper(manager).request_manager, manager)

    def test_a_request_that_times_out_is_made_again(self) -> None:
        """A hang costs one request, not a courtroom's rulings."""
        scraper, manager = _scraper(rulings_search_page("ALH,X,09/14/2026"))
        manager.failures = [requests.Timeout("hung")]

        with (
            mock.patch.object(base_module.time, "sleep") as slept,
            self.assertLogs(level="WARNING"),
        ):
            options = scraper.tentative_ruling_options()

        self.assertEqual(len(options), 1)
        self.assertEqual(len(manager.calls), 2)
        slept.assert_called_once()


class LASCCaseSummaryScraperTest(unittest.TestCase):
    """Looking up one case."""

    SEARCH_PAGE = _example("case_summary", "search_not_found_25STCV99998.html")

    def test_a_lookup_posts_the_number_with_the_forms_token(self) -> None:
        """The form carries an anti-forgery token, so the search page has to
        be fetched before a case number can be posted."""
        scraper, manager = _scraper(
            self.SEARCH_PAGE,
            _example("case_summary", "lasc_case_summary_25STCV20242.html"),
        )

        case = scraper.case_summary("25STCV20242")

        self.assertEqual(case.docket_number, "25STCV20242")
        self.assertEqual(
            manager.sequence,
            [
                ("GET", CASE_SUMMARY_SEARCH_URL),
                ("POST", CASE_SUMMARY_SEARCH_URL),
            ],
        )
        posted = manager.calls[1][2]
        self.assertEqual(posted["txtCaseNumber"], "25STCV20242")
        self.assertTrue(posted["__RequestVerificationToken"])

    def test_one_token_serves_many_lookups(self) -> None:
        """The token the form carries is good for as long as the session is,
        so looking up a second case is one request, not two. At a case per
        row of a county-wide calendar sweep, the saved request is the larger
        half of the work."""
        scraper, manager = _scraper(
            self.SEARCH_PAGE,
            _example("case_summary", "lasc_case_summary_25STCV20242.html"),
            _example("case_summary", "lasc_case_summary_24STLC08093.html"),
        )

        first = scraper.case_summary("25STCV20242")
        second = scraper.case_summary("24STLC08093")

        self.assertEqual(first.docket_number, "25STCV20242")
        self.assertEqual(second.docket_number, "24STLC08093")
        self.assertEqual(
            manager.sequence,
            [
                ("GET", CASE_SUMMARY_SEARCH_URL),
                ("POST", CASE_SUMMARY_SEARCH_URL),
                ("POST", CASE_SUMMARY_SEARCH_URL),
            ],
        )

    def test_a_form_the_court_has_forgotten_is_fetched_again(self) -> None:
        """A token outlives many searches but not its session, and a search
        the court refuses is worth one more try with a fresh form."""
        scraper, manager = _scraper(
            self.SEARCH_PAGE,
            _example("case_summary", "lasc_case_summary_24STLC08093.html"),
            self.SEARCH_PAGE,
            _example("case_summary", "lasc_case_summary_25STCV20242.html"),
        )
        scraper.case_summary("24STLC08093")
        # The session lapses between one lookup and the next.
        manager.failures = [requests.HTTPError("500 from a lost session")]

        with self.assertLogs(level="INFO"):
            case = scraper.case_summary("25STCV20242")

        self.assertEqual(case.docket_number, "25STCV20242")
        self.assertEqual(
            manager.sequence[-3:],
            [
                ("POST", CASE_SUMMARY_SEARCH_URL),
                ("GET", CASE_SUMMARY_SEARCH_URL),
                ("POST", CASE_SUMMARY_SEARCH_URL),
            ],
        )

    def test_a_number_the_court_doesnt_know(self) -> None:
        """The court answers with the search page and a message instead of
        redirecting, which is the only way to tell a lookup failed."""
        scraper, _ = _scraper(
            self.SEARCH_PAGE,
            _example("case_summary", "search_not_found_25STCV99998.html"),
        )

        with self.assertRaises(LASCCaseNotFound) as caught:
            scraper.case_summary("25STCV99998")

        self.assertEqual(caught.exception.case_number, "25STCV99998")
        self.assertIn("No match found", caught.exception.message)

    def test_a_case_only_its_parties_may_view(self) -> None:
        """A confidential case redirects to a notice, not to a summary."""
        scraper, _ = _scraper(
            self.SEARCH_PAGE,
            _example("case_summary", "restricted_26STCV00002.html"),
        )

        with self.assertRaises(LASCRestrictedCase) as caught:
            scraper.case_summary("26STCV00002")

        self.assertIn(
            "confidential Unlawful Detainer", caught.exception.message
        )


class LASCTentativeRulingsScraperTest(unittest.TestCase):
    """Collecting what the courtrooms are publishing."""

    def test_lists_every_publishing_courtroom(self) -> None:
        """The search page names each courtroom and the date it is
        publishing for."""
        scraper, manager = _scraper(
            _example("tentative_rulings", "search_form.html")
        )

        options = scraper.tentative_ruling_options()

        self.assertTrue(options)
        self.assertEqual(manager.sequence, [("GET", TENTATIVE_RULINGS_URL)])

    def test_every_courtroom_is_asked_for_from_the_one_search_page(
        self,
    ) -> None:
        """A rulings page carries ASP.NET's state but not the courtroom list,
        so the next courtroom can't be asked for from the last one's page.
        The search page can be posted from as often as the session lasts,
        which is one request per courtroom rather than two."""
        scraper, manager = _scraper(
            rulings_search_page("ALH,X,09/14/2026", "LAM,534,09/15/2026"),
            rulings_page(ruling()),
            rulings_page(ruling(case_number="24STCV00001")),
        )
        first, second = scraper.tentative_ruling_options()

        [one] = scraper.tentative_rulings(first)
        [two] = scraper.tentative_rulings(second)

        self.assertEqual(one.case_number, "24NNCV01819")
        self.assertEqual(two.case_number, "24STCV00001")
        self.assertEqual(
            manager.sequence,
            [
                ("GET", TENTATIVE_RULINGS_URL),
                ("POST", TENTATIVE_RULINGS_URL),
                ("POST", TENTATIVE_RULINGS_URL),
            ],
        )
        self.assertEqual(
            [
                call[2]["ctl00$body$List2DeptDate"]
                for call in manager.calls[1:]
            ],
            ["ALH,X,09/14/2026", "LAM,534,09/15/2026"],
        )

    def test_a_search_page_the_court_has_forgotten_is_fetched_again(
        self,
    ) -> None:
        """A kept page outlives many posts but not the session it belongs to.
        When the court refuses one built from a page it has forgotten, the
        page is fetched again and the courtroom asked for once more."""
        scraper, manager = _scraper(
            rulings_search_page("ALH,X,09/14/2026"),
            rulings_search_page("ALH,X,09/14/2026"),
            rulings_page(ruling()),
        )
        [option] = scraper.tentative_ruling_options()
        manager.failures = [requests.HTTPError("500 from a lost session")]

        with self.assertLogs(level="INFO"):
            [found] = scraper.tentative_rulings(option)

        self.assertEqual(found.case_number, "24NNCV01819")
        self.assertEqual(
            manager.sequence,
            [
                ("GET", TENTATIVE_RULINGS_URL),
                ("POST", TENTATIVE_RULINGS_URL),
                ("GET", TENTATIVE_RULINGS_URL),
                ("POST", TENTATIVE_RULINGS_URL),
            ],
        )

    def test_a_courtroom_whose_page_cant_be_read_is_skipped(self) -> None:
        """One courtroom's malformed rulings shouldn't cost a sweep the
        others, so a page that won't parse is logged and passed over."""
        search_page = rulings_search_page(
            "ALH,X,09/14/2026", "LAM,534,09/15/2026"
        )
        scraper, _ = _scraper(
            search_page,
            # The first courtroom's ruling has a header but no text.
            rulings_page(ruling(text="")),
            rulings_page(ruling(case_number="24STCV00001")),
        )

        with self.assertLogs(level="WARNING"):
            collected = list(scraper.all_tentative_rulings())

        self.assertEqual(
            [option.department for option, _ in collected], ["534"]
        )
        self.assertEqual(
            [r.case_number for _, rulings in collected for r in rulings],
            ["24STCV00001"],
        )


class LASCCalendarScraperTest(unittest.TestCase):
    """Reading the calendars, which needs a session of four posts."""

    def test_a_search_is_the_fourth_request_of_a_session(self) -> None:
        """The site hides the form behind a disclaimer and fills the
        department list from the courthouse by postback, so a search can't be
        the first thing asked of it."""
        scraper, manager = _scraper(
            DISCLAIMER_PAGE,
            calendar_page(departments=()),
            calendar_page(departments=("310",)),
            calendar_page(calendar_row(), departments=("310",)),
        )

        events = scraper.calendar(
            LOCATION, "310", date(2026, 9, 21), date(2026, 9, 21)
        )

        self.assertEqual([e.case_number for e in events], ["23STCV04845"])
        self.assertEqual(
            manager.sequence,
            [
                ("GET", CIVIL_CALENDAR_URL),
                ("POST", CIVIL_CALENDAR_URL),
                ("POST", CIVIL_CALENDAR_URL),
                ("POST", CIVIL_CALENDAR_URL),
            ],
        )
        searched = manager.calls[-1][2]
        self.assertEqual(searched["ctl00$body$ddlDept"], "310")
        self.assertEqual(searched["ctl00$body$dateFrom"], "09/21/2026")
        self.assertEqual(searched["hdnType"], "TYPE")

    def test_a_second_department_is_searched_from_the_last_result(
        self,
    ) -> None:
        """A result page carries the whole form, so sweeping a courthouse
        costs one post per department rather than a new session."""
        scraper, manager = _scraper(
            DISCLAIMER_PAGE,
            calendar_page(departments=()),
            calendar_page(departments=("310", "311")),
            calendar_page(calendar_row(), departments=("310", "311")),
            calendar_page(calendar_row(), departments=("310", "311")),
        )
        scraper.calendar(LOCATION, "310", date(2026, 9, 21), date(2026, 9, 21))

        scraper.calendar(LOCATION, "311", date(2026, 9, 21), date(2026, 9, 21))

        self.assertEqual(len(manager.calls), 5)
        self.assertEqual(manager.calls[-1][2]["ctl00$body$ddlDept"], "311")

    def test_backfill_names_a_case_once(self) -> None:
        """A case is listed once per scheduled event, and the sweep is after
        the cases, so its later events are dropped."""
        scraper, _ = _scraper(
            DISCLAIMER_PAGE,
            calendar_page(departments=()),
            calendar_page(departments=("310",)),
            calendar_page(
                calendar_row(event="Jury Trial"),
                calendar_row(event="Status Conference"),
                calendar_row(case_number="22STCV19043"),
                departments=("310",),
            ),
        )

        rows = list(
            scraper.backfill(
                LASCScraper.COURT_IDS,
                (date(2026, 9, 21), date(2027, 9, 21)),
                courthouses=["LAM"],
            )
        )

        self.assertEqual(
            [row["case_number"] for row in rows],
            ["23STCV04845", "22STCV19043"],
        )
        self.assertEqual(rows[0]["department"], "310")
        self.assertEqual(rows[0]["courthouse"], "Stanley Mosk Courthouse")
        self.assertEqual(rows[0]["hearing_date"], date(2026, 9, 21))
        self.assertEqual(rows[0]["date_filed"], date(2023, 3, 6))
        self.assertEqual(
            rows[0]["case_url"],
            "https://www.lacourt.ca.gov/CivilCalendar/ui/"
            "CalendarCase.aspx?caseNumber=23STCV04845",
        )

    def test_backfill_warns_about_a_courthouse_the_site_doesnt_publish(
        self,
    ) -> None:
        """A courthouse code that names nothing is worth saying out loud
        rather than quietly sweeping nothing."""
        scraper, _ = _scraper(DISCLAIMER_PAGE, calendar_page())

        with self.assertLogs(level="WARNING") as logs:
            rows = list(
                scraper.backfill(
                    [],
                    (date(2026, 9, 21), date(2027, 9, 21)),
                    courthouses=["ZZZ"],
                )
            )

        self.assertEqual(rows, [])
        self.assertIn("ZZZ", "\n".join(logs.output))

    def test_backfill_takes_court_ids_like_its_base_class(self) -> None:
        """`courts` means court ids, as it does for every other state
        scraper, so sweeping this court's one id sweeps the county. A court
        this scraper doesn't handle sweeps nothing, and says so."""
        scraper, manager = _scraper()

        with self.assertLogs(level="WARNING") as logs:
            rows = list(
                scraper.backfill(
                    ["texas_cossup"], (date(2026, 9, 21), date(2027, 9, 21))
                )
            )

        self.assertEqual(rows, [])
        self.assertEqual(manager.calls, [])
        self.assertIn("lasc is the only court", "\n".join(logs.output))

    def test_backfill_warns_that_a_past_range_names_nothing(self) -> None:
        """The calendar only covers hearings from today on, so a range that
        ends before today is a mistake worth flagging."""
        # The courthouse comes back with no departments, so the sweep of it
        # ends there.
        scraper, _ = _scraper(
            DISCLAIMER_PAGE,
            calendar_page(departments=()),
            calendar_page(departments=()),
        )

        with self.assertLogs(level="WARNING") as logs:
            list(scraper.backfill([], (date(2020, 1, 1), date(2020, 12, 31))))

        self.assertIn("2020-12-31", "\n".join(logs.output))


if __name__ == "__main__":
    unittest.main()
