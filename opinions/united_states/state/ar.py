from GenericSite import GenericSite
import time
from datetime import date
import requests
import lxml
import lxml.html
import mechanize
import urllib
import urlparse
import math

class Site(GenericSite):
    def __init__(self):
        super(Site, self).__init__()
        self.url = 'http://opinions.aoc.arkansas.gov'
        self.method = 'POST'

        self.accumulated_case_names=[]
        self.accumulated_case_dates = []
        self.accumulated_download_links = []
        self.accumulated_docket_numbers = []
        self.accumulated_precedential_statuses = []

        self.court_id = self.__module__

    def _download_latest(self):
        self.headers = {}

        br = mechanize.Browser()
        br.set_handle_robots(False)
        br.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')]
        response_open = br.open('http://opinions.aoc.arkansas.gov/WebLink8/Search.aspx')
        br.select_form("Form1")
        inputs = []
        
        #set post parameters (add Independent Field) and re-submit
        br['TheSearchForm:_ctl1'] = ['3']
        br.form.find_control("__EVENTTARGET").readonly = False
        br["__EVENTTARGET"] = 'TheSearchForm$_ctl1'
        response_independent_field = br.submit()

        #set post parameters (add Court field) and re-submit
        br.select_form("Form1")
        br.form.find_control("__EVENTTARGET").readonly = False
        br["__EVENTTARGET"] = 'TheSearchForm$_ctl6$_ctl7'
        #remove the reset button from the form controls
        the_s_f1 = br.form.find_control('TheSearchForm:_ctl6:_ctl9')
        br.form.controls.remove(the_s_f1)
        br['TheSearchForm:_ctl6:_ctl7'] = ['21']
        response_court = br.submit()
        
        #set post parameters (add Court of appeals field) and submit/search
        br.select_form("Form1")
        br.form.find_control("__EVENTTARGET").readonly = False
        br["__EVENTTARGET"] = 'RunButton'
        #remove the reset button from the form controls
        the_s_f1 = br.form.find_control('TheSearchForm:_ctl6:_ctl9')
        br.form.controls.remove(the_s_f1)
        br['TheSearchForm:_ctl6:_ctl7'] = ['21']
        br['TheSearchForm:_ctl6:_ctl10:_ctl0'] = ['Court of Appeals']
        response_search = br.submit()
        
        self.status = response_search.code
        content = response_search.read()
        
        text = self._clean_text(content)
        html_tree = lxml.html.fromstring(text)
        html_tree.make_links_absolute(self.url)
        def remove_anchors(href):
            # Some courts have anchors on their links that must be stripped.
            return href.split('#')[0]
        html_tree.rewrite_links(remove_anchors)
        d = self._get_article_count(html_tree)
        print str(d)
        #add court cases information from the first result page
        self._extend_all_properties(html_tree)

        #iterate all the result pages and extend court cases information
        iterator = 1 #start case index
        page_iterator = 21
        stop_iter = int(math.ceil(d/20)) #20 cases per page
        print str(stop_iter)
        while iterator <= stop_iter:
            br.select_form("Form1")
            br.form.find_control("__EVENTTARGET").readonly = False
            br["__EVENTTARGET"] = 'TheSearchResultsBrowser'
            br.form.find_control("__EVENTARGUMENT").readonly = False
            br["__EVENTARGUMENT"] = 'StartIndex:'+str(iterator)
            #remove the reset button from the form controls
            the_s_f1 = br.form.find_control('TheSearchForm:_ctl6:_ctl9')
            br.form.controls.remove(the_s_f1)
            br['TheSearchForm:_ctl6:_ctl7'] = ['21']
            br['TheSearchForm:_ctl6:_ctl10:_ctl0'] = ['Court of Appeals']
            
            response_next_page = br.submit()
            self.headers = response_next_page.info()
            self.status = response_next_page.code
            content = response_next_page.read()
            text = self._clean_text(content)
            html_tree = lxml.html.fromstring(text)
            html_tree.make_links_absolute(self.url)
            html_tree.rewrite_links(remove_anchors)
            #add court cases information from the following result pages
            self._extend_all_properties(html_tree)
            print str(iterator)
            page_iterator = page_iterator + 20
            iterator = iterator + 1

        return html_tree

    def _get_article_count(self, html):
        count_text = html.xpath('//div[@class="SearchResultHeader"]/div/text()[2]')
        count_text = count_text[0].strip()
        count_text = count_text[3:]
        return int(count_text)

    def _extend_all_properties(self, html):
        self.accumulated_case_names.extend(self.get_case_names(html))
        self.accumulated_case_dates.extend(self.get_case_dates(html))
        self.accumulated_download_links.extend(self.get_download_links(html))
        self.accumulated_docket_numbers.extend(self.get_docket_numbers(html))
        self.accumulated_precedential_statuses.extend(self.get_precedential_statuses(html))

    def get_case_names(self, html):
        names = []
        for e in html.xpath('//div[@class="FieldSection"]/em[contains(text(), "Case Name:")]/following-sibling::text()[1]'):
            length = len(e)
            val_strip_dash = e[:length-3]
            val = val_strip_dash.strip()
            names.append(val)
        return names

    def get_download_links(self, html):
        _download_links = []
        for e in html.xpath('//a[@class="DocumentTitle"]/@href'):
            k = list(urlparse.urlparse(e))
            k[2] = '/WebLink8' + k[2]
            real_url = urlparse.urlunparse(tuple(k))
            _download_links.append(real_url)
        return _download_links

    def get_case_dates(self, html):
        dates = []
        for date_string in html.xpath('//div[@class="FieldSection"]/em[contains(text(), "Date:")]/following-sibling::text()[1]'):
            length = len(date_string)
            val_strip_dash = date_string[:length-3]
            val = val_strip_dash.strip()
            if val == '':
                dates.append('')
            else:
                dates.append(date.fromtimestamp(time.mktime(time.strptime(val, '%m/%d/%Y'))))
        return dates

    def get_docket_numbers(self, html):
        return [e for e in html.xpath('//div[@class="FieldSection"]/em[contains(text(), "Docket Number:")]/following-sibling::text()[1]')]

    def get_precedential_statuses(self, html):
        statuses = []
        for link in html.xpath('//div[@class="FieldSection"]/em[contains(text(), "Docket Number:")]/following-sibling::text()[1]'):
            statuses.append("Unknown")
        return statuses


    def _get_case_names(self):
        return self.accumulated_case_names

    def _get_download_links(self):
        return self.accumulated_download_links
    
    def _get_case_dates(self):
        return self.accumulated_case_dates

    def _get_docket_numbers(self):
        return self.accumulated_docket_numbers

    def _get_precedential_statuses(self):
        return self.accumulated_precedential_statuses


