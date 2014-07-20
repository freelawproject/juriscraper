"""Scraper for Ninth Circuit of Appeals
CourtID: ca9
Court Short Name: ca9
Author: Andrei Chelaru
Reviewer: mlr
Date created: 20 July 2014
"""

from datetime import date

from juriscraper.OralArgumentSite import OralArgumentSite
from juriscraper.lib.string_utils import titlecase


class Site(OralArgumentSite):
    def __init__(self):
        super(Site, self).__init__()
        self.court_id = self.__module__
        self.case_date = date.today()
        #self.case_date = date(month=7, day=18, year=2014)
        self.url = 'http://www.ca9.uscourts.gov/media/'
        self.parameters = {
            'c_page_size': '100',
            'c_sort_field': '',
            'c_sort_field_by': '',
            'c_sort_field_type': '',
            'c_sort_type': '',
            'c__ff_cms_media_video_media_type_operator': '%3D',
            'c__ff_cms_media_video_media_type': '',
            'c__ff_cms_media_case_name_operator': 'like',
            'c__ff_cms_media_case_name': '',
            'c__ff_cms_media_case_num_operator': 'like',
            'c__ff_cms_media_case_num': '',
            'c__ff_cms_media_case_panel_operator': 'like',
            'c__ff_cms_media_case_panel': '',
            'c__ff_cms_media_hearing_loc_operator': 'like',
            'c__ff_cms_media_hearing_loc': '',
            'c__ff_cms_media_hearing_date_mod_operator': 'like',
            'c__ff_cms_media_hearing_date_mod': '{date}'.format(date=self.case_date.strftime('%m/%d/%Y')),
            'c__ff_selSearchType': '0',
            'c__ff_onSUBMIT_FILTER': 'Search',
        }
        self.method = 'POST'

    def _get_download_urls(self):
        """Note that the links from the root page go to a second page, where the real links are posted."""
        path = "//*[contains(concat(' ',@id,' '),' case_num')]/text()"
        return map(self._return_download_url, self.html.xpath(path))

    def _return_download_url(self, e):
        link = "http://cdn.ca9.uscourts.gov/datastore/media/{date}/{docket_nr}.wma".format(
            date=self.case_date.strftime('%Y/%m/%d'),
            docket_nr=e
        )
        return link

    def _get_case_names(self):
        path = "//*[contains(concat(' ',@id,' '),' case_name')]/text()"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = "//*[contains(concat(' ',@id,' '),' mod_hearing_date')]/text()"
        return [self.case_date] * len(self.html.xpath(path))

    def _get_judges(self):
        path = "//*[contains(concat(' ',@id,' '),' case_panel')]/text()"
        return [titlecase(s.lower()) for s in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = "//*[contains(concat(' ',@id,' '),' case_num')]/text()"
        return list(self.html.xpath(path))
