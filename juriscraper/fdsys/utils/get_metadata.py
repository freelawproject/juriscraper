#!/usr/bin/python
import argparse
import glob
import json
import pprint

from lxml import etree

__author__ = "mlissner"


def xpath(tree, query):
    return tree.xpath(
        query,
        namespaces={
            "m": "http://www.loc.gov/mods/v3",
            "xlink": "http://www.w3.org/1999/xlink",
        },
    )


def get_court_id(fdsys_court):
    """Map the fdsys_court string to a CourtListener string"""
    return fdsys_court


def clean_up_rough_data(data):
    """Clean up the data so it's good.

    - [ ] Strip extra spaces from all nodes.
    - [ ] Convert newlines into spaces.
    - [ ] Ensure good encodings?
    - [ ] Review other items from Juriscraper.

    """
    return data


def get_unique_nodes(node_list):
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


def get_parties(tree):
    """Extract the parties from the XML into a nice object."""
    party_nodes = xpath(tree, "//m:party")
    party_nodes = get_unique_nodes(party_nodes)

    parties = []
    for party_node in party_nodes:
        parties.append(
            {
                "name_first": xpath(party_node, "@m:firstName"),
                "name_last": xpath(party_node, "@m:lastName"),
                "name_middle": xpath(party_node, "@m:middleName"),
                "name_suffix": xpath(party_node, "@m:generation"),
                "role": xpath(party_node, "@m:role"),
            }
        )
    return parties


def get_documents(tree):
    """Get the documents from the XML into a nice object."""
    document_nodes = xpath(tree, "//m:mods/m:relatedItem")
    documents = []
    for document_node in document_nodes:
        documents.append(
            {
                "download_url": xpath(
                    document_node, "m:relatedItem/@xlink:href"
                ),
                "description": xpath(document_node, "//m:subTitle"),
                "date_filed": xpath(document_node, "XXX"),
            }
        )


def print_xpath_results():
    for f in glob.glob("../examples/*.xml"):
        tree = etree.parse(f)
        rough_data = {
            "download_url": xpath(
                tree, "(//m:identifier[@type='uri'])[1]/text()"
            ),
            "fdsys_id": xpath(tree, "(//m:accessId/text())[1]"),
            "court_id": get_court_id(xpath(tree, "(//m:courtCode/text())[1]")),
            "docket_number": xpath(tree, "(//m:caseNumber/text())[1]"),
            "court_location": xpath(tree, "(//m:caseOffice/text())[1]"),
            "parties": get_parties(tree),
            "case_name": xpath(tree, "(//m:titleInfo/m:title/text())[1]"),
            "documents": get_documents(tree),
        }
        data = clean_up_rough_data(rough_data)
        pprint.pprint(data)


def main():
    parser = argparse.ArgumentParser(
        description="Get all the metadata from a mods file."
    )
    args = parser.parse_args()

    print_xpath_results()


def get_fdsys_court_names():
    response = glob.glob("../examples/2015_USCOURTS_sitemap.xml")
    tree = etree.parse(response[0])
    # print(etree.tostring(tree, pretty_print=True))
    data = dict()

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

    with open("./fdsys_court_names.json", "w") as f:
        json.dump(data, f)


if __name__ == "__main__":
    main()
    # get_fdsys_court_names()
