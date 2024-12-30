"""Scraper for Superior Court of Maine
CourtID: mesuperct
Court Short Name: Me. Super Ct
Author: William E. Palin
Date created: December 28, 2023

History:
  2023-12-28: Created
"""

from datetime import date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"https://apps.maine.edu/SuperiorCourt/show_list.jsp?plaintiff=&defendant=&year={date.today().year}&code=&rule=&title=&number=&section=&Search=Search"
        self.base_path = ["placeholder"]
        self.back_scrape_iterable = [1]

    def _download_backwards(self, d: date) -> None:
        """Sets the URL for the backwards download based on the given date.

        :param d: Just a placeholder value
        :return: None
        """
        self.url = "https://apps.maine.edu/SuperiorCourt/show_list.jsp?plaintiff=&defendant=&year=&code=&rule=&title=&number=&section=&Search=Search"

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
