# Scraper for Kansas Supreme Court
# CourtID: kan
# Court Short Name: kan
# Author: Andrei Chelaru
# Updated: William Palin
# Reviewer: mlr
# Date created: 25 July 2014
# Date updated: 2/29/2020

from juriscraper.OpinionSiteAspx import OpinionSiteAspx
from juriscraper.lib.string_utils import convert_date_string
from datetime import datetime, timedelta


class Site(OpinionSiteAspx):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.kscourts.org"
        self.url = "https://www.kscourts.org/Cases-Opinions/Opinions.aspx"
        self.case_date = datetime.now()
        self.backwards_days = 14
        self.court = "Select Court"  # Supreme Court, Court of Appeals / BOTH
        self.status = "Select Status"  # Published, Unpublished / BOTH
        self.html = None
        self.data = None

        self.go_until_date = self.case_date - timedelta(self.backwards_days)
        self.page = 1
        self.rs = "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$drp"
        self.date_xp = './/td/a[@class="link-pdf"]/ancestor::tr/td[1]'
        self.row_xp = './/td/a[@class="link-pdf"]/ancestor::tr'

    # Required for OpinionSiteAspx
    def _get_event_target(self):
        return "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl06$UniversalPager$pagerElem"

    # Required for OpinionSiteAspx
    def _get_data_template(self):
        return {
            "__EVENTTARGET": None,
            "__VIEWSTATE": None,
        }

    def _download(self, request_dict={}):
        # Load the homepage
        self._update_html(self.url)

        # Iterate over the pages until we reach our go until date
        while self.page:
            self._update_data()
            self._update_html(self.url)
            self.rows = self.html.xpath(self.row_xp)

            last_dt = self.html.xpath(self.date_xp)[-1].text_content().strip()
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
        # Call the super class version, which creates a new data dict from the
        # template and fills in ASPX specific values.
        super(Site, self)._update_data()

        self.data.update(
            {
                "__EVENTARGUMENT": self.page,
                "%sCourt" % self.rs: self.court,
                "%sPublished" % self.rs: self.status,
            }
        )
