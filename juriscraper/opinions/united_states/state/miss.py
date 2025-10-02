# Court Contact: bkraft@courts.ms.gov (see https://courts.ms.gov/aoc/aoc.php)
from datetime import date, timedelta
from urllib.parse import urljoin

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.method = "GET"
        self.publish_date = "09/11/2025"
        self.status = "Published"
        self.url = f"https://courts.ms.gov/appellatecourts/sc/scdecisions.php?date={self.publish_date}"
        self.use_proxy = True
        self.additional_params = {
            "wait_for": "#dispAreaHD > p:nth-child(2) > a"
        }

    @staticmethod
    def most_recent_release_date(day: int):
        """"""
        delta = (date.today().weekday() - day) % 7
        return (date.today() - timedelta(days=delta or 7)).strftime("%m/%d/%Y")

    def _process_html(self):
        """Process the html

        :return: None
        """
        for link in self.html.xpath(
            "//div[@id='dispAreaHD']//a[contains(@href, '.pdf')]"
        ):
            slug = link.xpath("./@href")[0]
            if not slug.startswith("http"):
                slug = urljoin(
                    "https://courts.ms.gov/images/",
                    slug[3:].replace("\\", "/"),
                )
            ul_nodes = link.xpath("./following::ul[1]")
            if not ul_nodes:
                continue
            self.cases.append(
                {
                    "date": self.publish_date,
                    "docket": link.text_content().strip(),
                    "name": ul_nodes[0]
                    .xpath(".//b")[0]
                    .text_content()
                    .strip(),
                    "summary": ul_nodes[0].text_content().strip(),
                    "url": slug,
                }
            )
