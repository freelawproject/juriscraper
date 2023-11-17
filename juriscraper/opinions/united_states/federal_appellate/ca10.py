from lxml import html

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = (
            "http://www.ca10.uscourts.gov/opinions/new/daily_decisions.rss"
        )
        self.court_id = self.__module__

    def _process_html(self):
        for item in self.html.xpath(".//item"):
            for e in item.xpath(
                ".//description/text()",
                namespaces={"dc": "http://purl.org/dc/elements/1.1/"},
            ):
                if "Published Opinion" in e:
                    status = "Published"
                else:
                    status = "Unpublished"
                docket = e.split()[1].strip()
            date = convert_date_string(item.xpath(".//pubdate/text()")[0])
            formatted_date = date.strftime("%Y-%m-%d")
            self.cases.append(
                {
                    "url": html.tostring(item.xpath("link")[0], method="text")
                    .decode()
                    .replace("\\n", "")
                    .strip(),
                    "name": item.xpath(".//title/text()")[0],
                    "date": formatted_date,
                    "status": status,
                    "docket": docket,
                }
            )
