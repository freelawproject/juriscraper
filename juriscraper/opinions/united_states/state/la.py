# Scraper for Louisiana Supreme Court
# CourtID: la
# Court Short Name: LA
# Contact: Community relations department
#          Robert Gunn
#          504-310-2592
#          rgunn@lasc.org
import datetime
from datetime import date

from lxml import html

from casemine.casemine_util import CasemineUtil
from juriscraper.lib.html_utils import get_html_parsed_text
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = date.today().year
        self.url = "https://www.lasc.org/CourtActions/2025"#"http://www.lasc.org/CourtActions/%d" % self.year
        self.status = "Published"

    def _download(self, request_dict={}):
        landing_page = OpinionSiteLinear._download(self, request_dict)
        if self.test_mode_enabled():
            return [self._get_subpage_html_by_page(landing_page)]
        path = (
            "//tr["
            "contains(./td[3], 'Opinion') or "
            "contains(./td[3], 'Actions') or "
            "contains(./td[3], 'Rehearings') or "
            "contains(./td[3], 'PER CURIAM')"
            "]//td[2]//@href"
        )
        # parse 2 most recent Opinon/PerCuriam sub-pages
        urls = landing_page.xpath(path)
        return [self._get_subpage_html_by_url(url) for url in urls]

    def _process_html(self):
        for h in self.html:
            date=""
            for row in h.xpath(".//div[@class='nrbody']//p"):
                text = row.text_content().strip()
                date_span = row.xpath(".//span")
                # if date_span and "day of" in date_span[
                #     0].text_content().strip():
                date_span = row.xpath(".//span[@class='nrdate']")
                if date_span:
                    current_date = date_span[0].text_content().strip()
                    parts = current_date.split("day of")
                    day = parts[0].split()[-1]
                    month = parts[1].split()[0]
                    year = parts[1].split()[1].strip(",")
                    date = " ".join([month, day, year])
                    continue


                for anchor in row.xpath(".//a["
                    "contains(., 'v.') or "
                    "contains(., 'IN RE') or "
                    "contains(., 'IN THE') or "
                    "contains(., 'vs.') or "
                    "contains(., 'VS.')"
                    "]"):
                    text = anchor.text_content()
                    parts = text.split(None, 1)
                    summary_lines = anchor.getparent().xpath("./text()")
                    judges=[]
                    if self._get_judge_above_anchor(anchor) :
                        judges.append(self._get_judge_above_anchor(anchor))

                    url = f"http://www.lasc.org{anchor.get('href')}"

                    self.cases.append(
                        {
                            "docket": [parts[0]],
                            "judge": judges,
                            "name": titlecase(parts[1]),
                            "date": date,
                            "summary": " ".join(summary_lines).replace(text, ""),
                            "url": url
                        }
                    )

    def _get_date_for_opinions(self, h):
        element_date = h.xpath("//span")[0]
        element_date_text = element_date.text_content().strip()
        parts = element_date_text.split("day of")
        day = parts[0].split()[-1]
        month = parts[1].split()[0]
        year = parts[1].split()[1].strip(",")
        return " ".join([month, day, year])

    def _get_judge_above_anchor(self, anchor):
        path = (
            "./preceding::*["
            "starts-with(., 'BY ') or "
            "contains(., 'CURIAM:')"
            "]"
        )
        try:
            text = anchor.xpath(path)[-1].text_content()
        except IndexError:
            return None

        if "PER CURIAM" in text : return None
        return text.rstrip(":").lstrip("BY").strip()

    def _get_subpage_html_by_url(self, url):
        page = self._get_html_tree_by_url(url)
        return self._get_subpage_html_by_page(page)

    def _get_subpage_html_by_page(self, page):
        path = ".//textarea[@id='PostContent']"
        html = page.xpath(path)[0].text_content()
        return get_html_parsed_text(html)

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        if not self.downloader_executed:
            self.html = self._download()
            self._process_html()

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            self.case_name_shorts = self._get_case_name_shorts()
        self._post_parse()
        self._check_sanity()
        self._date_sort()
        self._make_hash()
        return 0

    def get_class_name(self):
        return 'la'

    def get_court_name(self):
        return 'Supreme Court of Louisiana'

    def get_court_type(self):
        return 'state'

    def get_state_name(self):
        return 'Louisiana'
