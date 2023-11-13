from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.courts.state.va.us/scndex.htm"
        self.status = "Published"

    def _process_html(self):
        for row in self.html.xpath("//p"):
            links = row.xpath(".//a")
            if len(links) != 2:
                continue
            name = row.xpath(".//b/text()")[0].strip()
            summary = row.text_content().split(name)[1].strip()
            date = summary.split("\n")[0].strip()
            if "Revised" in date:
                date = date.split("Revised")[1].strip()
            self.cases.append(
                {
                    "name": row.xpath(".//b/text()")[0].strip(),
                    "docket": links[0].get("name"),
                    "url": links[1].get("href"),
                    "summary": summary,
                    "date": date,
                }
            )
