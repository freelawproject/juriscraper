"""Scraper for Kentucky Supreme Court
CourtID: ky
Court Short Name: Ky.
Contact: https://courts.ky.gov/aoc/technologyservices/Pages/ContactTS.aspx

History:
    2014-08-07: Created by mlr.
    2014-12-15: Updated to fetch 100 results instead of 30. For reasons unknown
                this returns more recent results, while a smaller value leaves
                out some of the most recent items.
    2016-03-16: Restructured by arderyp to pre-process all data at donwload time
                to work around resources whose case names cannot be fetched to
                to access restrictions.
    2020-08-28: Updated to use new secondary search portal at https://appellatepublic.kycourts.net/
Notes:
    This scraper is unique. Kentucky does not provide case names in the primary
    search portal's result page, making them almost useless. They have a secondary
    search portal that allows a lookup by case year and number, which *does* provide
    the case name.

    Primary Search Portal:          http://apps.courts.ky.gov/supreme/sc_opinions.shtm
    Primary Search Portal POST:     http://162.114.92.72/dtsearch.asp
    Secondary Search Portal:        https://appellatepublic.kycourts.net/
    Secondary Search Portal POST:   https://appellatepublic.kycourts.net/api/api/v1/cases/search


    Our two step process is as follows:
      1. Get the pdf url, case date, and docket number from the Primary Search Portal
      2. If the above data is valid, use publication year and docket number
         to fetch case name from Secondary Search Portal

    Unlike other scrapers, all of the metadata above is gathered at download time,
    saved on the local object, and merely echoed back in by the standard getters.
    This design allows us to avoid issues with cases that have restricted access
    in the Secondary Search Portal (example: year=2015, docket=000574).  These
    restricted resources will be skipped.

    Also fun, they use IP addresses instead of DNS and hide them behind HTML
    frames hosted by real domains.

    I tried calling to get more information, and though they've heard of us (a
    first!), they didn't want to help, and seemed downright aggressive in their
    opposition. Curious. Anyway, don't bother calling  again.

    You can contact support@dtsearch.com with questions about the search
    interface. Best of luck.
"""

import re

from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.lib.string_utils import titlecase


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        # Sometimes they change the ip/endpoint below, in which
        # case the scraper will throw a 404 error. just go to
        # http://apps.courts.ky.gov/supreme/sc_opinions.shtm
        # and inspect the form html and grab the new "action" url
        self.url = "http://162.114.92.72/dtSearch/dtisapi6.dll"
        # Sometimes they also change up the key/value pairs below.
        # What you want to do is go to the url in the comment above,
        # open your browser inspector's network tab, then search on
        # the page's form for "xfirstword", 100 results, sorted by
        # date, click search, and then inspect the Params for the
        # POST request that was just triggered. This site sucks.
        self.parameters = {
            "index": "*{aa61be39717dafae0e114c24b74f68db}+Supreme+Court+Opinions+(1996+)",
            "request": "xfirstword",
            "fuzziness": "0",
            "MaxFiles": "100",
            "autoStopLimit": "0",
            "sort": "Date",
            "cmd": "search",
            "SearchForm": "%%SearchForm%%",
            "dtsPdfWh": "*",
            "OrigSearchForm": "/dtsearch_form.html",
            "pageSize": "1000",
            "fileConditions": "",
            "booleanConditions": "",
        }
        self.method = "POST"
        self.docket_number_regex = re.compile(
            r"(?P<year>\d{4})-(?P<court>[SC]{2})-(?P<number>\d+)"
        )
        self.hrefs_contain = "Opinions"

    def _process_html(self):
        # Search second column cells for valid opinions
        data_cell_path = "//table//tr/td[2]/font"
        for cell in self.html.xpath(data_cell_path):
            # Cell must contain a link
            if cell.xpath("a"):
                link_href = cell.xpath("a/@href")[0].strip()
                cell_text = cell.xpath("text()")
                date = self._parse_date_from_cell_text(cell_text)
                # Cell must contain a parse-able date
                if date:
                    docket_match = self.docket_number_regex.search(link_href)
                    # Link must contain a docket number conforming to expected format
                    if docket_match:
                        if self.test_mode_enabled():
                            # Don't fetch names when running tests
                            name = "No case names fetched during tests."
                        else:
                            # Fetch case name from external portal search (see doc string at top for details)
                            case_number = "%s-%s-%s" % (
                                docket_match.group("year"),
                                docket_match.group("court"),
                                docket_match.group("number")[-4:],
                            )
                            name = self._fetch_case_name(case_number)
                        if name:
                            docket_number = "%s %s %s" % (
                                docket_match.group("year"),
                                docket_match.group("court"),
                                docket_match.group("number"),
                            )
                            self.cases.append(
                                {
                                    "date": date,
                                    "docket": docket_number,
                                    "name": name,
                                    "status": "Unknown",
                                    "url": link_href,
                                }
                            )

    def _parse_date_from_cell_text(self, cell_text):
        date = False
        for text in cell_text:
            try:
                date = text.strip()
                convert_date_string(date)
                break
            except ValueError:
                pass
        return date

    def _fetch_case_name(self, case_number):
        """Fetch case name for a given docket number + publication year pair."""

        # If case_number is not expected 12 characters, skip it, since
        # we can't know how to fix the courts typo. They likely forgot
        # to '0' pad the beginning or the end of the 'number' suffix,
        # but we can't know for sure.
        if len(case_number) != 12:
            return False

        url = "https://appellatepublic.kycourts.net/api/api/v1/cases/search"
        self.request["parameters"] = {
            "params": {
                "queryString": "true",
                "searchFields[0].searchType": "Starts With",
                "searchFields[0].operation": "=",
                "searchFields[0].values[0]": case_number,
                "searchFields[0].indexFieldName": "caseNumber",
            }
        }

        self._request_url_get(url)
        json = self.request["response"].json()

        try:
            title = json["resultItems"][0]["rowMap"]["shortTitle"]
        except IndexError:
            return False
        return titlecase(title)
