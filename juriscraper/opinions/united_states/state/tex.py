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
from typing import Optional, Dict

from juriscraper.AbstractSite import logger
from juriscraper.lib.string_utils import titlecase
from juriscraper.NewOpinionSite import NewOpinionSite


class Site(NewOpinionSite):
    oci_mapper = {
        # Court of Appelas Information
        "COA Case": "docket_number",
        "COA District": "appeal_from_str",
        "COA Justice": "assigned_to_str",
        "Opinion Cite": "citation",  # may contain date data
        # Trial Court Information
        "Court Case": "docket_number",
        "Court Judge": "assigned_to_str",
        "Court": "appeal_from_str",
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
            parsed = self.parse_case_page(row.xpath(".//a")[2].get("href"))
            parsed["oc.date_filed"] = row.xpath("td[2]")[0].text_content()
            parsed["d.docket_number"] = row.xpath("td[5]")[0].text_content()
            
            if not parsed.get("opinions"):
                opinion = {"download_url": row.xpath(".//a")[1].get("href")}
                parsed["opinions"] = [opinion]
            
            self.cases.append(parsed)

    def parse_case_page(self, link: str):
        """Parses the case page

        Usually we would defer getting extra data until dup checking
        is done by the caller. However, we get the `case_name` from this
        page, which is need for site hash computing, which cannot be deferred

        :param link: url of the case page
        """
        parsed = {}
        if self.test_mode_enabled():
            return parsed

        html = self._get_html_tree_by_url(link)
        parsed["d.case_name"] = self.get_name(html, link)
        parsed["d.date_filed"] = self.get_by_label_from_case_page(html, "Date Filed:")
        
        # For example:
        # on texapp: "Protective Order", "Contract", "Personal Injury"
        # on tex: "Petition for Review originally filed as 53.7(f)"
        parsed["oc.nature_of_suit"] =  self.get_by_label_from_case_page(html, "Case Type:")
        self.get_opinions(html, parsed)
        
        coa_id, trial_id = (
            "ctl00_ContentPlaceHolder1_divCOAInfo",
            "ctl00_ContentPlaceHolder1_pnlTrialCourt2",
        )
        if self.checkbox == 0:
            oci = self.parse_originating_court_info(html, coa_id)
        else:
            oci = self.parse_originating_court_info(html, trial_id)
        parsed["oci"] = oci

        # TODO: we could extract people_db models: Party, Attorneys, PartyType
        return parsed

    def parse_originating_court_info(self, html, table_id):
        """Parses OCI section

        Some Supreme Case cases have OCI for both Appeal and Trial court
        In Courtlistener, OCI and Docket have a 1-1 relation
        So we may only pick one

        Example: https://search.txcourts.gov/Case.aspx?cn=22-0431&coa=cossup
        """
        labels = html.xpath(
            f"//div[@id='{table_id}']//div[class='span2']/label/text()"
        )
        values = html.xpath(
            f"//div[@id='{table_id}']//div[class='span4']/text()[last()]"
        )

        data = {}
        for lab, val in zip(labels, values):
            key = self.oci_mapper.get(lab.strip())
            if not key or not val.strip():
                continue
            data[lab] = val

        if "COA" in table_id:
            if data.get("appeal_from_str"):
                data["appeal_from"] = "texapp"
            if data.get("citation") and "," in data["citation"]:
                _, data["date_judgment"] = data.pop("citation").split(",")

        return data

    def get_name(self, html, link: str) -> Optional[str]:
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

    def get_opinions(self, html, parsed):
        # In texcrimapp, opinion is in upper case OPINION ISSD
        disp = "//div[contains(text(), 'Case Events')]//td[contains(text(), 'opinion')]/following-sibling::td[1]/text()"
        if html.xpath(disp):
            parsed["oc.disposition"] = html.xpath(disp)[0]

        # 2 Opinions: main and concurring
        # https://search.txcourts.gov/Case.aspx?cn=PD-0984-19&coa=coscca
        
        # 3 opinions
        # https://search.txcourts.gov/Case.aspx?cn=PD-0037-22&coa=coscca
        
        # supreme court has 'remarks' field, which may have per_curiam field
        # https://search.txcourts.gov/Case.aspx?cn=22-0424&coa=cossup
        
        # https://search.txcourts.gov/Case.aspx?cn=23-0390&coa=cossup
        # structure is not so clear
        
        # TODO
        # build object
        # clean values
        # propagate shared values
        # fill defaults
        # validate JSON
        # rebuild examples, including the extra page
        # transform another priority source to see how it looks
        
    
    def get_by_label_from_case_page(self, html, label:str) -> str:
        xpath = f'//label[contains(text(), "{label}")]/parent::div/following-sibling::div/text()'
        value = html.xpath(xpath)
        return value[0].strip() if value else ""
        