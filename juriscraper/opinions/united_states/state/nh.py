"""
Scraper for New Hampshire Supreme Court
CourtID: nh
Court Short Name: NH
Court Contact: webmaster@courts.state.nh.us
Author: Andrei Chelaru
Reviewer: mlr
History:
    - 2014-06-27: Created
    - 2014-10-17: Updated by mlr to fix regex error.
    - 2015-06-04: Updated by bwc so regex catches comma, period, or
    whitespaces as separator. Simplified by mlr to make regexes more semantic.
    - 2016-02-20: Updated by arderyp to handle strange format where multiple
    case names and docket numbers appear in anchor text for a single case pdf
    link. Multiple case names are concatenated, and docket numbers are
    concatenated with ',' delimiter
    - 2021-12-22: Updated for new web site, by satsuki-chan
"""

from datetime import date

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = f"https://www.courts.nh.gov/our-courts/supreme-court/orders-and-opinions/opinions/{date.today().year}"
        self.cases = []

    def _process_html(self) -> None:
        path = "//div[@class='tabulator-cell']/div[@class='document__detail']/div[@class='document__detail__container']"
        for item in self.html.xpath(path):
            title = item.xpath(
                "./div[@class='document__detail__title']/h3//text()"
            )[0]
            url = item.xpath(
                "./div[@class='document__detail__title']/h3/a/@href"
            )[0]
            date = item.xpath(
                "./div[@class='document__detail__information'][2]/div/text()"
            )[0]
            docket_name = title.split(", ", 1)
            if not docket_name:
                continue
            docket = docket_name[0].strip()
            name = docket_name[1].strip()

            self.cases.append(
                {
                    "name": name,
                    "url": url,
                    "date": date,
                    "status": "Published",
                    "docket": docket,
                }
            )
