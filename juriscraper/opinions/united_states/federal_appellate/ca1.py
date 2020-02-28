from six.moves.urllib.parse import urlencode
from datetime import date, timedelta, datetime

import re
from dateutil.rrule import DAILY, rrule
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.base_url = "http://media.ca1.uscourts.gov/cgi-bin/opinions.pl"
        self.court_id = self.__module__
        today = date.today()
        params = urlencode(
            {
                "FROMDATE": (today - timedelta(7)).strftime("%m/%d/%Y"),
                "TODATE": today.strftime("%m/%d/%Y"),
                "puid": "",
            }
        )
        self.url = "{}/?{}".format(self.base_url, params)
        # self.url = "http://media.ca1.uscourts.gov/cgi-bin/opinions.pl/?TODATE=06%2F24%2F1993&puid=&FROMDATE=05%2F25%2F1993"
        self.interval = 30
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                DAILY,
                interval=self.interval,
                dtstart=date(1992, 1, 1),
                until=date(2016, 1, 1),
            )
        ]

    def _get_case_names(self):
        return [
            e.strip()
            for e in self.html.xpath(
                "//tr[position() > 1]/td[4]/text()[contains(., 'v.')]"
            )
        ]

    def _get_download_urls(self):
        return [
            e for e in self.html.xpath("//tr[position() > 1]/td[2]//@href")
        ]

    def _get_case_dates(self):
        dates = []
        for s in self.html.xpath("//tr[position() > 1]/td[1]//text()"):
            s = s.replace(r"\t", "").replace(r"\n", "").strip()
            if s == "1996/05/32":
                s = "1996/05/30"  # My life is thus lain to waste.
            dates.append(datetime.strptime(s.strip(), "%Y/%m/%d").date())
        return dates

    def _get_docket_numbers(self):
        regex = re.compile(r"(\d{2}-.*?\W)(.*)$")
        docket_numbers = []
        for s in self.html.xpath("//tr[position() > 1]/td[2]/a/text()"):
            s = s.replace("O1-", "01-")  # I grow older, the input grows worse.
            docket_numbers.append(
                regex.search(s).group(1).strip().replace(".", "")
            )
        return docket_numbers

    def _get_precedential_statuses(self):
        statuses = []
        for text in self.html.xpath("//tr[position() > 1]/td[2]//@href"):
            if "U" in text:
                statuses.append("Unpublished")
            elif "P" in text:
                statuses.append("Published")
            elif "E" in text:
                statuses.append("Errata")
            else:
                statuses.append("Unknown")
        return statuses

    def _get_lower_courts(self):
        lower_courts = []
        for e in self.html.xpath("//tr[position() > 1]/td[4]/font"):
            try:
                lower_courts.append(e.xpath("./text()")[0].strip())
            except IndexError:
                lower_courts.append("")
        return lower_courts

    def _download_backwards(self, d):
        params = urlencode(
            {
                "FROMDATE": d.strftime("%m/%d/%Y"),
                "TODATE": (d + timedelta(self.interval)).strftime("%m/%d/%Y"),
                "puid": "",
            }
        )
        self.url = "{}/?{}".format(self.base_url, params)

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    def _post_parse(self):
        """This will remove the cases without a case name"""
        to_be_removed = [
            index
            for index, case_name in enumerate(self.case_names)
            if not case_name.replace("v.", "").strip()
        ]

        for attr in self._all_attrs:
            item = getattr(self, attr)
            if item is not None:
                new_item = self.remove_elements(item, to_be_removed)
                self.__setattr__(attr, new_item)

    @staticmethod
    def remove_elements(list_, indexes_to_be_removed):
        return [
            i for j, i in enumerate(list_) if j not in indexes_to_be_removed
        ]
