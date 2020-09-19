#!/usr/bin/env python
# coding=utf-8


import unittest
from datetime import date

from juriscraper.lib.utils import clean_court_object
from juriscraper.pacer.utils import (
    get_court_id_from_url,
    get_pacer_case_id_from_nonce_url,
    get_pacer_doc_id_from_doc1_url,
    make_doc1_url,
    reverse_goDLS_function,
)


class PacerUtilTest(unittest.TestCase):
    """A variety of tests of our simple utilities."""

    def test_getting_case_id_from_urls(self):
        qa_pairs = (
            ("https://ecf.almd.uscourts.gov/cgi-bin/DktRpt.pl?56120", "56120"),
            (
                "https://ecf.azb.uscourts.gov/cgi-bin/iquery.pl?625371913403797-L_9999_1-0-663150",
                "663150",
            ),
            (
                "https://ecf.canb.uscourts.gov/cgi-bin/iquery.pl?382858949667811-L_1_0-0-12612",
                "12612",
            ),
        )
        for q, a in qa_pairs:
            self.assertEqual(get_pacer_case_id_from_nonce_url(q), a)

    def test_getting_court_id_from_url(self):
        qa_pairs = (
            ("https://ecf.almd.uscourts.gov/cgi-bin/DktRpt.pl?56120", "almd"),
        )
        for q, a in qa_pairs:
            self.assertEqual(get_court_id_from_url(q), a)

    def test_get_pacer_document_number_from_doc1_url(self):
        qa_pairs = (
            ("https://ecf.almd.uscourts.gov/doc1/01712427473", "01702427473"),
            ("/doc1/01712427473", "01702427473"),
            (
                "https://ecf.akb.uscourts.gov/doc1/02201247000?caseid=7738&de_seq_num=723284&dm_id=1204742&doc_num=8805&pdf_header=0",
                "02201247000",
            ),
        )
        for q, a in qa_pairs:
            self.assertEqual(get_pacer_doc_id_from_doc1_url(q), a)

    def test_reverse_dls_function(self):
        """Can we parse the javascript correctly to get a good dict?"""
        qa_pairs = (
            (
                "goDLS('/doc1/01712427473','56121','69','','','1','','');return(false);",
                {
                    "form_post_url": "/doc1/01712427473",
                    "caseid": "56121",
                    "de_seq_num": "69",
                    "got_receipt": "",
                    "pdf_header": "",
                    "pdf_toggle_possible": "1",
                    "magic_num": "",
                    "hdr": "",
                },
            ),
        )
        for q, a in qa_pairs:
            self.assertEqual(reverse_goDLS_function(q), a)

    def test_make_doc1_url(self):
        """Can we make good doc1 urls?"""
        qa_pairs = (
            (
                ("cand", "01712427473", False),
                "https://ecf.cand.uscourts.gov/doc1/01712427473",
            ),
            (
                ("cand", "01702427473", False),
                "https://ecf.cand.uscourts.gov/doc1/01702427473",
            ),
            (
                ("cand", "01712427473", True),
                "https://ecf.cand.uscourts.gov/doc1/01712427473",
            ),
            (
                ("cand", "01702427473", True),
                "https://ecf.cand.uscourts.gov/doc1/01712427473",
            ),
        )
        for q, a in qa_pairs:
            self.assertEqual(make_doc1_url(*q), a)

    def test_clean_pacer_objects(self):
        """Can we properly clean various types of data?"""
        tests = (
            {
                # Basic string
                "q": "asdf , asdf",
                "a": "asdf, asdf",
            },
            {
                # Basic list
                "q": ["asdf , asdf", "sdfg , sdfg"],
                "a": ["asdf, asdf", "sdfg, sdfg"],
            },
            {
                # Basic dict
                "q": {"a": "asdf , asdf"},
                "a": {"a": "asdf, asdf"},
            },
            {
                # Nested dict in a list with a string
                "q": [{"a": "asdf , asdf"}, "asdf , asdf"],
                "a": [{"a": "asdf, asdf"}, "asdf, asdf"],
            },
            {
                # Multi-deep nest
                "q": {"a": ["asdf, asdf", "asdf", {"a": "asdf  , asdf"}]},
                "a": {"a": ["asdf, asdf", "asdf", {"a": "asdf, asdf"}]},
            },
            {
                # Date object
                "q": [date(2017, 5, 5), "asdf , asdf"],
                "a": [date(2017, 5, 5), "asdf, asdf"],
            },
            {
                # Stripping and normalizing whitespace junk
                "q": [" asdf , asdf\n  asdf"],
                "a": ["asdf, asdf asdf"],
            },
        )
        for test in tests:
            self.assertEqual(clean_court_object(test["q"]), test["a"])
