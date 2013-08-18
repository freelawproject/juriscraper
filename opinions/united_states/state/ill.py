# Author: Krist Jin
# Date created:2013-08-16

from datetime import date
from datetime import datetime
from lxml import html
import requests

from juriscraper.GenericSite import GenericSite
from juriscraper.lib.string_utils import titlecase
from juriscraper.DeferringList import DeferringList


class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.url = 'http://www.state.il.us/court/Opinions/recent_supreme.asp'

    def _get_download_urls(self):
        path = '//td[@class="center"]/table[3]//a[contains(@href,".pdf")]/@href'
        return ["http://www.state.il.us/court/Opinions/"+url_string
                for url_string in self.html.xpath(path)]

    def _get_case_names(self):
        case_names = []
        for e in self.html.xpath('//td[@class="center"]/table[3]//a[contains(@href,".pdf")]'):
            s = html.tostring(e, method='text', encoding='unicode')
            case_names.append(titlecase(s))
        return case_names

    def _get_case_dates(self):
        path = '//td[@class="center"]/table[3]/tr/td[1]//div/text()'
        return [datetime.strptime(date_string, '%m/%d/%y').date()
                for date_string in self.html.xpath(path)]

    def _get_precedential_statuses(self):
        statuses = []
        for e in self.html.xpath('//td[@class="center"]/table[3]/tr/td[3]//div/strong[text()]'):
            s = html.tostring(e, method='text', encoding='unicode')
            if 'NRel' in s:
                statuses.append('Unpublished')
            else:
                statuses.append('Published')
        return statuses

    def _get_docket_numbers(self):
        docket_numbers=[]
        for e in self.html.xpath('//td[@class="center"]/table[3]/tr/td[3]/div/text()[not(preceding-sibling::br)]'):
            e = e.replace(" ","")
            e = e.replace("\n","")
            if(len(e) > 0):
                docket_numbers.append(e)
        return docket_numbers

    def _get_neutral_citations(self):
        neutral_citations = []
        for e in self.html.xpath('//td[@class="center"]/table[3]/tr/td[4]/div'):
            s = html.tostring(e, method='text', encoding='unicode')
            neutral_citations.append(s)
        return neutral_citations

    def _get_summaries(self):
        def fetcher(url):
            r = requests.get(url,
                             allow_redirects=False,
                             headers={'User-Agent': 'Juriscraper'})
            # Throw an error if a bad status code is returned.
            r.raise_for_status()

            html_tree = html.fromstring(r.text)
            html_tree.make_links_absolute(self.url)

            path = '//p[contains(@style, "justify")]/span[@style="font-weight: bold" ]/../following-sibling::p[not(contains(@style, "justify"))][position()=2]/following-sibling::p'
            summary_string = ""
            for e in html_tree.xpath(path):
                s = html.tostring(e, method='text', encoding='unicode')
                s = s.replace("\n","")
                summary_string = summary_string+s+"\n"
            return summary_string

        path = "//td[@class='center']/table[3]/tr/td[6]/div/a/@href"
        seed_urls = self.html.xpath(path)
        for url in seed_urls:
            url = "http://www.state.il.us/court/Opinions/"+url
        if seed_urls:
            summaries = DeferringList(seed=seed_urls, fetcher=fetcher)
            return summaries
        else:
            return []
