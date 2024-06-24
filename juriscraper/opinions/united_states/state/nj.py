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

            name_content = row.xpath(
                ".//a[@class='text-underline-hover']/text()"
            )[0]
            name_str, _, _ = name_content.partition("(")

            docket = row.xpath('.//*[contains(@class, "mt-1")]/text()')[
                0
            ].strip()
            date = row.xpath(
                ".//div[@class='col-lg-12 small text-muted mt-2']/text()"
            )[0]

            case = {
                "date": date,
                "docket": docket,
                "name": titlecase(name_str.strip()),
                "url": url,
            }

            if self.status == "Published":
                summary = row.xpath(".//div[@class='modal-body']/p/text()")
                case["summary"] = "\n".join(summary)

            self.cases.append(case)
