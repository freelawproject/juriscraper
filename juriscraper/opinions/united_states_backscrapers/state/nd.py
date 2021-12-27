# Author: Michael Lissner
# Date created: 2013-06-06

import re
from datetime import date, datetime

import requests

from juriscraper.DeferringList import DeferringList
from juriscraper.opinions.united_states.state import nd


class Site(nd.Site):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = date.today()
        self.url = "http://www.ndcourts.gov/opinions/month/%s.htm" % (
            today.strftime("%b%Y")
        )

    def _get_download_urls(self):
        """We use a fetcher and a DeferringList object and a HEAD request
        to test whether the wpd exists for a case"""

        def fetcher(html_link):
            if self.test_mode_enabled():
                return html_link  # Can't fetch remote during tests
            case_number = re.search(r"(\d+)", html_link).group(0)
            wpd_link = f"http://www.ndcourts.gov/wp/{case_number}.wpd"
            r = requests.head(
                wpd_link,
                allow_redirects=False,
                headers={"User-Agent": "Juriscraper"},
            )
            if r.status_code == 200:
                return wpd_link
            else:
                return html_link

        if self.crawl_date >= date(1998, 10, 1):
            path = '//a/@href[contains(., "/court/opinions/")]'
            seed = list(self.html.xpath(path))
        else:
            path = "//ul//a[text()]/@href"
            seed = list(self.html.xpath(path))
        return DeferringList(seed=seed, fetcher=fetcher)

    def _get_case_names(self):
        if self.crawl_date >= date(1998, 10, 1):
            path = '//a[contains(@href, "/court/opinions/")]/text()'
            return list(self.html.xpath(path))
        else:
            path = "//ul//a/text()"
            names = self.html.xpath(path)
            case_names = []
            if self.crawl_date < date(1996, 11, 1):
                # A bad time.
                for name in names:
                    name = name.rsplit("-")[0]
                    case_names.append(name)
                return case_names
            else:
                return list(names)

    def _get_case_dates(self):
        # A tricky one. We get the case dates, but each can have different number of cases below it, so we have to
        # count them.
        case_dates = []
        if self.crawl_date >= date(1998, 10, 1):
            test_path = "//body/a"
            if len(self.html.xpath(test_path)) == 0:
                # It's a month with no cases (like Jan, 2009)
                return []
            path = "//body/a|//body/font"
            for e in self.html.xpath(path):
                if e.tag == "font":
                    date_str = e.text
                    dt = datetime.strptime(date_str, "%B %d, %Y").date()
                elif e.tag == "a":
                    try:
                        case_dates.append(dt)
                    except NameError:
                        # When we don't yet have the date
                        continue
        else:
            path = "//h4|//li"
            for e in self.html.xpath(path):
                if e.tag == "h4":
                    # We make dates on h4's because there's one h4 per date.
                    date_str = e.text.strip()
                    dt = datetime.strptime(date_str, "%B %d, %Y").date()
                elif e.tag == "li":
                    try:
                        # We append on li's, because there's one li per case.
                        case_dates.append(dt)
                    except NameError:
                        # When we don't yet have the date
                        continue
        return case_dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        if self.crawl_date >= date(1998, 10, 1):
            path = '//a/@href[contains(., "/court/opinions/")]'
        else:
            path = "//ul//a[text()]/@href"
        docket_numbers = []
        for html_link in self.html.xpath(path):
            try:
                docket_numbers.append(re.search(r"(\d+)", html_link).group(0))
            except AttributeError:
                continue
        return docket_numbers

    def _get_neutral_citations(self):
        if self.crawl_date < date(1997, 2, 1):
            # Old format, but no neutral cites, thus short circuit the function.
            return None
        elif self.crawl_date < date(1998, 10, 1):
            # Old format with: 1997 ND 30 - Civil No. 960157 or 1997 ND 30
            path = "//li/text()"
        elif self.crawl_date >= date(1998, 10, 1):
            # New format with: 1997 ND 30
            path = "//body/text()"
        neutral_cites = []
        for t in self.html.xpath(path):
            try:
                neutral_cites.append(
                    re.search(
                        r"^.{0,5}(\d{4} ND (?:App )?\d{1,4})", t, re.MULTILINE
                    ).group(1)
                )
            except AttributeError:
                continue
        return neutral_cites

    def _post_parse(self):
        # Remove any information that applies to non-appellate cases.
        if self.neutral_citations:
            delete_items = []
            for i in range(0, len(self.neutral_citations)):
                if "App" in self.neutral_citations[i]:
                    delete_items.append(i)

            for i in sorted(delete_items, reverse=True):
                del self.download_urls[i]
                del self.case_names[i]
                del self.case_dates[i]
                del self.precedential_statuses[i]
                del self.docket_numbers[i]
                del self.neutral_citations[i]
        else:
            # When there aren't any neutral cites that means they're all supreme court cases.
            pass

    def _download_backwards(self, d):
        self.crawl_date = d
        self.url = "http://www.ndcourts.gov/opinions/month/%s.htm" % (
            d.strftime("%b%Y")
        )
        self.html = self._download()
