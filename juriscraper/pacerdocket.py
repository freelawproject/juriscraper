#!/usr/bin/env python
#
#  Takes an .html file on the command line, parses it using the PACER
#  Docket Report parser, and outputs json to stdout.

import sys

import jsondate3 as json

from juriscraper.pacer import DocketReport
from juriscraper.pacer.http import PacerSession

pacer_session = PacerSession(username="tr1234", password="Pass!234")
report = DocketReport("psc", pacer_session)

for path in sys.argv[1:]:
    with open(path) as f:
        report._parse_text(f.read())
    data = report.data
    print(json.dumps(data, indent=2, sort_keys=True, separators=(",", ": ")))
