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
#  - 2023-03-08: Updated by grossir to collect more data
import re
from datetime import date, timedelta
from typing import Dict, List

from dateutil import parser
from lxml import html as lxmlHTML

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.NewOpinionSite import NewOpinionSite


class Site(NewOpinionSite):
    oci_mapper = {
        # Court of Appelas Information
        "COA Case": "docket_number",
        "COA District": "origin_court",
        "COA Justice": "assigned_to_str",
        "Opinion Cite": "citation",  # may contain date data
        # Trial Court Information
        "Court Case": "docket_number",
        "Court Judge": "assigned_to_str",
        "Court": "origin_court",
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
        self.status = "Published"
        self.url = "https://search.txcourts.gov/CaseSearch.aspx?coa=cossup"
        self.seen_case_urls = set()

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

        self.parameters = {
            "ctl00$ContentPlaceHolder1$SearchType": "rbSearchByDocument",  # "Document Search" radio button
            "ctl00$ContentPlaceHolder1$dtDocumentFrom": str(last_month),
            "ctl00$ContentPlaceHolder1$dtDocumentFrom$dateInput": last_month_str,
            "ctl00_ContentPlaceHolder1_dtDocumentFrom_dateInput_ClientState": date_param,
            "ctl00$ContentPlaceHolder1$dtDocumentTo": str(today),
            "ctl00$ContentPlaceHolder1$dtDocumentTo$dateInput": today_str,
            "ctl00$ContentPlaceHolder1$chkListDocTypes$0": "on",  # "Opinion" checkbox
            "ctl00$ContentPlaceHolder1$btnSearchText": "Search",
            "__VIEWSTATE": view_state,
            f"ctl00$ContentPlaceHolder1$chkListCourts${self.checkbox}": "on",  # Court checkbox
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

        for row in self.html.xpath(self.rows_xpath):
            # `Document search` page returns OpinionClusters separated,
            # each opinion in a single row. We keep track to skip if we already parsed the case
            case_url = row.xpath(".//a")[2].get("href")
            if case_url in self.seen_case_urls:
                continue
            self.seen_case_urls.add(case_url)

            parsed = self.parse_case_page(case_url)
            parsed["oc.date_filed"] = row.xpath("td[2]")[0].text_content()
            parsed["d.docket_number"] = row.xpath("td[5]")[0].text_content()

            if not parsed.get("opinions"):
                opinion = {"download_url": row.xpath(".//a")[1].get("href")}
                parsed["opinions"] = [opinion]
            else:
                judges, dispositions = [], []
                for op in parsed["opinions"]:
                    judges.extend(op.get("joined_by_str", []))
                    judges.append(op.get("author_str"))
                    dispositions.append(op.pop("disposition", ""))
                parsed["oc.judges"] = list(filter(bool, judges))
                parsed["oc.disposition"] = self.get_cluster_disposition(
                    dispositions
                )

            self.cases.append(parsed)

    def parse_case_page(self, link: str) -> Dict:
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

        parsed["d.case_name"] = self.get_name(html, link)
        parsed["d.date_filed"] = self.get_by_label_from_case_page(
            html, "Date Filed:"
        )

        # For example:
        # on texapp: "Protective Order", "Contract", "Personal Injury"
        # on tex: "Petition for Review originally filed as 53.7(f)"
        parsed["oc.nature_of_suit"] = self.get_by_label_from_case_page(
            html, "Case Type:"
        )
        parsed["opinions"] = self.get_opinions(html)

        coa_id, trial_id = (
            "ctl00_ContentPlaceHolder1_divCOAInfo",
            "ctl00_ContentPlaceHolder1_pnlTrialCourt2",
        )
        oci = None
        if self.checkbox in [0, 1]:
            oci = self.parse_originating_court_info(html, coa_id)
            if oci:
                parsed["d.appeal_from_str"] = oci.pop("origin_court", "")
                if parsed["d.appeal_from_str"]:
                    parsed["d.appeal_from_id"] = "texapp"
        if not oci:
            oci = self.parse_originating_court_info(html, trial_id)
            parsed["d.appeal_from_str"] = oci.pop("origin_court", "")

        parsed["oci"] = oci

        # Further work:
        # we could extract people_db models: Party, Attorneys, PartyType
        return parsed

    def parse_originating_court_info(
        self, html: lxmlHTML, table_id: str
    ) -> Dict:
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

    def get_opinions(self, html: lxmlHTML) -> List[Dict]:
        """Parses opinions present in case page.
        If we fail to find any opinions here, the scraper will default to using
        the URL in the search results page

        `tex`, `texcrimapp` and `texapp_*` differ on how opinions are presented,
        so this method is overridden in inheriting classes so as to not
        overcrowd it with all the if clauses

        Examples:

        Cluster with 3 opinions (Supreme Court)
        https://search.txcourts.gov/Case.aspx?cn=22-0242&coa=cossup

        Counter Examples:
        'Opinion' text does not appear on 'Event Type' column; but there is indeed an opinion
        https://search.txcourts.gov/Case.aspx?cn=21-1008&coa=cossup

        :param html: page's HTML object
        :return List of opinions
        """
        opinions = []
        opinion_xpath = "//div[div[contains(text(), 'Case Events')]]//tr[td[contains(text(), 'pinion issu')]]"
        for opinion in html.xpath(opinion_xpath):
            op = {}
            link = opinion.xpath(".//td//a/@href")
            if not link:
                continue
            op["download_url"] = link[0]
            op["disposition"] = opinion.xpath(".//td[3]/text()")[0]

            # Remarks may contain Per Curiam flag. Does not exist in texcrim
            remark = opinion.xpath(".//td[4]/text()")[0]
            if "per curiam" in remark.lower():
                op["per_curiam"] = True

            author_match = re.search(
                r"(?P<judge>[A-Z][a-z-]+)\s+filed\s+a", remark
            )
            if author_match:
                op["author_str"] = author_match.group("judge")

            joined_match = re.findall(
                r"Justice\s+(?P<judge>[A-Z][a-z-]+) (?!filed)(?!delivered)",
                remark,
            )
            if joined_match:
                op["joined_by_str"] = joined_match

            op_type = opinion.xpath(".//td[2]/text()")[0].lower()
            if "concur" in op_type:
                op["type"] = "030concurrence"
            elif "diss" in op_type:
                op["type"] = "040dissent"
            else:
                op["type"] = "010combined"

            opinions.append(op)

        return opinions

    def get_cluster_disposition(self, dispositions: List) -> str:
        """Get oc.disposition from each opinion's disposition value

        In tex, disposition ir is usually the longest string.
        On texcrimapp, disposition is the same for all opinions
        In texapp_*, disposition is found on the 'main' opinion

        :param dispositions: disposition strings
        :return: dispositon of the cluster
        """
        return sorted(dispositions, key=len)[-1]

    def get_by_label_from_case_page(self, html: lxmlHTML, label: str) -> str:
        """Selects from first / main table of case page

        :param html: HTML object that supports selection
        :param label: label to be used in selector

        :return case page string value
        """
        xpath = f'//label[contains(text(), "{label}")]/parent::div/following-sibling::div/text()'
        value = html.xpath(xpath)
        return value[0].strip() if value else ""
