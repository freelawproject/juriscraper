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
        for table in self.html.xpath(".//table"):
            date_tags = table.xpath("preceding::time[1]/text()")
            if not date_tags:
                print("NO DATE TAGS")
                continue
            for row in table.xpath(".//tr"):
                cells = row.xpath(".//td")
                # make sure its a valid row - and not the ending of the table
                if len(cells) != 3 or cells[0].xpath(".//text()") is None:
                    continue

                docket = cells[0].xpath(".//text()")[0].strip()
                citation = cells[1].xpath(".//text()")[0].strip()
                url = cells[2].xpath(".//a")[0].get("href")
                name = cells[2].xpath(".//a/text()")[0].strip()
                date = date_tags[0]

                self.cases.append(
                    {
                        "date": date,
                        "docket": docket,
                        "name": name,
                        "citation": citation,
                        "url": url,
                    }
                )
