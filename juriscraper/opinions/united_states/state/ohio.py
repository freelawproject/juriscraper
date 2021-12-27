"""Scraper for the Supreme Court of Ohio
CourtID: ohio
Court Short Name: Ohio
Author: Andrei Chelaru
Reviewer: mlr
History:
 - Stubbed out by Brian Carver
 - 2014-07-30: Finished by Andrei Chelaru
 - 2015-07-31: Redone by mlr to use ghost driver. Alas, their site used to be
               great, but now it's terribly frustrating.
"""
from datetime import date, datetime

from lxml import html
from lxml.html import tostring

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import fix_links_in_lxml_tree
from juriscraper.lib.string_utils import clean_if_py3
from juriscraper.OpinionSiteWebDriven import OpinionSiteWebDriven


class Site(OpinionSiteWebDriven):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Changing the page # in the url will get additional pages
        # Changing the source # (0-13) will get the 12 Courts of Appeals and
        # the Court of Claims. We do not use the "all sources" link because a
        # single day might yield more than 25 opinions and this scraper is
        # not designed to walk through multiple pages.
        self.court_index = 0
        self.year = str(date.today().year)
        self.url = "http://www.supremecourtofohio.gov/rod/docs/"
        self.court_id = self.__module__
        self.base_path = "id('MainContent_gvResults')//tr[position() > 1]/td[2][string-length(normalize-space(text())) > 1]"
        self.uses_selenium = True

    def _download(self, request_dict={}):
        """This is another of the cursed MS asp.net pages with damned POST
        parameters like __EVENTVALIDATION. These are near impossible to
        scrape without using Selenium.
        """
        if self.test_mode_enabled():
            return super()._download(request_dict=request_dict)

        logger.info(f"Now downloading case page at: {self.url}")
        self.initiate_webdriven_session()

        # Court drop down...
        self.find_element_by_xpath(
            "//select[@id='MainContent_ddlCourt']"
            "/option[@value='{court}']".format(court=self.court_index)
        ).click()

        # Year drop down...
        yearDropDownId = "MainContent_ddlDecidedYear"
        yearDropDownPath = (
            "//select[@id='{id}']/option[@value='%s']" % self.year
        )
        yearDropdownPaths = [
            yearDropDownPath.format(id=yearDropDownId),  # Legacy examples
            yearDropDownPath.format(
                id=f"{yearDropDownId}Min"
            ),  # current (2017)
        ]
        self.find_element_by_xpath(" | ".join(yearDropdownPaths)).click()

        # Hit submit
        submitPath = "//input[@id='MainContent_btnSubmit']"
        self.find_element_by_xpath(submitPath).click()

        # Selenium doesn't give us the actual code, we have to hope.
        self.status = 200

        text = self._clean_text(self.webdriver.page_source)
        html_tree = html.fromstring(text)
        html_tree.rewrite_links(
            fix_links_in_lxml_tree, base_href=self.request["url"]
        )
        return html_tree

    def _get_case_names(self):
        path = f"{self.base_path}/preceding::td[1]"
        case_names = []
        for e in self.html.xpath(path):
            case_names.append(
                tostring(e, method="text", encoding="unicode").strip()
            )
        return case_names

    def _get_download_urls(self):
        path = f"{self.base_path}/preceding::td[1]//a[1]/@href"
        return list(self.html.xpath(path))

    def _get_docket_numbers(self):
        path = f"{self.base_path}//text()"
        return list(self.html.xpath(path))

    def _get_summaries(self):
        path = f"{self.base_path}/following::td[1]//text()"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = f"{self.base_path}/following::td[4]//text()"
        dates = []
        for s in self.html.xpath(path):
            dates.append(
                datetime.strptime(clean_if_py3(s).strip(), "%m/%d/%Y").date()
            )
        return dates

    def _get_neutral_citations(self):
        path = f"{self.base_path}/following::td[6]//text()"
        return [s.replace("-", " ") for s in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_judges(self):
        path = f"{self.base_path}/following::td[2]"
        return list(map(self._return_judge, self.html.xpath(path)))

    @staticmethod
    def _return_judge(e):
        txt = e.xpath(".//text()")
        return txt[0] if txt else ""
