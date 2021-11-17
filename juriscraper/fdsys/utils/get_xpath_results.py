# !/usr/bin/python
import argparse
import glob

from lxml import etree
from lxml.etree import _ElementStringResult

__author__ = "mlissner"


def print_xpath_results(query):
    total_result_count = 0
    total_file_count = 0
    equalities = 0
    unique_items = set()
    for f in glob.glob("../examples/*.xml"):
        total_file_count += 1
        indent = ""
        print(f"\n{indent}{f}:")
        indent = "    "
        tree = etree.parse(f)
        results = tree.xpath(
            query, namespaces={"m": "http://www.loc.gov/mods/v3"}
        )
        count = 0
        if type(results) in [bool, float]:
            print(f"{indent}{count}.\t{results}")

        elif type(results) == list:
            s = set()
            for result in results:
                if type(result) == _ElementStringResult:
                    print(f"{indent}{count}.\t{result}")
                    s.add("".join(result.split()))
                else:
                    result = etree.tostring(result).strip()
                    print(f"{indent}{count}.\t{result}")
                    s.add("".join(result.split()))
                count += 1
            if len(s) == 1:
                print(f"\n{indent}All items were equal!")
                equalities += 1
            else:
                print(f"\n{indent}{len(s)} unique items")
            unique_items = unique_items.union(s)
        total_result_count += count

    print(f"\nTotal found: {total_result_count}")
    print(f"All items same in {equalities}/{total_file_count} sample files")
    print(f"Unique items: {len(unique_items)}/{total_result_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Apply an XPath query against all the example files, "
        "printing the results."
    )
    parser.add_argument(
        "-q",
        "--query",
        required=True,
        help="XPath query to apply to the example files. Note that "
        "namespaces must be applied to your queries, and that the "
        "mods elements are under the namespace m. So, a query might "
        'look like: "//m:titleInfo"',
    )
    args = parser.parse_args()

    print_xpath_results(args.query)


if __name__ == "__main__":
    main()
