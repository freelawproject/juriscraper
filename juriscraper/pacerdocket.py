#!/usr/bin/env python
#
#  Takes an .html file on the command line, parses it using the PACER
#  Docket Report parser, and outputs json to stdout.

import jsondate as json
import sys

from juriscraper.pacer.http import PacerSession
from juriscraper.pacer import DocketReport

pacer_session = PacerSession(username='tr1234',
                             password='Pass!234')
report = DocketReport('psc', pacer_session)

for path in sys.argv[1:]:
    with open(path, 'r') as f:
        report._parse_text(f.read().decode('utf-8'))
    data = report.data
    print json.dumps(data, indent=2, sort_keys=True, separators=(',', ': '))
