# Scraper for Louisiana Supreme Court
#CourtID: la
#Court Short Name: LA
#Author: Andrei Chelaru
#Reviewer:
#Date: 2014-07-16

from lxml import html, etree
import requests
from requests.exceptions import HTTPError
from tests import MockRequest

from juriscraper.OpinionSite import OpinionSite
import re
import time
from datetime import date


class Site(OpinionSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.nr_of_documents = []
        self.url = 'http://search.lasc.org/isysquery/04779a78-7808-4cad-8c59-1fe2898d9d65/1-5766/list/'
        # self.url = 'http://search.lasc.org/search/'
        # self.parameters = {
        #     'IW_FIELD_TERM': '',
        #     'IW_FIELD_TEXT': '.pdf and Louisiana',
        #     'IW_FILTER_FNAME_LIKE': '',
        #     'IW_FILTER_DATE_AFTER': '',
        #     'IW_SEARCH_SCOPE': '',
        #     'IW_DATABASE': 'Opinions and News Releases',
        # }
        # self.method = 'POST'

    # def tweak_request_object(self, r):
    #     r.raise_for_status()
    #
    #     # If the encoding is iso-8859-1, switch it to cp1252 (a superset)
    #     if r.encoding == 'ISO-8859-1':
    #         r.encoding = 'cp1252'
    #     # Grab the content
    #     text = self._clean_text(r.text)
    #     html_tree = html.fromstring(text)
    #     html_tree.make_links_absolute(self.url)
    #
    #     remove_anchors = lambda url: url.split('#')[0]
    #     html_tree.rewrite_links(remove_anchors)
    #
    #     results = html_tree.xpath("//td[@align='right'][contains(., 'Results')]/text()")
    #     if results:
    #         results_match = re.search('Results.*of (.*)', results[0])
    #         if not results_match:
    #             return r
    #         else:
    #             nr_results = results_match.group(1)
    #             nr_results = re.sub(',', '', nr_results)
    #             print(nr_results)
    #             if int(nr_results) <= 10:
    #                 return r
    #             else:
    #                 # create and return a new request with a modified URL
    #                 new_url = html_tree.xpath("//a[@class='isys'][1]/@href")[0]
    #                 new_mod_url = re.sub('11-\d{2}', '1-{n}'.format(n=nr_results), new_url)
    #                 print(new_mod_url)
    #                 self.url = new_mod_url
    #                 new_s = requests.session()
    #                 new_r = new_s.get(new_mod_url, headers={'User-Agent': 'Juriscraper'})
    #                 return new_r
    #     else:
    #         return r

    def _get_case_names(self):
        return map(self._return_case_name, self.nr_of_documents)

    def _return_case_name(self, element):
        text = element.xpath('./ancestor::tr[1]/td[2]//text()')
        text = ' '.join(text)
        match_case_name = re.search('(\d{2,4}-?.{2}-?\d{4}(?!.*\d{2,4}-?.{2}-\d{4})) +([A-Z v\.,:]+)', text)
        if match_case_name:
            return match_case_name.group(2)
        else:
            # the docket link should be opened and searched for the case name
            return ''

    def _get_download_urls(self):
        return map(self._return_download_url, enumerate(self.nr_of_documents))

    def _return_download_url(self, l):
        text = l[1].xpath('./ancestor::tr[1]/following::tr[1]/td[2]/span/text()[1]')[0]
        text = ' '.join(text.split())
        url_end = re.search("(.*\.pdf)", text, re.IGNORECASE).group(0)
        url = 'http://www.lasc.org/opinions/{year}/{end}'.format(year = self.case_dates[l[0]].year, end=url_end)
        return url

    def _get_case_dates(self):
        self.nr_of_documents = self.html.xpath('//*[contains(concat(" ", normalize-space(@name), " "), " SearchForm ")]//img')
        path = '//*[contains(concat(" ", normalize-space(@name), " "), " SearchForm ")]//img/ancestor::tr[1]/td[5]/text()'
        return map(self._return_case_date, self.html.xpath(path))

    @staticmethod
    def _return_case_date(element):
        case_date = date.fromtimestamp(time.mktime(time.strptime(element, '%m/%d/%Y')))
        return case_date

    def _get_precedential_statuses(self):
        return ['Published'] * len(self.case_dates)

    def _get_docket_numbers(self):
        return map(self._return_docket_number, self.nr_of_documents)

    def _return_docket_number(self, element):
        pos = element.xpath('./ancestor::tr[1]/td[2]/a/text()')[0]
        case_nr = re.search('(\d{2,4}-? ?[a-zA-Z].*-?\d{4})[ \w]', pos)
        if case_nr:
            return case_nr.group(1)
        else:
            # the docket link should be opened and searched for the docket number
            return ''
    
    def _get_judges(self):
        return map(self._return_judge, self.nr_of_documents)

    def _return_judge(self, element):
        judge = element.xpath('./ancestor::tr[1]/td[3]//text()')
        if judge:
            return judge[0]
        else:
            # the docket link should be opened and searched for the judge
            return ''