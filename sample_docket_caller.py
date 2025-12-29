"""Sample caller for docket scrapers.

Similar to sample_caller.py but designed for DocketSite scrapers that return
structured docket objects instead of opinion-style parallel lists.

Usage:
    python sample_docket_caller.py -c juriscraper.dockets.united_states.state.tex \
        --backscrape --backscrape-start 2025/12/01 --backscrape-end 2025/12/08
"""

import json
import logging
import os
import signal
import sys
from collections import defaultdict
from datetime import date, datetime
from optparse import OptionParser

from juriscraper.lib.importer import build_module_list, site_yielder
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.string_utils import trunc

logger = make_default_logger()
die_now = False


def signal_handler(signal, frame):
    """Handle SIGTERM for graceful shutdown."""
    logger.debug("**************")
    logger.debug("Signal caught. Finishing the current court, then exiting...")
    logger.debug("**************")
    global die_now
    die_now = True


def log_docket(docket: dict, verbosity: int = 0) -> None:
    """Log a docket entry with appropriate detail level.

    Args:
        docket: The docket dictionary to log
        verbosity: 0=summary, 1=details, 2+=full
    """
    court_id = docket.get("court_id", "unknown")
    docket_number = docket.get("docket_number", "unknown")
    case_name = docket.get("case_name", "unknown")
    date_filed = docket.get("date_filed", "unknown")

    if verbosity == 0:
        logger.info(
            "  [%s] %s - %s (%s)",
            court_id,
            docket_number,
            trunc(case_name, 50, ellipsis="..."),
            date_filed,
        )
    else:
        logger.debug("\nDocket: %s", docket_number)
        for key, value in docket.items():
            if isinstance(value, str):
                value = trunc(value, 200, ellipsis="...")
            elif isinstance(value, list) and len(value) > 3:
                value = f"[{len(value)} items]"
            elif isinstance(value, dict):
                value = f"{{...{len(value)} keys...}}"
            logger.debug("    %s: %s", key, value)


def scrape_dockets(site, limit: int = 1000, verbosity: int = 0) -> dict:
    """Process dockets from a DocketSite scraper.

    Args:
        site: The DocketSite instance with parsed dockets
        limit: Maximum number of dockets to process
        verbosity: Logging detail level

    Returns:
        Dictionary with count and any exceptions
    """
    exceptions = defaultdict(list)
    count = 0

    for index, docket in enumerate(site):
        if index >= limit:
            break

        try:
            log_docket(docket, verbosity)
            count += 1
        except Exception as e:
            logger.warning("Error processing docket %d: %s", index, e)
            exceptions["processing"].append(str(e))

    logger.info(
        "\n%s: Successfully processed %d dockets.", site.court_id, count
    )
    return {"count": count, "exceptions": exceptions}


def save_dockets_json(site, output_dir: str = "/tmp/juriscraper/") -> str:
    """Save dockets to a JSON file.

    Args:
        site: The DocketSite instance with parsed dockets
        output_dir: Directory to save the JSON file

    Returns:
        Path to the saved file
    """
    os.makedirs(output_dir, exist_ok=True)

    court = site.court_id.split(".")[-1]
    now_str = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    filename = f"{output_dir}{court}_dockets_{now_str}.json"

    # Convert dates to strings for JSON serialization
    def json_serializer(obj):
        if isinstance(obj, date):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    with open(filename, "w") as f:
        json.dump(list(site.dockets), f, indent=2, default=json_serializer)

    logger.info("Saved %d dockets to %s", len(site.dockets), filename)
    return filename


def save_response(site):
    """Save response content and headers into /tmp/.

    Called after each request if --save-responses is passed.
    """
    now_str = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    court = site.court_id.split(".")[-1]
    response = site.request["response"]
    directory = "/tmp/juriscraper/"
    os.makedirs(directory, exist_ok=True)

    headers_filename = f"{directory}{court}_headers_{now_str}.json"
    with open(headers_filename, "w") as f:
        json.dump(dict(response.headers), f, indent=4)
    logger.debug("Saved headers to %s", headers_filename)

    filename = f"{directory}{court}_content_{now_str}.html"
    with open(filename, "w") as f:
        f.write(response.text)

    logger.info("Saved response to %s", filename)


