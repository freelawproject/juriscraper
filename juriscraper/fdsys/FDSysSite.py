from __future__ import annotations

import asyncio
import glob
import json
import re
from collections import defaultdict
from collections.abc import Iterator
from contextlib import nullcontext
from datetime import date
from io import BytesIO
from typing import Self
from urllib.parse import urlsplit

import httpx
from lxml import etree
from typing_extensions import Unpack, override

from juriscraper.AbstractSite import (
    AbstractSite,
    RequestParameters,
    SiteOptions,
)
from juriscraper.lib.string_utils import CaseNameTweaker
from juriscraper.lib.type_utils import AsyncClientOptions, PostRequestOptions

NAMESPACES = {
    "m": "http://www.loc.gov/mods/v3",
    "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "xlink": "http://www.w3.org/1999/xlink",
}


async def get_tree(
    url: str,
    *,
    session: httpx.AsyncClient | None = None,
    request_options: PostRequestOptions | None = None,
    **kwargs: Unpack[AsyncClientOptions],
) -> etree._ElementTree[etree._Element]:
    """Load XML, leaving a supplied session open for its owner."""
    if session is not None and bool(kwargs):
        raise ValueError("Configure client options on the supplied session.")
    if not bool(urlsplit(url).scheme):
        return etree.parse(url)
    if request_options is None:
        request_options = {}
    kwargs.setdefault("http2", True)
    async with (
        nullcontext(session)
        if session is not None
        else httpx.AsyncClient(**kwargs)
    ) as client:
        response = await client.request("GET", url, **request_options)
        response.raise_for_status()
        return etree.parse(BytesIO(response.content))


class FDSysModsContent:
    def __init__(self, tree: etree._ElementTree[etree._Element]) -> None:
        self.tree = tree
        self.download_url = self._get_download_url()
        self.fdsys_id = self._get_fdsys_id()
        self.court_id = self._get_court_id()
        self.docket_number = self._get_docket_number()
        self.court_location = self._get_court_location()
        self.parties = self._get_parties()
        self.case_name = self._get_case_name()
        self.documents = self._get_documents()

    def get_content(self) -> dict[str, object]:
        """Return the parsed MODS metadata as a dictionary."""
        return {
            "download_url": self.download_url,
            "fdsys_id": self.fdsys_id,
            "court_id": self.court_id,
            "docket_number": self.docket_number,
            "court_location": self.court_location,
            "parties": self.parties,
            "case_name": self.case_name,
            "documents": self.documents,
        }

    def _get_download_url(self) -> str:
        values: list[str] = self.tree.xpath(
            "(//m:identifier[@type='uri'])[1]/text()", namespaces=NAMESPACES
        )
        return "".join(values).strip()

    def _get_fdsys_id(self) -> str:
        values: list[str] = self.tree.xpath(
            "(//m:accessId/text())[1]", namespaces=NAMESPACES
        )
        return "".join(values)

    def _get_docket_number(self) -> str:
        values: list[str] = self.tree.xpath(
            "(//m:caseNumber/text())[1]", namespaces=NAMESPACES
        )
        return "".join(values)

    def _get_court_id(self) -> str:
        values: list[str] = self.tree.xpath(
            "(//m:courtCode/text())[1]", namespaces=NAMESPACES
        )
        return "".join(values).lower()

    def _get_court_location(self) -> str:
        values: list[str] = self.tree.xpath(
            "(//m:caseOffice/text())[1]", namespaces=NAMESPACES
        )
        return "".join(values)

    def _get_case_name(self) -> str:
        values: list[str] = self.tree.xpath(
            "(//m:titleInfo/m:title/text())[1]", namespaces=NAMESPACES
        )
        return "".join(values)

    def _get_parties(self) -> list[dict[str, str]]:
        """Extract the parties from the XML into a nice object."""
        party_nodes: list[etree._Element] = self.tree.xpath(
            "(//m:extension[m:party])[1]//m:party", namespaces=NAMESPACES
        )

        return list(map(self._get_party, party_nodes))

    @staticmethod
    def _get_party(party_node: etree._Element) -> dict[str, str]:
        return {
            "name_first": "".join(
                party_node.xpath("./@firstName", namespaces=NAMESPACES)
            ),
            "name_last": "".join(
                party_node.xpath("./@lastName", namespaces=NAMESPACES)
            ),
            "name_middle": "".join(
                party_node.xpath("./@middleName", namespaces=NAMESPACES)
            ),
            "name_suffix": "".join(
                party_node.xpath("./@generation", namespaces=NAMESPACES)
            ),
            "role": "".join(
                party_node.xpath("./@role", namespaces=NAMESPACES)
            ),
        }

    def _get_documents(self) -> list[dict[str, str]]:
        """Get the documents from the XML into a nice object."""
        document_nodes: list[etree._Element] = self.tree.xpath(
            "//m:mods/m:relatedItem", namespaces=NAMESPACES
        )

        return list(map(self._get_document, document_nodes))

    def _get_document(self, document_node: etree._Element) -> dict[str, str]:
        values: list[str] = document_node.xpath(
            ".//m:subTitle/text()", namespaces=NAMESPACES
        )
        desription = " ".join("".join(values).split())
        return {
            "download_url": "".join(
                document_node.xpath(
                    "./m:relatedItem/@xlink:href", namespaces=NAMESPACES
                )
            ).strip(),
            "description": desription,
            "date_filed": "".join(
                document_node.xpath(
                    "./m:originInfo/m:dateIssued/text()", namespaces=NAMESPACES
                )
            ),
            # 'type': self._get_document_type(desription),
            "number": "".join(
                document_node.xpath(
                    ".//m:partNumber/text()", namespaces=NAMESPACES
                )
            ),
        }

    @staticmethod
    def _get_mods_file_url(url: str) -> str:
        """replaces content-detail.html with mods.xml"""
        return url.replace("content-detail.html", "mods.xml")

    # def _get_document_type(self, description):
    #     # get the first 5 words
    #     return ''


