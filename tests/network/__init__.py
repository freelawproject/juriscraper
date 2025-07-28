import os
import unittest

from juriscraper.pacer.http import PacerSession

PACER_USERNAME = os.environ.get("PACER_USERNAME", None)
PACER_PASSWORD = os.environ.get("PACER_PASSWORD", None)
PACER_SETTINGS_MSG = (
    "Skipping test. Please set PACER_USERNAME and "
    "PACER_PASSWORD environment variables to run this test."
)
SKIP_IF_NO_PACER_LOGIN = unittest.skipUnless(
    (PACER_USERNAME and PACER_PASSWORD), reason=PACER_SETTINGS_MSG
)


def pacer_credentials_are_defined():
    return bool(PACER_USERNAME and PACER_PASSWORD)


def get_pacer_session():
    return PacerSession(username=PACER_USERNAME, password=PACER_PASSWORD)
