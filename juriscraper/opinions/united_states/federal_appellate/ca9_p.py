"""
History:
    - 2014-08-05: Updated by mlr because it was not working, however, in middle
      of update, site appeared to change. At first there were about five
      columns in the table and scraper was failing. Soon, there were seven and
      the scraper started working without my fixing it. Very odd.
"""

from datetime import date

from dateutil.rrule import DAILY, rrule

from juriscraper.lib.string_utils import convert_date_string, titlecase
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "http://www.ca9.uscourts.gov/opinions/"
        self.position = "[position() > 1]"
        self.base = self.get_base_path()
        self.back_scrape_date_start = date(2005, 1, 3)
        self.back_scrape_date_end = date(2015, 1, 1)
        self.back_scrape_iterable = self.get_backscrape_iterable()
        self.back_scrape_url = self.url

    def get_backscrape_iterable(self):
        date_rules = rrule(
            DAILY,
            dtstart=self.back_scrape_date_start,
            until=self.back_scrape_date_end,
        )
        return [rule.date() for rule in date_rules]

    def get_back_scrape_parameters(self, d):
        return {
            "c_page_size": "50",
            "c__ff_cms_opinions_case_name_operator": "like",
            "c__ff_cms_opinions_case_num_operator": "like",
            "c__ff_cms_opinions_case_origin_operator": "like",
            "c__ff_cms_opinions_case_origin": "like",
            "c__ff_j1_name_operator": "like%25",
            "c__ff_j2_name_operator": "like%25",
            "c__ff_cms_opinions_case_type_operator": "%3D",
            "c__ff_cms_opinion_date_published_operator": "like",
            "c__ff_cms_opinion_date_published": d.strftime("%m/%d/%Y"),
            "c__ff_onSUBMIT_FILTER": "Search",
        }

    def get_base_path(self):
        return (
            '//table[@id="search-results-table"]//tr['
            '    not(@id="c_row_") and '
            "    not("
            '        contains(child::td//text(), "NO OPINIONS") or'
            '        contains(child::td//text(), "No Opinions") or'
            '        contains(child::td//text(), "NO MEMO") or'
            '        contains(child::td//text(), "No Memo")'
            "    )"
            "]" + self.position
        )

    def _get_case_names(self):
        path = f"{self.base}/td[1]/a/text()"
        return [titlecase(text) for text in self.html.xpath(path)]

    def _get_download_urls(self):
        path = f"{self.base}/td[1]/a/@href"
        return self.html.xpath(path)

    def _get_case_dates(self):
        path = f"{self.base}/td[7]//text()"
        return [
            convert_date_string(date_string)
            for date_string in self.html.xpath(path)
        ]

    def _get_docket_numbers(self):
        path = f"{self.base}/td[2]"
        return [cell.text_content() for cell in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        if "opinion" in self.url.lower():
            status = "Published"
        elif "memoranda" in self.url.lower():
            status = "Unpublished"
        else:
            status = "Unknown"
        return [status] * len(self.case_names)

    def _get_nature_of_suit(self):
        natures = []
        path = f"{self.base}/td[5]"
        for cell in self.html.xpath(path):
            text = cell.text_content()
            natures.append("" if text.lower().strip() == "n/a" else text)
        return natures

    def _get_lower_court(self):
        path = f"{self.base}/td[3]//text()"
        return self.html.xpath(path)

    def _download_backwards(self, d):
        self.method = "POST"
        self.url = self.back_scrape_url
        self.parameters = self.get_back_scrape_parameters(d)

        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
