#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime
import unittest

from juriscraper.lib.date_utils import (
    fix_future_year_typo,
    make_date_range_tuples,
    parse_dates,
)
from juriscraper.lib.string_utils import convert_date_string


class DateTest(unittest.TestCase):
    def test_various_date_extractions(self):
        test_pairs = (
            # Dates separated by semicolons and JUMP words
            (
                "February 5, 1980; March 14, 1980 and May 28, 1980.",
                [
                    datetime.datetime(1980, 2, 5, 0, 0),
                    datetime.datetime(1980, 3, 14, 0, 0),
                    datetime.datetime(1980, 5, 28, 0, 0),
                ],
            ),
            # Misspelled month value.
            ("Febraury 17, 1945", [datetime.datetime(1945, 2, 17, 0, 0)]),
            ("Sepetmber 19 1924", [datetime.datetime(1924, 9, 19)]),
            # Using 'Term' as an indicator.
            ("November Term 2004.", [datetime.datetime(2004, 11, 1)]),
            ("April 26, 1961.[†]", [datetime.datetime(1961, 4, 26)]),
        )
        for pair in test_pairs:
            dates = parse_dates(pair[0])
            self.assertEqual(dates, pair[1])

    def test_fix_future_year_typo(self):
        correct = str(datetime.date.today().year)
        transposed = correct[0] + correct[2] + correct[1] + correct[3]
        expectations = {
            "12/01/%s" % transposed: "12/01/%s" % correct,  # Here's the fix
            "12/01/%s" % correct: "12/01/%s" % correct,  # Should not change
            "12/01/2806": "12/01/2806",  # Should not change
            "12/01/2886": "12/01/2886",  # Should not change
        }
        for before, after in list(expectations.items()):
            fixed_date = fix_future_year_typo(convert_date_string(before))
            self.assertEqual(fixed_date, convert_date_string(after))

    def test_date_range_creation(self):
        q_a = (
            {
                # Five days (though it looks like four)
                "q": {
                    "start": datetime.date(2017, 1, 1),
                    "end": datetime.date(2017, 1, 5),
                    "gap": 7,
                },
                "a": [(datetime.date(2017, 1, 1), datetime.date(2017, 1, 5))],
            },
            {
                # Six days (though it looks like five)
                "q": {
                    "start": datetime.date(2017, 1, 1),
                    "end": datetime.date(2017, 1, 6),
                    "gap": 7,
                },
                "a": [(datetime.date(2017, 1, 1), datetime.date(2017, 1, 6))],
            },
            {
                # Eight days (though it looks like seven)
                "q": {
                    "start": datetime.date(2017, 1, 1),
                    "end": datetime.date(2017, 1, 8),
                    "gap": 7,
                },
                "a": [
                    (datetime.date(2017, 1, 1), datetime.date(2017, 1, 7)),
                    (datetime.date(2017, 1, 8), datetime.date(2017, 1, 8)),
                ],
            },
            {
                # Gap bigger than range
                "q": {
                    "start": datetime.date(2017, 1, 1),
                    "end": datetime.date(2017, 1, 5),
                    "gap": 1000,
                },
                "a": [(datetime.date(2017, 1, 1), datetime.date(2017, 1, 5))],
            },
            {
                # Ends before starts
                "q": {
                    "start": datetime.date(2017, 1, 5),
                    "end": datetime.date(2017, 1, 1),
                    "gap": 7,
                },
                "a": [],
            },
        )
        for test in q_a:
            result = make_date_range_tuples(**test["q"])
            self.assertEqual(result, test["a"])
