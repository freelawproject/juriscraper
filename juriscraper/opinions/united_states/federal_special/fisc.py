from urllib.parse import urljoin

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.fisc.uscourts.gov/public-filings"
        self.status = "Published"
        self.back_scrape_iterable = ["placeholder"]
        self.do_backscrape = False

    def _process_html(self) -> None:
        """Parse HTML into case objects

        :return None
        """
        for row in self.html.xpath("//tr[td/a]"):
            filing_name, *_, filename = row.xpath("td/a/text()")
            if "opinion" not in filing_name.lower():
                continue

            docket = row.xpath("string(td[4])").strip()
            date_filed = row.xpath("td[1]/span/text()")[0]

            if self.skip_record(docket, filename):
                continue

            url = row.xpath(".//a/@href")[-1]
            self.cases.append(
                {
                    "date": date_filed.split(",")[-1],
                    "docket": docket,
                    "name": filing_name,
                    "url": url,
                }
            )

            next_page = self.html.xpath("//a[@title='Go to next page']/@href")
            if self.do_backscrape and next_page:
                # Perform download since we are not yielding a site for each
                # element in the backscrape iterable
                self.url = urljoin(self.url, next_page[0])
                self.html = self._download()
                self._process_html()

    def skip_record(self, docket: str, filename: str) -> bool:
        """Check if a record belongs to 'FISCR'

        :param docket: docket number
        :param filename: opinion title

        :return: True if record should skipped
        """
        return "FISCR" in docket or "FISCR" in filename

    def _download_backwards(self, _) -> None:
        """Start from second page up to last page

        :return None
        """
        self.do_backscrape = True
        self.url = "https://www.fisc.uscourts.gov/public-filings?page=1"
