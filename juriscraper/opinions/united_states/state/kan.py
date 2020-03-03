# Scraper for Kansas Supreme Court
# CourtID: kan
# Court Short Name: kan
# Author: Andrei Chelaru
# Updated: William Palin
# Reviewer: mlr
# Date created: 25 July 2014
# Date updated: 2/29/2020

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string
from datetime import datetime, timedelta
from lxml.html import fromstring


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.kscourts.org"
        self.url = "https://www.kscourts.org/Cases-Opinions/Opinions.aspx"
        self.case_date = datetime.now()
        self.backwards_days = 14
        self.court = "Select Court"  # Supreme Court, Court of Appeals / BOTH
        self.status = "Select Status"  # Published, Unpublished / BOTH
        self.soup = None
        self.data = None

    def _download(self, request_dict={}):
        # Set our local variables
        self.set_local_variables()

        # Load the homepage
        self.make_soup(self.url)

        # Iterate over the pages until we reach our go until date
        while self.page:
            self.set_data()
            self.make_soup(self.url)
            self.rows = self.soup.xpath(self.row_xp)

            last_dt = self.soup.xpath(self.date_xp)[-1].text_content().strip()
            if datetime.strptime(last_dt, "%m/%d/%Y") < self.go_until_date:
                break
            self.page = self.page + 1

    def _get_case_names(self):
        return [x.xpath(".//a/text()")[2] for x in self.rows]

    def _get_download_urls(self):
        return [
            "%s%s" % (self.base_url, row.xpath(".//td[6]/a/@href")[0].strip())
            for row in self.rows
        ]

    def _get_case_dates(self):
        return [
            convert_date_string(
                row.xpath(".//td[1]")[0].text_content().strip()
            )
            for row in self.rows
        ]

    def _get_precedential_statuses(self):
        return [
            row.xpath(".//td[5]")[0].text_content().strip()
            for row in self.rows
        ]

    def _get_docket_numbers(self):
        return [
            row.xpath(".//td[2]")[0].text_content().strip()
            for row in self.rows
        ]

    def set_data(self):
        self.data = {
            "__EVENTTARGET": self.event_target_key,
            "__EVENTARGUMENT": self.page,
            "__VIEWSTATE": self.soup.xpath(self.view_state_xp)[0],
            "%sCourt" % self.rs: self.court,
            "%sPublished" % self.rs: self.status,
        }

    def make_soup(self, process_url):
        if self.data is None:
            r = self.request["session"].get(process_url)
        else:
            r = self.request["session"].post(process_url, data=self.data)
        self.soup = fromstring(r.text)

    def set_local_variables(self):
        self.go_until_date = self.case_date - timedelta(self.backwards_days)
        self.page = 1
        self.rs = "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$drp"
        self.event_target_key = "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl06$UniversalPager$pagerElem"
        self.date_xp = './/td/a[@class="link-pdf"]/ancestor::tr/td[1]'
        self.row_xp = './/td/a[@class="link-pdf"]/ancestor::tr'
        self.view_state_xp = '//*[@id="__VIEWSTATE"]/@value'
