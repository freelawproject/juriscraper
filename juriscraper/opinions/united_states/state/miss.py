# Court Contact: bkraft@courts.ms.gov (see https://courts.ms.gov/aoc/aoc.php)

import datetime
from juriscraper.OpinionSiteLinear import OpinionSiteLinear
from juriscraper.lib.string_utils import convert_date_string


# Landing page: https://courts.ms.gov/appellatecourts/sc/scdecisions.php
class Site(OpinionSiteLinear):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.domain = "https://courts.ms.gov"
        self.court_id = self.__module__
        self.method = "POST"
        self.number_of_dates_to_process = 5
        self.pages = {}
        self.parameters = {"crt": self.get_court_parameter()}
        self.status = "Published"
        self.url = "%s/appellatecourts/docket/gethddates.php" % self.domain

    def get_court_parameter(self):
        return "SCT"

    """Retrieve dates for which there are case listings.
    This site's architecture is no bueno. We have to issue
    a POST request to this page to get a array (in the form
    of a string) or dates that have cases associated with
    them.
    """

    def _download(self, request_dict={}):
        dates_page = super(Site, self)._download(request_dict)
        self.parse_date_pages(dates_page)

    """Keep track of the most recent N date pages.
    We dont want to crawl all the way back to 1996, so we only
    parse the most recent [self.number_of_dates_to_process]
    number of date pages.  Since cases are usually published
    once a week, this means scraping about the most recent
    months worth of cases.
    """

    def parse_date_pages(self, dates_page):
        # For testing, each example file should be a specific sub-date page,
        # like https://courts.ms.gov/Images/HDList/SCT02-27-2020.html
        if self.test_mode_enabled():
            # date below is arbitrary and doesnt matter, it just
            # needs to be static for testing to work
            self.pages["2020-02-28"] = dates_page
            return
        for date in self.get_dates_from_date_page(dates_page):
            url = "%s/Images/HDList/SCT%s.html" % (
                self.domain,
                datetime.date.strftime(date, "%m-%d-%Y"),
            )
            page = self._get_html_tree_by_url(url)
            self.pages["%s" % date] = page

    """Convert string of dates on page into list of date objects.
    """

    def get_dates_from_date_page(self, dates_page):
        dates = []
        substrings = dates_page.text_content().split('"')
        for substring in substrings:
            try:
                dates.append(convert_date_string(substring))
            except ValueError:
                pass
        dates.sort(reverse=True)
        return dates[: self.number_of_dates_to_process]

    def _process_html(self):
        for date, page in self.pages.items():
            for anchor in page.xpath(".//a[contains(./@href, '.pdf')]"):
                parent = anchor.getparent()

                # sometimes the first opinion on the pages is nested
                # in a <p> tag for whatever reason.
                while parent.getparent().tag != "body":
                    parent = parent.getparent()

                sections = parent.xpath("./following-sibling::ul")
                if not sections:
                    # the while loop above should mean we never fall in here
                    continue

                section = sections[0]
                self.cases.append(
                    {
                        "date": date,
                        "docket": anchor.text_content().strip(),
                        "name": section.xpath(".//b")[0]
                        .text_content()
                        .strip(),
                        "summary": section.text_content().strip(),
                        "url": anchor.xpath("./@href")[0],
                    }
                )
