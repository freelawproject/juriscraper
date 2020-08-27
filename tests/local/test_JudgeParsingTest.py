#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import unittest

from juriscraper.lib.judge_parsers import (
    normalize_judge_names,
    normalize_judge_string,
)
from juriscraper.pacer.docket_utils import normalize_party_types


class JudgeParsingTest(unittest.TestCase):
    def test_title_name_splitter(self):
        pairs = [
            {
                "q": "Magistrate Judge George T. Swartz",
                "a": ("George T. Swartz", "mag"),
            },
            {
                "q": "J. Frederick Motz",
                "a": ("Frederick Motz", "jud"),
            },
            {
                "q": "Honorable Susan W. Wright",
                "a": ("Susan W. Wright", "jud"),
            },
        ]

        for pair in pairs:
            self.assertEqual(pair["a"], normalize_judge_string(pair["q"]))

    def test_name_normalization(self):
        pairs = [
            {
                "q": "Michael J Lissner",
                "a": "Michael J. Lissner",
            },
            {
                "q": "Michael Lissner Jr",
                "a": "Michael Lissner Jr.",
            },
            {
                "q": "J Michael Lissner",
                "a": "Michael Lissner",
            },
            {
                "q": "J. Michael J Lissner Jr",
                "a": "Michael J. Lissner Jr.",
            },
            {
                "q": "J. J. Lissner",
                "a": "J. J. Lissner",
            },
        ]
        for pair in pairs:
            self.assertEqual(pair["a"], normalize_judge_names(pair["q"]))

    def test_party_type_normalization(self):
        pairs = [
            {
                "q": "Defendant                                 (1)",
                "a": "Defendant",
            },
            {
                "q": "Debtor 2",
                "a": "Debtor",
            },
            {
                "q": "ThirdParty Defendant",
                "a": "Third Party Defendant",
            },
            {
                "q": "ThirdParty Plaintiff",
                "a": "Third Party Plaintiff",
            },
            {
                "q": "3rd Pty Defendant",
                "a": "Third Party Defendant",
            },
            {
                "q": "3rd party defendant",
                "a": "Third Party Defendant",
            },
            {
                "q": "Counter-defendant",
                "a": "Counter Defendant",
            },
            {
                "q": "Counter-Claimaint",
                "a": "Counter Claimaint",
            },
            {
                "q": "US Trustee",
                "a": "U.S. Trustee",
            },
            {
                "q": "United States Trustee",
                "a": "U.S. Trustee",
            },
            {
                "q": "U. S. Trustee",
                "a": "U.S. Trustee",
            },
            {
                "q": "BUS BOY",
                "a": "Bus Boy",
            },
            {
                "q": "JointAdmin Debtor",
                "a": "Jointly Administered Debtor",
            },
            {
                "q": "Intervenor-Plaintiff",
                "a": "Intervenor Plaintiff",
            },
            {
                "q": "Intervenor Dft",
                "a": "Intervenor Defendant",
            },
        ]
        for pair in pairs:
            print(
                "Normalizing PACER type of '%s' to '%s'..."
                % (pair["q"], pair["a"]),
                end="",
            )
            result = normalize_party_types(pair["q"])
            self.assertEqual(result, pair["a"])
            print("✓")
