"""
Scraper for Maryland Court of Appeals
CourtID: md
Court Short Name: MD
Author: Andrei Chelaru
Date created: 06/27/2014
Court Support: webmaster@mdcourts.gov, mdlaw.library@mdcourts.gov
"""

from datetime import date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://www.mdcourts.gov/cgi-bin/indexlist.pl?court={}&year={}&order=bydate&submit=Submit"
    court = "coa"
    start_year = 1995
    current_year = date.today().year
    empty_cite_strings = {"slip.op.", "."}
    no_judge_strings = {"Order", "PC Order", "Per Curiam"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = self.base_url.format(self.court, self.current_year)
        self.court_id = self.__module__
        self.disable_certificate_verification()
        self.status = "Published"
        self.make_backscrape_iterable(kwargs)

    def _process_html(self) -> None:
        """Parse HTML into case dictionaries

        :return None
        """
        for row in self.html.xpath("//table//tr[td and not (.//h2)]"):
            url = row.xpath("td//a[contains(@href,'pdf')]/@href")[0]
            docket = row.xpath("td[1]//text()")[0]
            date_filed, _, other_date = row.xpath("td[3]/font/text()")[
                0
            ].partition(" ")
            name = row.xpath("td[5]/font/text()")[0].split("(")[0].strip()

            per_curiam = False
            judge = row.xpath("td[4]/font/text()")[0].split("()")[0].strip()
            if judge in self.no_judge_strings:
                # Other strings in self.no_judge_strings point to
                # Per Curiam opinions
                per_curiam = judge != "Order"
                judge = ""

            cite = row.xpath("td[2]/font/text()")[0].strip()
            if cite in self.empty_cite_strings:
                cite = ""

            self.cases.append(
                {
                    "name": name,
                    "url": url,
                    "judge": judge,
                    "date": date_filed,
                    "docket": docket,
                    "citation": cite,
                    "per_curiam": per_curiam,
                    "other_date": other_date.strip(),
                }
            )

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        start = int(start) if start else self.start_year
        end = int(end) + 1 if end else self.current_year

        self.back_scrape_iterable = range(start, end)

    def _download_backwards(self, year: int) -> None:
        """Build URL with year input and scrape

        :param year: year to scrape
        :return None
        """
        self.url = self.base_url.format(self.court, year)
        self.html = self._download()
        self._process_html()
