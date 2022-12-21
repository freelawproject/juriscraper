from datetime import date, datetime, timedelta

from dateutil.rrule import DAILY, rrule
from lxml.html import fromstring

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = "http://www.ca5.uscourts.gov/electronic-case-filing/case-information/current-opinions"
        self.court_id = self.__module__
        self.interval = 2
        self.data = {}
        self.headers = {
            "Host": "www.ca5.uscourts.gov",
            "Origin": "http://www.ca5.uscourts.gov",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Safari/605.1.15",
            "Referer": "http://www.ca5.uscourts.gov/electronic-case-filing/case-information/current-opinions",
            "Connection": "keep-alive",
        }

        self.start_date = None
        self.end_date = None

        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                DAILY,
                interval=self.interval,  # Every interval days
                dtstart=date(2022, 8, 11),
                until=date(2022, 8, 13),
            )
        ]

    def _download(self):
        r = self.request["session"].get(self.url)
        vs_xpath = "//input[@name='__VIEWSTATE']"
        ev_xpath = "//input[@name='__EVENTVALIDATION']"
        et_xpath = "//input[@name='__EVENTTARGET']"
        vsg_xpath = "//input[@name='__VIEWSTATEGENERATOR']"
        x = "ctl00$Body$C010$ctl00$ctl00"
        y = "ctl00_Body_C010_ctl00_ctl00"

        self.data[f"{x}$startDate$dateInput"] = self.d2
        self.data[f"{x}$endDate$dateInput"] = self.e2
        self.data[f"{y}_startDate_dateInput_ClientState"] = self.start_date
        self.data[f"{y}_endDate_dateInput_ClientState"] = self.end_date
        self.data[f"{x}$btnSearch"] = "Search"
        self.data[
            f"{x}$radGridOpinions$ctl00$ctl03$ctl01$PageSizeComboBox"
        ] = "20"

        html = fromstring(r.text)
        self.data["__VIEWSTATE"] = html.xpath(vs_xpath)[0].attrib["value"]
        self.data["__EVENTVALIDATION"] = html.xpath(ev_xpath)[0].attrib[
            "value"
        ]
        self.data["__EVENTTARGET"] = html.xpath(et_xpath)[0].attrib["value"]
        self.data["__VIEWSTATEGENERATOR"] = html.xpath(vsg_xpath)[0].attrib[
            "value"
        ]

        # Get first set of dates
        r = self.request["session"].post(self.url, data=self.data)
        return fromstring(r.text)

    def _process_html(self) -> None:
        """Process the html and extract out the opinions

        :return: None
        """
        x = "ctl00$Body$C010$ctl00$ctl00"
        y = "ctl00_Body_C010_ctl00_ctl00"
        vs_xpath = "//input[@name='__VIEWSTATE']"
        ev_xpath = "//input[@name='__EVENTVALIDATION']"

        key = f"{y}_radGridOpinions_ctl00"
        more_rows = self.html.xpath(f"//tr[contains(@id, '{key}')]")
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

        del self.data[f"{x}$btnSearch"]
        rad_script = f"{x}${x}$radGridOpinionsPanel|{x}$radGridOpinions$ctl00$ctl03$ctl01$ctl10"

        # switch to search mode for pagination
        self.data[f"{x}$searchMode"] = "search"
        self.data["__ASYNCPOST"] = "true"
        self.data["RadAJAXControlID"] = f"{y}_radAjaxManager1"
        self.data["ctl00$RadScriptManager1"] = rad_script

        last = self.html.xpath(
            "//div[@class='rgWrap rgNumPart']/a/span/text()"
        )[-1]

        current = self.html.xpath("//a[@class='rgCurrentPage']/span/text()")[0]

        # All remaining pages
        while last != current:
            target = self.html.xpath("//input[@class='rgPageNext']")[0].attrib[
                "name"
            ]
            if int(current) > 1:
                viewstate = r.text.split("__VIEWSTATE|")[1].split("|")[0]
                valiation = r.text.split("__EVENTVALIDATION|")[1].split("|")[0]
            else:
                viewstate = self.html.xpath(vs_xpath)[0].attrib["value"]
                valiation = self.html.xpath(ev_xpath)[0].attrib["value"]

            self.data["__EVENTTARGET"] = target
            self.data["__VIEWSTATE"] = viewstate
            self.data["__EVENTVALIDATION"] = valiation

            r = self.request["session"].post(
                self.url, headers=self.headers, data=self.data
            )
            self.html = fromstring(r.text)
            more_rows = self.html.xpath(f"//tr[contains(@id, '{key}')]")
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
            current = self.html.xpath(
                "//a[@class='rgCurrentPage']/span/text()"
            )[0]

    def _download_backwards(self, d):
        self.case_date = d
        logger.info(
            "Running backscraper with date range: %s to %s"
            % (
                self.case_date - timedelta(days=self.interval),
                self.case_date,
            )
        )
        d1 = self.case_date - timedelta(days=self.interval)
        self.d2 = datetime.strftime(d1, "%m/%d/%Y")
        e1 = self.case_date
        self.e2 = datetime.strftime(e1, "%m/%d/%Y")
        self.start_date = str(
            {
                "valueAsString": f"{d1}-00-00-00",
                "lastSetTextBoxValue": f"{self.d2}",
            }
        )
        self.end_date = str(
            {
                "valueAsString": f"{e1}-00-00-00",
                "lastSetTextBoxValue": f"{self.e2}",
            }
        )
