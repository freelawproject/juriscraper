# Author: Phil Ardery
# Date created: 2017-01-27
# Contact: 501-682-9400 (Administrative Office of the Curt)

import time
from juriscraper.AbstractSite import logger
from juriscraper.OpinionSite import OpinionSite
from juriscraper.lib.string_utils import titlecase, convert_date_string

## WARNING: THIS SCRAPER IS FAILING:
## This scraper is succeeding in development, but
## is failing in production.  We are not exactly
## sure why, and suspect that the hosting court
## site may be blocking our production IP and/or
## throttling/manipulating requests from production.


class Site(OpinionSite):
    """This website implements anti-bot mechanisms. There is some threshold
    where, after some X number of rapid requests, the service requires a
    catptcha to continue. I have no idea where the threshold is. I think
    it's pretty generous, and shouldn't be triggered during the course of
    normal operations. However, it may be triggered during extensive testing,
    when running the scraper many times in succession.
    """
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.cases = []
        self.subpage_html = False
        self.url_id = 'supremecourt'
        self.url = self.get_url()

    def get_url(self):
        return 'https://opinions.arcourts.gov/ark/%s/en/rss.do' % self.url_id

    def _download(self, request_dict={}):
        """We have to scrape each item url in the RSS feed, since the
        docket number and other info isn't included in the RSS result
        """
        html = super(Site, self)._download(request_dict)
        self.extract_cases_from_subpages(html)
        return html

    def extract_cases_from_subpages(self, html):
        """In order for testing to work, and to prevent hitting the
        network while running tests, each example file should correspond
        to a specific case page, NOT the main RSS feed page. When creating
        a new example file, you can retrieve the html with:
            curl "<CASE-PAGE-URL>?iframe=true"
        """
        if self.method == 'LOCAL':
            self.subpage_html = html
            self.extract_case_from_subpage()
        else:
            filter_by_citation = 'contains(./title, "Ark.") or contains(./title, "ARK.")'
            path = '//item[%s]/link' % filter_by_citation
            subpage_urls = [href.tail.strip() for href in html.xpath(path)]
            for i, subpage_url in enumerate(subpage_urls):
                time.sleep(2.5)  # Avoid anti-bot mechanism
                subpage_url = subpage_url + '?iframe=true'
                # cat /var/log/juriscraper/debug.log for more info
                logger.info('%s: Scraping sub-page: %s' % (self.court_id, subpage_url))
                self.subpage_html = self._get_html_tree_by_url(subpage_url)
                self.extract_case_from_subpage()

    def extract_case_from_subpage(self):
        self.cases.append({
            'name': self.subpage_html.xpath('//h3[@class="title"]')[0].text_content().strip(),
            'url': self.subpage_html.xpath('//div[@class="documents"]/a/@href')[0],
            'date': self.get_subpage_value_by_key('Date'),
            'judge': self.get_subpage_value_by_key('Author'),
            'docket': self.get_subpage_value_by_key('Docket Number'),
            'citation': self.get_subpage_value_by_key('Neutral Citation'),
        })

    def get_subpage_value_by_key(self, key):
        """Return value in column 2 where column 1 includes $key.
        If no $key in column 1, return empty string (for example,
        not all records have docket numbers).
        """
        path = '//tr[contains(./td[@class="label"], "%s")]/td[@class="metadata"]' % key
        elements = self.subpage_html.xpath(path)
        return elements[0].text_content().strip() if elements else ''

    def _get_download_urls(self):
        return [case['url'] for case in self.cases]

    def _get_case_names(self):
        return [case['name'] for case in self.cases]

    def _get_case_dates(self):
        return [convert_date_string(case['date']) for case in self.cases]

    def _get_precedential_statuses(self):
        return ["Published"] * len(self.case_names)

    def _get_docket_numbers(self):
        return [case['docket'] for case in self.cases]

    def _get_judges(self):
        return [case['judge'].lower().title() for case in self.cases]

    def _get_neutral_citations(self):
        return [case['citation'] for case in self.cases]

    def _get_dispositions(self):
        return [titlecase(case['docket']) for case in self.cases]