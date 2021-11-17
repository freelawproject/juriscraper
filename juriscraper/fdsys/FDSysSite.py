import glob
import json
import re
from collections import defaultdict
from datetime import date
from pprint import pprint

import requests
from lxml import etree
from requests.exceptions import MissingSchema

from juriscraper.AbstractSite import AbstractSite


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
            "m": "http://www.loc.gov/mods/v3",
            "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
            "xlink": "http://www.w3.org/1999/xlink",
        },
    )


class FDSysModsContent:
    def __init__(self, url):

        self._all_attrs = [
            "download_url",
            "fdsys_id",
            "court_id",
            "docket_number",
            "court_location",
            "parties",
            "case_name",
            "documents",
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
            self.__setattr__(attr, getattr(self, f"_get_{attr}")())

    def _get_download_url(self):
        return "".join(
            xpath(self.tree, "(//m:identifier[@type='uri'])[1]/text()")
        ).strip()

    def _get_fdsys_id(self):
        return "".join(xpath(self.tree, "(//m:accessId/text())[1]"))

    def _get_docket_number(self):
        return "".join(xpath(self.tree, "(//m:caseNumber/text())[1]"))

    def _get_court_id(self):
        return "".join(xpath(self.tree, "(//m:courtCode/text())[1]")).lower()

    def _get_court_location(self):
        return "".join(xpath(self.tree, "(//m:caseOffice/text())[1]"))

    def _get_case_name(self):
        return "".join(xpath(self.tree, "(//m:titleInfo/m:title/text())[1]"))

    def _get_parties(self):
        """Extract the parties from the XML into a nice object."""
        party_nodes = xpath(self.tree, "(//m:extension[m:party])[1]//m:party")

        return list(map(self._get_party, party_nodes))

    @staticmethod
    def _get_party(party_node):
        return {
            "name_first": "".join(xpath(party_node, "./@firstName")),
            "name_last": "".join(xpath(party_node, "./@lastName")),
            "name_middle": "".join(xpath(party_node, "./@middleName")),
            "name_suffix": "".join(xpath(party_node, "./@generation")),
            "role": "".join(xpath(party_node, "./@role")),
        }

    def _get_documents(self):
        """Get the documents from the XML into a nice object."""
        document_nodes = xpath(self.tree, "//m:mods/m:relatedItem")

        return list(map(self._get_document, document_nodes))

    def _get_document(self, document_node):
        desription = " ".join(
            "".join(xpath(document_node, ".//m:subTitle/text()")).split()
        )
        return {
            "download_url": "".join(
                xpath(document_node, "./m:relatedItem/@xlink:href")
            ).strip(),
            "description": desription,
            "date_filed": "".join(
                xpath(document_node, "./m:originInfo/m:dateIssued/text()")
            ),
            # 'type': self._get_document_type(desription),
            "number": "".join(xpath(document_node, ".//m:partNumber/text()")),
        }

    @staticmethod
    def _get_mods_file_url(url):
        """replaces content-detail.html with mods.xml"""
        return url.replace("content-detail.html", "mods.xml")

    # def _get_document_type(self, description):
    #     # get the first 5 words
    #     return ''


class FDSysSite(AbstractSite):
    """Contains generic methods for scraping fdsys. Should be extended by all
    scrapers for fdsys.

    Should not contain lists that can't be sorted by the _date_sort function.


    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_year = date.today().year
        self.base_url = "https://www.gpo.gov/smap/fdsys/sitemap_{year}/{year}_USCOURTS_sitemap.xml"
        self.url = self.base_url.format(year=current_year)
        self.back_scrape_iterable = list(range(1982, current_year + 1))

    def __iter__(self):
        for i, url in enumerate(xpath(self.html, "//s:loc/text()")):
            self.save_mods_file(url)
            mods_file = FDSysModsContent(url)
            yield mods_file.get_content()

    def __getitem__(self, i):
        mods_file = FDSysModsContent(xpath(self.html, "//s:loc/text()")[i])
        return mods_file.get_content()

    def __len__(self):
        return len(xpath(self.html, "//s:loc/text()"))

    def save_mods_file(self, url):
        mods_url = FDSysModsContent._get_mods_file_url(url)
        name = "-".join(mods_url.split("/")[-2].split("-")[1:])
        with open(f"./examples/2006/{name}.xml", "w") as handle:
            response = requests.get(mods_url, stream=True)
            for block in response.iter_content(1024):
                handle.write(block)

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


def get_court_locations_list():
    """
    parses the examples directories and gets the court ids and the court locations
    """
    court_locations_list = defaultdict(set)
    # parse all the example files
    for f in glob.glob("./examples/*/*.xml"):
        fm = FDSysModsContent(f)
        print(f, fm.court_id, fm.court_location)
        court_locations_list[fm.court_id].add(fm.court_location)

    # change set to list
    cl = {}
    for k, v in court_locations_list.items():
        cl[k] = list(v)

    # save as json
    with open("court_locations.json", "w") as j:
        json.dump(cl, j)


def get_the_first_5_words():
    l = defaultdict(list)
    p = defaultdict(list)
    word_counter = defaultdict(int)
    for f in glob.glob("./examples/*/*.xml"):
        fm = FDSysModsContent(f)
        print(f, fm.court_id, fm.court_location)
        for document in fm.documents:
            try:
                words_to_use = document["description"].split()[:8]
            except IndexError:
                words_to_use = document["description"].split()
            ws = []
            for word in words_to_use:
                try:
                    w = re.findall("[a-zA-Z]+", word)[0]
                except IndexError:
                    w = None

                if w:
                    word_counter[w] += 1
                ws.append(w)
            l[f.__repr__()].append(ws)
            p[f.__repr__()].append(" ".join(words_to_use))

    with open("first_8_words_string.json", "w") as pc:
        json.dump(p, pc)

    with open("first_five_words.json", "w") as j:
        json.dump(l, j)

    with open("first_five_words_counter.json", "w") as c:
        json.dump(word_counter, c)


if __name__ == "__main__":
    # get_court_locations_list()
    get_the_first_5_words()
    # for f in glob.glob('./examples/*/*.xml'):
    #     fm = FDSysModsContent(f)
    #
    #     pprint(fm.get_content())
    # f = FDSysSite()
    # f.url = "./sitemaps_examples/2006_USCOURTS_sitemap.xml"
    # f.parse()
    # for i in f:
    #     print(i)
    # #     pprint(i)0
