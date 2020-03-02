#  - 2014-11-07: Updated by mlr to account for new website.
#  - 2014-12-09: Updated by mlr to make the date range wider and more thorough.
#  - 2015-08-19: Updated by Andrei Chelaru to add backwards scraping support.
#  - 2015-08-27: Updated by Andrei Chelaru to add explicit waits
#  - 2020-03-01: Updated by flooie to remove selenium


import requests
from datetime import datetime, timedelta
from lxml import html
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string, titlecase


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.case_date = datetime.now()
        self.backwards_days = 7
        self.data = {}
        self.courts = {
            "all": -1,
            "sc": 0,
            "ccrimapp": 1,
            "capp_1": 2,
            "capp_2": 3,
            "capp_3": 4,
            "capp_4": 5,
            "capp_5": 6,
            "capp_6": 7,
            "capp_7": 8,
            "capp_8": 9,
            "capp_9": 10,
            "capp_10": 11,
            "capp_11": 12,
            "capp_12": 13,
            "capp_13": 14,
            "capp_14": 15,
        }
        self.court_name = "sc"
        self.url = (
            "http://www.search.txcourts.gov/CaseSearch.aspx"
        )
        self.base_url = "http://www.search.txcourts.gov"

    def _download(self, request_dict={}):
        orders = []
        self.set_local_variables()
        s = requests.session()
        r = s.get(self.url)
        soup = html.fromstring(r.text)
        self.data["__VIEWSTATE"] = (
            soup.xpath('//*[@id="__VIEWSTATE"]/@value')[0],
        )
        r = s.post(self.url, params=self.params, data=self.data)

        soup = html.fromstring(r.text)
        for link in soup.xpath('.//a[text()="Opinion"]/ancestor::tr'):
            orders.append(link)

        while int(soup.xpath(self.total_regex)[0].text_content()) > 25:
            data = {
                "__VIEWSTATE": soup.xpath('//*[@id="__VIEWSTATE"]/@value')[0],
                "__EVENTTARGET": soup.xpath('.//a[@class="rgCurrentPage"]')[0]
                .getnext()
                .get("href")
                .split("'")[1],
            }

            response = s.post(self.url, data=data)
            soup = html.fromstring(response.text)

            for link in soup.xpath('.//a[text()="Opinion"]/ancestor::tr'):
                orders.append(link)
            if soup.xpath('.//a[@class="rgCurrentPage"]')[0].getnext() is None:
                break
        return orders

    def _get_case_names(self):
        case_names = []
        case_urls = [row.xpath(".//td[5]/a/@href")[0] for row in self.html]
        for case_url in case_urls:
            soup = self._get_html_tree_by_url(
                "%s/%s" % (self.base_url, case_url)
            )
            case = " v. ".join([x.strip() for x in soup.xpath(self.xp)])
            case_names.append(titlecase(case))
        return case_names

    def _get_case_dates(self):
        return [
            convert_date_string(row.xpath(".//td[2]/text()")[0])
            for row in self.html
        ]

    def _get_precedential_statuses(self):
        return ["" for row in self.html]

    def _get_download_urls(self):
        return [
            "%s/%s"
            % (self.base_url, row.xpath('.//a[text()="Opinion"]/@href')[0])
            for row in self.html
        ]

    def _get_docket_numbers(self):
        return [row.xpath(".//td[5]/a/text()")[0] for row in self.html]

    def set_local_variables(self):
        back_date = self.case_date - timedelta(self.backwards_days)
        future_date_ymd = self.case_date.strftime("%Y-%m-%d-%H-%M-%S")
        past_date_ymd = back_date.strftime("%Y-%m-%d-%H-%M-%S")
        future_date_mdy = self.case_date.strftime("%m/%d/%Y")
        past_date_mdy = back_date.strftime("%m/%d/%Y")

        self.data = {
            # 'ctl00$ContentPlaceHolder1$chkAllCourts': 'on',
            "ctl00$ContentPlaceHolder1$chkListCourts$%s"
            % self.courts[self.court_name]: "on",
            "ctl00$ContentPlaceHolder1$dtDocumentFrom$dateInput": past_date_mdy,
            "ctl00_ContentPlaceHolder1_dtDocumentFrom_dateInput_ClientState": '{"valueAsString":"%s","lastSetTextBoxValue":"%s"}'
            % (past_date_ymd, past_date_mdy),
            "ctl00$ContentPlaceHolder1$dtDocumentTo$dateInput": future_date_mdy,
            "ctl00_ContentPlaceHolder1_dtDocumentTo_dateInput_ClientState": '{"valueAsString":"%s","lastSetTextBoxValue":"%s"}'
            % (future_date_ymd, future_date_mdy),
            "ctl00$ContentPlaceHolder1$chkListDocTypes$0": "on",
            "ctl00$ContentPlaceHolder1$btnSearchText": "Search",
        }
        self.total_regex = (
            '//*[@id="ctl00_ContentPlaceHolder1_grdDocuments_ctl00"]'
            "/thead/tr[1]/td/table/tbody/tr/td/div[5]/strong[1]"
        )
        self.xp = (
            "//text()[contains(., 'Style:') or contains(., 'v.:')]"
            "//ancestor::div[@class='span2']/following-sibling::div/text()"
        )

        self.params = (
            ('coa', 'cossup'),
            ('d', '1'),
        )
