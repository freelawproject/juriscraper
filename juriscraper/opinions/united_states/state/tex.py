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
#  - 2024-02-21; Updated by grossir: handle dynamic backscrapes

from datetime import date, datetime, timedelta
from typing import Dict, Optional, Tuple

from juriscraper.AbstractSite import logger
from juriscraper.DeferringList import DeferringList
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    rows_xpath = (
        "//table[@class='rgMasterTable']/tbody/tr[not(@class='rgNoRecords')]"
    )
    param_date_format = "%-m/%-d/%Y"
    first_opinion_date = datetime(2002, 1, 24, 0, 0, 0)
    next_page_xpath = (
        "//input[@title='Next Page' and not(@onclick='return false;')]"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.checkbox = 0
        self.status = "Published"
        self.url = "https://search.txcourts.gov/CaseSearch.aspx?coa=cossup"
        self.make_backscrape_iterable(kwargs)
        self.next_page = None
        # Default scrape range if not doing a backscrape
        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=30)

    def _set_parameters(self) -> None:
        """Set ASPX post parameters

        This method - chooses the court and date parameters.
        ctl00$ContentPlaceHolder1$chkListCourts$[KEY] is what selects a ct

         0: Supreme
         1: Court of Criminal Appeals
         2: 1st District Court of Appeals
         3: 2nd District Court of Appeals
         ...etc

        :return: None
        """
        start_date_str = self.start_date.strftime(self.param_date_format)
        end_date_str = self.end_date.strftime(self.param_date_format)

        from_date_param = self.make_date_param(self.start_date, start_date_str)
        to_date_param = self.make_date_param(self.end_date, end_date_str)

        self.parameters = {}
        for hidden in self.html.xpath("//input[@type='hidden']"):
            value = hidden.xpath("@value")[0] if hidden.xpath("@value") else ""
            self.parameters[hidden.xpath("@name")[0]] = value

        self.parameters.update(
            {
                "ctl00$ContentPlaceHolder1$SearchType": "rbSearchByDocument",  # "Document Search" radio button
                "ctl00$ContentPlaceHolder1$dtDocumentFrom": str(
                    self.start_date
                ),
                "ctl00$ContentPlaceHolder1$dtDocumentFrom$dateInput": start_date_str,
                "ctl00$ContentPlaceHolder1$dtDocumentTo": str(self.end_date),
                "ctl00$ContentPlaceHolder1$dtDocumentTo$dateInput": end_date_str,
                "ctl00_ContentPlaceHolder1_dtDocumentFrom_dateInput_ClientState": from_date_param,
                "ctl00_ContentPlaceHolder1_dtDocumentTo_dateInput_ClientState": to_date_param,
                "ctl00$ContentPlaceHolder1$btnSearchText": "Search",
                "ctl00$ContentPlaceHolder1$chkListDocTypes$0": "on",  # "Opinion" checkbox
                f"ctl00$ContentPlaceHolder1$chkListCourts${self.checkbox}": "on",  # Court checkbox
                "ctl00$ContentPlaceHolder1$txtSearchText": "",
                "ctl00_ContentPlaceHolder1_dtDocumentFrom_ClientState": '{"minDateStr":"1900-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00"}',
                "ctl00_ContentPlaceHolder1_dtDocumentTo_ClientState": '{"minDateStr":"1900-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00"}',
                "ctl00$ContentPlaceHolder1$Stemming": "on",
                "ctl00$ContentPlaceHolder1$Fuzziness": "0",
            }
        )

        # "Next page" arrow button has a name
        # "ctl00$ContentPlaceHolder1$grdDocuments$ctl00$ctl02$ctl00$ctl18"
        # Couldn't get pagination working when using the numbered page anchors,
        # whose id goes into __EVENTTARGET
        if self.next_page:
            self.parameters[self.next_page[0].xpath("@name")[0]] = ""
            self.parameters["__EVENTTARGET"] = ""
            self.parameters["__SCROLLPOSITIONX"] = "0"
            self.parameters["__SCROLLPOSITIONY"] = "345"
            self.parameters["__EVENTARGUMENT"] = ""
            self.parameters["__LASTFOCUS"] = ""

    def _process_html(self) -> None:
        """Process HTML and paginates if needed

        :return: None
        """
        if not self.test_mode_enabled():
            # Make our post request to get our data
            self.method = "POST"
            self._set_parameters()
            self.html = super()._download()

        for row in self.html.xpath(self.rows_xpath):
            # In texas we also have to ping the case page to get the name
            # this is unfortunately part of the process.
            self.cases.append(
                {
                    "date": row.xpath("td[2]")[0].text_content(),
                    "docket": row.xpath("td[5]")[0].text_content().strip(),
                    "url": row.xpath(".//a")[1].get("href"),
                }
            )

        self.next_page = self.html.xpath(self.next_page_xpath)
        if self.next_page and not self.test_mode_enabled():
            self._process_html()

    def _get_case_names(self) -> DeferringList:
        """Get case names using a deferring list."""
        seeds = []
        for row in self.html.xpath(self.rows_xpath):
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

    def make_backscrape_iterable(self, kwargs: Dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordinly

        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.strptime(start, "%m/%d/%Y")
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%m/%d/%Y")
        else:
            end = datetime.now() - timedelta(days=30)

        self.back_scrape_iterable = [(start, end)]

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Overrides present scraper start_date and end_date

        :param dates: (start_date, end_date) tuple
        :return None
        """
        self.start_date = dates[0].date()
        self.end_date = dates[1].date()

    @staticmethod
    def make_date_param(date_obj: date, date_str: str) -> str:
        """Make JSON encoded string with dates as expected by formdata

        :param date_obj: a date object
        :param date_str: string representation of the date in expected format

        :return: JSON encoded string
        """
        return (
            '{"enabled":true,"emptyMessage":"",'
            f'"validationText":"{date_obj}-00-00-00",'
            f'"valueAsString":"{date_obj}-00-00-00",'
            '"minDateStr":"1900-01-01-00-00-00",'
            '"maxDateStr":"2099-12-31-00-00-00",'
            f'"lastSetTextBoxValue":"{date_str}"'
            "}"
        )
