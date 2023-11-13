from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.vacourts.gov/wpcap.htm"
        self.status = "Published"

    def _process_html(self):
        for row in self.html.xpath("//p"):
            links = row.xpath(".//a")
            name = row.xpath(".//b/text()")
            if not name:
                continue
            date, disposition, *_ = row.text_content().splitlines()
            date = date.split(name[0])[1]
            self.cases.append(
                {
                    "name": name[0].strip(),
                    "docket": links[0].get("href").split("/")[-1][:-4],
                    "url": links[0].get("href"),
                    "disposition": disposition,
                    "date": date.strip(),
                }
            )
