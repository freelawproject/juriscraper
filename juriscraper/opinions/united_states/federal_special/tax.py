# Scraper for the United States Tax Court
# CourtID: tax
# Court Short Name: Tax Ct.
# Neutral Citation Format (Tax Court opinions): 138 T.C. No. 1 (2012)
# Neutral Citation Format (Memorandum opinions): T.C. Memo 2012-1
# Neutral Citation Format (Summary opinions: T.C. Summary Opinion 2012-1

import re
import requests
from datetime import date, datetime, timedelta
from dateutil.rrule import WEEKLY, rrule
from lxml import html

from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.url = "https://www.ustaxcourt.gov/UstcInOp/OpinionSearch.aspx"
        self.base_path = (
            '//tr[@class="ResultsOddRow" or ' '@class="ResultsEvenRow"]'
        )
        self.case_date = date.today()
        self.backwards_days = 14
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                WEEKLY, dtstart=date(1995, 9, 25), until=self.case_date,
            )
        ]

        self.court_id = self.__module__

    def _download(self, request_dict={}):
        """

        :param request_dict:
        :return:
        """
        s = requests.session()
        r = s.get(self.url)

        self.set_local_variables(r)

        r = requests.post(self.url,
                          headers=self.headers,
                          data=self.data)

        return html.fromstring(r.text)


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

    def set_local_variables(self, r):
        """"""

        backdate = self.case_date - timedelta(self.backwards_days)

        f1_today = self.case_date.strftime("%m/%d/%Y")
        f2_today = self.case_date.strftime("%Y-%m-%d-%H-%M-%S")

        f1_backdate = backdate.strftime("%m/%d/%Y")
        f2_backdate = backdate.strftime("%Y-%m-%d-%H-%M-%S")

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        }

        self.data = {
            'ctl00$Content$dpDateSearch$dateInput': f1_backdate,
            'ctl00_Content_dpDateSearch_dateInput_ClientState': '{"enabled":true,"emptyMessage":"","validationText":"%s","valueAsString":"%s","minDateStr":"1980-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":"%s"}' % (
            f2_backdate, f2_backdate, f1_backdate),
            'ctl00$Content$dpDateSearchTo$dateInput': f1_today,
            'ctl00_Content_dpDateSearchTo_dateInput_ClientState': '{"enabled":true,"emptyMessage":"","validationText":"%s","valueAsString":"%s","minDateStr":"1980-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":"%s"}' % (
            f2_today, f2_today, f1_today),
            'ctl00$Content$ddlJudges': '0',
            'ctl00$Content$ddlOpinionTypes': '0',
            'ctl00$Content$rdoCaseName': 'D',
            'ctl00$Content$ddlDocumentNumHits': 'All',
            'ctl00$Content$btnSearch': 'Search',
        }

        soup = html.fromstring(r.text)
        self.data['__VIEWSTATE'] = soup.xpath('//*[@id="__VIEWSTATE"]/@value')[0]
        self.data['__EVENTVALIDATION'] = soup.xpath('//*[@id="__EVENTVALIDATION"]/@value')[0]
