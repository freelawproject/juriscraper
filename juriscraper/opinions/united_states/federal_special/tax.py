# Scraper for the United States Tax Court
# CourtID: tax
# Court Short Name: Tax Ct.
# Neutral Citation Format (Tax Court opinions): 138 T.C. No. 1 (2012)
# Neutral Citation Format (Memorandum opinions): T.C. Memo 2012-1
# Neutral Citation Format (Summary opinions: T.C. Summary Opinion 2012-1

import re
from lxml import html
from datetime import date, datetime, timedelta
from juriscraper.OpinionSiteAspx import OpinionSiteAspx


class Site(OpinionSiteAspx):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "https://www.ustaxcourt.gov/UstcInOp/OpinionSearch.aspx"
        self.base_path = (
            '//tr[@class="ResultsOddRow" or ' '@class="ResultsEvenRow"]'
        )
        self.case_date = date.today()
        self.backwards_days = 14
        self.court_id = self.__module__
        self.data = None
        self.spoof_user_agent = True

    def _get_data_template(self):
        return {
            "ctl00$Content$ddlJudges": "0",
            "ctl00$Content$ddlOpinionTypes": "0",
            "ctl00$Content$rdoCaseName": "D",
            "ctl00$Content$ddlDocumentNumHits": "All",
            "ctl00$Content$btnSearch": "Search",
            "__VIEWSTATE": None,
            "__EVENTVALIDATION": None,
        }

    def _download(self, request_dict={}):
        self.method = "GET"
        self._update_html()
        self._update_data()
        self.method = "POST"
        self._update_html()
        return self.html

    def _get_download_urls(self):
        # URLs here take two forms. For precedential cases, they're simple, and
        # look like:
        #   https://www.ustaxcourt.gov/UstcInOp/OpinionViewer.aspx?ID=11815
        # But for non-precedential cases, they have an annoying JS thing, and
        # links look like:
        #   https://www.ustaxcourt.gov/UstcInOp/OpinionSearch.aspx#11813
        # Note the hash instead of the ID.
        #
        # This is annoying, but we just have to swap out the ending and it
        # should be fine.
        hrefs = []
        path = self.base_path + "//@href"
        for href in self.html.xpath(path):
            if "?ID" in href:
                hrefs.append(href)
            else:
                hrefs.append(
                    href.replace(
                        "OpinionSearch.aspx#", "OpinionViewer.aspx?ID="
                    )
                )
        return hrefs

    def _get_case_names(self):
        case_names = []
        path = self.base_path + "//td[1]"
        for td in self.html.xpath(path):
            case_names.append(td.text_content().strip() + " v. Commissioner")
        return case_names

    def _get_case_name_shorts(self):
        # The normal values are particularly bad, usually just returning
        # "Commissioner" for all cases. Just nuke these values.
        return [""] * len(self.case_names)

    def _get_precedential_statuses(self):
        statuses = []
        path = self.base_path + "//td[2]"
        for td in self.html.xpath(path):
            status = td.text_content().strip().lower()
            if "opinion" in status:
                statuses.append("Published")
            elif "memorandum" in status:
                statuses.append("Unpublished")
            elif "summary" in status:
                statuses.append("Unpublished")
            else:
                statuses.append("Unknown")
        return statuses

    def _get_case_dates(self):
        dates = []
        path = self.base_path + "//td[3]"
        for td in self.html.xpath(path):
            date_string = td.text_content().strip()
            dates.append(datetime.strptime(date_string, "%m/%d/%Y").date())
        return dates

    def extract_from_text(self, scraped_text):
        """Can we extract the citation and related information

        :param scraped_text: The content of the docuemnt downloaded
        :return: dictionary of citations, reporter, volume and page
        """
        metadata = {
            "Citation": {"type": "SPECIALTY"},
            "OpinionCluster": {"precedential_status": ""},
        }

        tax_court_reports_regex = re.compile(
            r"""
            ([0-9]{1,4})\s{1,}                           # (volume)
            UNITED\ STATES\ TAX\ COURT\ REPORTS?\s{1,}   # (reporter)
            \((\d{1,4})\)                                # (page)
            """,
            re.VERBOSE | re.IGNORECASE,
        )

        tax_court_alt_regex = re.compile(
            r"""
            ((T\.\ ?C\.\s((Memo\.?)|(Summm?ary\ Opinion))\s{1,} # T.C. Memo or Summary Opinion (reporter)
            ([0-9]{4})                                          # Four digit year (volume)
            .                                                   # hyphen, em-dash etc.
            ([0-9]{1,3})\b)                                     # 1-3 digit number in order of publication (page)
            |                                                   # or 
            ([0-9]{1,4})\s{1,}                                  # (volume)
            (T\.\ ?C\.\ No\.)(?:\s{1,})?                        # T.C. No. (reporter)
            (\d{1,4}))                                          # (page)
            """,
            re.VERBOSE | re.IGNORECASE,
        )

        match = re.search(tax_court_reports_regex, scraped_text)

        if match:
            metadata["Citation"]["volume"] = match.group(1)
            metadata["Citation"]["page"] = match.group(2)
            metadata["Citation"]["reporter"] = "T.C."
            metadata["OpinionCluster"]["precedential_status"] = "Published"
        else:
            match = re.search(tax_court_alt_regex, scraped_text)
            if match:
                if "No." in match.group():
                    metadata["Citation"]["reporter"] = "T.C. No."
                    metadata["Citation"]["volume"] = match.group(8)
                    metadata["Citation"]["page"] = match.group(10)
                    metadata["OpinionCluster"][
                        "precedential_status"
                    ] = "Published"
                else:
                    if "Memo" in match.group():
                        metadata["Citation"]["reporter"] = "T.C. Memo."
                    elif "Summ" in match.group():
                        metadata["Citation"][
                            "reporter"
                        ] = "T.C. Summary Opinion"
                    metadata["Citation"]["volume"] = match.group(6)
                    metadata["Citation"]["page"] = match.group(7)
                    metadata["OpinionCluster"][
                        "precedential_status"
                    ] = "Unpublished"

        return metadata

    def _update_data(self):
        # Call the super class version, which creates a new data dict from the
        # template and fills in ASPX specific values.
        super(Site, self)._update_data()

        self.backdate = self.case_date - timedelta(self.backwards_days)

        f1_today = self.case_date.strftime("%m/%d/%Y")
        f2_today = self.case_date.strftime("%Y-%m-%d-%H-%M-%S")

        f1_backdate = self.backdate.strftime("%m/%d/%Y")
        f2_backdate = self.backdate.strftime("%Y-%m-%d-%H-%M-%S")

        self.data.update(
            {
                "ctl00$Content$dpDateSearch$dateInput": f1_backdate,
                "ctl00_Content_dpDateSearch_dateInput_ClientState": '{"validationText":"%s","valueAsString":"%s","lastSetTextBoxValue":"%s"}'
                % (f2_backdate, f2_backdate, f1_backdate),
                "ctl00$Content$dpDateSearchTo$dateInput": f1_today,
                "ctl00_Content_dpDateSearchTo_dateInput_ClientState": '{"validationText":"%s","valueAsString":"%s","lastSetTextBoxValue":"%s"}'
                % (f2_today, f2_today, f1_today),
            }
        )
