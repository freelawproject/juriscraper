import asyncio
import json

import httpx
from lxml import etree, html
from lxml.html import HtmlElement
from typing_extensions import Unpack

from juriscraper.lib.type_utils import AsyncClientOptions


async def get_court_names(**kwargs: Unpack[AsyncClientOptions]) -> None:
    kwargs.setdefault("http2", True)
    async with httpx.AsyncClient(**kwargs) as client:
        response = await client.get(
            "https://www.courtlistener.com/api/jurisdictions/"
        )
    tree = html.fromstring(response.text)

    data: dict[str, str] = {}

    rows: list[HtmlElement] = tree.xpath("//tr")
    for tr in rows:
        pre: list[str] = tr.xpath("./td[5]/a/text()")
        name: list[str] = tr.xpath("./td[1]/text()")
        if bool(pre) and bool(name):
            data[pre[0].strip()] = name[0].strip()

    with open("./court_names.json", "w") as f:
        json.dump(data, f)


async def get_fdsys_court_names(**kwargs: Unpack[AsyncClientOptions]) -> None:
    kwargs.setdefault("http2", True)
    async with httpx.AsyncClient(**kwargs) as client:
        response = await client.get(
            "https://www.gpo.gov/smap/fdsys/sitemap_2014/2014_USCOURTS_sitemap.xml",
        )
        tree = etree.fromstring(response.content)

    data: dict[str, str] = {}

    urls: list[str] = tree.xpath(
        "//m:loc/text()",
        namespaces={
            "m": "http://www.sitemaps.org/schemas/sitemap/0.9",
            "xlink": "http://www.w3.org/1999/xlink",
        },
    )
    for url in urls:
        pre = url.split("-")[1]
        # if pre not in data and url:
        data[pre] = url

    with open("./fdsys_court_names_2014.json", "w") as f:
        json.dump(data, f)


if __name__ == "__main__":
    # get_court_names()
    asyncio.run(get_fdsys_court_names())
