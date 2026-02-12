import re
from datetime import date, datetime

from dateutil.rrule import MONTHLY, rrule

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    lower_court_regexes = [
        re.compile(r"(?P<lower_court>U\.S\. District Court.+)"),
        re.compile(r"(?P<lower_court>Board of Immigration Appeals)"),
        re.compile(r"(?P<lower_court>U\.S\. Bankruptcy Court.+)"),
        re.compile(r"(?P<lower_court>Securities (&|and) Exchange Commission)"),
    ]
    first_opinion_date = datetime(1995, 11, 1)
    days_interval = 365 * 35  # we just need the start and end input dates
    base_url = "https://media.ca8.uscourts.gov/cgi-bin/opnByMM.pl?theMM=%02d&theYY=%s&A1=Get+Opinions"
    is_bap_scraper = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__

        today = date.today()
        self.url = self.base_url % (today.month, today.year)

        self.request["verify"] = False
        self.make_backscrape_iterable(kwargs)

    def _process_html(self):
        for link in self.html.xpath('//a[contains(@href, "opndir")]'):
            url = link.get("href")
            text = link.xpath("following-sibling::text()")[0].strip()

            lower_court, is_bap_opinion = self.get_lower_court(text)
            if is_bap_opinion:
                if not self.is_bap_scraper:
                    logger.info("Skipping `bap8` opinion %s", text)
                    continue
            elif self.is_bap_scraper:
                logger.info("Skipping `ca8` opinion %s", text)
                continue

            first_line = text.split("\n")[0]
            date_filed, case_name = first_line.strip().split(" ", 1)
            docket_number = ", ".join(re.findall(r"\d{2}-\d{4}", text))

            doc_name = link.text_content().split(".")[0].lower()
            if "p" in doc_name:
                status = "Published"
            elif "u" in doc_name:
                status = "Unpublished"
            else:
                status = "Unknown"

            self.cases.append(
                {
                    "date": date_filed,
                    "docket": docket_number,
                    "url": url,
                    "status": status,
                    "name": case_name.strip(),
                    "lower_court": lower_court,
                }
            )

    def get_lower_court(self, text: str) -> tuple[str, bool]:
        """Parse the lower court and identify if it is a bankruptcy court

        :param text: the raw lower court text
        :return: a tuple (lower_court, true if the lower court is a bankrupcy
            court)
        """
        for pattern in self.lower_court_regexes:
            if match := pattern.search(text):
                court = match.group("lower_court").strip()
                return court, "Bankruptcy Court" in court

        return "", False

    def make_backscrape_iterable(self, kwargs) -> None:
        """Parse the input dates, and create a tick for each month"""
        super().make_backscrape_iterable(kwargs)
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                MONTHLY,
                dtstart=self.back_scrape_iterable[0][0],
                until=self.back_scrape_iterable[0][1],
            )
        ]

    def _download_backwards(self, d: date) -> None:
        """
        If an updated backscraper is needed in the future, this court
        updates the HTML with new values with a 4/5 months lag.
        Among the new values, I have seen the following fields we collect:
        per_curiam, judges and summaries are available
        """
        self.url = (
            "http://media.ca8.uscourts.gov/cgi-bin/opnByMM.pl?theMM=%02d&theYY=%s&A1=Get+Opinions"
            % (d.month, d.year)
        )
        logger.info("Backscraping %s-%s", d.year, d.month)
        self.html = self._download()
        self._process_html()
