import datetime
from urllib.parse import urljoin

from dateutil.rrule import DAILY, rrule

from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.court_name = (
            "United States District Court Eastern District of Louisiana"
        )
        today = datetime.date.today().strftime("%Y-%m-%d")

        self.base_url = "http://www.gpo.gov"
        self.query = 'collection:USCOURTS and courttype:District and courtname:"{court}" and publishdate:{date} and accode:USCOURTS'
        self.url_template = "http://www.gpo.gov/fdsys/search/uscourtsFwdSearch.action?forwadedQuery={}"
        self.url = self.url_template.format(
            # self.query.format(court=self.court_name, date="2015-10-26")
            self.query.format(court=self.court_name, date=today)
        )
        self.interval = 30
        self.back_scrape_iterable = [
            i.date()
            for i in rrule(
                DAILY,
                interval=self.interval,
                dtstart=datetime.date(2003, 2, 1),
                until=datetime.date(datetime.date.today().year + 1, 1, 1),
            )
        ]

        self.base_path = "//table[@class='search-results-item']"

    def _download(self, request_dict={}):
        """
        returns a list of html trees
        """

        html_tree = super()._download(request_dict)
        tree_list = [
            html_tree,
        ]
        next_page = html_tree.xpath(
            "//div[@class='search-results-pagination']//a[contains(., 'Next')]/@href"
        )
        if next_page:
            self.url = urljoin(self.base_url, next_page[0])
            tree_list.extend(self._download())
        return tree_list

    def _get_case_names(self):
        case_names = []
        for html_tree in self.html:
            for element in html_tree.xpath(self.base_path):
                case_name = "".join(
                    e.strip()
                    for e in element.xpath(
                        ".//a/span[@class='results-line1-title']//text()"
                    )
                )
                case_names.append(case_name.split(" - ")[-1])
        # print >>sys.stderr, case_names
        return case_names

    def _get_download_urls(self):
        download_urls = []
        for html_tree in self.html:
            for element in html_tree.xpath(self.base_path):
                download_urls.append(
                    "".join(
                        x
                        for x in element.xpath(
                            ".//a[span[@class='results-line1-pdf']]/@href"
                        )
                    )
                )
        return download_urls

    def _get_case_dates(self):
        case_dates = []
        for html_tree in self.html:
            for element in html_tree.xpath(self.base_path):
                case_date = "".join(
                    element.xpath(".//span[@class='results-line2']/text()")
                )
                case_date = case_date.split(",")
                case_date = f"{case_date[-2]}{case_date[-1]}".strip()
                # January 26, 2015.
                case_dates.append(
                    datetime.datetime.strptime(case_date.strip(), "%B %d %Y.")
                )
        return case_dates

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_numbers = []
        for html_tree in self.html:
            for element in html_tree.xpath(self.base_path):
                docket_number = "".join(
                    e.strip()
                    for e in element.xpath(
                        ".//a/span[@class='results-line1-title']//text()"
                    )
                )
                docket_numbers.append(docket_number.split(" - ")[0])
        return docket_numbers

    def _download_backwards(self, d):
        # range(2015-01-01,2015-02-01)
        date_range = "range({start_date},{end_date})".format(
            start_date=(d - datetime.timedelta(days=self.interval)).strftime(
                "%Y-%m-%d"
            ),
            end_date=d.strftime("%Y-%m-%d"),
        )
        self.url = self.url_template.format(
            self.query.format(court=self.court_name, date=date_range)
        )
        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
