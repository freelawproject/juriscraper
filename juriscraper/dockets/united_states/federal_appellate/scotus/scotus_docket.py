"""Downloading and parsing of dockets from the Supreme Court.

Dockets offering a JSON rendering use the following URL naming pattern:

Base URL: https://www.supremecourt.gov/RSS/Cases/JSON/< YY >< DT >< # >.json
Term (YY): Two-digit year of the Supreme Court term beginning in October.
Docket type (DT): One of {'-', 'A', 'M', 'O'}, corresponding to the nature of the
    docket.
    '-': Petitions, typically for writs of certiorari or mandamus
    'A': Applications, not yet reviewed by the Court
    'M': Motions, such as for leave to file as a veteran
    'O': 'Orig.' cases; this designation is unclear and there are few
Case number (#): Two increasing ranges of integers.
    'Paid' cases number from 1 to 4999 in a given term
    'IFP' (in forma pauperis) a.k.a pauper cases number 5001 and up each term
"""

# from concurrent.futures import ThreadPoolExecutor, as_completed
from math import sqrt
from time import sleep

import requests
from requests.exceptions import ConnectionError

from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.exceptions import AccessDeniedError
from .clients import (
    download_client,
    response_handler,
    jitter,
    is_docket,
    is_not_found_page,
    is_stale_content,
)
from . import utils


logger = make_default_logger()


def linear_download(
    docket_numbers: list,
    delay: float = 0.25,
    since_timestamp: str = None,
    fails_allowed: int = 5000,
    **kwargs,
):
    """Iterate over specific docket numbers and yield valid responses.

    :param docket_numbers: List of docket numbers in valid format.
    :param delay: Float value of throttling delay between download attempts.
    """
    base_url = "https://www.supremecourt.gov/RSS/Cases/JSON/{}.json"
    session = requests.Session()

    # store docket not found instances to estimate data endpoint
    not_found = set()
    stale_set = set()
    fresh_set = set()

    # truncate possible values for rate-limiting delay
    trunc_delay = max(0, min(delay, 2.0))

    logger.info("Querying docket numbers...")
    for dn in docket_numbers:
        docketnum = utils.endocket(dn)
        logger.debug(f"Trying docket {docketnum}...")

        # exception handling delegated to downloader
        response = download_client(
            url=base_url.format(docketnum),
            session=session,
            since_timestamp=since_timestamp,
        )
        try:
            valid_response = response_handler(response)
        except (AccessDeniedError, ConnectionError) as e:
            logger.critical(f"Abording download at {docketnum}", exc_info=e)
            raise

        if is_stale_content(valid_response):
            logger.debug(f"{docketnum} returned 304; skipping.")
            stale_set.add(docketnum)
            continue  # no delay
        elif is_docket(valid_response):
            logger.debug(f"Found docket {docketnum}.")
            fresh_set.add(
                (
                    docketnum,
                    utils.makedate(response.headers.get("Last-Modified")),
                )
            )
            yield response
            # delay to rate-limit requests
            sleep(trunc_delay + jitter(sqrt(delay)))
        elif is_not_found_page(valid_response):
            not_found.add(docketnum)
            logger.debug(f"Not found {docketnum}")
            if len(not_found) > fails_allowed:
                # stop downloading when cumulative `fails_allowed` is exceeded
                break
            else:
                # delay to rate-limit requests
                sleep(trunc_delay + jitter(sqrt(delay)))
        else:
            raise RuntimeError(f"Found edge case downloading {docketnum}")

    session.close()

    # log download results
    logger.info(
        f"Finished updating --> {{Updated: {len(fresh_set)}, "
        f"Stale (ignored): {len(stale_set)}, "
        f"'Not Found': {len(not_found)}}}"
    )
    _fs = sorted(list(fresh_set), key=lambda z: utils.docket_priority(z[0]))
    logger.debug(f"Updated dockets: {_fs}")

    _nf = sorted(list(not_found), key=utils.docket_priority)
    logger.debug(f"Not Found: {_nf}")

    _ss = sorted(list(stale_set), key=utils.docket_priority)
    logger.debug(f"Stale dockets: {_ss}")
