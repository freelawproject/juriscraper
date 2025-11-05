import hashlib
import json
import logging
import os
import re
import signal
import sys
import webbrowser
from collections import defaultdict
from datetime import datetime
from optparse import OptionParser
from urllib import parse

import requests

from juriscraper.lib.exceptions import BadContentError
from juriscraper.lib.importer import build_module_list, site_yielder
from juriscraper.lib.log_tools import make_default_logger
from juriscraper.lib.microservices_utils import (
    MICROSERVICE_URLS,
    get_extension,
)
from juriscraper.lib.string_utils import trunc

logger = make_default_logger()
die_now = False


def signal_handler(signal, frame):
    # Trigger this with CTRL+4
    logger.debug("**************")
    logger.debug("Signal caught. Finishing the current court, then exiting...")
    logger.debug("**************")
    global die_now
    die_now = True


# Copied from django
def force_bytes(s, encoding="utf-8", strings_only=False, errors="strict"):
    """
    Similar to smart_bytes, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    # Handle the common case first for performance reasons.
    if isinstance(s, bytes):
        if encoding == "utf-8":
            return s
        else:
            return s.decode("utf-8", errors).encode(encoding, errors)
    if isinstance(s, memoryview):
        return bytes(s)
    return str(s).encode(encoding, errors)


# Copied from Courtlistener
def sha1(s):
    """Return the sha1sum of a string.

    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    ! This algorithm is obsolete for most purposes. Its !
    ! usage is discouraged. Please use SHA256 instead.  !
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    :param s: The data to hash. Ideally bytes, but if unicode is passed in, it
    will convert it to bytes first.
    :return: a hexadecimal SHA1 hash of the data
    """
    if isinstance(s, str):
        s = s.encode()
    sha1sum = hashlib.sha1()
    sha1sum.update(s)
    return sha1sum.hexdigest()


def log_dict(dic: dict) -> None:
    """Logs key-value pairs from a dictionary,
    truncating string values
    """
    for k, v in dic.items():
        if isinstance(v, str):
            v = trunc(v, 200, ellipsis="...")
        logger.debug('    %s: "%s"', k, v)


def extract_doc_content(
    data, extract_from_text: bool, site, doctor_host: str, filename: str
):
    """Extracts document's content using a local doctor host

    For complete and integrated testing, use the Courtlistener caller
    from a docker compose environment

    :param data: the response content
    :param extract_from_text: if True, extract doc content using doctor
        if False, return content as is
    :param site: current site object
    :param doctor_host: local doctor instance host. calls will fail if
        the doctor host is not valid
    :param filename: Name for saving extracted content into a file in tmp

    :return: a tuple with:
        the extracted content
        the structured metadata parsed by Site.extract_from_text
    """
    if not extract_from_text:
        return data, {}

    extension = get_extension(data)

    files = {"file": (f"something.{extension}", data)}
    url = MICROSERVICE_URLS["document-extract"].format(doctor_host)
    extraction__response = requests.post(url, files=files, timeout=120)
    extraction__response.raise_for_status()
    extracted_content = extraction__response.json()["content"]

    # The extracted content is embedded for display in Courtlistener.
    # We save it into /tmp/ to have an idea how it would look. You can
    # inspect it your browser by going into f'file://tmp/juriscraper/{filename}.html'
    court_id = site.court_id.split(".")[-1]
    directory = "/tmp/juriscraper/"
    os.makedirs(directory, exist_ok=True)
    # remove illegal characters
    illegal_chars = r'[\/:*?"<>|]'
    filename = re.sub(illegal_chars, "_", filename)

    # save raw data for inspection; useful for looking for hash-duplicating
    # timestamps. Open it in a code editor; the browser will auto correct
    # bad HTML elements; or execute some javascript
    filepath_raw_data = (
        f"{directory}{court_id}_{filename}_downloaded.{extension}"
    )
    with open(filepath_raw_data, "wb") as f:
        f.write(data)

    logger.info(
        "\nOpen downloaded content with 'file://%s'", filepath_raw_data
    )

    filepath = f"{directory}{court_id}_{filename}.html"
    with open(filepath, "w") as f:
        if extension != ".html":
            f.write(f"<pre>{extracted_content}</pre>")
        else:
            f.write(extracted_content)

    logger.info("\nOpen extracted content with 'file://%s'", filepath)

    cleaned_extracted_text = site.cleanup_extracted_text(extracted_content)

    metadata_dict = site.extract_from_text(cleaned_extracted_text)
    return cleaned_extracted_text, metadata_dict


def check_hashes(data: bytes, download_url: str, site) -> None:
    """Detect timestamped content by downloading the same URL twice and
    comparing hashes

    :param data: data downloaded on the regular loop
    :param download_url: the URL to get the same data as in the first argument
    :param site: the site object
    """
    datas = [data, site.download_content(download_url)]
    hashes = []

    for data in datas:
        sha_before = sha1(force_bytes(data))
        data = site.cleanup_content(data)
        sha_after = sha1(force_bytes(data))

        # useful for double checking if a Site.cleanup_content is working
        # If implemented properly, the hash should change
        if sha_before == sha_after:
            logger.warning("SHA has NOT changed after `Site.cleanup_content`")
        else:
            logger.info(
                "SHA has changed after `Site.cleanup_content`. It's OK"
            )

        hashes.append(sha_after)

    if hashes[0] != hashes[1]:
        logger.warning(
            "Same URL hashes are not the same. Check the document for timestamps"
        )
    else:
        logger.info("Same URL hashes are the same. It's OK")


def scrape_court(
    site,
    binaries=False,
    extract_content=False,
    doctor_host="",
    test_hashes: bool = False,
    limit: int = 1000,
):
    """Calls the requested court(s), gets its binary content, and
    extracts the content if possible. See --extract-content option

    Note that this is a very basic caller lacking important functionality, such
    as:
     - checking whether the HTML of the page has changed since last visited
     - checking whether the downloaded content is already in your data store

    Nonetheless, this caller is useful for testing, and for demonstrating some
    basic pitfalls that a caller will run into.
    """
    exceptions = defaultdict(list)
    for index, item in enumerate(site):
        if index == limit:
            break
        # First turn the download urls into a utf-8 byte string
        item_download_urls = item["download_urls"].encode("utf-8")
        # Percent encode URLs (this is a Python wart)
        download_url = parse.quote(
            item_download_urls, safe="%/:=&?~#+!$,;'@()*[]"
        )

        # Normally, you'd do your save routines here...
        logger.debug("\nAdding new item:")
        log_dict(item)

        if not binaries:
            continue

        try:
            data = site.download_content(
                download_url, doctor_is_available=extract_content
            )
        except BadContentError:
            continue

        if test_hashes:
            check_hashes(data, download_url, site)

        filename = item["case_names"].lower().replace(" ", "_")[:40]

        data, metadata_from_text = extract_doc_content(
            data, extract_content, site, doctor_host, filename
        )
        logger.log(
            5, "\nShowing extracted document data (500 chars):\n%s", data[:500]
        )

        if metadata_from_text:
            logger.debug("\nValues obtained by Site.extract_from_text:")
            for object_type, value_dict in metadata_from_text.items():
                logger.debug(object_type)
                if object_type != "Citation":
                    log_dict(value_dict)
                else:
                    logger.debug(value_dict)

        # Separate cases for easier reading when verbosity=DEBUG
        logger.debug("\n%s\n", "=" * 60)

    logger.info(
        "\n%s: Successfully crawled %s items.", site.court_id, len(site)
    )
    return {"count": len(site), "exceptions": exceptions}


def save_response(site):
    """
    Save response content and headers into /tmp/

    This will be called after each `Site._request_url_get`
    or `Site._request_url_post`, if the --save-responses
    optional flag was passed
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

    try:
        # Brute force test to see if it's a JSON
        json_data = json.loads(response.content)
    except Exception:
        json_data = None

    if json_data:
        filename = f"{directory}{court}_content_{now_str}.json"
        with open(filename, "w") as f:
            json.dump(json_data, f, indent=4)
    else:
        filename = f"{directory}{court}_content_{now_str}.html"
        with open(filename, "w") as f:
            f.write(response.text)

    logger.info("Saved response to %s", filename)

    if response.history:
        logger.info("Response history: %s", response.history)

    # open the tmp file in the browser
    webbrowser.open(f"file://{filename}")


