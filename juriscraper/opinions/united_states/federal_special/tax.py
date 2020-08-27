# -*- coding: utf-8 -*-
# Scraper for the United States Tax Court
# CourtID: tax
# Court Short Name: Tax Ct.
# Neutral Citation Format (Tax Court opinions): 138 T.C. No. 1 (2012)
# Neutral Citation Format (Memorandum opinions): T.C. Memo 2012-1
# Neutral Citation Format (Summary opinions: T.C. Summary Opinion 2012-1

import re
from datetime import date, datetime, timedelta
from dateutil.rrule import WEEKLY, rrule

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSiteWebDriven import OpinionSiteWebDriven
from juriscraper.lib.html_utils import fix_links_but_keep_anchors
from juriscraper.lib.models import citation_types


class Site(OpinionSiteWebDriven):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.uses_selenium = True
        self.url = "https://www.ustaxcourt.gov/UstcInOp/OpinionSearch.aspx"
        self.base_path = (
            '//tr[@class="ResultsOddRow" or ' '@class="ResultsEvenRow"]'
        )
        self.case_date = date.today()
        self.backwards_days = 14
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                WEEKLY,
                dtstart=date(1995, 9, 25),
                until=date(2018, 11, 13),
            )
        ]

        self.court_id = self.__module__

    def _download(self, request_dict={}):
        """Uses Selenium because doing it with requests is a pain."""
        if self.test_mode_enabled():
            return super(Site, self)._download(request_dict=request_dict)

        logger.info("Now downloading case page at: %s" % self.url)
        self.initiate_webdriven_session()

        # Set the start and end dates
        start_date_id = "ctl00_Content_dpDateSearch_dateInput"
        start_date_input = self.webdriver.find_element_by_id(start_date_id)
        start_date_input.send_keys(
            (self.case_date - timedelta(days=self.backwards_days)).strftime(
                "%-m/%-d/%Y"
            )
        )

        end_date_id = "ctl00_Content_dpDateSearchTo_dateInput"
        end_date_input = self.webdriver.find_element_by_id(end_date_id)
        end_date_input.send_keys(self.case_date.strftime("%-m/%-d/%Y"))
        # self.take_screenshot()

        # Check ordering by case date (this orders by case date, *ascending*)
        ordering_id = "Content_rdoCaseName_1"
        self.webdriver.find_element_by_id(ordering_id).click()

        # Submit
        self.webdriver.find_element_by_id("Content_btnSearch").click()

        # Do not proceed until the results show up.
        self.wait_for_id("Content_ddlResultsPerPage")
        # self.take_screenshot()

        text = self._clean_text(self.webdriver.page_source)
        self.webdriver.quit()
        html_tree = self._make_html_tree(text)
        html_tree.rewrite_links(fix_links_but_keep_anchors, base_href=self.url)
        return html_tree

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

    def _download_backwards(self, d):
        self.backwards_days = 7
        self.case_date = d
        logger.info(
            "Running backscraper with date range: %s to %s",
            self.case_date - timedelta(days=self.backwards_days),
            self.case_date,
        )
        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    def extract_from_text(self, scraped_text):
        """Can we extract the citation and related information

        :param scraped_text: The content of the docuemnt downloaded
        :return: dictionary of citations, reporter, volume and page
        """
        metadata = {
            "Citation": {"type": citation_types["SPECIALTY"]},
            "Docket": {"docket_number": ""},
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

        metadata["Docket"]["docket_number"] = self.get_tax_docket_numbers(
            scraped_text
        )
        return metadata

    def get_tax_docket_numbers(self, opinion_text):
        """Parse opinion plain text for docket numbers.

        First we idenitify where the docket numbers are in the document.
        This is normally at the start of the document but can often follow
         a lengthy case details section.

        :param opinion_text: is the opinions plain_text
        :return docket_string: as string of docket numbers Ex. (18710-94, 12321-95)
        """
        opinion_text = self.remove_en_em_dash(opinion_text)
        parsed_text = ""
        docket_no_re = r"Docket.? Nos?.? .*[0-9]{3,5}"
        matches = re.finditer(docket_no_re, opinion_text)

        for matchNum, match in enumerate(matches, start=1):
            parsed_text = opinion_text[match.start() :]
            break

        matches2 = re.finditer(
            r"[0-9]{3,5}(-|–)[\w]{2,4}([A-Z])?((\.)| [A-Z]\.)", parsed_text
        )
        for m2, match2 in enumerate(matches2, start=0):
            parsed_text = parsed_text[: match2.end()]
            break

        docket_end_re = r"[0-9]{3,5}(-|–)[\w]{2,4}([A-Z])?((\,|\.)| [A-Z]\.)"

        matches = re.finditer(docket_end_re, parsed_text, re.MULTILINE)
        hits = []
        for matchNum, match in enumerate(matches, start=1):
            hits.append(match.group())
        docket_string = ", ".join(hits).replace(",,", ",").replace(".", "")
        return docket_string.strip()

    def remove_en_em_dash(self, opinion_text):
        opinion_text = re.sub(u"–", "-", opinion_text)
        opinion_text = re.sub(u"—", "-", opinion_text)
        opinion_text = re.sub(u"–", "-", opinion_text)
        return opinion_text