class FDSysSite(AbstractSite[int]):
    """Contains generic methods for scraping fdsys. Should be extended by all
    scrapers for fdsys.

    Should not contain lists that can't be sorted by the _date_sort function.


    """

    def __init__(
        self,
        cnt: CaseNameTweaker | None = None,
        user_agent: str = "Juriscraper",
        **kwargs: Unpack[SiteOptions[int]],
    ) -> None:
        kwargs.setdefault("follow_redirects", False)
        super().__init__(cnt, user_agent, **kwargs)
        current_year = date.today().year
        self.base_url = "https://www.gpo.gov/smap/fdsys/sitemap_{year}/{year}_USCOURTS_sitemap.xml"
        self.url = self.base_url.format(year=current_year)
        self.back_scrape_iterable = list(range(1982, current_year + 1))
        self._items: list[dict[str, object]] = []

    @override
    def __iter__(self) -> Iterator[dict[str, object]]:
        return iter(self._items)

    @override
    def __getitem__(self, i: int) -> dict[str, object]:
        return self._items[i]

    @override
    def __len__(self) -> int:
        return len(self._items)

    async def save_mods_file(
        self,
        url: str,
        *,
        request_options: PostRequestOptions | None = None,
        **kwargs: Unpack[AsyncClientOptions],
    ) -> None:
        mods_url = FDSysModsContent._get_mods_file_url(url)
        if request_options is None:
            request_options = {}
        name = "-".join(mods_url.split("/")[-2].split("-")[1:])
        with open(f"./examples/2006/{name}.xml", "wb") as handle:
            if bool(kwargs):
                kwargs.setdefault("http2", True)
            async with (
                (
                    httpx.AsyncClient(**kwargs)
                    if bool(kwargs)
                    else nullcontext(self.request["session"])
                ) as client,
                client.stream(
                    "GET",
                    mods_url,
                    **request_options,
                ) as response,
            ):
                response.raise_for_status()
                async for block in response.aiter_bytes():
                    handle.write(block)

    @override
    async def _download(
        self, request_dict: RequestParameters | None = None
    ) -> etree._ElementTree[etree._Element]:
        """
        it actually builds an XML tree
        """
        if self.url is None:
            raise ValueError("A sitemap URL is required before downloading.")
        tree = await get_tree(
            self.url,
            session=self.request["session"],
            request_options=request_dict,
        )
        self.downloader_executed = True
        return tree

    @override
    async def _download_backwards(self, year: int) -> None:
        self.url = self.base_url.format(year=year)
        self.html = await self._download()

    @override
    def _check_sanity(self) -> None:
        pass

    @override
    async def parse(self) -> Self:
        """Load the sitemap and its MODS files for synchronous iteration."""
        if not self.downloader_executed:
            self.html = await self._download()
        items = []
        if not isinstance(self.html, etree._ElementTree):
            raise ValueError(
                "A parsed sitemap is required before loading MODS files."
            )
        urls: list[str] = self.html.xpath(
            "//s:loc/text()", namespaces=NAMESPACES
        )
        for url in urls:
            mods_url = FDSysModsContent._get_mods_file_url(url)
            mods_file = FDSysModsContent(
                await get_tree(mods_url, session=self.request["session"])
            )
            items.append(mods_file.get_content())
        self._items = items
        return self


async def get_court_locations_list() -> None:
    """
    parses the examples directories and gets the court ids and the court locations
    """
    court_locations_list = defaultdict(set)
    # parse all the example files
    for f in glob.glob("./examples/*/*.xml"):
        mods_url = FDSysModsContent._get_mods_file_url(f)
        fm = FDSysModsContent(await get_tree(mods_url))
        print(f, fm.court_id, fm.court_location)
        court_locations_list[fm.court_id].add(fm.court_location)

    # change set to list
    cl = {}
    for k, v in court_locations_list.items():
        cl[k] = list(v)

    # save as json
    with open("court_locations.json", "w") as j:
        json.dump(cl, j)


async def get_the_first_5_words() -> None:
    l = defaultdict(list)  # noqa: E741
    p = defaultdict(list)
    word_counter = defaultdict(int)
    for f in glob.glob("./examples/*/*.xml"):
        mods_url = FDSysModsContent._get_mods_file_url(f)
        fm = FDSysModsContent(await get_tree(mods_url))
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

                if bool(w):
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
    # asyncio.run(get_court_locations_list())
    asyncio.run(get_the_first_5_words())
    # for f in glob.glob('./examples/*/*.xml'):
    #     fm = FDSysModsContent(asyncio.run(get_tree(f)))
    #
    #     pprint(fm.get_content())
    # f = FDSysSite()
    # f.url = "./sitemaps_examples/2006_USCOURTS_sitemap.xml"
    # asyncio.run(f.parse())
    # for i in f:
    #     print(i)
    # #     pprint(i)0
