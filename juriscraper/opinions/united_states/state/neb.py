from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = (
            "https://supremecourt.nebraska.gov/courts/supreme-court/opinions"
        )
        self.status = "Published"

    def _process_html(self):
        path = {
            "group": '//div[contains(@class, "view-grouping")]',
            "date": './/span[contains(@class, "date-display-single")]',
            "row": ".//tbody/tr",
        }
        for group in self.html.xpath(path["group"]):
            date_element = group.xpath(path["date"])
            if not date_element:
                continue
            date = date_element[0].text_content()
            for row in group.xpath(path["row"]):
                url = row.xpath(".//td[3]//a/@href")

                # skip rows without url in third cell
                if not url:
                    continue

                self.cases.append(
                    {
                        "date": date,
                        "docket": row.xpath(".//td[1]")[0].text_content(),
                        "name": row.xpath(".//td[3]")[0].text_content(),
                        "citation": row.xpath(".//td[2]")[0].text_content(),
                        "url": url[0],
                    }
                )
