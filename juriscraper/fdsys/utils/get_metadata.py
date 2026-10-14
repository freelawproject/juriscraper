#!/usr/bin/python
import argparse
import glob
import json
import pprint
from collections.abc import Sequence
from typing import TypeAlias, TypeVar

from lxml import etree

from juriscraper.fdsys.FDSysSite import NAMESPACES

__author__ = "mlissner"

_DataT = TypeVar("_DataT")
XMLTree: TypeAlias = "etree._ElementTree[etree._Element] | etree._Element"


def get_court_id(fdsys_court: list[str]) -> list[str]:
    """Map the fdsys_court string to a CourtListener string"""
    return fdsys_court


def clean_up_rough_data(data: _DataT) -> _DataT:
    """Clean up the data so it's good.

    - [ ] Strip extra spaces from all nodes.
    - [ ] Convert newlines into spaces.
    - [ ] Ensure good encodings?
    - [ ] Review other items from Juriscraper.

    """
    return data


def get_unique_nodes(
    node_list: Sequence[etree._Element],
) -> list[etree._Element]:
    """Lots of duplication in the XML. Nuke duplicates."""
    good_nodes = []
    nodes_as_txt = []
    for node in node_list:
        txt = etree.tostring(node).strip()
        if txt in nodes_as_txt:
            # Duplicate. Move on.
            pass
        else:
            nodes_as_txt.append(txt)
            good_nodes.append(node)
    return good_nodes


def get_parties(tree: XMLTree) -> list[dict[str, list[str]]]:
    """Extract the parties from the XML into a nice object."""
    party_nodes: list[etree._Element] = tree.xpath(
        "//m:party", namespaces=NAMESPACES
    )
    party_nodes = get_unique_nodes(party_nodes)

    parties: list[dict[str, list[str]]] = []
    for party_node in party_nodes:
        parties.append(
            {
                "name_first": party_node.xpath(
                    "@m:firstName", namespaces=NAMESPACES
                ),
                "name_last": party_node.xpath(
                    "@m:lastName", namespaces=NAMESPACES
                ),
                "name_middle": party_node.xpath(
                    "@m:middleName", namespaces=NAMESPACES
                ),
                "name_suffix": party_node.xpath(
                    "@m:generation", namespaces=NAMESPACES
                ),
                "role": party_node.xpath("@m:role", namespaces=NAMESPACES),
            }
        )
    return parties


def get_documents(tree: XMLTree) -> list[dict[str, list[str]]]:
    """Get the documents from the XML into a nice object."""
    document_nodes: list[etree._Element] = tree.xpath(
        "//m:mods/m:relatedItem", namespaces=NAMESPACES
    )
    documents: list[dict[str, list[str]]] = []
    for document_node in document_nodes:
        documents.append(
            {
                "download_url": document_node.xpath(
                    "m:relatedItem/@xlink:href", namespaces=NAMESPACES
                ),
                "description": document_node.xpath(
                    ".//m:subTitle/text()", namespaces=NAMESPACES
                ),
                "date_filed": document_node.xpath(
                    "./m:originInfo/m:dateIssued/text()", namespaces=NAMESPACES
                ),
            }
        )
    return documents


def print_xpath_results() -> None:
    for f in glob.glob("../examples/*.xml"):
        tree = etree.parse(f)
        rough_data = {
            "download_url": tree.xpath(
                "(//m:identifier[@type='uri'])[1]/text()",
                namespaces=NAMESPACES,
            ),
            "fdsys_id": tree.xpath(
                "(//m:accessId/text())[1]", namespaces=NAMESPACES
            ),
            "court_id": get_court_id(
                tree.xpath("(//m:courtCode/text())[1]", namespaces=NAMESPACES)
            ),
            "docket_number": tree.xpath(
                "(//m:caseNumber/text())[1]", namespaces=NAMESPACES
            ),
            "court_location": tree.xpath(
                "(//m:caseOffice/text())[1]", namespaces=NAMESPACES
            ),
            "parties": get_parties(tree),
            "case_name": tree.xpath(
                "(//m:titleInfo/m:title/text())[1]", namespaces=NAMESPACES
            ),
            "documents": get_documents(tree),
        }
        data = clean_up_rough_data(rough_data)
        pprint.pprint(data)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Get all the metadata from a mods file."
    )
    parser.parse_args()

    print_xpath_results()


def get_fdsys_court_names() -> None:
    response = glob.glob("../examples/2015_USCOURTS_sitemap.xml")
    tree = etree.parse(response[0])
    # print(etree.tostring(tree, pretty_print=True))
    data = {}

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

    with open("./fdsys_court_names.json", "w") as f:
        json.dump(data, f)


if __name__ == "__main__":
    main()
    # get_fdsys_court_names()
