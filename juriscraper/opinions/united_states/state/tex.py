# Scraper for Texas Supreme Court
# CourtID: tex
# Court Short Name: TX
# Court Contacts:
#  - http://www.txcourts.gov/contact-us/
#  - Blake Hawthorne <Blake.Hawthorne@txcourts.gov>
#  - Eddie Murillo <Eddie.Murillo@txcourts.gov>
#  - Judicial Info <JudInfo@txcourts.gov>
# Author: Andrei Chelaru
# Reviewer: mlr
# History:
#  - 2014-07-10: Created by Andrei Chelaru
#  - 2014-11-07: Updated by mlr to account for new website.
#  - 2014-12-09: Updated by mlr to make the date range wider and more thorough.
#  - 2015-08-19: Updated by Andrei Chelaru to add backwards scraping support.
#  - 2015-08-27: Updated by Andrei Chelaru to add explicit waits
#  - 2021-12-23: Updated by flooie

from datetime import date, timedelta

import lxml
import lxml.html

from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.status = "Published"
        self.url = "https://search.txcourts.gov/CaseSearch.aspx?coa=cossup"
        today = date.today()
        last_month = today - timedelta(days=30)
        last_month_str = last_month.strftime("%m/%d/%Y")
        today_str = today.strftime("%m/%d/%Y")

        date_param = (
            '{"enabled":true,"emptyMessage":"",'
            f'"validationText":"{last_month}-00-00-00",'
            f'"valueAsString":"{last_month}-00-00-00",'
            '"minDateStr":"1900-01-01-00-00-00",'
            '"maxDateStr":"2099-12-31-00-00-00",'
            f'"lastSetTextBoxValue":"{last_month_str}"'
            "}"
        )

        self.parameters = {
            "ctl00$ContentPlaceHolder1$SearchType": "rbSearchByDocument",
            "ctl00$ContentPlaceHolder1$chkListCourts$0": "on",
            "ctl00$ContentPlaceHolder1$dtDocumentFrom": last_month,
            "ctl00$ContentPlaceHolder1$dtDocumentFrom$dateInput": last_month_str,
            "ctl00_ContentPlaceHolder1_dtDocumentFrom_dateInput_ClientState": date_param,
            "ctl00$ContentPlaceHolder1$dtDocumentTo": today,
            "ctl00$ContentPlaceHolder1$dtDocumentTo$dateInput": today_str,
            "ctl00$ContentPlaceHolder1$chkListDocTypes$0": "on",
            "ctl00$ContentPlaceHolder1$btnSearchText": "Search",
        }

    def _process_html(self) -> None:
        if not self.test_mode_enabled():
            self.parameters["__VIEWSTATE"] = self.html.xpath(
                "//input[@id='__VIEWSTATE']"
            )[0].get("value")
            self._request_url_post(self.url)
            self.html = lxml.html.fromstring(self.request["response"].text)

        for row in self.html.xpath("//table[@class='rgMasterTable']/tbody/tr"):
            case_slug = row.xpath(".//a")[2].get("href")
            case_url = f"https://search.txcourts.gov/{case_slug}"
            if self.test_mode_enabled():
                name = "No case names fetched during tests."
            else:
                self._request_url_get(case_url)
                case_page = lxml.html.fromstring(self.request["response"].text)
                name = case_page.xpath("//div[@class='span10']")[-2:]
                name = " v. ".join([x.text_content().strip() for x in name])
                name = titlecase(name)
            url = row.xpath(".//a")[1].get("href")
            if "http" not in url:
                url = f"https://search.txcourts.gov/{url}"
            self.cases.append(
                {
                    "date": row.xpath(f".//td[2]")[0].text_content(),
                    "docket": row.xpath(f".//td[5]")[0].text_content(),
                    "name": name,
                    "url": url,
                }
            )