def main():
    global die_now

    # this line is used for handling SIGTERM (CTRL+4), so things can die safely
    signal.signal(signal.SIGTERM, signal_handler)

    usage = (
        "usage: %prog -c COURTID [-d|--daemon] [-b|--binaries]\n\n"
        "To test ca1, downloading binaries, use: \n"
        "    python %prog -c juriscraper.opinions.united_states.federal_appellate.ca1 -b\n\n"
        "To test all federal courts, omitting binaries, use: \n"
        "    python %prog -c juriscraper.opinions.united_states.federal_appellate\n\n"
    )
    parser = OptionParser(usage)
    parser.add_option(
        "-c",
        "--courts",
        dest="court_id",
        metavar="COURTID",
        help=(
            "The court(s) to scrape and extract. This should be in "
            "the form of a python module or package import "
            "from the Juriscraper library, e.g. "
            '"juriscraper.opinions.united_states.federal.ca1" or '
            'simply "opinions" to do all opinions. If desired, '
            "you can use slashes instead of dots to separate"
            "the import path."
        ),
    )
    parser.add_option(
        "-b",
        "--download_binaries",
        action="store_true",
        dest="binaries",
        default=False,
        help=(
            "Use this flag if you wish to download the pdf, "
            "wpd, and doc files."
        ),
    )
    parser.add_option(
        "--extract-content",
        action="store_true",
        default=False,
        help=(
            "Extract document's content using `doctor`. "
            "Then, execute Site.extract_from_text method. "
            "If this flag is set to True, it will "
            "make `binaries` True, too. This requires "
            "having a running `doctor` instance"
        ),
    )
    parser.add_option(
        "--doctor-host",
        default=os.environ.get(
            "JURISCRAPER_DOCTOR_HOST", "http://0.0.0.0:5050"
        ),
        help=(
            "Customize `doctor` host. The default is the host used "
            "by the doctor docker image. May be set via environment "
            "variable `JURISCRAPER_DOCTOR_HOST`. If running directly "
            "on a local env, you can make the default work by running "
            "`python manage.py runserver 5050` on your doctor Django folder"
        ),
    )

    parser.add_option(
        "-v",
        "--verbosity",
        action="count",
        default=0,
        help=(
            "Default verbosity=0 will use log level INFO. "
            "Passing -v will set log level to DEBUG"
        ),
    )
    parser.add_option(
        "--backscrape",
        dest="backscrape",
        action="store_true",
        default=False,
        help="Download the historical corpus using the _download_backwards method.",
    )
    parser.add_option(
        "--backscrape-start",
        dest="backscrape_start",
        help="Starting value for backscraper iterable creation",
    )
    parser.add_option(
        "--backscrape-end",
        dest="backscrape_end",
        help="End value for backscraper iterable creation",
    )
    parser.add_option(
        "--days-interval",
        dest="days_interval",
        help="Days interval size for each backscrape iterable tuple",
        type=int,
    )
    parser.add_option(
        "--save-responses",
        action="store_true",
        default=False,
        help="Save response headers and returned HTML or JSON",
    )
    parser.add_option(
        "--test-hashes",
        action="store_true",
        default=False,
        help=(
            "Download the opionion twice and compute hashes to detect "
            "timestamped content. Also useful to see if Site.cleanup_content"
            " works (hash should change)"
        ),
    )
    parser.add_option(
        "--limit-per-scrape",
        type=int,
        default=1000,
        help="How many items to scrape per `scrape_court` call",
    )

    (options, args) = parser.parse_args()

    court_id = options.court_id
    backscrape = options.backscrape
    backscrape_start = options.backscrape_start
    backscrape_end = options.backscrape_end
    days_interval = options.days_interval
    binaries = options.binaries
    doctor_host = options.doctor_host
    extract_content = options.extract_content
    verbosity = options.verbosity
    save_responses = options.save_responses
    test_hashes = options.test_hashes
    limit_per_scrape = options.limit_per_scrape

    if test_hashes:
        binaries = True

    if extract_content:
        binaries = True
        # If we are making the effort of downloading documents
        # we should force the user to actually see the outputs
        verbosity = verbosity if verbosity else 1

    if verbosity == 0:
        # default level will only show that the scrapers are working
        logger.setLevel(logging.INFO)
    elif verbosity == 1:
        logger.setLevel(logging.DEBUG)
    elif verbosity > 1:
        # Lower value than logging.DEBUG, used only to print out
        # the extracted content first 500 characters
        logger.setLevel(5)

    # use the easiest to read format
    logger.handlers[0].setFormatter(logging.Formatter("%(message)s"))

    if not court_id:
        parser.error("You must specify a court as a package or module.")
    else:
        court_id = court_id.replace("/", ".")
        if court_id.endswith(".py"):
            court_id = court_id[:-3]

        module_strings = build_module_list(court_id)
        if len(module_strings) == 0:
            parser.error("Unable to import module or package. Aborting.")

        logger.debug("Starting up the scraper.")
        for module_string in module_strings:
            # this catches SIGINT, so the code can be killed safely.
            if die_now:
                logger.debug("The scraper has stopped.")
                sys.exit(1)

            package, module = module_string.rsplit(".", 1)
            logger.debug("Current court: %s.%s", package, module)

            mod = __import__(
                f"{package}.{module}", globals(), locals(), [module]
            )

            site_kwargs = {}
            if save_responses:
                site_kwargs = {"save_response_fn": save_response}

            if backscrape:
                bs_iterable = mod.Site(
                    backscrape_start=backscrape_start,
                    backscrape_end=backscrape_end,
                    days_interval=days_interval,
                ).back_scrape_iterable
                sites = site_yielder(bs_iterable, mod, **site_kwargs)
            else:
                sites = [mod.Site(**site_kwargs)]

            for site in sites:
                site.parse()
                scrape_court(
                    site,
                    binaries,
                    extract_content,
                    doctor_host,
                    test_hashes,
                    limit_per_scrape,
                )

    logger.debug("The scraper has stopped.")

    sys.exit(0)


if __name__ == "__main__":
    main()
