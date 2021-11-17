# Author: Michael Lissner
# History:
# - 2013-06-11: Birth.
# - 2013-08-06: Revised by Brian Carver
# - 2014-08-05: Updated URL by mlr

import re

from lxml import html

from juriscraper.AbstractSite import logger
from juriscraper.lib.html_utils import fix_links_in_lxml_tree
from juriscraper.lib.string_utils import convert_date_string, titlecase
from juriscraper.OpinionSiteWebDriven import OpinionSiteWebDriven


class Site(OpinionSiteWebDriven):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://ujs.sd.gov/Supreme_Court/opinions.aspx"
        self.back_scrape_iterable = [
            (0, 2014),
            (1, 2014),
            (2, 2014),
            (3, 2014),
            (0, 2013),
            (1, 2013),
            (2, 2013),
            (3, 2013),
            (4, 2013),
            (5, 2013),
            (6, 2013),
        ]
        self.uses_selenium = True
        regex_year_group = r"(\d{4} S\.?D\.? \d{1,4})"
        self.regex = f"(.*){regex_year_group}"
        # The court decided to publish 5 records on January 24th 2018
        # in an alternate format where the neutral citation appears
        # before the case name, instead of vice versa.  We contacted the
        # court multiple times, but they wouldn't respond, so we had to
        # add the additional regex below to handle this use case.
        self.regex_alt = f"{regex_year_group}, (.*)"
        self.base_path = "//table[@id='ContentPlaceHolder1_PageContent_gvOpinions']//tr[position()>1]/td"

    def _get_download_urls(self):
        path = f"{self.base_path}//a/@href[contains(.,'pdf')]"
        return list(self.html.xpath(path))

    def _get_case_names(self):
        path = f"{self.base_path}/a[contains(@href, 'pdf')]/text()"
        case_names = []
        for s in self.html.xpath(path):
            case_name = self.extract_regex_group(1, s)
            if not case_name:
                case_name = self.extract_regex_group(2, s, True)
            case_names.append(titlecase(case_name.upper()))
        return case_names

    def _get_case_dates(self):
        path = f"{self.base_path}[1]/text()"
        return [convert_date_string(ds) for ds in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_neutral_citations(self):
        path = f"{self.base_path}/a[contains(@href, 'pdf')]/text()"
        neutral_cites = []
        for s in self.html.xpath(path):
            neutral_cite = self.extract_regex_group(2, s)
            if not neutral_cite:
                neutral_cite = self.extract_regex_group(1, s, True)
            # Make the citation SD instead of S.D. The former is a neutral cite, the latter, the South Dakota Reporter
            neutral_cites.append(neutral_cite.replace(".", "").upper())
        return neutral_cites

    def _download_backwards(self, page_year):
        logger.info(f"Running with params: {page_year}")
        self.initiate_webdriven_session()

        # Select the year (this won't trigger a GET unless it's changed)
        path = "//*[@id='ContentPlaceHolder1_PageContent_OpinionYears']/option[@value={year}]".format(
            year=page_year[1]
        )
        option = self.find_element_by_xpath(path)
        option.click()

        if page_year[0] != 0:
            # Not the first, page, go to the one desired.
            links = self.find_elements_by_xpath(
                "//a[@href[contains(., 'Page')]]"
            )
            links[page_year[0] - 1].click()

        text = self._clean_text(self.webdriver.page_source)
        self.webdriver.quit()
        html_tree = html.fromstring(text)

        html_tree.rewrite_links(
            fix_links_in_lxml_tree, base_href=self.request["url"]
        )
        self.html = html_tree
        self.status = 200

    def extract_regex_group(self, group, string, alt=False):
        regex = self.regex_alt if alt else self.regex
        return re.search(regex, string, re.MULTILINE).group(group)
