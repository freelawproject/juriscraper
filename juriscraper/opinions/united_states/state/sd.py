# Author: Michael Lissner
# History:
# - 2013-06-11: Birth.
# - 2013-08-06: Revised by Brian Carver
# - 2014-08-05: Updated URL by mlr

from lxml import html
from datetime import datetime
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string, titlecase


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://ujs.sd.gov/Supreme_Court/opinions.aspx"
        self.year = int(datetime.today().year)
        self.y = "%0*d" % (2, int(datetime.today().year) - self.year)
        self.rows = []
        self.soup = None

        self.next_button_regex = (
            '//*[@id="ContentPlaceHolder1_ChildContent1_LinkButton_Next"]'
        )

    def _download(self, request_dict={}):
        self.first_data()
        self.make_soup(self.url)

        self.update_event_and_view()
        self.make_soup(self.url)

        for link in self.soup.xpath('//tr[contains(.//a/@href, ".pdf")]'):
            row = [
                x.text_content().strip() for x in link.xpath(".//td")
            ] + link.xpath(".//a/@href")
            self.rows.append(row)

        while self.soup.xpath(self.next_button_regex)[0].get("href"):
            self.second_data()
            self.update_event_and_view()

            response = self.request["session"].post(self.url, data=self.data)
            self.soup = html.fromstring(response.text)

            for link in self.soup.xpath('//tr[contains(.//a/@href, ".pdf")]'):
                more_orders = [
                    x.text_content().strip() for x in link.xpath(".//td")
                ] + link.xpath(".//a/@href")
                self.rows.append(more_orders)

    def _get_download_urls(self):
        return ["https://ujs.sd.gov%s" % x[3] for x in self.rows]

    def _get_case_names(self):
        return [
            titlecase(x[1].split(", %s" % self.year)[0]) for x in self.rows
        ]

    def _get_case_dates(self):
        return [convert_date_string(x[0]) for x in self.rows]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_neutral_citations(self):
        return [x[1].split(", %s" % self.year)[1].strip() for x in self.rows]

    def first_data(self):
        self.data = {
            "ctl00$ctl00$ScriptManager1": "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$UpdatePanel_Opinions|ctl00$ctl00$ContentPlaceHolder1$ChildContent1$Repeater_OpinionsYear$ctl%s$LinkButton1"
            % self.y,
            "__EVENTTARGET": "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$Repeater_OpinionsYear$ctl%s$LinkButton1"
            % self.y,
            "__EVENTARGUMENT": "",
            "__VIEWSTATEENCRYPTED": "",
        }

    def update_event_and_view(self):
        self.data["__VIEWSTATE"] = (
            self.soup.xpath('//*[@id="__VIEWSTATE"]/@value')[0],
        )
        self.data["__EVENTVALIDATION"] = self.soup.xpath(
            '//*[@id="__EVENTVALIDATION"]/@value'
        )[0]

    def second_data(self):
        self.data[
            "ctl00$ctl00$ScriptManager1"
        ] = "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$UpdatePanel_Opinions|ctl00$ctl00$ContentPlaceHolder1$ChildContent1$LinkButton_Next"
        self.data[
            "__EVENTTARGET"
        ] = "ctl00$ctl00$ContentPlaceHolder1$ChildContent1$LinkButton_Next"

    def make_soup(self, process_url):
        if self.data is not None:
            r = self.request["session"].get(process_url)
        else:
            r = self.request["session"].post(process_url, data=self.data)
        self.soup = html.fromstring(r.text)
