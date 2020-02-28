from juriscraper.OpinionSite import OpinionSite
import time
from datetime import date
from lxml import html


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = (
            "http://www.armfor.uscourts.gov/newcaaf/opinions/2005Term.htm"
        )
        self.court_id = self.__module__

    def _get_case_names(self):
        return [t for t in self.html.xpath("//table//tr/td[1]/font/text()")]

    def _get_download_urls(self):
        return [
            t
            for t in self.html.xpath(
                '//table//tr/td[2]/font/a/@href[contains(., ".pdf")]'
            )
        ]

    def _get_case_dates(self):
        dates = []
        for e in self.html.xpath(
            "//table/tr[3]/td[2]/blockquote/table/tbody/tr[position() > 1]/td[3]"
        ):
            s = html.tostring(e, method="text", encoding="unicode").strip()
            dates.append(
                date.fromtimestamp(time.mktime(time.strptime(s, "%b %d, %Y")))
            )
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath("//table//table//tr[position() > 1]/td[2]"):
            s = html.tostring(e, method="text", encoding="unicode")
            docket_numbers.append(s.strip()[:-5])
        return docket_numbers

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_neutral_citations(self):
        neutral_citations = []
        for e in self.html.xpath(
            "//table/tr[3]/td[2]/blockquote/table/tbody/tr[position() > 1]/td[4]"
        ):
            s = html.tostring(e, method="text", encoding="unicode")
            neutral_citations.append(s)
        return neutral_citations
