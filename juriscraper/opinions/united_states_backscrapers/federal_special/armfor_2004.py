import time
from datetime import date

from lxml import html

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = (
            "http://www.armfor.uscourts.gov/newcaaf/opinions/2004Term.htm"
        )
        self.court_id = self.__module__

    def _get_case_names(self):
        return [t for t in self.html.xpath("//table//tr/td[1]/font/text()")]

    def _get_download_urls(self):
        download_urls = []
        for t in self.html.xpath(
            "//table//table//tr[position() > 1]/td[2]/div/font/a[2]/@href"
        ):
            download_urls.append(t)
        return download_urls

    def _get_case_dates(self):
        dates = []
        for e in self.html.xpath(
            "//table/tr[3]/td[2]/blockquote/table/tbody/tr[position() > 1]/td[3]"
        ):
            s = html.tostring(e, method="text", encoding="unicode")
            s = s.replace("June", "Jun").replace("July", "Jul")
            s = " ".join(s.split())
            dates.append(
                date.fromtimestamp(time.mktime(time.strptime(s, "%b %d, %Y")))
            )
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for t in self.html.xpath(
            "//table/tr[3]/td[2]/blockquote/table/tbody/tr/td[2]/div/font/a[1]/text()"
        ):
            docket_numbers.append(t)
        return docket_numbers

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_citations(self):
        neutral_citations = []
        for e in self.html.xpath(
            "//table/tr[3]/td[2]/blockquote/table/tbody/tr[position() > 1]/td[4]"
        ):
            s = html.tostring(e, method="text", encoding="unicode")
            neutral_citations.append(s)
        return neutral_citations
