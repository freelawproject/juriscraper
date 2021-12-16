import re
from urllib.parse import quote

from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.utcourts.gov/opinions/appopin/index.htm"
        self.court_id = self.__module__
        self.regex = r"Case No. (.*?), Filed (.*?), (\d{4} UT App \d+)"

    def _process_html(self) -> None:
        for row in self.html.xpath("//a[@class='pdf']/parent::p"):
            link = row.xpath("./a")[0]
            x = " ".join(row.xpath(".//text()")).strip()
            if "Superseded" in x:
                continue
            m = re.search(self.regex, x)
            if not m:
                continue
            date = m.groups()[1]
            if "Filed" in date:
                date = date.replace("Filed", "").strip()
            citation = m.groups()[2]
            docket_number = m.groups()[0]
            self.cases.append(
                {
                    "date": date,
                    "name": row.xpath(".//text()")[0],
                    "neutral_citation": citation,
                    "url": quote(link.attrib["href"], safe=":/"),
                    "docket": docket_number,
                    "status": "Published",
                }
            )
