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

import re
from datetime import date, datetime, timedelta

from dateutil import parser
from lxml import html as lxmlHTML

from juriscraper.AbstractSite import logger
from juriscraper.ClusterSite import ClusterSite
from juriscraper.lib.string_utils import titlecase
from juriscraper.lib.type_utils import OpinionType


class Site(ClusterSite):
    param_date_format = "%-m/%-d/%Y"
    first_opinion_date = datetime(2002, 1, 24, 0, 0, 0)
    # Interval for default scrape and backscrape iterable generation
    days_interval = 15

    # opinions in a single cluster may be published in different, but nearby
    # days
    max_days_to_cluster = 10

    oci_mapper = {
        # Court of Appeals Information
        "COA Case": "lower_court_number",
        "COA District": "lower_court",
        "COA Justice": "lower_court_judge",
        # "Opinion Cite": "lower_court_citation",  # may contain date data
        # Trial Court Information
        "Court Case": "lower_court_number",
        "Court Judge": "lower_court_judge",
        "Court": "lower_court",
        "Reporter": "court_reporter",
        ## Extra available fields: "Punishment", "County"
    }

    rows_xpath = (
        "//table[@class='rgMasterTable']/tbody/tr[not(@class='rgNoRecords')]"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.checkbox = 0
        self.court_number = "0"
        self.status = "Published"
        self.url = "https://search.txcourts.gov/CaseSearch.aspx?coa=cossup"
        self.make_backscrape_iterable(kwargs)

        self.next_page = None
        self.current_page = 1
        # Default scrape range if not doing a backscrape
        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=self.days_interval)
        self.is_first_request = True

        self.seen_case_urls = set()
        self.expected_content_types = [
            "application/vnd.ms-word",
            "application/pdf",
        ]

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

        # "Next page" arrow button has a name like
        # "ctl00$ContentPlaceHolder1$grdDocuments$ctl00$ctl02$ctl00$ctl18"
        # Couldn't get pagination working when using the numbered page anchors,
        # whose id goes into __EVENTTARGET
        if self.next_page:
            self.parameters[self.next_page[0].xpath("@name")[0]] = ""

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
            # `Document search` page returns OpinionClusters separated,
            # each opinion in a single row. We keep track to skip if we already
            # parsed the case
            case_url = row.xpath(".//a")[2].get("href")
            if case_url in self.seen_case_urls:
                continue
            self.seen_case_urls.add(case_url)

            op_date = row.xpath("td[2]")[0].text_content()
            case_dict = self.parse_case_page(case_url, op_date)
            case_dict["date"] = op_date
            case_dict["docket"] = row.xpath("td[5]")[0].text_content().strip()

            judges = [
                op["author"]
                for op in case_dict["sub_opinions"]
                if op.get("author")
            ]
            case_dict["judge"] = "; ".join(judges)

            if (
                self.checkbox >= 2  # only checking for COA's not crim
                and self.court_number
                != case_dict["docket"][
                    :2
                ]  # first to docket numbers indicate the court (03-26-00075-CV)
            ):
                logger.warning(
                    "Skipping docket %s - belongs to court %s, not %s",
                    case_dict["docket"],
                    case_dict["docket"][:2],
                    self.court_number,
                )
                continue
            self.cases.append(case_dict)

        # pagination
        next_page_xpath = (
            "//input[@title='Next Page' and not(@onclick='return false;')]"
        )
        self.next_page = self.html.xpath(next_page_xpath)
        if self.next_page and not self.test_mode_enabled():
            self.current_page += 1
            logger.info(f"Paginating to page {self.current_page}")
            self._process_html()

    def parse_case_page(self, link: str, opinion_date: str) -> dict:
        """Parses the case page

        Usually we would defer getting extra data until dup checking
        is done by the caller. However, we get the `case_name` from this
        page, which is need for site hash computing, which cannot be deferred

        :param link: url of the case page
        :return: parsed case dictionary
        """
        parsed = {}
        if self.test_mode_enabled():
            # Support "sub" pages on test_ScraperExampleTest by modifying
            # the href attribute of the case page, to point to the proper local file
            self.url = link
            self._request_url_mock(link)
            html = self._return_response_text_object()
        else:
            html = self._get_html_tree_by_url(link)

        parsed["name"] = self.get_name(html, link)

        start_date = self.get_by_label_from_case_page(html, "Date Filed:")
        if start_date:
            parsed["other_dates"] = (
                f"Date case began in court of appeals: {start_date}"
            )

        # For example:
        # on texapp: "Protective Order", "Contract", "Personal Injury"
        # on tex: "Petition for Review originally filed as 53.7(f)"
        parsed["nature_of_suit"] = self.get_by_label_from_case_page(
            html, "Case Type:"
        )
        opinions, disposition = self.get_opinions(html, opinion_date)
        parsed["sub_opinions"] = opinions
        parsed["disposition"] = disposition

        coa_id, trial_id = (
            "ctl00_ContentPlaceHolder1_divCOAInfo",
            "ctl00_ContentPlaceHolder1_pnlTrialCourt2",
        )

        # Prioritize the "higher" (COA) lower court
        oci = {}
        if self.checkbox in [0, 1]:
            oci = self.parse_originating_court_info(html, coa_id)
        if not oci:
            oci = self.parse_originating_court_info(html, trial_id)
        parsed.update(oci)

        return parsed

    def parse_originating_court_info(
        self, html: lxmlHTML, table_id: str
    ) -> dict:
        """Parses Originating Court Information section

        Some Supreme Court or texcrimapp cases have OCI for both Appeals
        and Trial courts. In Courtlistener, OCI and Docket have a 1-1 relation,
        so we can only pick one

        Example: https://search.txcourts.gov/Case.aspx?cn=22-0431&coa=cossup

        :param html: object for aplying selectors
        :table_id: either COA or Trial Courts information tables

        :return: dict with parsed OCI data
        """
        labels = html.xpath(
            f"//div[@id='{table_id}']//div[@class='span2']/label/text()"
        )
        values = html.xpath(f"//div[@id='{table_id}']//div[@class='span4']")

        data = {}
        for lab, val in zip(labels, values):
            key = self.oci_mapper.get(lab.strip())
            val = (
                val.xpath("div/a/text()")[0]
                if val.xpath("div/a")
                else val.xpath("text()[last()]")[0]
            )
            if not key or not val.strip():
                continue
            data[key] = val.strip()

        if "COA" in table_id:
            citation = data.pop("citation", "")
            if "," in citation:
                _, data["date_judgment"] = citation.split(",")
            elif "-" in citation or "/" in citation:
                try:
                    data["date_judgment"] = parser.parse(citation).date()
                except parser.ParserError:
                    pass

        # delete placeholder names
        if data.get("lower_court_judge") and re.search(
            "County|District", data["lower_court_judge"]
        ):
            data["lower_court_judge"] = ""
        if data.get("court_reporter") and re.search(
            "Court Reporter", data["court_reporter"]
        ):
            data["court_reporter"] = ""

        return data

    def get_name(self, html: lxmlHTML, link: str) -> str:
        """Abstract out the case name from the case page."""
        try:
            plaintiff = self.get_by_label_from_case_page(html, "Style:")
            defendant = self.get_by_label_from_case_page(html, "v.:")

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
            return ""

    def get_opinions(
        self, html: lxmlHTML, op_date: str
    ) -> tuple[list[dict], str]:
        """Get opinions belonging to this cluster from the case page

        Use the search interface date to look for clusters around that date,
        since a case may have older or more recent opinions (in a backscrape)

        Some texapp courts mark the 'Judgement' document
        as having a 'Opinion' type. For example, texapp 4 and 6.

        On some case pages, the Court of Criminal Appeals opinion appears
        in the lower court. See texapp_12_subexample_2

        Some cases have been re-heard in the same court, or remanded,
        and their pages have multiple opinions that do not belong
        to the same cluster. See texapp_10_subexample_3

        :param html: page's HTML object
        :return List of opinions
        """
        opinions = []
        opinion_xpath = "//div[div[contains(text(), 'Case Events')]]//tr[td[contains(text(), 'pinion issued')]]"
        link_xpath = ".//tr[td[1]/a and td[2][contains(text(), 'pinion') or normalize-space(text())='CCA']]"
        disposition = ""

        try:
            search_date = datetime.strptime(op_date, "%m/%d/%Y").date()
        except ValueError:
            search_date = parser.parse(op_date)

        for opinion in html.xpath(opinion_xpath):
            op = {}
            link = opinion.xpath(link_xpath)
            if not link:
                logger.warning("No link for this opinion")
                continue

            try:
                date_string = opinion.xpath(".//td[1]/text()")[0]
                opinion_date = datetime.strptime(
                    date_string, "%m/%d/%Y"
                ).date()
            except ValueError:
                logger.warning("Could not parse date '%s'", date_string)
                continue

            if (
                abs((search_date - opinion_date).days)
                > self.max_days_to_cluster
            ):
                # this opinion belongs to an older opinion cluster
                logger.warning("Skipping older opinion clusters")
                continue

            op["url"] = link[0].xpath("td/a/@href")[0]

            op_type = link[0].xpath("td[2]/text()")[0].strip().lower()
            concur = "concur" in op_type
            dissent = "dissent" in op_type
            if concur and dissent:
                op["type"] = (
                    OpinionType.CONCURRING_IN_PART_AND_DISSENTING_IN_PART.value
                )
            elif concur:
                op["type"] = OpinionType.CONCURRENCE.value
            elif dissent:
                op["type"] = OpinionType.DISSENT.value
            else:
                op["type"] = OpinionType.MAJORITY.value
                # use the 'main' opinion disposition as cluster disposition
                disposition = opinion.xpath(".//td[3]/text()")[0]

            opinions.append(op)

        return opinions, disposition

    def get_by_label_from_case_page(self, html: lxmlHTML, label: str) -> str:
        """Helper to get text following a label on the case page"""
        try:
            return html.xpath(
                f'//label[contains(text(), "{label}")]/parent::div/following-sibling::div/text()'
            )[0].strip()
        except IndexError:
            return ""

    def _download_backwards(self, dates: tuple[date, date]) -> None:
        """Overrides present scraper start_date and end_date

        :param dates: (start_date, end_date) tuple
        :return None
        """
        start, end = dates
        self.start_date = (
            start.date() if not isinstance(start, date) else start
        )
        self.end_date = end.date() if not isinstance(end, date) else end
        logger.info(
            "Backscraping for range %s %s", self.start_date, self.end_date
        )

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
