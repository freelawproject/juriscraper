import re
import time
from datetime import date

from dateutil.rrule import MONTHLY, rrule

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        self.url = (
            "http://media.ca8.uscourts.gov/cgi-bin/opnByMM.pl?theMM=%02d&theYY=%s&A1=Get+Opinions"
            % (today.month, today.year)
        )
        self.court_id = self.__module__

        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                MONTHLY,
                dtstart=date(1995, 11, 1),
                until=date(2015, 1, 1),
            )
        ]

    def _get_case_names(self):
        case_names = []
        case_name_regex = re.compile(r"(\d{2}/\d{2}/\d{4})(.*)")
        for text in self.html.xpath(
            '//a[contains(@href, "opndir")]/following-sibling::b/text()'
        ):
            case_names.append(case_name_regex.search(text).group(2))
        return case_names

    def _get_download_urls(self):
        return [
            e for e in self.html.xpath('//a[contains(@href, "opndir")]/@href')
        ]

    def _get_case_dates(self):
        case_dates = []
        case_date_regex = re.compile(r"(\d{2}/\d{2}/\d{4})(.*)")
        for text in self.html.xpath(
            '//a[contains(@href, "opndir")]/following-sibling::b/text()'
        ):
            date_string = case_date_regex.search(text).group(1)
            case_dates.append(
                date.fromtimestamp(
                    time.mktime(time.strptime(date_string, "%m/%d/%Y"))
                )
            )
        return case_dates

    def _get_docket_numbers(self):
        docket_numbers = []
        docket_number_regex = re.compile(r"(\d{2})(\d{4})(u|p)", re.IGNORECASE)
        for docket_number in self.html.xpath(
            '//a[contains(@href, "opndir")]/text()'
        ):
            regex_results = docket_number_regex.search(docket_number)
            docket_numbers.append(
                f"{regex_results.group(1)}-{regex_results.group(2)}"
            )
        return docket_numbers

    def _get_precedential_statuses(self):
        statuses = []
        for docket_number in self.html.xpath(
            '//a[contains(@href, "opndir")]/text()'
        ):
            docket_number = docket_number.split(".")[0]
            if "p" in docket_number.lower():
                statuses.append("Published")
            elif "u" in docket_number.lower():
                statuses.append("Unpublished")
            else:
                statuses.append("Unknown")
        return statuses

    def _download_backwards(self, d):

        self.url = (
            "http://media.ca8.uscourts.gov/cgi-bin/opnByMM.pl?theMM=%02d&theYY=%s&A1=Get+Opinions"
            % (d.month, d.year)
        )

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
