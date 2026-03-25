"""Scraper for the Louisiana Third Circuit Court of Appeal
CourtID: lactapp_3
Court Short Name: La. Ct. App. 3d Cir.
Author: grossir
History:
  2026-03-19: Created by grossir
  2026-03-24: Switched from calendar navigation to month/year search
Notes:
  The site uses Cloudflare which blocks httpx via TLS fingerprinting.
  We use urllib.request which is not blocked.The site is an ASP.NET
  app. We search opinions by
  month and year using the site's search form.
"""

import re
import urllib.parse
from datetime import date, datetime
from urllib.parse import urljoin

from lxml import html as lxml_html

from juriscraper.lib.date_utils import unique_year_month
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear

logger = make_default_logger()


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

    async def _download(self, request_dict=None):
        """Override to perform the month/year search POST after initial load

        :param request_dict: optional request parameters
        :return: lxml HTML tree of search results
        """
        tree = await super()._download(request_dict)
        if self.test_mode_enabled():
            return tree

        target = self.target_date
        month_name = target.strftime("%B")
        params = self._get_form_params(tree)
        params["ctl00$MainContent$ddlSearchOpinions2_Month"] = month_name
        params["ctl00$MainContent$ddlSearchOpinions2_Year"] = str(
            target.year
        )
        params["ctl00$MainContent$btnSearchOpinionsByMonthYear"] = "Search"
        data = urllib.parse.urlencode(params).encode("utf-8")
        headers = dict(self.request["headers"])
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["Accept-Encoding"] = "gzip, deflate"
        raw = self._urllib_fetch(self.url, data=data, headers=headers)
        return lxml_html.fromstring(raw.decode("utf-8"))

    def _process_html(self):
        self._extract_opinions(self.html)

    def _extract_opinions(self, tree):
        """Extract opinion data from search results

        :param tree: lxml HTML tree containing opinion results
        """
        rows = tree.xpath(
            '//table[.//strong[contains(text(),"Opinion Search by")]]'
            "//tbody/tr[.//a]"
        )
        if not rows:
            # Fallback for test mode (example uses divOpinionSearchByDate)
            rows = tree.xpath(
                '//div[@id="divOpinionSearchByDate"]//tbody/tr[.//a]'
            )
        for row in rows:
            td = row.xpath(".//td")[0]
            link = td.xpath(".//h4/a/@href")
            if not link:
                text = td.text_content().strip()[:100]
                logger.warning(
                    "No link found in row, skipping: %s", text
                )
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
        self._process_html()

    def make_backscrape_iterable(self, kwargs):
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = unique_year_month(
            self.back_scrape_iterable
        )
