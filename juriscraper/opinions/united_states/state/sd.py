# Author: Michael Lissner
# History:
# - 2013-06-11: Birth.
# - 2013-08-06: Revised by Brian Carver
# - 2014-08-05: Updated URL by mlr

from lxml import html
from datetime import datetime, timedelta
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string, titlecase


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://ujs.sd.gov/Supreme_Court/opinions.aspx"
        self.backwards_days = 14
        self.case_date = datetime.now()
        self.soup = None
        self.data = None

    def _download(self, request_dict={}):
        self.set_local_variables()
        self.make_soup(self.url)
        if int(datetime.today().year) != self.year:
            self.set_data()
            self.make_soup(self.url)
        self.rows = self.soup.xpath(self.row_xp)
        last_dt = self.soup.xpath(self.date_xp)[-1].text_content().strip()
        if datetime.strptime(last_dt, "%m/%d/%Y") < self.go_until_date:
            return

        while self.soup.xpath(self.next_button_xp)[0].get("href"):
            self.update_data()
            self.make_soup(self.url)
            self.rows = self.rows + self.soup.xpath(self.row_xp)

            last_dt = self.soup.xpath(self.date_xp)[-1].text_content().strip()
            if datetime.strptime(last_dt, "%m/%d/%Y") < self.go_until_date:
                break

    def _get_download_urls(self):
        hrefs = [row.xpath(".//a")[0].get("href") for row in self.rows]
        return ["https://ujs.sd.gov%s" % href for href in hrefs]

    def _get_case_names(self):
        titles = [row.xpath(".//a/text()")[0] for row in self.rows]
        return [titlecase(title.split(",")[0]) for title in titles]

    def _get_case_dates(self):
        dates = [row.xpath(".//td/text()")[0].strip() for row in self.rows]
        return [convert_date_string(date) for date in dates]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_neutral_citations(self):
        cites = [row.xpath(".//td/text()")[1].strip() for row in self.rows]
        return ["%s S.D. %s" % (self.year, cite) for cite in cites]

    def set_data(self):
        year_variable = "%0*d" % (2, int(datetime.today().year) - self.year)
        self.yearKey = self.yearKey % year_variable
        self.data = {
            "ctl00$ctl00$ScriptManager1": "%s|%s" % (self.upKey, self.yearKey),
            "__EVENTTARGET": self.yearKey,
            "__EVENTARGUMENT": "",
            "__VIEWSTATEENCRYPTED": "",
            "__VIEWSTATE": self.soup.xpath(self.vs)[0],
            "__EVENTVALIDATION": self.soup.xpath(self.ev)[0],
        }

    def update_data(self):
        self.data["ctl00$ctl00$ScriptManager1"] = "%s|%s" % (
            self.upKey,
            self.nxtKey,
        )
        self.data["__EVENTTARGET"] = "%s" % self.nxtKey
        self.data["__VIEWSTATE"] = self.soup.xpath(self.vs)[0]
        self.data["__EVENTVALIDATION"] = self.soup.xpath(self.ev)[0]

    def make_soup(self, process_url):
        if self.data is None:
            r = self.request["session"].get(process_url)
        else:
            r = self.request["session"].post(process_url, data=self.data)
        self.soup = html.fromstring(r.text)

    def set_local_variables(self):
        self.year = int(self.case_date.year)
        self.go_until_date = self.case_date - timedelta(self.backwards_days)
        self.next_button_xp = (
            '//*[@id="ContentPlaceHolder1_ChildContent1_LinkButton_Next"]'
        )
        self.upKey = "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$UpdatePanel_Opinions"
        self.nxtKey = (
            "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$LinkButton_Next"
        )
        self.yearKey = "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$Repeater_OpinionsYear$ctl%s$LinkButton1"
        self.vs = '//*[@id="__VIEWSTATE"]/@value'
        self.ev = '//*[@id="__EVENTVALIDATION"]/@value'
        self.row_xp = '//tr[contains(.//a/@href, ".pdf")]'
        self.date_xp = '//tr[contains(.//a/@href, ".pdf")]/td[1]'
