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
#  - 2021-12-28: Updated by flooie to remove selenium.

from datetime import date, timedelta
from typing import Optional

from juriscraper.AbstractSite import logger
from juriscraper.DeferringList import DeferringList
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.checkbox = 0
        self.status = "Published"
        self.url = "https://search.txcourts.gov/CaseSearch.aspx?coa=cossup"

    def _set_parameters(
        self,
        view_state: str,
    ) -> None:
        """Set ASPX post parameters

        This method - chooses the court and date parameters.
        ctl00$ContentPlaceHolder1$chkListCourts$[KEY] is what selects a ct

         0: Supreme
         1: Court of Criminal Appeals
         2: 1st District Court of Appeals
         3: 2nd District Court of Appeals
         ...etc

        :param view_state: view state of the page
        :return: None
        """
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

        # The parameters required to filter in Texas
        self.parameters = {
            "ctl00$ContentPlaceHolder1$SearchType": "rbSearchByDocument",
            "ctl00$ContentPlaceHolder1$dtDocumentFrom": str(last_month),
            "ctl00$ContentPlaceHolder1$dtDocumentFrom$dateInput": last_month_str,
            "ctl00_ContentPlaceHolder1_dtDocumentFrom_dateInput_ClientState": date_param,
            "ctl00$ContentPlaceHolder1$dtDocumentTo": str(today),
            "ctl00$ContentPlaceHolder1$dtDocumentTo$dateInput": today_str,
            "ctl00$ContentPlaceHolder1$chkListDocTypes$0": "on",
            "ctl00$ContentPlaceHolder1$btnSearchText": "Search",
            "__VIEWSTATE": view_state,
            f"ctl00$ContentPlaceHolder1$chkListCourts${self.checkbox}": "on",
        }

    def _process_html(self) -> None:
        if not self.test_mode_enabled():
            # Make our post request to get our data
            self.method = "POST"
            view_state = self.html.xpath("//input[@id='__VIEWSTATE']")[0].get(
                "value"
            )
            self._set_parameters(view_state)
            self.html = super()._download()

        for row in self.html.xpath("//table[@class='rgMasterTable']/tbody/tr"):
            # In texas we also have to ping the case page to get the name
            # this is unfortunately part of the process.
            self.cases.append(
                {
                    "date": row.xpath(f".//td[2]")[0].text_content(),
                    "docket": row.xpath(f".//td[5]")[0].text_content().strip(),
                    "url": row.xpath(".//a")[1].get("href"),
                }
            )

    def _get_case_names(self) -> DeferringList:
        """Get case names using a deferring list."""
        seeds = []
        for row in self.html.xpath("//table[@class='rgMasterTable']/tbody/tr"):
            # In texas we also have to ping the case page to get the name
            # this is unfortunately part of the process.
            seeds.append(row.xpath(".//a")[2].get("href"))

        def get_name(link: str) -> Optional[str]:
            """Abstract out the case name from the case page."""
            if self.test_mode_enabled():
                return "No case names fetched during tests."
            html = self._get_html_tree_by_url(link)
            try:
                plaintiff = html.xpath(
                    '//label[contains(text(), "Style:")]/parent::div/following-sibling::div/text()'
                )[0].strip()
                defendant = html.xpath(
                    '//label[contains(text(), "v.:")]/parent::div/following-sibling::div/text()'
                )[0].strip()

                # In many cases the court leaves off the plaintiff (The State of Texas).  But
                # in some of these cases the appellant is ex parte.  So we need to
                # add the state of texas in some cases but not others.
                if defendant:
                    return titlecase(f"{plaintiff} v. {defendant}")
                elif "WR-" not in link:
                    return titlecase(f"{plaintiff} v. The State of Texas")
                else:
                    return titlecase(f"{plaintiff}")
            except IndexError:
                logger.warning(f"No title or defendant found for {self.url}")
                return None

        return DeferringList(seed=seeds, fetcher=get_name)
