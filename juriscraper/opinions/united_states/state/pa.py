# -*- coding: utf-8 -*-

# Scraper for Pennsylvania Supreme Court
# CourtID: pa
# Court Short Name: pa

import re

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string
from juriscraper.lib.string_utils import clean_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.regex = False
        self.url = "http://www.pacourts.us/assets/rss/SupremeOpinionsRss.ashx"
        self.set_regex(r"(.*)(?:[,-]?\s+Nos?\.)(.*)")
        self.base = (
            "//item[not(contains(title/text(), 'Judgment List'))]"
            "[not(contains(title/text(), 'Reargument Table'))]"
            "[contains(title/text(), 'No.')]"
        )
        self.cases = []

    def _download(self, request_dict={}):
        html = super(Site, self)._download(request_dict)
        self._extract_case_data_from_html(html)
        return html

    def _extract_case_data_from_html(self, html):
        for item in html.xpath(self.base):
            creator = item.xpath("./creator")[0].text_content()
            pubdate = item.xpath("./pubdate")[0].text_content()
            pubdate_sanitized = self.sanitize_text(pubdate)
            title = item.xpath("./title")[0].text_content()
            title_sanitized = self.sanitize_text(title)
            title_clean = clean_string(title_sanitized)
            search = self.regex.search(title_clean)
            url = item.xpath(".//@href")[0]

            if search:
                name = search.group(1)
                docket = search.group(2)
            else:
                name = title_clean
                docket = self._extract_docket_from_url(url)

            self.cases.append(
                {
                    "name": name,
                    "date": convert_date_string(pubdate_sanitized),
                    "docket": docket,
                    "judge": self.sanitize_text(creator),
                    "url": url,
                }
            )

    def _extract_docket_from_url(self, url):
        """Sometimes the court doesnt include the docket number in the title,
        in which case we need to derive it based on the opinion url (it is
        included in the PDF file name)
        """
        parts = url.split("/")[-1].split("CD")
        number = parts[0]
        year_suffix_text = parts[1].split("_")[0]
        year_suffix = re.sub(
            "[^0-9]", "", year_suffix_text
        )  # Strip non-numeric characters
        return "%s C.D. 20%s" % (number, year_suffix)

    def _get_case_names(self):
        return [case["name"] for case in self.cases]

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _get_case_dates(self):
        return [case["date"] for case in self.cases]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.cases)

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases]

    def _get_judges(self):
        return [case["judge"] for case in self.cases]

    def sanitize_text(self, text):
        text = clean_string(text)
        return text.replace(r"\n", "\n").replace(u"–", "-")

    def set_regex(self, pattern):
        self.regex = re.compile(pattern)
