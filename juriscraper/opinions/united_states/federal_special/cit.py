# Scraper for the United States Court of International Trade
# CourtID: cit
# Court Short Name: Ct. Int'l Trade
# Neutral Citation Format: Ct. Int'l Trade No. 12-1
from abc import ABC
import time
from datetime import date, datetime

from lxml import html

from juriscraper.OpinionSite import OpinionSite
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    doc_dates = []
    case_title = []
    case_docks = []
    case_urls  = []
    case_cites = []
    case_stats = []
    case_judge = []
    case_suits = []
    case_filed = []


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.url = "http://www.cit.uscourts.gov/SlipOpinions/index.html"
        self.court_id = self.__module__
        self.base = '//tr[../tr/th[contains(., "Caption")]]'

    def _get_download_urls(self):
        # return [t for t in self.html.xpath(f"{self.base}/td[1]/a/@href")]
        return self.case_urls

    def _get_citations(self):
        # neutral_citations = []
        # for t in self.html.xpath(f"{self.base}/td[1]/a/text()"):
        #     year, item_number = t.split("-")
        #     neutral_citations.append(f"20{year} CIT {item_number}")
        return self.case_cites

    def _get_date_filed_is_approximate(self):
        return [False for _ in self.case_urls]

    def _get_case_names(self):
        # Exclude confidential rows by ensuring there is a sibling row that
        # contains an anchor (which confidential cases do not)
        # case_names = []
        # path = f"{self.base}/td[2][../td/a]"
        # for e in self.html.xpath(path):
        #     text = e.text_content().strip()
        #     case_name = text.split("\n")[0]
        #     case_names.append(case_name)
        return self.case_title

    def _get_precedential_statuses(self):
        # statuses = []
        # for e in self.html.xpath(f"{self.base}/td[2][../td/a]"):
        #     s = (
        #         html.tostring(e, method="text", encoding="unicode")
        #         .lower()
        #         .strip()
        #     )
        #     if "errata" in s:
        #         statuses.append("Errata")
        #     else:
        #         statuses.append("Published")
        return self.case_stats

    def _get_case_dates(self):
        # This does not capture the release dates for the errata documents.
        # The errata release date is listed in column 2. This will use the
        # original release date instead.
        # dates = []
        # date_formats = ["%m/%d/%Y", "%m/%d/%y"]
        # for date_string in self.html.xpath(
        #     f"{self.base}/td[3][../td/a]//text()"
        # ):
        #     for date_format in date_formats:
        #         try:
        #             d = date.fromtimestamp(
        #                 time.mktime(
        #                     time.strptime(date_string.strip(), date_format)
        #                 )
        #             )
        #             dates.append(d)
        #             break
        #         except ValueError:
        #             # Try the next format
        #             continue
        return self.doc_dates

    def _get_docket_numbers(self):
        # docket_numbers = []
        # for e in self.html.xpath(f"{self.base}/td[4][../td/a]"):
        #     docket_numbers.append(
        #         html.tostring(e, method="text", encoding="unicode").strip()
        #     )
        return self.case_docks

    def _get_judges(self):
        # judges = []
        # for e in self.html.xpath(f"{self.base}/td[5][../td/a]"):
        #     s = html.tostring(e, method="text", encoding="unicode")
        #     judges.append(s)
        return self.case_judge


    def _get_nature_of_suit(self):
        # return [    t for t in self.html.xpath(f"{self.base}/td[6][../td/a]/text()")]
        return self.case_suits

    def _process_html(self):
        for t in self.html.xpath(f"{self.base}/td[1]/a/@href"):
            self.case_urls.append(t)

        for t in self.html.xpath(f"{self.base}/td[6][../td/a]/text()"):
            self.case_suits.append(t)

        for e in self.html.xpath(f"{self.base}/td[5][../td/a]"):
            s = html.tostring(e, method="text", encoding="unicode")
            self.case_judge.append(s.split())

        for e in self.html.xpath(f"{self.base}/td[4][../td/a]"):
            self.case_docks.append(html.tostring(e, method="text", encoding="unicode").replace("\n\t\t\t"," ").replace("Consol.","").strip().split(" "))

        date_formats = ["%m/%d/%Y", "%m/%d/%y"]
        for date_string in self.html.xpath(f"{self.base}/td[3][../td/a]//text()"):
            for date_format in date_formats:
                try:
                    d = date.fromtimestamp(time.mktime(time.strptime(date_string.strip(), date_format)))
                    self.doc_dates.append(d)
                    break
                except ValueError:
                    # Try the next format
                    continue

        for e in self.html.xpath(f"{self.base}/td[2][../td/a]"):
            s = (html.tostring(e, method="text", encoding="unicode").lower().strip())
            if "errata" in s:
                self.case_stats.append("Errata")
            else:
                self.case_stats.append("Published")

        path = f"{self.base}/td[2][../td/a]"
        for e in self.html.xpath(path):
            text = e.text_content().strip()
            case_name = text.split("\n")[0]
            self.case_title.append(case_name)

        for t in self.html.xpath(f"{self.base}/td[1]/a/text()"):
            year, item_number = t.split("-")
            self.case_cites.append([f"20{year} CIT {item_number}"])


    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        for year in range(start_date.year,end_date.year+1):
            self.url=f"https://www.cit.uscourts.gov/content/slip-opinions-{year}"
            self.parse()
            self.downloader_executed=False
        return 0

    def get_class_name(self):
        return "cit"

    def get_court_type(self):
        return "Special"

    def get_state_name(self):
        return "Trade"

    def get_court_name(self):
        return "US Court of International Trade"
