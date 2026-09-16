#!/usr/bin/env python


import unittest

from juriscraper.lib.utils import clean_court_object


class UtilTest(unittest.TestCase):
    def test_clean_court_object(self):
        unclean_str = "1,  2, 3,4  ,5  ,  6 "
        unclean_dict: dict = {
            "string": unclean_str,
            "array": [
                unclean_str,
                [1, 2, 3, 4, 5, 6],
            ],
            "dict": {
                "string": unclean_str,
                "array": [
                    unclean_str,
                    [1, 2, 3, 4, 5, 6],
                ],
                "dict": {1: "1"},
                "other": 1,
            },
            "other": 1,
        }
        unclean_list: list = [
            unclean_str,
            {
                "string": unclean_str,
            },
            [1, 2, 3, 4, 5, 6],
        ]

        clean_str = "1, 2, 3,4,5, 6"
        clean_dict: dict = {
            "string": clean_str,
            "array": [
                clean_str,
                [1, 2, 3, 4, 5, 6],
            ],
            "dict": {
                "string": clean_str,
                "array": [
                    clean_str,
                    [1, 2, 3, 4, 5, 6],
                ],
                "dict": {1: "1"},
                "other": 1,
            },
            "other": 1,
        }
        clean_list: list = [
            clean_str,
            {
                "string": clean_str,
            },
            [1, 2, 3, 4, 5, 6],
        ]

        self.assertEqual(clean_court_object(unclean_str), clean_str)
        self.assertEqual(clean_court_object(unclean_dict), clean_dict)
        self.assertEqual(clean_court_object(unclean_list), clean_list)
        self.assertEqual(clean_court_object(1234), 1234)
