"""Sample caller for BaseStateScraper subclasses.

Similar to sample_caller.py but designed for BaseStateScraper subclasses that
use generators to yield structured docket objects.

Usage:
    python sample_state_scraper_caller.py -s juriscraper.state.texas.tames.TAMESScraper \
        --start 2025/12/01 --end 2025/12/08

    python sample_state_scraper_caller.py -s juriscraper.state.texas.TAMESScraper \
        --backfill --start 2025/01/01 --end 2025/12/31
"""

import json
import logging
import os
import signal
import sys
from datetime import date, datetime
from optparse import OptionParser

import requests

from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.string_utils import trunc
from juriscraper.state.BaseStateScraper import ScraperRequestManager

logger = make_default_logger()
die_now = False


def signal_handler(signal, frame):
    """Handle SIGTERM for graceful shutdown."""
    logger.debug("**************")
    logger.debug("Signal caught. Exiting after current item...")
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


def parse_date(date_str: str) -> date:
    """Parse a date string in YYYY/MM/DD or YYYY-MM-DD format.

    Args:
        date_str: Date string to parse

    Returns:
        Parsed date object
    """
    date_str = date_str.replace("/", "-")
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def save_response_callback(
    request_manager: ScraperRequestManager,
    response: requests.Response,
) -> None:
    """Save response content and headers to /tmp/.

    This is a callback function passed to ScraperRequestManager.

    Args:
        request_manager: The request manager instance
        response: The HTTP response object
    """
    now_str = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    directory = "/tmp/juriscraper/"
    os.makedirs(directory, exist_ok=True)

    # Save headers
    headers_filename = f"{directory}state_headers_{now_str}.json"
    with open(headers_filename, "w") as f:
        json.dump(dict(response.headers), f, indent=4)
    logger.debug("Saved headers to %s", headers_filename)

    # Save content
    try:
        json_data = response.json()
        filename = f"{directory}state_content_{now_str}.json"
        with open(filename, "w") as f:
            json.dump(json_data, f, indent=4)
    except Exception:
        filename = f"{directory}state_content_{now_str}.html"
        with open(filename, "w") as f:
            f.write(response.text)

    logger.info("Saved response to %s", filename)


def save_dockets_json(
    dockets: list,
    scraper_name: str,
    output_dir: str = "/tmp/juriscraper/",
) -> str:
    """Save dockets to a JSON file.

    Args:
        dockets: List of docket dictionaries
        scraper_name: Name of the scraper for the filename
        output_dir: Directory to save the JSON file

    Returns:
        Path to the saved file
    """
    os.makedirs(output_dir, exist_ok=True)

    now_str = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    filename = f"{output_dir}{scraper_name}_dockets_{now_str}.json"

    # Convert dates to strings for JSON serialization
    def json_serializer(obj):
        if isinstance(obj, date):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    with open(filename, "w") as f:
        json.dump(dockets, f, indent=2, default=json_serializer)

    logger.info("Saved %d dockets to %s", len(dockets), filename)
    return filename


def import_scraper_class(class_path: str):
    """Import a scraper class from a module path.

    Args:
        class_path: Full path like 'juriscraper.state.texas.tames.TAMESScraper'

    Returns:
        The scraper class
    """
    parts = class_path.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(
            f"Invalid class path: {class_path}. "
            "Expected format: 'module.path.ClassName'"
        )

    module_path, class_name = parts
    module = __import__(module_path, globals(), locals(), [class_name])
    return getattr(module, class_name)


