# Scraper for Florida Supreme Court
# CourtID: fla
# Court Short Name: fla

from datetime import datetime

from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import convert_date_string


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        today = datetime.today().strftime("%m/%d/%Y")
        this_year = datetime.today().year
        last_year = this_year - 1
        today_last_year = today.replace(str(this_year), str(last_year))
        # Get 50 most recent opinions from past year--even though you can
        # put whatever number you want as limit, 50 seems to be max
        self.url = (
            "https://www.floridasupremecourt.org/search/?searchtype=opinions&limit=50&startdate=%s&enddate=%s"
            % (today_last_year, today)
        )
        self.path_cell = '//div[@class="search-results"]//tr/td[%d]'
        self.cases = []

    def _download(self, request_dict={}):
        html = super(Site, self)._download(request_dict)
        self._extract_cases_from_html(html)
        return html

    def _extract_cases_from_html(self, html):
        path = '//div[@class="search-results"]//tbody/tr'
        for row in html.xpath(path):
            cells = row.xpath("./td")
            url = cells[4].xpath("./a/@href")
            if not url:
                # Skip rows without PDFs
                continue
            self.cases.append(
                {
                    "url": url[0],
                    "name": cells[2].text_content(),
                    "docket": cells[1].text_content(),
                    "date": convert_date_string(cells[0].text_content()),
                }
            )

    def _get_case_names(self):
        return [case["name"] for case in self.cases]

    def _get_download_urls(self):
        return [case["url"] for case in self.cases]

    def _get_case_dates(self):
        return [case["date"] for case in self.cases]

    def _get_docket_numbers(self):
        return [case["docket"] for case in self.cases]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.cases)
