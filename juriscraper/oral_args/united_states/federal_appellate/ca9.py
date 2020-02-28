"""Scraper for Ninth Circuit of Appeals
CourtID: ca9
Court Short Name: ca9
Author: Andrei Chelaru
Reviewer: mlr
Date created: 20 July 2014
History:
 - 2014-11-04: Updated by mlr to account for (1) varied audio file locations,
               (2) Finding the latest 100 items, (3) Handling bad audio URLs.
"""

from datetime import datetime

from juriscraper.DeferringList import DeferringList
from juriscraper.OralArgumentSite import OralArgumentSite
from juriscraper.lib.exceptions import InsanityException
from juriscraper.lib.string_utils import titlecase


class Site(OralArgumentSite):
    def __init__(self, *args, **kwargs):
        super(Site, self).__init__(*args, **kwargs)
        self.court_id = self.__module__
        self.url = "https://www.ca9.uscourts.gov/media/"
        self._set_parameters()
        self.method = "POST"
        # One less than total number of pages, because last page has a bit of a
        # mess, and it's easier to simply not deal with it.
        self.back_scrape_iterable = range(1, 268)

    def _set_parameters(self, page=1):
        self.parameters = {
            "c_mode": "view",
            "c_page_size": "100",
            "c_sort_field": "12",
            "c_sort_field_by": "7",
            "c_sort_type": "desc",
            "c_field_type": "",
            "c_p": str(page),
        }

    def _post_parse(self):
        """Unfortunately, some of the items do not have audio files despite
        appearing in the table and having a link to a supplementary audio page.

        For these items, we set the download_url to '' and this method finds
        the related information for those items and then removes it from all
        the other attributes for the Site object.
        """
        # Start by checking sanity. This will make sure we don't mess things
        # up. If this sanity check fails, we'll know things were messed up
        # before we began tinkering with them.
        self._check_sanity()

        # Items are purged in two steps. First, we identify the index of the
        # items that need purging.
        purge_indexes = []
        for i, url in enumerate(self.download_urls):
            if not url:
                purge_indexes.append(i)

        # Quick check: We did find *some* urls, right?
        if len(purge_indexes) == len(self.download_urls):
            raise InsanityException(
                "Didn't get any download URLs. Looks like "
                "something is wrong in the _post_parse() "
                "method."
            )

        # Second, we purge them, beginning at the end and moving forwards. This
        # ensures that we don't delete the wrong items.
        for index_to_purge in sorted(purge_indexes, reverse=True):
            for attr in self._all_attrs:
                item = getattr(self, attr)
                if item is not None:
                    # If we've added stuff to it, then delete the key.
                    del item[index_to_purge]

    def _get_download_urls(self):
        """Links from the root page go to a second page where the real links
        are posted.
        """

        def fetcher(seed_url):
            if self.method == "LOCAL":
                return "No links fetched during tests."
            else:
                # Goes to second page, grabs the link and returns it.
                html_tree = self._get_html_tree_by_url(seed_url)
                path_to_audio_file = (
                    "//*[@class='padboxauto_MediaContent']//a/@href"
                )
                try:
                    url = html_tree.xpath(path_to_audio_file)[0]
                except IndexError:
                    # The URL wasn't found, so something is wrong and we'll have to
                    # fix it in the _post_parse() method.
                    url = ""
                return url

        path = "//tr[@class='dg_tr']/td[6]//@href"
        seed_urls = self.html.xpath(path)
        return DeferringList(seed=seed_urls, fetcher=fetcher)

    def _get_download_urls_orig(self):
        """Note that the links from the root page go to a second page, where
        the real links are posted.
        """
        row_path = "//tr[@class='dg_tr'][.//*[contains(@id, 'case_num')]]"
        date_path = (
            ".//*[contains(concat(' ',@id,' '),' mod_hearing_date')]/text()"
        )
        docket_path = ".//*[contains(concat(' ',@id,' '),' case_num')]/text()"
        urls = []
        for row in self.html.xpath(row_path):
            date_string = row.xpath(date_path)[0]
            d = datetime.strptime(date_string, "%m/%d/%Y").date()
            docket_string = row.xpath(docket_path)[0]
            urls.append(self._return_download_url(d, docket_string))
        return urls

    @staticmethod
    def _return_download_url(d, docket_string):
        link = "http://cdn.ca9.uscourts.gov/datastore/media/{date}/{docket_nr}.wma".format(
            date=d.strftime("%Y/%m/%d"), docket_nr=docket_string,
        )
        return link

    def _get_case_names(self):
        path = "//*[contains(concat(' ',@id,' '),' case_name')]/text()"
        return list(self.html.xpath(path))

    def _get_case_dates(self):
        path = "//*[contains(concat(' ',@id,' '),' mod_hearing_date')]/text()"
        return [
            datetime.strptime(date_string, "%m/%d/%Y").date()
            for date_string in self.html.xpath(path)
        ]

    def _get_judges(self):
        path = "//*[contains(concat(' ',@id,' '),' case_panel')]/text()"
        return [titlecase(s.lower()) for s in self.html.xpath(path)]

    def _get_docket_numbers(self):
        path = "//*[contains(concat(' ',@id,' '),' case_num')]/text()"
        return list(self.html.xpath(path))

    def _download_backwards(self, page):
        self._set_parameters(page=page)
        self.html = self._download()
