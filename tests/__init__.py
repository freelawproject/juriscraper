import os

import juriscraper

JURISCRAPER_ROOT = os.path.realpath(
    os.path.join(
        os.path.realpath(juriscraper.__file__),
        '..'))
TESTS_ROOT = os.path.realpath(os.path.join(JURISCRAPER_ROOT, '../tests'))