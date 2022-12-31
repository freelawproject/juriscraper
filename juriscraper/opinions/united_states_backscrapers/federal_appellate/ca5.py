from datetime import date, datetime, timedelta

from dateutil.rrule import DAILY, rrule
from lxml.html import fromstring

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base = "http://www.ca5.uscourts.gov"
        self.url = f"{self.base}/electronic-case-filing/case-information/current-opinions"
        self.court_id = self.__module__
        self.interval = 7
        self.data = {}
        self.headers = {
            "Host": "www.ca5.uscourts.gov",
            "Origin": self.base,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Referer": self.url,
            "Connection": "keep-alive",
        }
        self.x = "ctl00$Body$C010$ctl00$ctl00"
        self.y = "ctl00_Body_C010_ctl00_ctl00"
        self.vs_xpath = "//input[@name='__VIEWSTATE']"
        self.ev_xpath = "//input[@name='__EVENTVALIDATION']"
        self.et_xpath = "//input[@name='__EVENTTARGET']"
        self.vsg_xpath = "//input[@name='__VIEWSTATEGENERATOR']"

        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                DAILY,
                interval=self.interval,  # Every interval days
                dtstart=date(2022, 7, 1),
                until=date(2022, 9, 1),
            )
        ]

    def _download(self):
        r = self.request["session"].get(self.url)
        html = fromstring(r.text)
        self._update_query_params(html)

        # Get first set of dates
        r = self.request["session"].post(self.url, data=self.data)
        return fromstring(r.text)

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        this is a larger function.  It processes the first page and then
        iterates over the remaining pages.  It requires an update to the params
        and there are plenty of janky names but its pretty fast and
        selenium free.

        :return: None
        """

        row_xpath = f"{self.y}_radGridOpinions_ctl00"
        more_rows = self.html.xpath(f"//tr[contains(@id, '{row_xpath}')]")
        for row in more_rows:
            self.cases.append(
                {
                    "date": row.xpath(".//td[3]")[0].text_content(),
                    "name": row.xpath(".//td[4]")[0].text_content(),
                    "url": row.xpath(".//td[2]/a")[0].attrib["href"],
                    "docket": row.xpath(".//td[2]/a")[0].attrib["title"],
                    "status": "Published"
                    if row.xpath(".//td[5]")[0].text_content() == "pub"
                    else "Unpublished",
                }
            )

        del self.data[f"{self.x}$btnSearch"]
        rad_script = f"{self.x}${self.x}$radGridOpinionsPanel|{self.x}$radGridOpinions$ctl00$ctl03$ctl01$ctl10"

        # switch to search mode for pagination
        self.data[f"{self.x}$searchMode"] = "search"
        self.data["__ASYNCPOST"] = "true"
        self.data["RadAJAXControlID"] = f"{self.y}_radAjaxManager1"
        self.data["ctl00$RadScriptManager1"] = rad_script

        last = self.html.xpath(
            "//div[@class='rgWrap rgNumPart']/a/span/text()"
        )[-1]

        page_content = None
        current_xp = "//a[@class='rgCurrentPage']/span/text()"
        while last != (current_page := self.html.xpath(current_xp)[0]):
            self._update_pagination_data(page_content, current_page)
            page_content = (
                self.request["session"]
                .post(self.url, headers=self.headers, data=self.data)
                .text
            )
            self.html = fromstring(page_content)
            rows = self.html.xpath(f"//tr[contains(@id, '{row_xpath}')]")
            for row in rows:
                self.cases.append(
                    {
                        "date": row.xpath(".//td[3]")[0].text_content(),
                        "name": row.xpath(".//td[4]")[0].text_content(),
                        "url": row.xpath(".//td[2]/a")[0].attrib["href"],
                        "docket": row.xpath(".//td[2]/a")[0].attrib["title"],
                        "status": "Published"
                        if row.xpath(".//td[5]")[0].text_content() == "pub"
                        else "Unpublished",
                    }
                )

    def _set_dates(self, case_date):
        """Set the backscrape dates"""
        d1 = case_date - timedelta(days=self.interval)
        e1 = case_date

        start_date_mdy = datetime.strftime(d1, "%m/%d/%Y")
        end_date_mdy = datetime.strftime(case_date, "%m/%d/%Y")
        start_date = str(
            {
                "valueAsString": f"{d1}-00-00-00",
                "lastSetTextBoxValue": f"{start_date_mdy}",
            }
        )
        end_date = str(
            {
                "valueAsString": f"{e1}-00-00-00",
                "lastSetTextBoxValue": f"{end_date_mdy}",
            }
        )
        self.data[f"{self.x}$startDate$dateInput"] = start_date_mdy
        self.data[f"{self.x}$endDate$dateInput"] = end_date_mdy
        self.data[f"{self.y}_startDate_dateInput_ClientState"] = start_date
        self.data[f"{self.y}_endDate_dateInput_ClientState"] = end_date
        self.data[f"{self.x}$btnSearch"] = "Search"
        self.data[
            f"{self.x}$radGridOpinions$ctl00$ctl03$ctl01$PageSizeComboBox"
        ] = "20"

    def _update_query_params(self, html):
        """Update the query parameters for next page"""
        self.data["__VIEWSTATE"] = html.xpath(self.vs_xpath)[0].attrib["value"]
        self.data["__EVENTVALIDATION"] = html.xpath(self.ev_xpath)[0].attrib[
            "value"
        ]
        self.data["__EVENTTARGET"] = html.xpath(self.et_xpath)[0].attrib[
            "value"
        ]
        self.data["__VIEWSTATEGENERATOR"] = html.xpath(self.vsg_xpath)[
            0
        ].attrib["value"]

    def _update_pagination_data(self, page_content, current):
        """Update subsequent pagination data if required."""
        target = self.html.xpath("//input[@class='rgPageNext']")[0].attrib[
            "name"
        ]
        if int(current) > 1:
            # After the first page - find view state etc here.
            viewstate = page_content.split("__VIEWSTATE|")[1].split("|")[0]
            valiation = page_content.split("__EVENTVALIDATION|")[1].split("|")[
                0
            ]
        else:
            viewstate = self.html.xpath(self.vs_xpath)[0].attrib["value"]
            valiation = self.html.xpath(self.ev_xpath)[0].attrib["value"]

        self.data["__EVENTTARGET"] = target
        self.data["__VIEWSTATE"] = viewstate
        self.data["__EVENTVALIDATION"] = valiation

    def _download_backwards(self, case_date):
        logger.info(
            "Running backscraper with date range: %s to %s"
            % (
                case_date - timedelta(days=self.interval),
                case_date,
            )
        )
        self._set_dates(case_date)
