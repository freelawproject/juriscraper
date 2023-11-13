from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.njcourts.gov/attorneys/opinions/supreme"
        self.status = "Published"

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        for row in self.html.xpath("//div[@class='card-body']"):
            url = row.xpath(".//a[@class='text-underline-hover']/@href")[0]
            name = row.xpath(".//a[@class='text-underline-hover']/text()")[0]
            if "njtax" in self.court_id:
                pass
            else:
                name, other = name.split("(", 1)
            docket = row.xpath(
                ".//div[@class='badge badge-default rounded-0 one-line-truncate me-1 mt-1']/text()"
            )[0]
            date = row.xpath(
                ".//div[@class='col-lg-12 small text-muted mt-2']/text()"
            )[0]
            self.cases.append(
                {
                    "date": date,
                    "docket": docket,
                    "name": titlecase(name.strip()),
                    "url": url,
                }
            )
