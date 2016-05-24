# Backscraper Scraper for California's First District Court of Appeal
# CourtID: calctapp_1st
# Court Short Name: Cal. Ct. App.
# Author: Andrei Chelaru
import urlparse
from datetime import date, timedelta, datetime
from dateutil.rrule import rrule, DAILY
from juriscraper.OpinionSite import OpinionSite


class Site(OpinionSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.interval = 30
        self.url = ''
        self.district = 1
        self.url_mold = 'http://appellatecases.courtinfo.ca.gov/search/searchCalendarResults.cfm?dist={district}&search=oralarg&startdate={start_date}&enddate={end_date}&divisionFilter=0&start=0'
        self.court_id = self.__module__
        self.back_scrape_iterable = [i.date() for i in rrule(
            DAILY,
            interval=self.interval,
            dtstart=date(1999, 2, 1),
            until=date(2016, 1, 1),
        )]
        self.base_url = 'http://appellatecases.courtinfo.ca.gov'
        self.base_path = '//tr[td[5]]'

    def _download(self, request_dict={}):
        """
        returns a list of html trees
        """

        html_tree = super(Site, self)._download(request_dict)
        tree_list = [html_tree, ]
        next_page = html_tree.xpath("(//a[@class='nextprev'][contains(., 'next')])[1]/@href")
        if next_page:
            self.url = urlparse.urljoin(self.base_url, next_page[0])
            tree_list.extend(self._download())
        return tree_list

    def _get_case_names(self):
        case_names = []
        for html_tree in self.html:
            for element in html_tree.xpath(self.base_path):
                case_names.append(''.join(e.strip() for e in element.xpath('./td[4]//text()')))
        return case_names

    def _get_download_urls(self):
        download_urls = []
        for html_tree in self.html:
            for element in html_tree.xpath(self.base_path):
                download_urls.append(''.join(x for x in element.xpath('./td[3]//@href')))
        return download_urls

    def _get_case_dates(self):
        case_dates = []
        for html_tree in self.html:
            for element in html_tree.xpath("{}/td[1]//text()".format(self.base_path)):
                case_dates.append(datetime.strptime(element.strip(), '%m/%d/%Y'))
        return case_dates

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_names)

    def _get_docket_numbers(self):
        docket_numbers = []
        for html_tree in self.html:
            for element in html_tree.xpath(self.base_path):
                docket_numbers.append(''.join(x.strip() for x in element.xpath('./td[3]//text()')))
        return docket_numbers

    def _download_backwards(self, d):
        self.url = self.url_mold.format(
            district=self.district,
            start_date=(d - timedelta(days=self.interval)).strftime("%d-%b-%y"),
            end_date=d.strftime("%d-%b-%y")
        )
        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200
