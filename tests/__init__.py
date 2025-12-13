import unittest
from pathlib import Path

import juriscraper

JURISCRAPER_ROOT = Path(juriscraper.__file__).resolve().parent
TESTS_ROOT = JURISCRAPER_ROOT.parent / "tests"
TESTS_ROOT_EXAMPLES = TESTS_ROOT / "examples"
TESTS_ROOT_EXAMPLES_PACER = TESTS_ROOT_EXAMPLES / "pacer"
TESTS_ROOT_EXAMPLES_LASC = TESTS_ROOT_EXAMPLES / "lasc"
TESTS_ROOT_EXAMPLES_SCOTUS = TESTS_ROOT_EXAMPLES / "scotus"
TESTS_ROOT_EXAMPLES_STATES = TESTS_ROOT_EXAMPLES / "state"


def test_local():
    return unittest.TestLoader().discover("./tests/local")
