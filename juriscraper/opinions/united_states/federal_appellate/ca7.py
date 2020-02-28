# Scraper for the United States Court of Appeals for the Seventh Circuit
# CourtID: ca7
# Court Short Name: 7th Cir.

import time
from six.moves.urllib.parse import urlencode
from datetime import date, timedelta
from dateutil.rrule import rrule, DAILY
from lxml import html

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.a_while_ago = date.today() - timedelta(days=60)
        self.url = (
            "http://media.ca7.uscourts.gov/cgi-bin/rssExec.pl?Time=any&FromMonth={month}&FromDay={day}&FromYear={year}&"
            "ToMonth=&ToDay=&ToYear=&Author=any&AuthorName=&Case=any&CaseY1=&CaseY2=&CaseN1=&CaseN2=&CaseN3=&"
            "CaseN4=&Submit=Submit&RssJudgeName=Easterbrook&OpsOnly=no".format(
                month=self.a_while_ago.month,
                day=self.a_while_ago.day,
                year=self.a_while_ago.year,
            )
        )
        self.court_id = self.__module__

        self.interval = 30
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                DAILY,
                interval=self.interval,  # Every interval days
                dtstart=date(1999, 10, 1),
                until=date(2015, 1, 1),
            )
        ]

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath("//table//table/tr[position() >= 3]/td[2]"):
            s = html.tostring(e, method="text", encoding="unicode")
            case_names.append(s)
        return case_names

    def _get_download_urls(self):
        return [
            e
            for e in self.html.xpath(
                "//table[2]/tr/td/table/tr[position() >=3]/td/a/@href"
            )
        ]

    def _get_case_dates(self):
        return [
            date.fromtimestamp(
                time.mktime(time.strptime(date_string.strip(), "%m/%d/%Y"))
            )
            for date_string in self.html.xpath(
                "//table//table/tr[position() >= 3]/td[4]/text()"
            )
        ]

    def _get_docket_numbers(self):
        return [
            docket_number
            for docket_number in self.html.xpath(
                "//table//table/tr[position() >= 3]/td[1]/text()"
            )
        ]

    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath("//table//table/tr[position() >= 3]/td[5]/a"):
            s = html.tostring(e, method="text", encoding="unicode")
            if "Opinion" in s:
                statuses.append("Published")
            elif "Nonprecedential" in s:
                statuses.append("Unpublished")
            else:
                statuses.append("Unknown")
        return statuses

    def _get_nature_of_suit(self):
        natures = []
        for e in self.html.xpath("//table//table/tr[position() >= 3]/td[3]"):
            natures.append(html.tostring(e, method="text", encoding="unicode"))
        return natures

    def _get_judges(self):
        judges = []
        for e in self.html.xpath("//table//table/tr[position() >= 3]/td[6]"):
            s = html.tostring(e, method="text", encoding="unicode")
            if s.lower().strip() == "percuriam":
                s = "Per Curiam"
            judges.append(s)
        return judges

    def _download_backwards(self, d):
        to_date = d + timedelta(self.interval)
        params = urlencode(
            {
                "Time": "any",
                "FromMonth": d.month,
                "FromDay": d.day,
                "FromYear": d.year,
                "ToMonth": to_date.month,
                "ToDay": to_date.day,
                "ToYear": to_date.year,
                "Author": "any",
                "AuthorName": "",
                "Case": "any",
                "CaseY1": "",
                "CaseY2": "",
                "CaseN1": "",
                "CaseN2": "",
                "CaseN3": "",
                "CaseN4": "",
                "Submit": "Submit",
                "RssJudgeName": "Easterbrook",
                "OpsOnly": "no",
            }
        )
        self.base_url = "http://media.ca7.uscourts.gov/cgi-bin/rssExec.pl"
        self.url = "{}?{}".format(self.base_url, params)

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
