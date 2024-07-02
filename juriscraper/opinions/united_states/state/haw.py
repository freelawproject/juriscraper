# Author: Michael Lissner
# Date created: 2013-05-23


from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = (
            "https://www.courts.state.hi.us/opinions_and_orders/opinions"
        )
        self.court_id = self.__module__
        self.court_code = "S.Ct"
        self.status = "Published"

    def _process_html(self) -> None:
        """Parse HTML into case objects

        :return: None
        """
        for row in self.html.xpath("//tr[@class='row-']"):
            date, court, docket, name, lower_court, citation = row.xpath(
                ".//td"
            )
            court = court.text_content()
            if court != self.court_code:
                continue

            if not docket.xpath(".//a"):
                continue

            name = name.text_content().split("(")[0]
            self.cases.append(
                {
                    "date": date.text_content(),
                    "name": name,
                    "docket": docket.text_content()
                    .strip()
                    .split("\t")[0]
                    .split()[0],
                    "url": docket.xpath(".//a")[0].get("href"),
                    "lower_court": lower_court.text_content(),
                    "citation": citation.text_content(),
                }
            )
