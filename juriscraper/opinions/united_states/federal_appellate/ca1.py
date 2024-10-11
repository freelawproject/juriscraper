import json
from datetime import date, datetime
from typing import Tuple
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from lxml import etree

from casemine.CaseMineCrawl import CaseMineCrawl
from casemine.casemine_util import CasemineUtil
from juriscraper.AbstractSite import logger
from juriscraper.lib.date_utils import make_date_range_tuples
from juriscraper.OpinionSiteLinear import OpinionSiteLinear


class Site(OpinionSiteLinear):
    # This URL will show most recent opinions
    dbObj = CaseMineCrawl.get_crawl_config_details('ca1')
    from_date = str(dbObj.get('CrawlTill'))
    till_date = date.today()
    first_opinion_date = datetime(2003, 3, 23)
    days_interval = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.make_backscrape_iterable(kwargs)

    def crawling_range(self, start_date: datetime, end_date: datetime) -> int:
        self.url = "https://www.ca1.uscourts.gov/views/ajax?field_opn_csno_value_op=starts&OPINNUM=&field_opn_short_title_value=&field_opn_issdate_value%5Bmin%5D%5Bdate%5D=" + str(
            start_date.month) + "%2F" + str(start_date.day) + "%2F" + str(
            start_date.year) + "&field_opn_issdate_value%5Bmax%5D%5Bdate%5D=" + str(
            end_date.month) + "%2F" + str(end_date.day) + "%2F" + str(
            end_date.year)
        self.method = "POST"
        self.parameters = {"page": 0, "view_name": "opn_files_view",
                           "view_display_id": "opn_search_results",
                           "view_args": "", "view_path": "opn%2Faci",
                           "view_base_path": "opn%2Faci",
                           "view_dom_id": "13a9efd116e0db177942aee81f5208d2",
                           "pager_element": "0",
                           "ajax_html_ids%5B%5D": "header-outline",
                           "ajax_html_ids%5B%5D": "page-wrapper",
                           "ajax_html_ids%5B%5D": "block-search-form",
                           "ajax_html_ids%5B%5D": "search-block-form",
                           "ajax_html_ids%5B%5D": "edit-search-block-form--2",
                           "ajax_html_ids%5B%5D": "edit-actions",
                           "ajax_html_ids%5B%5D": "edit-submit",
                           "ajax_html_ids%5B%5D": "block-us-courts-stock-font-resizer",
                           "ajax_html_ids%5B%5D": "block-menu-block-us-courts-menu-blocks-main-nav",
                           "ajax_html_ids%5B%5D": "main-content-wrapper",
                           "ajax_html_ids%5B%5D": "main-content",
                           "ajax_html_ids%5B%5D": "page-title",
                           "ajax_html_ids%5B%5D": "block-nodeblock-nb-footer-coptright",
                           "ajax_html_ids%5B%5D": "node-38",
                           "ajax_html_ids%5B%5D": "block-nodeblock-nb-footer-quick-links",
                           "ajax_html_ids%5B%5D": "node-33",
                           "ajax_page_state%5Btheme%5D": "appeals",
                           "ajax_page_state%5Btheme_token%5D": "CrRWyaTR7aSMQtn1VuRZibFvkf2gEuqY0fwxj0DygcU",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fomega%2Fomega%2Fcss%2Fmodules%2Fsystem%2Fsystem.base.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fomega%2Fomega%2Fcss%2Fmodules%2Fsystem%2Fsystem.menus.theme.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fomega%2Fomega%2Fcss%2Fmodules%2Fsystem%2Fsystem.messages.theme.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fomega%2Fomega%2Fcss%2Fmodules%2Fsystem%2Fsystem.theme.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fcalendar%2Fcss%2Fcalendar_multiday.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bmodules%2Fnode%2Fnode.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fomega%2Fomega%2Fcss%2Fmodules%2Faggregator%2Faggregator.theme.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fomega%2Fomega%2Fcss%2Fmodules%2Fcomment%2Fcomment.theme.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Ffeatures%2Fus_courts_court_calendar%2Fcss%2Fuscourts_calendar.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fomega%2Fomega%2Fcss%2Fmodules%2Ffield%2Ffield.theme.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Ffeatures%2Fus_courts_file_management%2Fcss%2Fus_courts_file_management.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fextlink%2Fextlink.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fomega%2Fomega%2Fcss%2Fmodules%2Fsearch%2Fsearch.theme.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fviews%2Fcss%2Fviews.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fomega%2Fomega%2Fcss%2Fmodules%2Fuser%2Fuser.base.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fomega%2Fomega%2Fcss%2Fmodules%2Fuser%2Fuser.theme.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fckeditor_lts%2Fcss%2Fckeditor.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bmisc%2Fui%2Fjquery.ui.core.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bmisc%2Fui%2Fjquery.ui.theme.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bmisc%2Fui%2Fjquery.ui.accordion.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bmisc%2Fui%2Fjquery.ui.tabs.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bmisc%2Fui%2Fjquery.ui.button.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bmisc%2Fui%2Fjquery.ui.resizable.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bmisc%2Fui%2Fjquery.ui.dialog.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fctools%2Fcss%2Fctools.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fcustom_search%2Fcustom_search.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fresponsive_menus%2Fstyles%2FmeanMenu%2Fmeanmenu.min.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcustom%2Fus_courts_home_slider%2Fcss%2Fflexslider.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fcustom%2Fus_courts_home_slider%2Fcss%2Fus_courts_home_slider.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Flibraries%2Ffontawesome%2Fcss%2Ffont-awesome.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fcstbase%2Fcss%2Fcstbase.normalize.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fcstbase%2Fcss%2Fcstbase.hacks.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fcstbase%2Fcss%2Fcstbase.styles.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fadaptive%2Fcss%2Fadaptive.normalize.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fadaptive%2Fcss%2Fadaptive.hacks.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fadaptive%2Fcss%2Fadaptive.styles.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fappeals%2Fcss%2Fappeals.normalize.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fappeals%2Fcss%2Fappeals.hacks.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fappeals%2Fcss%2Fappeals.styles.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fcstbase%2Fcss%2Fcstbase.no-query.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fadaptive%2Fcss%2Fadaptive.no-query.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Fappeals%2Fcss%2Fappeals.no-query.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Ball%3A0%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bpublic%3A%2F%2Fcss_injector%2Fcss_injector_15.css%5D": "1",
                           "ajax_page_state%5Bcss%5D%5Bpublic%3A%2F%2Fcss_injector%2Fcss_injector_17.css%5D": "1",
                           "ajax_page_state%5Bjs%5D%5B0%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcustom%2Fus_courts_extlink%2Fus_courts_extlink.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Flibraries%2Fmodernizr%2Fmodernizr.custom.45361.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bhttps%3A%2F%2Fcode.jquery.com%2Fjquery-3.7.0.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bhttps%3A%2F%2Fcdn.jsdelivr.net%2Fnpm%2Fjquery-migrate%403.4.1%2Fdist%2Fjquery-migrate.min.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bmisc%2Fjquery-extend-3.4.0.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bmisc%2Fjquery-html-prefilter-3.5.0-backport.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bmisc%2Fjquery.once.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bmisc%2Fdrupal.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fomega%2Fomega%2Fjs%2Fno-js.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fjquery_update%2Fjs%2Fjquery_browser.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bhttps%3A%2F%2Fcdnjs.cloudflare.com%2Fajax%2Flibs%2Fjqueryui%2F1.13.2%2Fjquery-ui.min.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fjquery_update%2Freplace%2Fui%2Fexternal%2Fjquery.cookie.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fjquery_update%2Freplace%2Fjquery.form%2F4%2Fjquery.form.min.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bmisc%2Fui%2Fjquery.ui.position-1.13.0-backport.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bmisc%2Fui%2Fjquery.ui.dialog-1.13.0-backport.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bmisc%2Fform-single-submit.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bmisc%2Fajax.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fjquery_update%2Fjs%2Fjquery_update.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fjquery_ui_filter%2Fjquery_ui_filter.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcustom%2Fus_courts_helpers%2Fjs%2Fjson2.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcustom%2Fus_courts_home_slider%2Fjs%2Fjquery.flexslider-min.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcustom%2Fus_courts_home_slider%2Fjs%2Fhome_slider.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fextlink%2Fextlink.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fadaptive%2Flibraries%2Fhtml5shiv%2Fhtml5shiv.min.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fadaptive%2Flibraries%2Fhtml5shiv%2Fhtml5shiv-printshiv.min.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fadaptive%2Flibraries%2Frespond%2Frespond.min.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fjquery_ui_filter%2Faccordion%2Fjquery_ui_filter_accordion.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fjquery_ui_filter%2Ftabs%2Fjquery_ui_filter_tabs.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fcustom_search%2Fjs%2Fcustom_search.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fviews%2Fjs%2Fbase.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bmisc%2Fprogress.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fviews%2Fjs%2Fajax_view.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fresponsive_menus%2Fstyles%2FmeanMenu%2Fjquery.meanmenu.min.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fresponsive_menus%2Fstyles%2FmeanMenu%2Fresponsive_menus_mean_menu.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fcstbase%2Fjs%2Fcstbase.behaviors.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fadaptive%2Fjs%2Fjquery.horizontalNav.min.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fthemes%2Fadaptive%2Fjs%2Fadaptive.behaviors.js%5D": "1",
                           "ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcontrib%2Fjquery_update%2Fjs%2Fjquery_position.js%5D": "1",
                           "ajax_page_state%5Bjquery_version%5D": "3.7.0",
                           "ajax_page_state%5Bjquery_version_token%5D": "5ADcyfYw147Kw0sCw45PxnRyEunFgqaSrZ9wWTz6wjQ"}
        self.parse()
        return 0

    def parse(self):
        if not self.downloader_executed:
            # Run the downloader if it hasn't been run already
            i = 0
            while (True):
                self.parameters.__setitem__("page", i)
                self._request_url_post(self.url)
                self._post_process_response()
                self.html = self._return_response_text_object()
                # Process the available html (optional)
                html_data = self.html[2]['data']
                # Create a BeautifulSoup object by parsing the HTML string
                soup = BeautifulSoup(html_data, 'html.parser')
                table = soup.find('table', class_='views-table')
                if (table == None):
                    print("hit-" + str(i) + " no Data found")
                    break
                rows = table.find_all('tr')
                print("hit-" + str(i) + " Data found")
                # Print each <tr> tag
                for row in rows:
                    td = row.find_all_next("td")
                    # title = row.xpath("td[2]/a/text()")[0]
                    name_tag = td.__getitem__(3)
                    lower_court = name_tag.find_next('span').text
                    name = name_tag.text.replace(lower_court, "")

                    url_tag = td.__getitem__(1)
                    title = url_tag.text
                    status = self.get_status_from_opinion_title(title)
                    url = url_tag.find_next("a").attrs.get('href')
                    date_filed = td.__getitem__(0).text
                    date_filed_2=date_filed.replace('\n','').strip()
                    # Format the date object to the new format
                    date_obj = datetime.strptime(date_filed_2, "%Y/%m/%d")
                    date_obj = date_obj.strftime('%d/%m/%Y')
                    res = CasemineUtil.compare_date(date_obj, self.crawled_till)
                    if(res == 1):
                        self.crawled_till = date_obj
                    dockets = []
                    docket = td.__getitem__(2).text.replace("\n","").strip()
                    dockets.append(docket)
                    self.cases.append(
                        {
                         "name": name.strip(),
                         "url": url,
                         "date": date_filed,
                         "status": status,
                         "docket": dockets,
                         "lower_court": lower_court,
                         'judge': [],
                         'citation': [],
                         'parallel_citation': [],
                         'summary': '',
                         'child_court': '',
                         'adversary_number': '',
                         'division': '',
                         'disposition': '',
                         'cause': '',
                         'docket_attachment_number': [],
                         'docket_document_number': [],
                         'nature_of_suit': '',
                         'lower_court_number': '',
                         'lower_court_judge': [],
                         'author': '',
                         'per_curiam': '',
                         'type': '',
                         'joined_by': '',
                         'other_date': ''
                    })
                i = i + 1

        # Set the attribute to the return value from _get_foo()
        # e.g., this does self.case_names = _get_case_names()
        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

        self._clean_attributes()
        if "case_name_shorts" in self._all_attrs:
            # This needs to be done *after* _clean_attributes() has been run.
            # The current architecture means this gets run twice. Once when we
            # iterate over _all_attrs, and again here. It's pretty cheap though.
            self.case_name_shorts = self._get_case_name_shorts()
            self._post_parse()
            self._check_sanity()
            self._date_sort()
            self._make_hash()
            return self

    def _download(self, request_dict={}):
        self._request_url_post(self.url)
        self._post_process_response()
        return self._return_response_text_object()

    def _process_html(self):
        html_data = self.html[2]['data']
        # Create a BeautifulSoup object by parsing the HTML string
        soup = BeautifulSoup(html_data, 'html.parser')
        table = soup.find('table', class_='views-table')
        rows = table.find_all('tr')

        # Print each <tr> tag
        for row in rows:
            td = row.find_all_next("td")
            # title = row.xpath("td[2]/a/text()")[0]
            name_tag = td.__getitem__(3)
            lower_court = name_tag.find_next('span').text
            name = name_tag.text.replace(lower_court, "")

            url_tag = td.__getitem__(1)
            title = url_tag.text
            status = self.get_status_from_opinion_title(title)
            url = url_tag.find_next("a").attrs.get('href')
            date_filed = td.__getitem__(0).text
            docket = td.__getitem__(2).text
            self.cases.append(
                {"name": name.strip(),
                 "url": url,
                 "date": date_filed,
                 "status": status,
                 "docket": docket,
                 "lower_court": lower_court,
            })

    def get_status_from_opinion_title(self, title: str) -> str:
        """Status is encoded in opinion's link title

        :param title: opinion title. Ex: 23-1667P.01A, 23-1639U.01A

        :return: status string
        """
        if "U" in title:
            status = "Unpublished"
        elif "P" in title:
            status = "Published"
        elif "E" in title:
            status = "Errata"
        else:
            status = "Unknown"
        return status

    def _download_backwards(self, dates: Tuple[date]) -> None:
        """Change URL to backscraping date range

        :param dates: tuple with date range to scrape
        :return None
        """
        start, end = dates
        params = {"field_opn_csno_value_op": "starts",
            "field_opn_issdate_value[min][date]": start.strftime("%m/%d/%Y"),
            "field_opn_issdate_value[max][date]": end.strftime("%m/%d/%Y"), }
        self.url = f"{self.base_url}?{urlencode(params)}"
        self.html = self._download()
        self._process_html()

    def make_backscrape_iterable(self, kwargs: dict) -> None:
        """Checks if backscrape start and end arguments have been passed
        by caller, and parses them accordingly

        :param kwargs: passed when initializing the scraper, may or
            may not contain backscrape controlling arguments
        :return None
        """
        start = kwargs.get("backscrape_start")
        end = kwargs.get("backscrape_end")

        if start:
            start = datetime.strptime(start, "%m/%d/%Y")
        else:
            start = self.first_opinion_date
        if end:
            end = datetime.strptime(end, "%m/%d/%Y")
        else:
            end = datetime.now()

        self.back_scrape_iterable = make_date_range_tuples(start, end,
            self.days_interval)

    def get_class_name(self):
        return "ca1"

    def get_court_name(self):
        return 'United States Court of Appeals For the First Circuit'

    def get_court_type(self):
        return 'Federal'
