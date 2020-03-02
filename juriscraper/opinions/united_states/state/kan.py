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
import requests
from lxml.html import fromstring


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.base_url = "https://www.kscourts.org"
        self.url = "https://www.kscourts.org/Cases-Opinions/Opinions.aspx"
        self.case_date = datetime.now()
        self.backwards_days = 14
        self.go_until_date = self.case_date - timedelta(self.backwards_days)
        self.court = "Select Court"  # Supreme Court, Court of Appeals / BOTH
        self.status = "Select Status"  # Published, Unpublished / BOTH

    def _download(self, request_dict={}):
        s = requests.session()
        r = s.get(self.url)
        soup = fromstring(r.text)
        content = []
        rows = []
        page = 1
        rs = "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl02$OpinionFilter1$filterControl$drp"
        ev = "p$lt$zonePagePlaceholder$pageplaceholder$p$lt$ctl06$UniversalPager$pagerElem"
        date_regex = './/td/a[@class="link-pdf"]/ancestor::tr/td[1]'
        while page:
            data = [
                ("__EVENTTARGET", ev),
                ("__EVENTARGUMENT", str(page)),
                (
                    "__VIEWSTATE",
                    soup.xpath('//*[@id="__VIEWSTATE"]/@value')[0],
                ),
                ("%sCourt" % rs, self.court),
                ("%sPublished" % rs, self.status),
            ]
            r = s.post(self.url, data=data)
            soup = fromstring(r.text)
            content.append(r)
            last_date_str = soup.xpath(date_regex)[-1].text_content().strip()
            last_date = datetime.strptime(last_date_str, "%m/%d/%Y")
            if last_date < self.go_until_date:
                break
            page = page + 1

        for page in content:
            soup = fromstring(page.text)
            for row in soup.xpath('.//td/a[@class="link-pdf"]/ancestor::tr'):
                rows.append(row)
        return rows

    def _get_case_names(self):
        return [
            x.xpath(".//td[3]")[0].text_content().strip() for x in self.html
        ]

    def _get_download_urls(self):
        return [
            "%s%s"
            % (self.base_url, x.xpath(".//td[6]/a")[0].get("href").strip())
            for x in self.html
        ]

    def _get_case_dates(self):
        return [
            convert_date_string(x.xpath(".//td[1]")[0].text_content().strip())
            for x in self.html
        ]

    def _get_precedential_statuses(self):
        return [
            x.xpath(".//td[5]")[0].text_content().strip() for x in self.html
        ]

    def _get_docket_numbers(self):
        return [
            x.xpath(".//td[2]")[0].text_content().strip() for x in self.html
        ]
