# Scraper for Louisiana Supreme Court
# CourtID: la
# Court Short Name: LA
# Contact: Community relations department
#          Robert Gunn
#          504-310-2592
#          rgunn@lasc.org

from datetime import date

from juriscraper.lib.html_utils import get_html_parsed_text
from juriscraper.lib.string_utils import titlecase
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.year = date.today().year
        self.url = "http://www.lasc.org/CourtActions/%d" % self.year
        self.status = "Published"

    def _download(self, request_dict={}):
        landing_page = OpinionSiteLinear._download(self, request_dict)
        if self.test_mode_enabled():
            return [self._get_subpage_html_by_page(landing_page)]
        path = (
            "//tr["
            "contains(./td[3], 'Opinion') or "
            "contains(./td[3], 'PER CURIAM')"
            "]//td[2]//@href"
        )
        # parse 2 most recent Opinon/PerCuriam sub-pages
        urls = landing_page.xpath(path)[:2]
        return [self._get_subpage_html_by_url(url) for url in urls]

    def _process_html(self):
        path = (
            "//a["
            "contains(., 'v.') or "
            "contains(., 'IN RE') or "
            "contains(., 'IN THE') or "
            "contains(., 'vs.') or "
            "contains(., 'VS.')"
            "]"
        )
        for html in self.html:
            for anchor in html.xpath(path):
                date_string = self._get_date_for_opinions(html)
                text = anchor.text_content()
                parts = text.split(None, 1)
                summary_lines = anchor.getparent().xpath("./text()")
                self.cases.append(
                    {
                        "date": date_string,
                        "docket": parts[0],
                        "judge": self._get_judge_above_anchor(anchor),
                        "name": titlecase(parts[1]),
                        "summary": " ".join(summary_lines).replace(text, ""),
                        "url": anchor.get("href"),
                    }
                )

    def _get_date_for_opinions(self, html):
        element_date = html.xpath("//span")[0]
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
        return text.rstrip(":").lstrip("BY").strip()

    def _get_subpage_html_by_url(self, url):
        page = self._get_html_tree_by_url(url)
        return self._get_subpage_html_by_page(page)

    def _get_subpage_html_by_page(self, page):
        path = ".//textarea[@id='PostContent']"
        html = page.xpath(path)[0].text_content()
        return get_html_parsed_text(html)
