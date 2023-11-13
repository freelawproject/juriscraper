# Base scraper
# CourtID: flaapp
# Court Short Name: flaapp

from datetime import datetime, timedelta

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

    def update_url(self):
        """"""
        today = datetime.now().strftime("%m/%d/%Y")
        prev = (datetime.now() - timedelta(days=7)).strftime("%m/%d/%Y")

        self.url = f"{self.base}/search?sort=opinion/disposition_date%20desc,%20opinion/case_number%20asc&view=full&searchtype=opinions&limit=10&scopes[]={self.number}_district_court_of_appeal&type[]=pca&type[]=written&startdate={prev}&enddate={today}&date[year]=&date[month]=&date[day]=&query=&offset={self.offset}"

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        for row in self.html.xpath("//tr"):
            if not len(row.xpath(".//td")):
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
            self.cases.append(
                {
                    "name": name.text_content().strip(),
                    "date": date_filed.text_content().strip(),
                    "disposition": disposition.text_content().strip(),
                    "url": link.xpath(".//a")[0].get("href"),
                    "status": "Published",
                    "docket": docket.text_content().strip(),
                }
            )

        if not self.html.xpath('.//li[@class="next disabled"]'):
            # If pagniation continues loop
            self.offset = self.offset + 10
            self.update_url()
            self.html = super()._download()
            self._process_html()
