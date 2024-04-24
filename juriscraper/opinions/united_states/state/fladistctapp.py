# Base scraper
# CourtID: flaapp
# Court Short Name: flaapp

from datetime import datetime, timedelta

from juriscraper.lib.exceptions import SkipRowError
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_number = None
        self.offset = 0
        self.number = None
        self.base = "https://1dca.flcourts.gov"
        self.update_url()

    def update_url(self) -> None:
        """Scrape last 7 days of opinions

        :return: none
        """
        today = datetime.now().strftime("%m/%d/%Y")
        prev = (datetime.now() - timedelta(days=7)).strftime("%m/%d/%Y")

        self.url = "".join(
            [
                self.base,
                "/search?sort=opinion/disposition_date%20desc,%20opinion/case_number%20asc&view=full",
                "&searchtype=opinions",
                "&limit=10",
                f"&scopes[]={self.number}_district_court_of_appeal",
                "&type[]=pca",
                "&type[]=written",
                f"&startdate={prev}",
                f"&enddate={today}",
                "&date[year]=",
                "&date[month]=",
                "&date[day]=",
                "&query=",
                f"&offset={self.offset}",
            ]
        )

    def parse_url(self, link):
        """Parse URL from link cell

        :param link: The html cell to parse
        :return: URL
        """
        try:
            url = link.xpath(".//a")[0].get("href")
            return url
        except IndexError:
            raise SkipRowError(f"Skipping row because document URL missing")

    def _process_html(self) -> None:
        """Process the html and extract out the opinions
        Paginates if necessary

        :return: None
        """
        for row in self.html.xpath("//tr"):
            if not row.xpath(".//td"):
                continue
            (
                link,
                filetype,
                docket,
                name,
                disposition,
                note,
                date_filed,
            ) = row.xpath(".//td")
            try:
                url = self.parse_url(link)
            except SkipRowError:
                continue
            self.cases.append(
                {
                    "name": name.text_content().strip(),
                    "date": date_filed.text_content().strip(),
                    "disposition": disposition.text_content().strip(),
                    "url": url,
                    "status": "Published",
                    "docket": docket.text_content().strip(),
                }
            )

        paginator_exists = self.html.xpath("//ul[@class='pagination']")
        paginator_disabled = self.html.xpath('//li[@class="next disabled"]')
        if paginator_exists and not paginator_disabled:
            self.offset = self.offset + 10
            self.update_url()
            self.html = super()._download()
            self._process_html()
