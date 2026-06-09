#!/usr/bin/env python

from tests.local.KentParserTestCase import KentParserTestCase


class KentParserExamplesTest(KentParserTestCase):
    """Run every KentParser in the codebase over its example fixtures.

    Parsers are discovered automatically — adding a new KentParser with
    fixtures under tests/examples/<scraper>/<ParserClass>/ is enough to
    get it tested here.
    """

    def test_kent_parsers_have_examples(self):
        self.assert_kent_parsers_have_examples()
