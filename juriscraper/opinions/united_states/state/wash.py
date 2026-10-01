from datetime import date, datetime

from juriscraper.AbstractSite import logger
from juriscraper.Backscraper import YearBackscraper
from juriscraper.lib.type_utils import OpinionType
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear, YearBackscraper):
    # Oldest opinion listed in the "byYear" pages; earlier years are empty
    first_opinion_date = date(2013, 2, 28)
    # Example URL:
    # https://www.courts.wa.gov/opinions/index.cfm?fa=opinions.byYear&fileYear=2025&crtLevel=S&pubStatus=PUB
    # crtLevel = S; is the Supreme Court
    crt_level = "S"
    pub_status = "PUB"

    url_template = "https://www.courts.wa.gov/opinions/index.cfm?fa=opinions.byYear&fileYear={}&crtLevel={}&pubStatus={}"

    name_td_index = 3
    type_td_index = 4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        year = datetime.today().year
        self.url = self.url_template.format(
            year, self.crt_level, self.pub_status
        )
        self.status = "Published"
        YearBackscraper.make_backscrape_iterable(self, kwargs)

    def _process_html(self):
        anchor_xpath = "a[contains(@href, '/opinions/pdf/')]"

        for row in self.html.xpath(f"//tr[td[{anchor_xpath}]]"):
            date = row.xpath("td[1]/text()")[0]
            url = row.xpath(f"td/{anchor_xpath}/@href")[0]
            docket = row.xpath(f"td[{anchor_xpath}]/a[1]/text()")[0]
            name = row.xpath(f"td[{self.name_td_index}]/text()")[0].strip()
            type_string = row.xpath(f"td[{self.type_td_index}]/text()")[0]

            if type_string == "Majority Opinion":
                op_type = OpinionType.MAJORITY
            else:
                # Example string values, which match the 'Combined' type
                # Majority Opinion and an Order
                # Maj., and Con. Opinions
                # Maj., and Dis. Opinions
                op_type = OpinionType.COMBINED

            self.cases.append(
                {
                    "date": date,
                    "url": url,
                    "docket": docket,
                    "name": name,
                    "type": op_type.value,
                }
            )

    async def _download_backwards(self, year: int) -> None:
        logger.info("Backscraping for year %s", year)
        self.url = self.url_template.format(
            year, self.crt_level, self.pub_status
        )
        self.html = await self._download()
        self._process_html()
