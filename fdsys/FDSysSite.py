# -*- coding: utf-8 -*-
import glob
from pprint import pprint

import requests
from juriscraper.AbstractSite import AbstractSite
from datetime import date

from lxml import etree
from requests.exceptions import MissingSchema


def get_tree(url):
    try:
        response = requests.get(url, stream=True)
        response.raw.decode_content = True
        return etree.parse(response.raw)
    except MissingSchema:
        return etree.parse(url)


def xpath(tree, query):
    return tree.xpath(
        query,
        namespaces={
            'm': 'http://www.loc.gov/mods/v3',
            's': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'xlink': 'http://www.w3.org/1999/xlink',
        }
    )


class FDSysModsContent(object):

    def __init__(self, url):

        self._all_attrs = [
            'download_url',
            'fdsys_id',
            'court_id',
            'docket_number',
            'court_location',
            'parties',
            'case_name',
            'documents'
        ]
        self.tree = None
        mods_url = self._get_mods_file_url(url)
        self.parse(mods_url)

    def get_content(self):
        """Using i, convert a single item into a dict. This is effectively a
        different view of the data.
        """
        item = {}
        for attr_name in self._all_attrs:
            item[attr_name] = getattr(self, attr_name)
        return item

    def parse(self, url):
        self.tree = get_tree(url)

        for attr in self._all_attrs:
            self.__setattr__(attr, getattr(self, '_get_%s' % attr)())

    def _get_download_url(self):
        return ''.join(xpath(self.tree, "(//m:identifier[@type='uri'])[1]/text()"))

    def _get_fdsys_id(self):
        return ''.join(xpath(self.tree, "(//m:accessId/text())[1]"))

    def _get_docket_number(self):
        return ''.join(xpath(self.tree, "(//m:caseNumber/text())[1]"))

    def _get_court_id(self):
        return ''.join(xpath(self.tree, "(//m:courtCode/text())[1]")).lower()

    def _get_court_location(self):
        return ''.join(xpath(self.tree, "(//m:caseOffice/text())[1]"))

    def _get_case_name(self):
        return ''.join(xpath(self.tree, "(//m:titleInfo/m:title/text())[1]"))

    def _get_parties(self):
        """Extract the parties from the XML into a nice object."""
        party_nodes = xpath(self.tree, "(//m:extension[m:party])[1]//m:party")

        return map(self._get_party, party_nodes)

    @staticmethod
    def _get_party(party_node):
        return {
            'name_first': ''.join(xpath(party_node, './@firstName')),
            'name_last': ''.join(xpath(party_node, './@lastName')),
            'name_middle': ''.join(xpath(party_node, './@middleName')),
            'name_suffix': ''.join(xpath(party_node, './@generation')),
            'role': ''.join(xpath(party_node, './@role')),
        }

    def _get_documents(self):
        """Get the documents from the XML into a nice object."""
        document_nodes = xpath(self.tree, "//m:mods/m:relatedItem")

        return map(self._get_document, document_nodes)

    @staticmethod
    def _get_document(document_node):
        return {
            'download_url': ''.join(xpath(document_node, './m:relatedItem/@xlink:href')),
            'description': ''.join(xpath(document_node, './/m:subTitle/text()')),
            'date_filed': ''.join(xpath(document_node, './m:originInfo/m:dateIssued/text()'))
        }

    @staticmethod
    def _get_mods_file_url(url):
        """replaces content-detail.html with mods.xml"""
        return url.replace('content-detail.html', 'mods.xml')


class FDSysSite(AbstractSite):
    """Contains generic methods for scraping fdsys. Should be extended by all
    scrapers for fdsys.

    Should not contain lists that can't be sorted by the _date_sort function.


    """

    def __init__(self, *args, **kwargs):
        super(FDSysSite, self).__init__(*args, **kwargs)
        current_year = date.today().year
        self.base_url = "https://www.gpo.gov/smap/fdsys/sitemap_{year}/{year}_USCOURTS_sitemap.xml"
        self.url = self.base_url.format(year=current_year)
        self.back_scrape_iterable = range(1982, current_year + 1)

    def __iter__(self):
        for url in xpath(self.html, "//s:loc/text()"):
            mods_file = FDSysModsContent(url)
            yield mods_file.get_content()

    def __getitem__(self, i):
        mods_file = FDSysModsContent(xpath(self.html, "//s:loc/text()")[i])
        return mods_file.get_content()

    def __len__(self):
        return len(xpath(self.html, "//s:loc/text()"))

    def _download(self, request_dict={}):
        """
        it actually builds an XML tree
        """
        return get_tree(self.url)

    def _download_backwards(self, year):
        self.url = self.base_url.format(year=year)
        self.html = self._download()
        if self.html is not None:
            # Setting status is important because it prevents the download
            # function from being run a second time by the parse method.
            self.status = 200

    def _check_sanity(self):
        pass

    def parse(self):
        if self.status is None:
            # Run the downloader if it hasn't been run already
            self.html = self._download()
        return self


if __name__ == '__main__':
    # for f in glob.glob('./examples/*.xml'):
    #     print f
    #     fm = FDSysModsContent(f)
    #     pprint(fm.get_content())
    f = FDSysSite()
    # f.url = "./examples/2015_USCOURTS_sitemap.xml"
    f.parse()
    for i in f:
        pprint(i)

