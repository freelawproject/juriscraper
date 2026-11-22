#!/usr/bin/env python
#
#  Takes an .html file on the command line, parses it using the PACER
#  Docket Report parser, and outputs json to stdout.

import sys

import jsondate3 as json

from juriscraper.pacer import DocketReport

for path in sys.argv[1:]:
    report = DocketReport.from_html_file(path)
    print(
        json.dumps(
            report.data, indent=2, sort_keys=True, separators=(",", ": ")
        )
    )
