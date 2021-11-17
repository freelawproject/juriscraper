# Editor: mlr
# Maintenance log
#    Date     | Issue
# 2013-01-28  | InsanityException due to the court adding busted share links.
# 2014-07-02  | New website required rewrite.

from datetime import datetime

from juriscraper.lib.string_utils import clean_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://media.ca11.uscourts.gov/opinions/pub/logname.php"
        self.back_scrape_iterable = list(range(20, 10000, 20))

    def _get_case_names(self):
        return [
            e for e in self.html.xpath("//tr[./td[1]/a//text()]/td[1]//text()")
        ]

    def _get_download_urls(self):
        return [
            e for e in self.html.xpath("//tr[./td[1]/a//text()]/td[1]/a/@href")
        ]

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath(
            "//tr[./td[1]/a//text()]/td[5]//text()"
        ):
            s = clean_string(date_string)
            if s == "00-00-0000" and "begin=21160" in self.url:
                # Bad data found during backscrape.
                s = "12-13-2006"
            dates.append(datetime.strptime(clean_string(s), "%m-%d-%Y").date())
        return dates

    def _get_docket_numbers(self):
        return [
            e for e in self.html.xpath("//tr[./td[1]/a//text()]/td[2]//text()")
        ]

    def _get_precedential_statuses(self):
        if "unpub" in self.url:
            return ["Unpublished"] * len(self.case_names)
        else:
            return ["Published"] * len(self.case_names)

    def _get_nature_of_suit(self):
        return [
            e for e in self.html.xpath("//tr[./td[1]/a//text()]/td[4]//text()")
        ]

    def _download_backwards(self, n):
        self.url = "http://media.ca11.uscourts.gov/opinions/pub/logname.php?begin={}&num={}&numBegin=1".format(
            n, n / 20 - 1
        )

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
