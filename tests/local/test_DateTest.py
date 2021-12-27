#!/usr/bin/env python


import datetime
import unittest

from juriscraper.lib.date_utils import (
    fix_future_year_typo,
    make_date_range_tuples,
)
from juriscraper.lib.string_utils import convert_date_string


class DateTest(unittest.TestCase):
    def test_fix_future_year_typo(self):
        correct = str(datetime.date.today().year)
        transposed = correct[0] + correct[2] + correct[1] + correct[3]
        expectations = {
            f"12/01/{transposed}": f"12/01/{correct}",  # Here's the fix
            f"12/01/{correct}": f"12/01/{correct}",  # Should not change
            "12/01/2806": "12/01/2806",  # Should not change
            "12/01/2886": "12/01/2886",  # Should not change
        }
        for before, after in expectations.items():
            fixed_date = fix_future_year_typo(convert_date_string(before))
            with self.subTest("Future years", before=before):
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
            with self.subTest("Checking dates", test=test["q"]):
                self.assertEqual(result, test["a"])
