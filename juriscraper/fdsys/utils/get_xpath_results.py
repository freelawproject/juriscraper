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
        print("\n%s%s:" % (indent, f))
        indent = "    "
        tree = etree.parse(f)
        results = tree.xpath(
            query, namespaces={"m": "http://www.loc.gov/mods/v3"}
        )
        count = 0
        if type(results) in [bool, float]:
            print("%s%s.\t%s" % (indent, count, results))

        elif type(results) == list:
            s = set()
            for result in results:
                if type(result) == _ElementStringResult:
                    print("%s%s.\t%s" % (indent, count, result))
                    s.add("".join(result.split()))
                else:
                    result = etree.tostring(result).strip()
                    print("%s%s.\t%s" % (indent, count, result))
                    s.add("".join(result.split()))
                count += 1
            if len(s) == 1:
                print("\n%sAll items were equal!" % indent)
                equalities += 1
            else:
                print("\n%s%s unique items" % (indent, len(s)))
            unique_items = unique_items.union(s)
        total_result_count += count

    print("\nTotal found: %s" % total_result_count)
    print(
        "All items same in %s/%s sample files" % (equalities, total_file_count)
    )
    print("Unique items: %s/%s" % (len(unique_items), total_result_count))


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
