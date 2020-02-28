# Scraper for the United States Court of International Trade
# CourtID: cit
# Court Short Name: Ct. Int'l Trade
# Neutral Citation Format: Ct. Int'l Trade No. 12-1
from juriscraper.OpinionSite import OpinionSite
import re
import time
from datetime import date
from lxml import html


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        # This is a special backscraper to deal with problems on the 2006 page.
        self.url = "http://www.cit.uscourts.gov/SlipOpinions/SlipOps-2006.html"
        self.court_id = self.__module__

    def _get_download_urls(self):
        return [
            t
            for t in self.html.xpath(
                "//table[3]/tr[position() > 1]/td[1]/a/@href | //table[3]/tr[position() > 1]/td[1]/font//@href"
            )
        ]

    def _get_neutral_citations(self):
        neutral_citations = []
        for e in self.html.xpath("//table[3]/tr[position() > 1]/td[1]"):
            s = html.tostring(e, method="text", encoding="unicode").strip()
            neutral_citations.append(s)
        return neutral_citations

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath("//table[3]/tr[position() > 1]/td[2]/font"):
            s = html.tostring(e, method="text", encoding="unicode").strip()
            # We strip "erratum: mm/dd/yyyy" from the case names of errata docs.
            if "erratum" in s:
                case_names.append(s.strip()[:-20])
            else:
                case_names.append(s.strip())
        return case_names

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_case_dates(self):
        case_dates = []
        for e in self.html.xpath("//table[3]/tr[position() > 1]/td[3]/font"):
            s = html.tostring(e, method="text", encoding="unicode").strip()
            case_dates.append(
                date.fromtimestamp(
                    time.mktime(time.strptime(s.strip(), "%m/%d/%Y"))
                )
            )
        return case_dates

    # Because there can be multiple docket numbers we have to replace some newlines.
    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath("//table[3]/tr[position() > 1]/td[4]"):
            s = html.tostring(e, method="text", encoding="unicode").strip()
            docket_numbers.append(s.replace("\r\n", " &"))
        return docket_numbers

    # Comment out the following section if backscraping years 1999-2005.
    # Because there are sometimes multiple judges we have to strip some whitespace.
    def _get_judges(self):
        judges = []
        for e in self.html.xpath("//table[3]/tr[position() > 1]/td[5]"):
            s = html.tostring(e, method="text", encoding="unicode")
            judges.append(s.strip())
        return judges
