"""Scraper for Superior Court of Maine
CourtID: mesuperct
Court Short Name: Me. Super Ct
Author: William E. Palin
Date created: December 28, 2023

History:
  2023-12-28: Created
  2025-02-25: Implement backscraper
"""

from datetime import date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    base_url = "https://apps.maine.edu/SuperiorCourt/show_list.jsp?plaintiff=&defendant=&year={}&code=&rule=&title=&number=&section=&Search=Search"
    start_year = 1999

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.current_year = date.today().year
        self.make_backscrape_iterable(kwargs)
        self.url = self.base_url.format(self.current_year)

    def _download_backwards(self, year: int) -> None:
        """Sets the URL for the backwards download based on the given year.

        :param year: year to scrape
        :return: None
        """
        self.url = self.base_url.format(year)
        self.html = self._download()
        self._process_html()

    def _process_html(self) -> None:
        """Processes the HTML content and extracts case information.

        Iterates over the rows of the HTML table, extracting case details and appending
        them to the cases list as dictionaries.

        :return: None
        """

        for row in self.html.xpath("//tr")[1:]:
            docket_number = row.xpath(".//td//a/text()")[0].strip()
            date = row.xpath(".//td/text()")[-1].strip()
            plaintiff = row.xpath(".//td/a/text()")[1].strip()
            defendant = row.xpath(".//td/a/text()")[2].strip()
            url = f"https://files.mainelaw.maine.edu/library/SuperiorCourt/decisions/{docket_number}.pdf"
            author = row.xpath(".//td/a/text()")[3].strip()
            self.cases.append(
                {
                    "date": date,
                    "docket": docket_number,
                    "url": url,
                    "name": f"{plaintiff} v. {defendant}",
                    "status": "Unpublished",
                    "judge": author,
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
