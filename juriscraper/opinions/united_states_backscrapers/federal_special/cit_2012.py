from juriscraper.opinions.united_states.federal_special import cit
import time
from datetime import date
from lxml import html


class Site(cit.Site):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "http://www.cit.uscourts.gov/SlipOpinions/SlipOps-2012.html"
        self.court_id = self.__module__

    def _get_download_urls(self):
        return [t for t in self.html.xpath("//table[4]//tr/td[1]//a/@href")]

    def _get_neutral_citations(self):
        return [t for t in self.html.xpath("//table[4]//tr/td[1]//a/text()")]

    def _get_case_names(self):
        # Exclude confidential rows by ensuring there is a sibling row that
        # contains an anchor (which confidential cases do not)
        # There is also one stray case within a <p> tag we have to catch.
        return [
            s
            for s in self.html.xpath(
                "//table[4]//tr[position() > 1]/td[2][../td//a]/text()[1] | //table[4]//tr[position() > 1]/td[2][../td//a]/p/text()[1]"
            )
        ]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_case_dates(self):
        # This does not capture the release dates for the errata documents.
        # The errata release date is listed in column 2. This will use the
        # original release date instead.
        dates = []
        date_formats = ["%m/%d/%Y", "%m/%d/%y"]
        for date_string in self.html.xpath(
            "//table[4]//tr/td[3][../td//a]/text()"
        ):
            for date_format in date_formats:
                try:
                    d = date.fromtimestamp(
                        time.mktime(time.strptime(date_string, date_format))
                    )
                    dates.append(d)
                    break
                except ValueError:
                    # Try the next format
                    continue
        return dates

    def _get_docket_numbers(self):
        docket_numbers = []
        for e in self.html.xpath(
            "//table[4]//tr[position() > 1]/td[4][../td//a]"
        ):
            docket_numbers.append(
                html.tostring(e, method="text", encoding="unicode").strip()
            )
        return docket_numbers

    def _get_judges(self):
        judges = []
        for e in self.html.xpath(
            "//table[4]//tr[position() > 1]/td[5][../td//a]"
        ):
            s = html.tostring(e, method="text", encoding="unicode")
            judges.append(s)
        return judges

    def _get_nature_of_suit(self):
        return [
            t for t in self.html.xpath("//table[4]//tr/td[6][../td//a]/text()")
        ]
