"""Scraper for Vermont Supreme Court
CourtID: vt
Court Short Name: VT
Court Contact: submit form here https://www.vermontjudiciary.org/website-feedback-form

If there are errors with the site, you can contact:

 Monica Bombard
 (802) 828-4784

She's very responsive.
"""

import re
from datetime import date, datetime
from typing import Optional
from urllib.parse import urlencode

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.vermontjudiciary.org/opinions-decisions"
    days_interval = 30
    first_opinion_date = datetime(2000, 1, 1)
    division = 7

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        if self.division == 7:
            self.first_opinion_date = datetime(1999, 5, 26)

        # status will be updated in extract_from_text
        self.status = "Unknown"
        self.set_url()
        self.make_backscrape_iterable(kwargs)
        self.needs_special_headers = True
        self.request["headers"] = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }

    def _process_html(self) -> None:
        """Process HTML into case dictionaries

        Source's page size is 25 rows

        :return None
        """
        for case in self.html.xpath(".//article"):
            name_url_span = case.xpath(
                ".//div[contains(@class, 'views-field-name')]"
            )[0]
            date_filed = (
                case.xpath(
                    ".//div[contains(@class, 'views-field-field-document-expiration')]"
                )[0]
                .text_content()
                .strip()
            )
            docket = (
                case.xpath(
                    ".//div[contains(@class, 'views-field-field-document-number')]"
                )[0]
                .text_content()
                .strip()
            )
            self.cases.append(
                {
                    "url": name_url_span.xpath(".//a/@href")[0],
                    "name": titlecase(name_url_span.text_content()),
                    "date": date_filed,
                    "docket": docket,
                }
            )

    def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Make custom date range request
        :param dates: (start_date, end_date) tuple
        :return None
        """
        logger.info("Backscraping for range %s %s", *dates)
        self.set_url(*dates)
        self.html = self._download()
        self._process_html()

    def set_url(
        self, start: Optional[date] = None, end: Optional[date] = None
    ) -> None:
        """Formats and sets `self.url` with date inputs
        If no start or end dates are given, scrape without date filter values

        There is a Document Type filter available, with an 'Opinion' value, that
        can be added to params like this:
            {"f[1]": "document_type:94"}a
        However, we are not using it since some documents marked as 'Decisions'
        also contain opinions. For example:
        https://www.vermontjudiciary.org/sites/default/files/documents/2020-10-13-57.pdf
        titled "Opinion and Order on Cross-Motions for Summary Judgment"
        has 8 pages, most of which are argumentation

        :param start: start date
        :param end: end date
        :return None
        """
        params = {
            "facet_from_date": "",
            "facet_to_date": "",
            "f[0]": f"court_division_opinions_library_:{self.division}",  # filter by court
        }
        if start:
            params["facet_from_date"] = start.strftime("%m/%d/%Y")
            params["facet_to_date"] = end.strftime("%m/%d/%Y")

        self.url = f"{self.base_url}?{urlencode(params)}"

    def extract_from_text(self, scraped_text: str):
        """Extract a neutral citation if it exists, and update court and status

        Some documents have this heading:
        > Decisions of a three-justice panel are not to be considered as
        > precedent before any tribunal.

        However, there are some edge cases of decisions by 3 judges that
        actually have a neutral citation, like:
        https://www.courtlistener.com/opinion/10350446/state-v-aaliyah-johnson/

        Docs with a neutral citation have another heading, so the presence
        of the above heading may be used
        > This opinion is subject to motions for reargument under V.R.A.P. 40
        > as well as formal revision before publication in the Vermont Reports.
        """
        metadata = {}
        cite_regex = r"\n\s*\d{4} VT \d+\s*\n"
        match = re.search(cite_regex, scraped_text[:1000])
        if match:
            metadata = {
                "Citation": match.group(0).strip(),
                "OpinionCluster": {"precedential_status": "Published"},
            }

            # update court_id for opinions that have a VT citation, that are
            # marked on the source as belonging to one of the superior court
            # divisions. Check test_ScraperExtractFromTextTest examples
            if "vtsuperct" in self.court_id:
                metadata["Docket"] = {"court_id": "vt"}

        non_precedential_heading = (
            "decisions of a three-justice panel are not to be considered as "
            "precedent before any tribunal"
        )
        if non_precedential_heading in scraped_text[:1000].lower():
            splitted = scraped_text.split("BY THE COURT:")
            if len(splitted) > 1:
                judge_regex = (
                    r"(?P<judge>[A-Za-z .,]+),\s+(Associate|Chief) Justice"
                )
                judges = [
                    j.group("judge").strip()
                    for j in re.finditer(judge_regex, splitted[-1])
                ]
                cluster = {"judges": "; ".join(judges)}

                if len(judges) == 3:
                    cluster["precedential_status"] = "Unpublished"

                metadata["OpinionCluster"] = cluster

        cleaned_text = "\n".join(
            line.rsplit("}", 1)[-1] if "}" in line else line
            for line in scraped_text[:1500].splitlines()
        )

        pattern = re.compile(
            r"APPEALED\s+FROM:\s*(?P<lower_court>.*?)"  # non-greedy, capture all up to Case No
            r"[.\n\r]*?"  # allow for dot, newlines, carriage returns, etc.
            r"CASE\s+NO[S]?\.?:?\s*([\n\r]*)?"  # match CASE NO. or CASE NOS. (case-insensitive)
            r"(?P<lower_court_number>[\w-]+)"  # the case number
            r"(?:.*?Trial\s+Judge:\s*(?P<lower_court_judge>[^\n\r]+))?",  # optional trial judge
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(cleaned_text)
        if match:
            lower_court = re.sub(
                r"\s+", " ", match.group("lower_court")
            ).strip()
            lower_court_number = match.group("lower_court_number").strip()
            lower_court_judge = match.group("lower_court_judge")
            docket = metadata.setdefault("Docket", {})
            originating_court_info = metadata.setdefault(
                "OriginatingCourtInformation", {}
            )
            if lower_court:
                docket["appeal_from_str"] = lower_court
            if lower_court_number:
                originating_court_info["docket_number"] = lower_court_number
            if lower_court_judge:
                originating_court_info["assigned_to_str"] = (
                    lower_court_judge.strip()
                )
        else:
            fall_back_pattern = re.compile(
                r"On\s+Appeal\s+from\s*\n*\s*(?:v\.)?\s*(?P<lower_court>.+?)(?:\n{2,}|$)",
                re.X | re.DOTALL,
            )
            match = fall_back_pattern.search(scraped_text[:1000])
            if match:
                lower_court = re.sub(
                    r"\s+", " ", match.group("lower_court")
                ).strip()
                docket = metadata.setdefault("Docket", {})
                docket["appeal_from_str"] = lower_court

        return metadata
