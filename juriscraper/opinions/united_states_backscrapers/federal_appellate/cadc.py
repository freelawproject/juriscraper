import ssl
import time
from datetime import date

from dateutil.rrule import MONTHLY, rrule

from juriscraper.lib.network_utils import SSLAdapter
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "https://www.cadc.uscourts.gov/internet/opinions.nsf/OpinionsByMonday?OpenView&StartKey=20151020150928&Count=2&scode=1"
        self.court_id = self.__module__
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                MONTHLY,
                dtstart=date(1997, 9, 1),
                until=date(2015, 1, 1),
            )
        ]

    def _get_adapter_instance(self):
        """Unfortunately this court doesn't support modern crypto, so you have
        to manually downgrade the crypto it uses.

        See: http://stackoverflow.com/questions/14102416/
        """
        return SSLAdapter(ssl_version=ssl.PROTOCOL_TLSv1)

    def _get_case_names(self):
        return [
            e
            for e in self.html.xpath(
                "//div[@class='row-entry'][position() mod 2 = 1]/span[2]/text()"
            )
        ]

    def _get_download_urls(self):
        return [
            e
            for e in self.html.xpath(
                "//div[@class='row-entry'][position() mod 2 = 1]/span[1]/a/@href"
            )
        ]

    def _get_case_dates(self):
        dates = []
        for date_string in self.html.xpath(
            "//div[@class='row-entry'][position() mod 2 = 0]/span[2]/text()"
        ):
            dates.append(
                date.fromtimestamp(
                    time.mktime(time.strptime(date_string, "%m/%d/%Y"))
                )
            )
        return dates

    def _get_docket_numbers(self):
        return [
            e
            for e in self.html.xpath(
                "//div[@class='row-entry'][position() mod 2 = 1]/span[1]/a/text()"
            )
        ]

    def _get_precedential_statuses(self):
        return ["Published" for _ in range(0, len(self.case_names))]

    def _download_backwards(self, d):
        self.url = "https://www.cadc.uscourts.gov/internet/opinions.nsf/OpinionsByRDate?OpenView&count=100&SKey={}".format(
            d.strftime("%Y%m")
        )

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
