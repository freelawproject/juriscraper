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
Notes:
    This scraper is unique. Kentucky does not provide case names in the primary
    search portal's result page, making them almost useless. They have a secondary
    search portal that allows a lookup by case year and number, which *does* provide
    the case name (and lots of other information). Note that it only provides
    this information for supreme court cases, so extending this to do kyctapp
    won't be possible.

    Primary Search Portal:          http://apps.courts.ky.gov/supreme/sc_opinions.shtm
    Primary Search Portal POST:     http://162.114.92.72/dtsearch.asp
    Secondary Search Portal:        https://appellate.kycourts.net/SC/SCDockets/
    Secondary Search Portal GET:    https://appellate.kycourts.net/SC/SCDockets/CaseDetails.aspx?cn={yyyySC######}

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

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import titlecase
from juriscraper.lib.string_utils import convert_date_string

## WARNING: THIS SCRAPER IS FAILING:
## This scraper is succeeding in development, but
## is failing in production.  We are not exactly
## sure why, and suspect that the hosting court
## site may be blocking our production IP and/or
## throttling/manipulating requests from production.


class Site(OpinionSite):
    CASE_NAMES = []
    CASE_DATES = []
    DOWNLOAD_URLS = []
    DOCKET_NUMBERS = []

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

    def _download(self, request_dict={}):
        html = super(Site, self)._download(request_dict)
        self._build_data_lists_from_html(html)
        return html

    def _build_data_lists_from_html(self, html):
        # Search second column cells for valid opinions
        data_cell_path = "//table/tr/td[2]/font"
        for cell in html.xpath(data_cell_path):
            # Cell must contain a link
            if cell.xpath("a"):
                link_href = cell.xpath("a/@href")[0].strip()
                link_text = cell.xpath("a/text()")[0].strip()
                cell_text = cell.xpath("text()")
                date = self._parse_date_from_cell_text(cell_text)
                # Cell must contain a parse-able date
                if date:
                    docket_match = self.docket_number_regex.search(link_text)
                    # Cell must contain a docket number conforming to expected format
                    if docket_match:
                        if self.test_mode_enabled():
                            # Don't fetch names when running tests
                            name = "No case names fetched during tests."
                        else:
                            # Fetch case name from external portal search (see doc string at top for details)
                            case_number = "%s%s%s" % (
                                docket_match.group("year"),
                                docket_match.group("court"),
                                docket_match.group("number"),
                            )
                            name = self._fetch_case_name(case_number)
                        if name:
                            docket_number = "%s %s %s" % (
                                docket_match.group("year"),
                                docket_match.group("court"),
                                docket_match.group("number"),
                            )
                            self.CASE_NAMES.append(name)
                            self.CASE_DATES.append(date)
                            self.DOCKET_NUMBERS.append(docket_number)
                            self.DOWNLOAD_URLS.append(link_href)

    def _parse_date_from_cell_text(self, cell_text):
        date = False
        for text in cell_text:
            try:
                date = convert_date_string(text.strip())
                break
            except ValueError:
                pass
        return date

    def _fetch_case_name(self, case_number):
        """Fetch case name for a given docket number + publication year pair.

        Some resources show 'Public Access Restricted' messages and do not
        provide parseable case name information.  These will be skipped by
        our system by returning False below.  The only other approach would
        be to parse the case name from the raw PDF text itself.
        """

        # If case_number is not expected 12 characters, skip it, since
        # we can't know how to fix the courts typo. They likely forgot
        # to '0' pad the beginning or the end of the 'number' suffix,
        # but we can't know for sure.
        if len(case_number) != 12:
            return False

        # HTTPS certificate is bad, but hopefully they'll fix it and we can remove the line below
        self.disable_certificate_verification()

        url = (
            "https://appellate.kycourts.net/SC/SCDockets/CaseDetails.aspx?cn=%s"
            % case_number
        )
        html = self._get_html_tree_by_url(url)

        # Halt if there is a (dismissible) error/warning on the page
        path_error_warning = '//div[contains(@class, "alert-dismissible")]'
        if html.xpath(path_error_warning):
            raise InsanityException(
                "Invalid sub-resource url (%s). Is case number (%s) invalid?"
                % (url, case_number)
            )

        # Ensure that only two substrings are present
        path_party = '//td[@class="party"]/text()'
        parties = html.xpath(path_party)
        if len(parties) != 2:
            raise InsanityException(
                "Unexpected party elements. Expected two substrings, got: %s"
                % ", ".join(parties)
            )

        return titlecase(" v. ".join(parties))

    def _get_download_urls(self):
        return self.DOWNLOAD_URLS

    def _get_case_names(self):
        return self.CASE_NAMES

    def _get_docket_numbers(self):
        return self.DOCKET_NUMBERS

    def _get_case_dates(self):
        return self.CASE_DATES

    def _get_precedential_statuses(self):
        return ["Unknown"] * len(self.CASE_NAMES)
