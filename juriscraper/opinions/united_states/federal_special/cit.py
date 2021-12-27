# Scraper for the United States Court of International Trade
# CourtID: cit
# Court Short Name: Ct. Int'l Trade
# Neutral Citation Format: Ct. Int'l Trade No. 12-1

import time
from datetime import date

from lxml import html

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.cit.uscourts.gov/SlipOpinions/index.html"
        self.court_id = self.__module__
        self.base = '//tr[../tr/th[contains(., "Caption")]]'

    def _get_download_urls(self):
        return [t for t in self.html.xpath(f"{self.base}/td[1]/a/@href")]

    def _get_neutral_citations(self):
        neutral_citations = []
        for t in self.html.xpath(f"{self.base}/td[1]/a/text()"):
            year, item_number = t.split("-")
            neutral_citations.append(f"20{year} CIT {item_number}")
        return neutral_citations

    def _get_case_names(self):
        # Exclude confidential rows by ensuring there is a sibling row that
        # contains an anchor (which confidential cases do not)
        case_names = []
        path = f"{self.base}/td[2][../td/a]"
        for e in self.html.xpath(path):
            text = e.text_content().strip()
            case_name = text.split("\n")[0]
            case_names.append(case_name)
        return case_names

    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath(f"{self.base}/td[2][../td/a]"):
            s = (
                html.tostring(e, method="text", encoding="unicode")
                .lower()
                .strip()
            )
            if "errata" in s:
                statuses.append("Errata")
            else:
                statuses.append("Published")
        return statuses

    def _get_case_dates(self):
        # This does not capture the release dates for the errata documents.
        # The errata release date is listed in column 2. This will use the
        # original release date instead.
        dates = []
        date_formats = ["%m/%d/%Y", "%m/%d/%y"]
        for date_string in self.html.xpath(
            f"{self.base}/td[3][../td/a]//text()"
        ):
            for date_format in date_formats:
                try:
                    d = date.fromtimestamp(
                        time.mktime(
                            time.strptime(date_string.strip(), date_format)
                        )
                    )
                    dates.append(d)
                    break
                except ValueError:
                    # Try the next format
                    continue
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath(f"{self.base}/td[4][../td/a]"):
            docket_numbers.append(
                html.tostring(e, method="text", encoding="unicode").strip()
            )
        return docket_numbers

    def _get_judges(self):
        judges = []
        for e in self.html.xpath(f"{self.base}/td[5][../td/a]"):
            s = html.tostring(e, method="text", encoding="unicode")
            judges.append(s)
        return judges

    def _get_nature_of_suit(self):
        return [
            t for t in self.html.xpath(f"{self.base}/td[6][../td/a]/text()")
        ]
