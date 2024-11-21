"""Scraper for the Supreme Court of Delaware
CourtID: del

Creator: Andrei Chelaru
Reviewer: mlr
"""
from datetime import datetime

from fontTools.misc.plistlib import end_date
from lxml import html

from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court="Supreme Court"
        self.dates = []
        self.urls = []
        self.names = []
        self.dockets = []
        self.status = []
        self.judges=[]
        # Note that we can't do the usual thing here because 'del' is a Python keyword.
        self.court_id = "juriscraper.opinions.united_states.state.del"

    def _get_case_dates(self):
        return self.dates

    def _get_download_urls(self):
        return self.urls

    def _get_case_names(self):
        return self.names

    def _get_docket_numbers(self):
        return self.dockets

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.dates)

    def _get_judges(self):
        # We need special logic here because they use <br> tags in the cell text
        return self.judges

    def _get_nth_cell_data(
        self, cell_number, text=False, href=False, link_text=False
    ):
        # Retrieve specific types of data from all nTH cells in the table
        path = "//table/tr/td[%d]" % cell_number
        if text:
            path += "/text()"
        elif href:
            path += "/a/@href"
        elif link_text:
            path += "/a/text()"
        return self.html.xpath(path)

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        flag = True
        page = 1
        while flag:
            self.url = 'https://courts.delaware.gov/opinions/'
            self.method = 'POST'
            self.parameters={
                "__VIEWSTATE": "q+vYLwcCJM5uANjCzVMRuixU0rRY0P+vw+LGu7rNHYpAuYSpF4krvJNkmOSvgg2oXNKXlqvQKtzFLiIdwDh/P10+7ufyQZm+g6nIbKCGbqk=",
                "__VIEWSTATEGENERATOR": "9190679E",
                "ctlOpinions1selagencies": self.court,
                "ctlOpinions1selperiods": "date",
                "ctlOpinions1txtstartdate": start_date.strftime('%m/%d/%Y'),
                "ctlOpinions1txtenddate": end_date.strftime('%m/%d/%Y'),
                "ctlOpinions1txtsearchtext": "",
                "ctlOpinions1selresults": "100",
                "ctlOpinions1hdnagency": self.court,
                "ctlOpinions1hdncasetype": "",
                "ctlOpinions1hdndivision": "",
                "ctlOpinions1hdnsortby": "",
                "ctlOpinions1hdnsortorder": "0",
                "ctlOpinions1hdnsortbynew": "",
                "ctlOpinions1hdnpageno": str(page)
            }
            if not self.downloader_executed:
                self.html = self._download()
                self._process_html()
                # Find the last <li> element using XPath
                last_li = self.html.xpath('//ul[@class="pagination"]/li[last()]')
                # Print the last <li> element
                if list(last_li).__len__()==0:
                    flag=False
                else:
                    disabled_li=html.tostring(last_li[0], pretty_print=True).decode()
                    if disabled_li.__contains__('class="disabled"'):
                        flag = False

                # appending dates
                for date in self._get_nth_cell_data(2, text=True):
                    self.dates.append(convert_date_string(date.strip()))

                # appending urls
                for url in self._get_nth_cell_data(1, href=True):
                    self.urls.append(url.strip())

                # appending title
                for name in self._get_nth_cell_data(1, link_text=True):
                    self.names.append(name.strip())

                # appending dockets
                for docket in self._get_nth_cell_data(3, link_text=True):
                    doc=docket.strip()
                    doc_arr=[]
                    if doc.__contains__("/"):
                        doc_arr = doc.split("/")
                    elif doc.__contains__("&"):
                        doc_arr = doc.split("&")
                    else:
                        doc_arr=[doc]
                    new_doc=[]
                    for i in doc_arr:
                        new_doc.append(i.strip())
                    self.dockets.append(new_doc)

                # appending judges
                for cell in self.html.xpath("//table/tr/td[6]"):
                    judge = " ".join(cell.xpath("text()")).strip().replace("\n","")
                    self.judges.append([judge])

            page = page + 1
            self.downloader_executed = False

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
        return 0

    def get_state_name(self):
        return "Delaware"

    def get_court_type(self):
        return "state"

    def get_court_name(self):
        return "Supreme Court of Delaware"

    def get_class_name(self):
        return "delaware"
