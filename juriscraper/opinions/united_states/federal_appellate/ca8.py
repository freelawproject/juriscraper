import re
import time
from datetime import date, datetime
from tkinter.scrolledtext import example

from lxml import html
import feedparser
from bs4 import BeautifulSoup
from dateutil.rrule import MONTHLY, rrule

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    exm=[]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                MONTHLY,
                dtstart=date(1995, 11, 1),
                until=date(2015, 1, 1),
            )
        ]

    def _get_case_names(self):
        return self.get_details('name')
        # case_names = []
        # case_name_regex = re.compile(r"(\d{2}/\d{2}/\d{4})(.*)")
        #
        # for text in self.html.xpath(
        #     '//a[contains(@href, "opndir")]/following-sibling::b/text()'
        # ):
        #     case_names.append(case_name_regex.search(text).group(2))


    def _get_download_urls(self):
        return self.get_details('url')
        # return [
        #     e for e in self.html.xpath('//a[contains(@href, "opndir")]/@href')
        # ]

    def _get_case_dates(self):
        return self.get_details('date')

        # for text in self.html.xpath(
        #     '//a[contains(@href, "opndir")]/following-sibling::*/text()'
        # ):
        #     date_string = case_date_regex.search(text).group(1)
        #     case_dates.append(
        #         date.fromtimestamp(
        #             time.mktime(time.strptime(date_string, "%m/%d/%Y"))
        #         )
        #     )


    def _get_docket_numbers(self):
        return self.get_details('docket')
        # docket_numbers = []
        # docket_number_regex = re.compile(r"(\d{2})(\d{4})(u|p)", re.IGNORECASE)
        # for docket_number in self.html.xpath(
        #     '//a[contains(@href, "opndir")]/text()'
        # ):
        #     regex_results = docket_number_regex.search(docket_number)
        #     docket_numbers.append(
        #         f"{regex_results.group(1)}-{regex_results.group(2)}"
        #     )


    def _get_precedential_statuses(self):
        return self.get_details('status')
        # statuses = []
        # for docket_number in self.html.xpath(
        #     '//a[contains(@href, "opndir")]/text()'
        # ):
        #     docket_number = docket_number.split(".")[0]
        #     if "p" in docket_number.lower():
        #         statuses.append("Published")
        #     elif "u" in docket_number.lower():
        #         statuses.append("Unpublished")
        #     else:
        #         statuses.append("Unknown")

    def _download_backwards(self, d):
        self.url = (
            "http://media.ca8.uscourts.gov/cgi-bin/opnByMM.pl?theMM=%02d&theYY=%s&A1=Get+Opinions"
            % (d.month, d.year)
        )

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        end_month = end_date.month
        end_year = end_date.year
        start_month = start_date.month
        for i in range(end_month):
            self.url = ("http://media.ca8.uscourts.gov/cgi-bin/opnByMM.pl?theMM=%02d&theYY=%s&A1=Get+Opinions" % (i+1, end_year))
            if not self.downloader_executed:
                # Run the downloader if it hasn't been run already
                self.html = self._download()
                # Process the available html (optional)
                self._process_html()
            # Set the attribute to the return value from _get_foo()
            # e.g., this does self.case_names = _get_case_names()
            for attr in self._all_attrs:
                self.__setattr__(attr, getattr(self, f"_get_{attr}")())
            self._clean_attributes()
            if "case_name_shorts" in self._all_attrs:
                # This needs to be done *after* _clean_attributes() has been run.
                # The current architecture means this gets run twice. Once when we
                # iterate over _all_attrs, and again here. It's pretty cheap though.
                self.case_name_shorts = self._get_case_name_shorts()
            self._post_parse()
            self._check_sanity()
            self._date_sort()
            self._make_hash()
            self.downloader_executed = False
        return 0

    def get_details(self,detail_type):
        case_dates = []
        case_names = []
        case_status = []
        case_dockets = []
        download_urls = []
        case_date_regex = re.compile(r"(\d{2}/\d{2}/\d{4})(.*)")
        docket_number_regex = re.compile(r"\d+\-\d+")
        status_regex = re.compile(r"\[PUBLISHED\]|\[UNPUBLISHED\]")
        summary_regex = re.compile(r"\][^\]]*$")
        html_string = html.tostring(self.html, pretty_print=True).decode('utf-8')
        soup = BeautifulSoup(html_string, 'html.parser')
        anchors = soup.find_all('a')
        flag = False
        for a in anchors:
            href = a.__str__()
            if (not href.__contains__('opndir')):
                continue
            href = href[href.find('http'):href.find('" target')]
            download_url = href
            a_text = a.next_sibling.text
            if (a_text.__eq__('')):
                continue
            a_date = case_date_regex.search(a_text).group(1)
            a_name = a_text[a_text.find(a_date) + a_date.__len__():a_text.find(
                'U.S. Court of Appeals Case No:')].strip()
            a_docket = docket_number_regex.search(a_text).group(0)
            a_status = status_regex.search(a_text)
            if(a_status is not None):
                a_status = a_status.group(0).replace('[', '').replace(']', '')
            lower_court = a_text[a_text.find(a_docket) + a_docket.__len__():a_text.find('[')].strip()
            judges = a_text.split(']')
            if judges.__len__()>1:
                judges = judges[1].replace('\n', '').replace('[', '').strip()
            summary = summary_regex.search(a_text)
            if(summary is not None):
                summary = summary.group(0).replace(']','').replace('\n', '').strip()
            case_status.append(a_status)
            case_names.append(a_name)
            case_dockets.append(a_docket)
            case_dates.append(date.fromtimestamp(time.mktime(time.strptime(a_date, "%m/%d/%Y"))))
            download_urls.append(download_url)  # self.case_status.append(a_status)  # self.case_status.append(a_status)  # print("DATE: "+a_date+"\nTITLE: "+a_name+"\nDOCKET: "+a_docket+"\nLOWER_COURT: "+lower_court+"\nSTATUS: "+a_status+"\nJUDGES: "+judges+"\nSUMMARY: "+summary+"\nDOWNLOAD_URL: "+download_url)

        if (detail_type.__eq__('date')):
            return case_dates

        if (detail_type.__eq__('name')):
            return case_names

        if (detail_type.__eq__('status')):
            return case_status

        if (detail_type.__eq__('docket')):
            return case_dockets

        if (detail_type.__eq__('url')):
            return download_urls