def main():
    global die_now

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    usage = (
        "usage: %prog -s SCRAPER_CLASS [options]\n\n"
        "To scrape Texas dockets for a date range:\n"
        "    python %prog -s juriscraper.state.texas.tames.TAMESScraper "
        "--start 2025/12/01 --end 2025/12/08\n\n"
        "To backfill Texas dockets:\n"
        "    python %prog -s juriscraper.state.texas.TAMESScraper "
        "--backfill --start 2025/01/01 --end 2025/12/31\n\n"
    )
    parser = OptionParser(usage)
    parser.add_option(
        "-s",
        "--scraper",
        dest="scraper_class",
        metavar="SCRAPER_CLASS",
        help=(
            "The scraper class to use. This should be a full Python import "
            "path including the class name, e.g. "
            '"juriscraper.state.texas.tames.TAMESScraper"'
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
        "--start",
        dest="start_date",
        help="Start date (format: YYYY/MM/DD or YYYY-MM-DD)",
    )
    parser.add_option(
        "--end",
        dest="end_date",
        help="End date (format: YYYY/MM/DD or YYYY-MM-DD)",
    )
    parser.add_option(
        "--backfill",
        dest="backfill",
        action="store_true",
        default=False,
        help="Use the backfill method instead of scrape.",
    )
    parser.add_option(
        "--courts",
        dest="courts",
        help=(
            "Comma-separated list of court identifiers for backfill "
            "(e.g., 'cossup,coscca,coa01'). Empty for all courts."
        ),
    )
    parser.add_option(
        "--days-interval",
        dest="days_interval",
        type=int,
        help="Days interval for each backfill chunk (scraper-specific default if not set)",
    )
    parser.add_option(
        "--save-responses",
        action="store_true",
        default=False,
        help="Save HTTP response headers and content to /tmp/juriscraper/",
    )
    parser.add_option(
        "--save-json",
        action="store_true",
        default=False,
        help="Save scraped dockets to JSON file in /tmp/juriscraper/",
    )
    parser.add_option(
        "--limit",
        type=int,
        default=0,
        help="Maximum dockets to process (0 for unlimited, default: 0)",
    )

    (options, args) = parser.parse_args()

    scraper_class_path = options.scraper_class
    verbosity = options.verbosity
    start_date_str = options.start_date
    end_date_str = options.end_date
    backfill = options.backfill
    courts_str = options.courts
    days_interval = options.days_interval
    save_responses = options.save_responses
    save_json = options.save_json
    limit = options.limit

    # Set logging level based on verbosity
    if verbosity == 0:
        logger.setLevel(logging.INFO)
    elif verbosity == 1:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(5)  # TRACE level

    logger.handlers[0].setFormatter(logging.Formatter("%(message)s"))

    if not scraper_class_path:
        parser.error("You must specify a scraper class with -s.")

    # Parse dates
    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = parse_date(start_date_str)
        except ValueError as e:
            parser.error(f"Invalid start date: {e}")
    if end_date_str:
        try:
            end_date = parse_date(end_date_str)
        except ValueError as e:
            parser.error(f"Invalid end date: {e}")

    # Parse courts list
    courts = []
    if courts_str:
        courts = [c.strip() for c in courts_str.split(",") if c.strip()]

    # Import the scraper class
    try:
        ScraperClass = import_scraper_class(scraper_class_path)
    except (ImportError, AttributeError, ValueError) as e:
        parser.error(f"Failed to import scraper class: {e}")

    logger.info("Starting state scraper: %s", scraper_class_path)

    # Create request manager with optional response callback
    request_manager_kwargs = {}
    if save_responses:
        request_manager_kwargs["all_response_fn"] = save_response_callback

    request_manager = ScraperRequestManager(**request_manager_kwargs)

    # Create scraper instance
    scraper_kwargs = {"request_manager": request_manager}
    if days_interval is not None:
        scraper_kwargs["days_interval"] = days_interval

    try:
        scraper = ScraperClass(**scraper_kwargs)
    except TypeError as e:
        # Some scrapers might not accept all kwargs
        logger.warning("Scraper initialization warning: %s", e)
        scraper = ScraperClass(request_manager=request_manager)

    scraper_name = ScraperClass.__name__

    # Run the scraper
    total_dockets = 0
    all_dockets = []

    try:
        if backfill:
            if start_date is None or end_date is None:
                parser.error(
                    "--backfill requires both --start and --end dates"
                )

            logger.info(
                "Backfilling from %s to %s (courts: %s)",
                start_date,
                end_date,
                courts if courts else "all",
            )

            generator = scraper.backfill(courts, (start_date, end_date))
        else:
            logger.info(
                "Scraping from %s to %s",
                start_date or "default",
                end_date or "default",
            )

            # Call scrape with available parameters
            scrape_kwargs = {}
            if start_date is not None:
                scrape_kwargs["start_date"] = start_date
            if end_date is not None:
                scrape_kwargs["end_date"] = end_date

            generator = scraper.scrape(**scrape_kwargs)

        # Process the generator
        for docket in generator:
            if die_now:
                logger.info("Stopping due to signal...")
                break

            if limit > 0 and total_dockets >= limit:
                logger.info("Reached limit of %d dockets", limit)
                break

            try:
                log_docket(docket, verbosity)
                total_dockets += 1

                if save_json:
                    all_dockets.append(docket)

            except Exception as e:
                logger.warning(
                    "Error processing docket: %s",
                    e,
                    exc_info=logger.isEnabledFor(logging.DEBUG),
                )

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user.")
    except Exception as e:
        logger.error(
            "Scraper error: %s",
            e,
            exc_info=logger.isEnabledFor(logging.DEBUG),
        )
    finally:
        # Save JSON if requested
        if save_json and all_dockets:
            save_dockets_json(all_dockets, scraper_name)

    logger.info("\n" + "=" * 60)
    logger.info("Scraping complete. Total dockets: %d", total_dockets)
    logger.info("=" * 60)

    sys.exit(0)


if __name__ == "__main__":
    main()
