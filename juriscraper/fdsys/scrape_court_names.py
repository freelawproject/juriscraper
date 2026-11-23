import asyncio
import json
import pathlib

import httpx
from lxml import etree, html


async def get_court_names(**kwargs):
    kwargs.setdefault("http2", True)
    async with httpx.AsyncClient(**kwargs) as client:
        response = await client.get(
            "https://www.courtlistener.com/api/jurisdictions/"
        )
    tree = html.fromstring(response.text)

    data = {}

    for tr in tree.xpath("//tr"):
        pre = tr.xpath("./td[5]/a/text()")
        name = tr.xpath("./td[1]/text()")
        if pre and name:
            data[pre[0].strip()] = name[0].strip()

    with pathlib.Path("./court_names.json").open("w") as f:
        json.dump(data, f)


async def get_fdsys_court_names(**kwargs):
    kwargs.setdefault("http2", True)
    async with httpx.AsyncClient(**kwargs) as client:
        response = await client.get(
            "https://www.gpo.gov/smap/fdsys/sitemap_2014/2014_USCOURTS_sitemap.xml",
        )
        tree = etree.parse(await response.aread())

    data = {}

    for url in tree.xpath(
        "//m:loc/text()",
        namespaces={
            "m": "http://www.sitemaps.org/schemas/sitemap/0.9",
            "xlink": "http://www.w3.org/1999/xlink",
        },
    ):
        pre = url.split("-")[1]
        # if pre not in data and url:
        data[pre] = url

    with pathlib.Path("./fdsys_court_names_2014.json").open("w") as f:
        json.dump(data, f)


if __name__ == "__main__":
    # get_court_names()
    asyncio.run(get_fdsys_court_names())