def main():
    global die_now

    signal.signal(signal.SIGTERM, signal_handler)

    usage = (
        "usage: %prog -c COURTID [options]\n\n"
        "To test Texas dockets for a date range:\n"
        "    python %prog -c juriscraper.dockets.united_states.state.tex "
        "--backscrape --backscrape-start 2025/12/01 --backscrape-end 2025/12/08\n\n"
        "To test all docket scrapers in a directory:\n"
        "    python %prog -c juriscraper.dockets.united_states.state\n\n"
    )
    parser = OptionParser(usage)
    parser.add_option(
        "-c",
        "--courts",
        dest="court_id",
        metavar="COURTID",
        help=(
            "The court(s) to scrape. This should be in "
            "the form of a python module or package import "
            "from the Juriscraper library, e.g. "
            '"juriscraper.dockets.united_states.state.tex"'
        ),
    )
    parser.add_option(
        "-v",
        "--verbosity",
        action="count",
        default=0,
        help=(
            "Increase verbosity. "
            "-v for DEBUG level, -vv for full docket details"
        ),
    )
    parser.add_option(
        "--backscrape",
        dest="backscrape",
        action="store_true",
        default=False,
        help="Download historical dockets using _download_backwards method.",
    )
    parser.add_option(
        "--backscrape-start",
        dest="backscrape_start",
        help="Start date for backscraping (format: YYYY/MM/DD)",
    )
    parser.add_option(
        "--backscrape-end",
        dest="backscrape_end",
        help="End date for backscraping (format: YYYY/MM/DD)",
    )
    parser.add_option(
        "--days-interval",
        dest="days_interval",
        type=int,
        help="Days interval for each backscrape chunk",
    )
    parser.add_option(
        "--save-responses",
        action="store_true",
        default=False,
        help="Save HTTP response headers and HTML to /tmp/juriscraper/",
    )
    parser.add_option(
        "--save-json",
        action="store_true",
        default=False,
        help="Save scraped dockets to JSON file in /tmp/juriscraper/",
    )
    parser.add_option(
        "--limit-per-scrape",
        type=int,
        default=1000,
        help="Maximum dockets to process per scrape (default: 1000)",
    )

    (options, args) = parser.parse_args()

    court_id = options.court_id
    backscrape = options.backscrape
    backscrape_start = options.backscrape_start
    backscrape_end = options.backscrape_end
    days_interval = options.days_interval
    verbosity = options.verbosity
    save_responses = options.save_responses
    save_json = options.save_json
    limit_per_scrape = options.limit_per_scrape

    # Set logging level based on verbosity
    if verbosity == 0:
        logger.setLevel(logging.INFO)
    elif verbosity == 1:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(5)  # TRACE level

    logger.handlers[0].setFormatter(logging.Formatter("%(message)s"))

    if not court_id:
        parser.error("You must specify a court as a package or module.")

    court_id = court_id.replace("/", ".")
    if court_id.endswith(".py"):
        court_id = court_id[:-3]

    module_strings = build_module_list(court_id)
    if len(module_strings) == 0:
        parser.error("Unable to import module or package. Aborting.")

    logger.info("Starting docket scraper.")

    total_dockets = 0

    for module_string in module_strings:
        if die_now:
            logger.debug("Scraper stopped by signal.")
            sys.exit(1)

        package, module = module_string.rsplit(".", 1)
        logger.info("\nProcessing: %s.%s", package, module)

        mod = __import__(f"{package}.{module}", globals(), locals(), [module])

        site_kwargs = {}
        if save_responses:
            site_kwargs["save_response_fn"] = save_response

        if backscrape:
            bs_iterable = mod.Site(
                backscrape_start=backscrape_start,
                backscrape_end=backscrape_end,
                days_interval=days_interval,
            ).back_scrape_iterable

            if not bs_iterable:
                logger.warning("No backscrape iterable created. Skipping.")
                continue

            logger.info("Backscraping %d date ranges...", len(bs_iterable))

            for site in site_yielder(bs_iterable, mod, **site_kwargs):
                if die_now:
                    break

                site.parse()
                result = scrape_dockets(site, limit_per_scrape, verbosity)
                total_dockets += result["count"]

                if save_json and site.dockets:
                    save_dockets_json(site)
        else:
            site = mod.Site(**site_kwargs)
            site.parse()
            result = scrape_dockets(site, limit_per_scrape, verbosity)
            total_dockets += result["count"]

            if save_json and site.dockets:
                save_dockets_json(site)

    logger.info("\n" + "=" * 60)
    logger.info("Scraping complete. Total dockets: %d", total_dockets)
    logger.info("=" * 60)

    sys.exit(0)


if __name__ == "__main__":
    main()
