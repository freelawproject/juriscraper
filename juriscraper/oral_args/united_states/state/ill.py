"""
CourtID: ill
Court Short Name: Ill.
Author: Rebecca Fordon
Reviewer: Mike Lissner
History:
* 2016-06-22: Created by Rebecca Fordon
"""


from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OralArgumentSite import OralArgumentSite


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.illinoiscourts.gov/Media/On_Demand.asp"
        self.cell_index_docket = 2
        self.cell_index_download = 5
        self.cell_index_name = 3
        # Extract data from all rows with mp3 url/link
        self.xpath_root = '(//table[(.//th)[1][contains(.//text(), "Argument Date")]])[last()]//tr[position() > 1][.//@href[contains(., ".mp3")]]'
        self.back_scrape_iterable = range(2008, 2016)

    def _get_download_urls(self):
        path = self.xpath_root + "/td[%d]//@href" % self.cell_index_download
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        dates = []
        path = self.xpath_root + "/td[1]"
        for e in self.html.xpath(path):
            s = e.text_content()
            try:
                d = convert_date_string(s, fuzzy=True)
            except ValueError:
                continue
            else:
                dates.append(d)
        return dates

    def _get_case_names(self):
        path = "%s/td[%d]" % (self.xpath_root, self.cell_index_name)
        cases = []
        for case in self.html.xpath(path):
            case = case.text_content().strip()
            if case:
                cases.append(case)
        return cases

    def _get_docket_numbers(self):
        path = "%s/td[%d]" % (self.xpath_root, self.cell_index_docket)
        dockets = []
        for docket in self.html.xpath(path):
            docket = docket.text_content()
            dockets.append(docket)
        return dockets

    def _download_backwards(self, date_str):
        """Backwards urls are just the regular ones with a year munged at the
        end.
        """
        # Set it to the value that seems to work everywhere.
        if getattr(self, "orig_url", None):
            # Set url back to its original value, if it has been reset already.
            self.url = self.orig_url
        else:
            # First iteration. Set aside the original value, so we can use it
            # in the remaining iterations.
            self.orig_url = self.url

        parts = self.url.rsplit(".", 1)
        self.url = "%s_%s.%s" % (parts[0], date_str, parts[1])
        self.html = self._download()
