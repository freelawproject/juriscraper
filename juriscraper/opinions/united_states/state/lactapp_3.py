"""Scraper for the Louisiana Third Circuit Court of Appeal
CourtID: lactapp_3
Court Short Name: La. Ct. App. 3d Cir.
Author: grossir
History:
  2026-03-19: Created by grossir
Notes:
  The site uses Cloudflare which blocks httpx via TLS fingerprinting.
  We use urllib.request which is not blocked. The site is an ASP.NET
  app with a calendar control. To get opinions, we navigate the
  calendar to a month, find highlighted dates (opinion dates), then
  click each date to get the opinion list.
"""

import re
import urllib.parse
from datetime import date, datetime
from urllib.parse import urljoin

from lxml import html as lxml_html

from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

# Days from Jan 1, 2000 (epoch for ASP.NET calendar serial numbers)
CALENDAR_EPOCH = date(2000, 1, 1)


class Site(OpinionSiteLinear):
    base_url = "https://www.la3circuit.org"
    first_opinion_date = datetime(1992, 1, 1)
    days_interval = 28
    use_urllib = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"{self.base_url}/index.aspx"
        self.status = "Unknown"
        self.needs_special_headers = True
        self.target_date = datetime.today()
        self.make_backscrape_iterable(kwargs)

    def _post_calendar(self, tree, event_argument):
        """POST to the calendar control

        :param tree: current page lxml tree (for extracting form params)
        :param event_argument: calendar event argument (date serial or
            V{serial} for navigation)
        :return: lxml HTML tree of response
        """
        params = self._get_form_params(tree)
        params["__EVENTTARGET"] = "ctl00$opiCalendar"
        params["__EVENTARGUMENT"] = str(event_argument)
        data = urllib.parse.urlencode(params).encode("utf-8")
        raw = self._urllib_fetch(self.url, data=data)
        return lxml_html.fromstring(raw.decode("utf-8"))

    @staticmethod
    def _get_form_params(tree):
        """Extract form parameters from an ASP.NET page

        :param tree: lxml HTML tree
        :return: dict of form parameters
        """
        params = {}
        for inp in tree.xpath("//form//input[@name]"):
            name = inp.get("name", "")
            if name and "btn" not in name.lower():
                params[name] = inp.get("value", "")
        for sel in tree.xpath("//form//select[@name]"):
            selected = sel.xpath(".//option[@selected]")
            if selected:
                params[sel.get("name")] = selected[0].get(
                    "value", selected[0].text_content()
                )
            else:
                first = sel.xpath(".//option")
                if first:
                    params[sel.get("name")] = first[0].get(
                        "value", first[0].text_content()
                    )
        return params

    @staticmethod
    def _get_opinion_date_serials(tree):
        """Find calendar dates that have opinions (highlighted yellow)

        :param tree: lxml HTML tree with calendar
        :return: list of date serial numbers with opinions
        """
        serials = []
        for td in tree.xpath('//table[@id="opiCalendar"]//td'):
            style = td.get("style", "")
            if "background-color:#fffde7" not in style:
                continue
            a = td.xpath(".//a")
            if not a:
                continue
            href = a[0].get("href", "")
            m = re.search(r"'(\d+)'\)", href)
            if m:
                serials.append(int(m.group(1)))
        return serials

    @staticmethod
    def _get_displayed_month(tree):
        """Get the month currently shown in the calendar

        :param tree: lxml HTML tree
        :return: (year, month) tuple or None
        """
        title = tree.xpath(
            '//table[@id="opiCalendar"]'
            "//td[@align='center' and @width='70%']"
        )
        if title:
            text = title[0].text_content().strip()
            try:
                dt = datetime.strptime(text, "%B %Y")
                return (dt.year, dt.month)
            except ValueError:
                return None
        return None

    async def _process_html(self):
        if self.test_mode_enabled():
            self._extract_opinions(self.html)
            return

        target = self.target_date
        first_of_month = date(target.year, target.month, 1)
        first_serial = (first_of_month - CALENDAR_EPOCH).days

        # Check if calendar is already showing the target month
        displayed = self._get_displayed_month(self.html)
        if displayed == (target.year, target.month):
            # Already on the target month, use current page
            tree = self.html
        else:
            # Navigate calendar to the target month
            tree = self._post_calendar(self.html, f"V{first_serial}")

        # Find which dates have opinions
        opinion_serials = self._get_opinion_date_serials(tree)
        if not opinion_serials:
            logger.warning(
                "No opinion dates found for %s/%s. "
                "The calendar highlight color may have changed.",
                target.month,
                target.year,
            )
            return

        logger.info(
            "Found %d opinion dates for %s/%s",
            len(opinion_serials),
            target.month,
            target.year,
        )

        # Click each opinion date to get the opinion list
        for serial in opinion_serials:
            tree = self._post_calendar(tree, serial)
            self._extract_opinions(tree)

    def _extract_opinions(self, tree):
        """Extract opinion data from the results div

        :param tree: lxml HTML tree containing opinion results
        """
        rows = tree.xpath(
            '//div[@id="divOpinionSearchByDate"]//tbody/tr[.//a]'
        )
        for row in rows:
            td = row.xpath(".//td")[0]
            link = td.xpath(".//h4/a/@href")
            if not link:
                continue

            url = urljoin(f"{self.base_url}/", link[0])
            strongs = td.xpath(".//strong/text()")

            # First strong is the docket number
            raw_docket = strongs[0].strip() if strongs else ""
            docket = re.sub(r"\s+", "", raw_docket)

            # Extract fields from text nodes following strong tags
            text = td.text_content()
            date_match = re.search(r"Opinion Date:\s*(\d{8})", text)
            title_match = re.search(
                r"Case Title:\s*(.+?)\s*(?:Vs\.\s*)?Parish:",
                text,
                re.DOTALL,
            )

            case_date = ""
            if date_match:
                raw = date_match.group(1)
                case_date = f"{raw[:2]}/{raw[2:4]}/{raw[4:]}"

            name = ""
            if title_match:
                name = re.sub(r"\s+", " ", title_match.group(1)).strip()
                # Strip trailing ", ET AL." variations
                name = re.sub(r",?\s*ET\s+AL\.?\s*$", "", name, flags=re.I)
                # Ensure space after colons for proper titlecasing
                name = re.sub(r":(\S)", r": \1", name)
                name = titlecase(name)
                # Normalize "Versus" to "v."
                name = re.sub(r"\bVersus\b", "v.", name)

            self.cases.append(
                {
                    "name": name,
                    "docket": docket,
                    "date": case_date,
                    "url": url,
                    "status": self.status,
                }
            )

    async def _download_backwards(self, target_date: date) -> None:
        self.target_date = target_date
        self.html = await self._download()
        await self._process_html()

    def make_backscrape_iterable(self, kwargs):
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )
