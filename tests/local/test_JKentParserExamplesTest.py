#!/usr/bin/env python

from tests.local.JKentParserTestCase import JKentParserTestCase


class JKentParserExamplesTest(JKentParserTestCase):
    """Run every JKentParser in the codebase over its example fixtures.

    Parsers are discovered automatically — adding a new JKentParser with
    fixtures under tests/examples/<scraper>/<ParserClass>/ is enough to
    get it tested here.
    """

    def test_kent_parsers_have_examples(self):
        self.assert_kent_parsers_have_examples()
