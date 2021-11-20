"""Scraper for Colorado Supreme Court
CourtID: colo
Court Short Name: Colo.
Author: Philip Ardery
Reviewer: mlr
Date created: 2016-06-03
Contact: Email "Internet and Technology" staff listed at http://www.cobar.org/staff
         they usually fix issues without resonding to the emails directly. You can
         also try submitting the form here: http://www.cobar.org/contact
"""

import re
from urllib.parse import urlparse

from lxml import html

from juriscraper.AbstractSite import logger
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    sub_page_opinion_link_path = "//a[@class='Head articletitle']"
    parent_summary_block_path = (
        'parent::p/following-sibling::div[@class="Normal"][1]'
    )
    # Regex to extract opinion's data: citation, docket and case name
    regex = r"(?:No\.\s*|)(\d+\s?\w{3}\s?\d+|\d+\s+\w+\s+\d+)(?:[.,]\s+|\.?,?\s*Nos?\.\s*)((?:\w{5,8},\s+)*\w{5,8}\s+(?:[aA][nN][dD]|&)\s+\w{5,8}|\w{5,8})(?:[.,]\s*|\s+)(.*)"
    # Regex for opinions with 2 cases
    regex_second = r"(.*)(?:\s*[,&]\s*No\.\s*)(\w{5,8})(?:,\s*)(.*)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.cobar.org/For-Members/Opinions-Rules-Statutes/Colorado-Supreme-Court-Opinions"
        self.base_path = "//div[@id='dnn_ctr2509_ModuleContent']/ul/li/a"
        self.next_subpage_path = "//a[@id='dnn_ctr2512_DNNArticle_List_MyArticleList_MyPageNav_cmdNext']"
        self.cases = []

    def _download(self, request_dict={}):
        self.request_dict = request_dict
        landing_page_html = super()._download(request_dict)

        # Test/example files should use html from direct resource page
        #
        # PLEASE NOTE: if your adding a new example file, ensure that,
        # if any of the opinion links on the page do not link directly to
        # a pdf url, that you manually edit your example file and add '.pdf'
        # to the end of all those opinion anchor hrefs. We do this in order
        # to prevent the tests form hitting the network.  HINT: if your new
        # test takes any more than a split second to run, its probably hitting
        # the network and needs ot be fixed as explained above.
        #
        # PLEASE ALSO NOTE: coloctapp_example_3.html is supposed to have 0
        # results.  It is a blank page test case covering is_this_a_blank_page().
        if self.test_mode_enabled():
            date_string = landing_page_html.xpath("//h3")[0].text_content()
            date_obj = convert_date_string(date_string)
            self._extract_cases_from_sub_page(landing_page_html, date_obj)
            return [landing_page_html]

        html_trees = []
        html_list = [landing_page_html]

        while len(html_list) > 0:
            html_l = html_list[0]
            html_list = html_list[1:]

            # Loop over sub-pages
            hrefs = html_l.xpath(self.base_path)
            for ahref in hrefs:
                date_string = ahref.xpath("./text()")[0]
                url = ahref.xpath("./@href")[0]
                date_obj = convert_date_string(date_string)
                logger.info(f"Getting sub-url: {url}")

                # Fetch sub-page's content
                html_tree = self._get_html_tree_by_url(url, self.request_dict)
                self._extract_cases_from_sub_page(html_tree, date_obj)
                html_trees.append((html_tree, date_obj))

                # DEACTIVATED BY arderyp ON 2018.06.07, SEE NOTE ON get_next_page()
                # # process all sub-pages
                # if self.next_subpage_path and self.test_mode_enabled():
                #     while True:
                #         next_subpage_html = self.get_next_page(html_tree, self.next_subpage_path, request_dict, url)
                #         if next_subpage_html is None:
                #             break
                #
                #         self._extract_cases_from_sub_page(next_subpage_html, date_obj)
                #         html_trees.append((next_subpage_html, date_obj))
                #         html_tree = next_subpage_html

        return html_trees

    # CALLS TO THIS FUNCTION DEACTIVATED BY arderyp ON 2018.06.07
    # This is (temporarily) disabled because it no longer works,
    # and I (arderyp) am not familiar enough with asp.net to get
    # it working agian without investing a lot of time.  In short,
    # this process is finding the "Next" pagination button, collecting
    # the asp.net <input> field/values from the page, and posting
    # these inputs back to the same page, using the special "Next"
    # button hash/id value.  However, something isn't working, because
    # the posted fields are not being picked up properly, as the same
    # page loads again, instead of the next page.  As a result, we
    # enter an infinite look of finding the next button, submitting
    # the data, landing back on the same page, finding the samenext
    # button, submitting the data, landing back on the same page yet
    # again... end on and on and on. Example pages to test againast:
    #   http://www.cobar.org/For-Members/Opinions-Rules-Statutes/Colorado-Court-of-Appeals-Opinions/Date/bdate/2018-4-19/edate/2018-4-19/cid/6
    #   http://www.cobar.org/For-Members/Opinions-Rules-Statutes/Colorado-Supreme-Court-Opinions/Date/bdate/2017-6-5/edate/2017-6-5/cid/4
    #
    def get_next_page(self, html_l, next_page_xpath, request_dict, url):
        result = None
        for nhref in html_l.xpath(next_page_xpath):
            evtarget = None
            class_, href = nhref.get("class"), nhref.get("href")
            exp_start, exp_end = "javascript:__doPostBack('", "','')"
            if (
                href is not None
                and href.startswith(exp_start)
                and href.endswith(exp_end)
            ):
                evtarget = href[len(exp_start) : -len(exp_end)]
            # a disabled 'next page' link will contains this string in the class list
            if evtarget is not None and "aspNetDisabled" not in class_.split():
                form = [("__EVENTTARGET", ("", evtarget))]
                form_items_xpath = "//input"
                for form_el in html_l.xpath(form_items_xpath):
                    name = form_el.get("name")
                    if name is not None:
                        value = form_el.get("value") or ""
                        # 1st tuple item is empty: don't include filename part
                        # in the multipart/form-data request
                        form.append((name, ("", value)))
                # use 'files' arg to make the request multipart/form-data
                files_request_dict = dict(request_dict)
                files_request_dict["files"] = form
                # temporarily override method and url
                prev_method, prev_url = self.method, self.url
                self.method = "POST"
                self.url = url
                # _download() in AbstractSite.py expects this to be not None
                self.parameters = {}
                result = super()._download(files_request_dict)
                # restore method and url
                self.method = prev_method
                self.url = prev_url
        return result

    def _extract_cases_from_sub_page(self, html_tree, date_obj):
        anchors = html_tree.xpath("//a[@class='Head articletitle']")
        if self.is_this_a_blank_page(anchors, date_obj):
            return []
        for anchor in anchors:
            text = self._extract_text_from_anchor(anchor)
            if self.is_this_skippable_date_anchor(text):
                # Sometimes COBAR includes link to worthless Opinion
                # Announcement PDF provided by colo court site. These
                # links usually have text that is a simple date string.
                # Skip them.
                continue
            name = self._extract_name_from_text(text)
            url = self._extract_url_from_anchor(anchor)

            # For whatever insane reason, some pages provide direct links
            # to PDFs, and other link off to subpages that must themselves
            # be scraped to extract the real PDF url.
            if not self.is_url_pdf(url):
                (
                    alt_url,
                    alt_name,
                ) = self.extract_pdf_url_and_name_from_resource(url)
                url = alt_url if alt_url else url
                name = alt_name if alt_name else name

            # In some weird cases, subpages are empty and don't include any
            # link to PDF files. Skip them
            # Examples:
            # 2021 CO 55 No. 21SA125, In re Title, Ballot Title & Submission Clause for 2021-2022 #16
            # https://www.cobar.org/For-Members/Opinions-Rules-Statutes/Colorado-Supreme-Court-Opinions/View/ArticleId/2374/2021-CO-55-No-21SA125-In-re-Title-Ballot-Title-Submission-Clause-for-2021-2022-16
            # 2021 CO 60 No.21SA3, In re People v. Sprinkle
            # https://www.cobar.org/For-Members/Opinions-Rules-Statutes/Colorado-Supreme-Court-Opinions/View/ArticleId/2383/2021-CO-60-No-21SA3-In-re-People-v-Sprinkle
            if not self.is_url_pdf(url):
                logger.info(f"Empty sub-page: {url}")
                continue

            self.cases.append(
                {
                    "url": url,
                    "name": name,
                    "date": date_obj,
                    "status": "Published",
                    "docket": self._extract_docket_from_text(text),
                    "citation": self._extract_citation_from_text(text),
                    "summary": self._extract_summary_relative_to_anchor(
                        anchor
                    ),
                    "nature": self._extract_nature_relative_to_anchor(anchor),
                }
            )

    @classmethod
    def _extract_docket_from_text(cls, text):
        """Extracts docket from opinion link
        Also checks for multiple dockets in the same link file
        One docket:
            - 2021 CO 27 No.19SC986, Dep't of Nat. Res. v. 5 Star Feedlot, Inc.
            - 2020 CO 89 No. 19SC354 Denver Health v. Houchin
            - 2019 CO 30. No. 16SC783. Gow v. People.
            - 2016 COA176. No. 14CA1321. Hawg Tools, LLC v. Newsco International Energy Services, Inc.
        Two dockets:
            - 2021 CO 65 No. 20SC261, Harvey v. Centura, No. 20SC784, Manzanares v. Centura
            - 2021 CO 43, Nos. 20SC365 & 20SC367, Board of Country Commissioners v. Colorado Department of Public Health and Environment
            - 2021 CO 10 No. 20SA262, In re People v. Subjack & No. 20SA283, In re People v. Lynch
            - 2019 CO 80 Nos. 18SC34 and 18SC35, People v. Iannicelli, and People v. Brandt
        """
        text = text.strip()
        try:
            match = re.match(cls.regex, text).group(2)
        except:
            logger.error(f'Unable to parse docket from "{text}"')
            raise InsanityException(f'Unable to parse docket from "{text}"')
        # Optional second docket inside case name
        try:
            match_second = re.match(cls.regex_second, text).group(2)
            match = f"{match} & {match_second}"
        except:
            pass
        dockets_raw = (
            match.replace(" & ", " ")
            .replace(" AND ", " ")
            .replace(" and ", " ")
            .replace(",", " ")
        )
        dockets = dockets_raw.split()
        return ", ".join(dockets)

    @classmethod
    def _extract_name_from_text(cls, text):
        """Extracts case name from opinion link
        Also checks for multiple cases names in the same link file
        One case name:
            - 2021 CO 27 No.19SC986, Dep't of Nat. Res. v. 5 Star Feedlot, Inc.
            - 2020 CO 89 No. 19SC354 Denver Health v. Houchin
            - 2019 CO 30. No. 16SC783. Gow v. People.
            - 2016 COA176. No. 14CA1321. Hawg Tools, LLC v. Newsco International Energy Services, Inc.
        Two case names:
            - 2021 CO 65 No. 20SC261, Harvey v. Centura, No. 20SC784, Manzanares v. Centura
            - 2021 CO 43, Nos. 20SC365 & 20SC367, Board of Country Commissioners v. Colorado Department of Public Health and Environment
            - 2021 CO 10 No. 20SA262, In re People v. Subjack & No. 20SA283, In re People v. Lynch
            - 2019 CO 80 Nos. 18SC34 and 18SC35, People v. Iannicelli, and People v. Brandt
        """
        text = text.strip()
        try:
            match = re.match(cls.regex, text).group(3)
        except:
            logger.error(f'Unable to parse docket from "{text}"')
            raise InsanityException(f'Unable to parse case name from "{text}"')
        # Optional second case name
        try:
            first_name = re.match(cls.regex_second, match).group(1)
            second_name = re.match(cls.regex_second, match).group(3)
            first_name = first_name.strip().rstrip("&")
            second_name = second_name.strip()
            match = f"{first_name} and {second_name}"
        except:
            pass
        return match.strip().rstrip(".")

    @classmethod
    def _extract_citation_from_text(cls, text):
        """Extracts citation from opinion link
        Examples:
            - 2021 CO 43, Nos.
            - 2020 CO 83 No.
            - 2017 CO 101. No.
            - 2016 COA176. No.
        """
        text = text.strip()
        try:
            match = re.match(cls.regex, text).group(1)
        except:
            logger.error(f'Unable to parse citation from "{text}"')
            raise InsanityException(f'Unable to parse citation from "{text}"')
        return match.strip()

    @classmethod
    def _extract_text_from_anchor(cls, anchor):
        text = anchor.xpath("text()")[0]
        return text

    @classmethod
    def _extract_url_from_anchor(cls, anchor):
        return anchor.xpath("@href")[0]

    def extract_pdf_url_and_name_from_resource(self, url):
        """Scrape the resource for a direct link to PDF or a backup case name

        A resource can only have one or the other. If the PDF is embedded,
        the name is not displayed in plain text format. These return values
        are used as backups in case the original source data is non-ideal.
        """
        html_tree = self._get_html_tree_by_url(url, self.request_dict)
        path1 = "//h2/a[contains(@href, '.pdf')]/@href"
        path2 = (
            "//div[@class='contentmain1']//a[contains(@href, '.pdf')]/@href"
        )
        href = html_tree.xpath(f"{path1} | {path2}")
        if href:
            return href[0], False
        path1 = '//p/strong[starts-with(text(), "Plaintiff-Appellee:")]/parent::p/text()'
        path2 = (
            '//p/strong[starts-with(text(), "Petitioner:")]/parent::p/text()'
        )
        parts = html_tree.xpath(f"{path1} | {path2}")
        if parts:
            name = " ".join(part.strip() for part in parts if part.strip())
            return False, name
        return False, False

    def _extract_summary_relative_to_anchor(self, anchor):
        parts = anchor.xpath(f"{self.parent_summary_block_path}/p")
        return " ".join([part.text_content().strip() for part in parts])

    def _extract_nature_relative_to_anchor(self, anchor):
        """Extract italicized nature summary that appears directly after download url

        The court uses a lot of different html method of presenting this information.
        If a "nature" field is showing blank in the results, it could be that they are
        using a new html path, which should be added to the path_patterns list below.
        """
        nature = ""
        # The order of this list matters.  Generally, put
        # the more complex paths as the top
        path_patterns = [
            "%s/p/strong/em/span/text()",
            "%s/p/em/text()",
            "%s/p/em/span/text()",
            "%s/p/i/span/text()",
            "%s/p/i/text()",
            "%s/em/text()",
            "%s/em/span/text()",
            "%s/p/span/i/text()",
            "%s/span/em/text()",
            "%s/p/strong/em/text()",
            "%s/strong/em/text()",
            "%s/span/text()",
            "%s/p/span/em/text()",
        ]
        for pattern in path_patterns:
            try:
                nature = anchor.xpath(
                    pattern % self.parent_summary_block_path
                )[0]
                break
            except:
                continue
        return nature.strip().rstrip(".")

    @staticmethod
    def cleanup_content(content):
        tree = html.fromstring(content)
        core_element = tree.xpath('//div[@class="contentmain"]')
        if core_element:
            # its an HTML opinion, return only the core element
            return html.tostring(
                core_element[0], pretty_print=True, encoding="unicode"
            )
        else:
            # its raw pdf file content, which doesn't need to be manipulated
            return content

    def is_this_a_blank_page(self, anchors, date_obj):
        """Man, colo/COBAR are not mkaing things easy for us.
        This is an unfortunate workaround for a recurring problem
        where the court publishes blank pages, which they don't
        populate with data until days/weeks later. Return True
        if there are no anchors, or there is only one anchor
        whose text is just the date string, a thing they do
        often for whatever reason.
        """
        anchor_count = len(anchors)
        if not anchor_count:
            return True
        if anchor_count == 1:
            text = self._extract_text_from_anchor(anchors[0])
            return self.is_this_skippable_date_anchor(text)

    def is_this_skippable_date_anchor(self, text):
        """Return true if link text is parsible date
        Also checks if text includes alternate names for links to
        COBAR Opinion Announcements
        Ex: Colorado Supreme Court Announcements 9.27.2021
        """
        try:
            convert_date_string(text)
            return True
        except:
            pass
        # Alternate names for links to COBAR Opinion Announcements
        announcements = [
            "colorado supreme court announcements",
            "supreme court announcements",
            "court announcements",
        ]
        for announ_link in announcements:
            if announ_link in text.lower():
                return True
        return False

    def is_url_pdf(self, url):
        parsed = urlparse(url)
        return parsed.path.lower().endswith(".pdf")

    def _get_case_names(self):
        return [case["name"] for case in self.cases]

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _get_case_dates(self):
        return [case["date"] for case in self.cases]

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases]

    def _get_citations(self):
        return [case["citation"] for case in self.cases]

    def _get_precedential_statuses(self):
        return [case["status"] for case in self.cases]

    def _get_summaries(self):
        return [case["summary"] for case in self.cases]

    def _get_nature_of_suit(self):
        return [case["nature"] for case in self.cases]
