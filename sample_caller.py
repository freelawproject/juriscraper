import os
import signal
import sys
import traceback
from collections import defaultdict
from optparse import OptionParser
from urllib import parse

import requests

from juriscraper.lib.importer import build_module_list, site_yielder
from juriscraper.lib.string_utils import trunc
from juriscraper.report import generate_scraper_report

die_now = False
MICROSERVICE_URLS = {
    # Extractor Endpoints
    "document-extract": {
        "url": "{}/extract/doc/text/",
    },
    "document-extract-ocr": {
        "url": "{}/extract/doc/text/",
    },
    "recap-extract": {
        "url": "{}/extract/recap/text/",
    },
    # Utils Endpoints
    "page-count": {
        "url": "{}/utils/page-count/pdf/",
    },
    "audio-duration": {
        "url": "{}/utils/audio/duration/",
    },
    "mime-type": {
        "url": "{}/utils/mime-type/",
    },
    "buffer-extension": {
        "url": "{}/utils/file/extension/",
    },
    "document-number": {
        "url": "{}/utils/document-number/pdf/",
    },
    # Converter Endpoints
    "generate-thumbnail": {
        "url": "{}/convert/pdf/thumbnail/",
    },
    "images-to-pdf": {
        "url": "{}/convert/images/pdf/",
    },
    "convert-audio": {
        "url": "{}/convert/audio/mp3/",
    },
    "downsize-audio": {
        "url": "{}/convert/audio/ogg/",
    },
}


def signal_handler(signal, frame):
    # Trigger this with CTRL+4
    v_print(3, "**************")
    v_print(3, "Signal caught. Finishing the current court, then exiting...")
    v_print(3, "**************")
    global die_now
    die_now = True


def print_dict(dic: dict):
    for k, v in dic.items():
        if isinstance(v, str):
            value = trunc(v, 200, ellipsis="...")
            v_print(1, f'    {k}: "{value}"')
        else:
            # Dates and such...
            v_print(1, f"    {k}: {v}")


def extract_doc_content(
    data, extract_from_text: bool, site, doctor_host: str, filename: str
):
    """Extracts document's content using a local doctor host

    For complete and integrated testing, run in a Courtlistener
    docker compose environment

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

    # Get the file type from the document's raw content
    extension_url = MICROSERVICE_URLS["buffer-extension"]["url"].format(
        doctor_host
    )
    extension_response = requests.post(
        extension_url, files={"file": ("filename", data)}, timeout=30
    )
    extension_response.raise_for_status()
    extension = extension_response.text

    # For HTML files, the extracted document may have modified tags
    files = {"file": (f"something.{extension}", data)}
    url = MICROSERVICE_URLS["document-extract"]["url"].format(doctor_host)
    extraction__response = requests.post(url, files=files, timeout=120)
    extraction__response.raise_for_status()
    extracted_content = extraction__response.json()["content"]

    # The extracted content is embeded for display in Courtlistener
    # We save it into /tmp/ to have an idea how it would look. You can
    # inspect it your browser by going into f'file://tmp/{filename}.html'
    court_id = site.court_id.split(".")[-1]
    with open(f"/tmp/{court_id}_{filename}.html", "w") as f:
        print(extension)
        if extension != ".html":
            f.write(f"<pre>{extracted_content}</pre>")
        else:
            f.write(extracted_content)

    metadata_dict = site.extract_from_text(extracted_content)
    return extracted_content, metadata_dict


def scrape_court(site, binaries=False, extract_content=False, doctor_host=""):
    """Calls the requested court(s), gets its content, then throws it away.

    Note that this is a very basic caller lacking important functionality, such
    as:
     - checking whether the HTML of the page has changed since last visited
     - checking whether the downloaded content is already in your data store
     - saving anything at all

    Nonetheless, this caller is useful for testing, and for demonstrating some
    basic pitfalls that a caller will run into.
    """
    exceptions = defaultdict(list)
    for item in site:
        # First turn the download urls into a utf-8 byte string
        item_download_urls = item["download_urls"].encode("utf-8")
        # Percent encode URLs (this is a Python wart)
        download_url = parse.quote(
            item_download_urls, safe="%/:=&?~#+!$,;'@()*[]"
        )

        # Normally, you'd do your save routines here...
        v_print(1, "\nAdding new item:")
        print_dict(item)

        if not binaries:
            continue

        try:
            # some sites require a custom ssl_context, contained in the Site's
            # session. However, we can't send a request with both a
            # custom ssl_context and `verify = False`
            has_cipher = hasattr(site, "cipher")
            s = site.request["session"] if has_cipher else requests.session()

            if site.needs_special_headers:
                headers = site.request["headers"]
            else:
                headers = {"User-Agent": "CourtListener"}

            # Note that we do a GET even if site.method is POST. This is
            # deliberate.
            r = s.get(
                download_url,
                verify=has_cipher,  # WA has a certificate we don't understand
                headers=headers,
                cookies=site.cookies,
                timeout=300,
            )

            # test for expected content type (thanks mont for nil)
            if site.expected_content_types:
                # Clean up content types like "application/pdf;charset=utf-8"
                # and 'application/octet-stream; charset=UTF-8'
                content_type = (
                    r.headers.get("Content-Type").lower().split(";")[0].strip()
                )
                m = any(
                    content_type in mime.lower()
                    for mime in site.expected_content_types
                )
                if not m:
                    exceptions["DownloadingError"].append(download_url)
                    v_print(3, f"DownloadingError: {download_url}")
                    v_print(3, traceback.format_exc())

            data = r.content

            # test for empty files (thank you CA1)
            if len(data) == 0:
                exceptions["EmptyFileError"].append(download_url)
                v_print(3, f"EmptyFileError: {download_url}")
                v_print(3, traceback.format_exc())
                continue
        except Exception:
            exceptions["DownloadingError"].append(download_url)
            v_print(3, f"DownloadingError: {download_url}")
            v_print(3, traceback.format_exc())
            continue

        filename = item["case_names"].lower().replace(" ", "_")
        # cleanup_content is called before the extraction task in CL
        # so it is only useful for cleaning HTML files
        data = site.cleanup_content(data)
        data, metadata_from_text = extract_doc_content(
            data, extract_content, site, doctor_host, filename
        )
        v_print(
            3,
            f"Showing extracted document data (500 chars):\n {data[:500]}\n{'='*40}",
        )

        if metadata_from_text:
            v_print(3, "Values obtained by Site.extract_from_text:")
            for object_type, value_dict in metadata_from_text.items():
                v_print(3, object_type)
                print_dict(value_dict)

    v_print(3, f"\n{site.court_id}: Successfully crawled {len(site)} items.")
    return {"count": len(site), "exceptions": exceptions}


v_print = None


def main():
    global die_now

    # this line is used for handling SIGTERM (CTRL+4), so things can die safely
    signal.signal(signal.SIGTERM, signal_handler)

    usage = (
        "usage: %prog -c COURTID [-d|--daemon] [-b|--binaries] [-r|--report]\n\n"
        "To test ca1, downloading binaries, use: \n"
        "    python %prog -c juriscraper.opinions.united_states.federal_appellate.ca1 -b\n\n"
        "To test all federal courts, omitting binaries, use: \n"
        "    python %prog -c juriscraper.opinions.united_states.federal_appellate\n\n"
        "Passing the --report option will generate an HTML report in "
        "the root directory after scrapers have run"
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
        "-d",
        "--daemon",
        action="store_true",
        dest="daemonmode",
        default=False,
        help=(
            "Use this flag to turn on daemon "
            "mode, in which all courts requested "
            "will be scraped in turn, non-stop."
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
        default=os.environ.get("JURISCRAPER_DOCTOR_HOST", ""),
        help=(
            "Customize `doctor` host. "
            "Defaults to an environment variable `JURISCRAPER_DOCTOR_HOST`. "
            "You can get your local host by running "
            "`python manage.py runserver` on your doctor install"
        ),
    )

    parser.add_option(
        "-v",
        "--verbosity",
        action="count",
        default=1,
        help="Increase output verbosity (e.g., -vv is more than -v).",
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
        "-r",
        "--report",
        action="store_true",
        default=False,
        help="Generate a report.html with the outcome of running the scrapers",
    )

    (options, args) = parser.parse_args()

    daemon_mode = options.daemonmode
    court_id = options.court_id
    backscrape = options.backscrape
    backscrape_start = options.backscrape_start
    backscrape_end = options.backscrape_end
    days_interval = options.days_interval
    generate_report = options.report
    extract_content = options.extract_content
    binaries = options.binaries or extract_content
    doctor_host = options.doctor_host

    # Set up the print function
    print(f"Verbosity is set to: {options.verbosity}")

    def _v_print(*verb_args):
        if verb_args[0] > (3 - options.verbosity):
            print(verb_args[1])

    global v_print
    v_print = _v_print

    results = {}

    if not court_id:
        parser.error("You must specify a court as a package or module.")
    else:
        court_id = court_id.replace("/", ".")
        if court_id.endswith(".py"):
            court_id = court_id[:-3]

        module_strings = build_module_list(court_id)
        if len(module_strings) == 0:
            parser.error("Unable to import module or package. Aborting.")

        v_print(3, "Starting up the scraper.")
        num_courts = len(module_strings)
        i = 0
        while i < num_courts:
            current_court = module_strings[i]
            results[current_court] = {"global_failure": False}
            # this catches SIGINT, so the code can be killed safely.
            if die_now:
                v_print(3, "The scraper has stopped.")
                sys.exit(1)

            package, module = module_strings[i].rsplit(".", 1)
            v_print(3, f"Current court: {package}.{module}")

            mod = __import__(
                f"{package}.{module}", globals(), locals(), [module]
            )
            try:
                if backscrape:
                    for site in site_yielder(
                        mod.Site(
                            backscrape_start=backscrape_start,
                            backscrape_end=backscrape_end,
                            days_interval=days_interval,
                        ).back_scrape_iterable,
                        mod,
                    ):
                        site.parse()
                        scrape_court(
                            site, binaries, extract_content, doctor_host
                        )
                else:
                    site = mod.Site()
                    v_print(
                        3,
                        f"Sent {site.method} request to: {site.url}",
                    )
                    if site.uses_selenium:
                        v_print(3, "Selenium will be used.")
                    site.parse()
                    results[current_court]["scrape"] = scrape_court(
                        site, binaries, extract_content, doctor_host
                    )
            except Exception:
                results[current_court][
                    "global_failure"
                ] = traceback.format_exc()
                results[current_court]["scrape"] = {}
                v_print(3, "*************!! CRAWLER DOWN !!****************")
                v_print(
                    3,
                    "*****scrape_court method failed on mod: %s*****"
                    % module_strings[i],
                )
                v_print(3, "*************!! ACTION NEEDED !!***************")
                v_print(3, traceback.format_exc())
                i += 1
                continue

            last_court_in_list = i == (num_courts - 1)
            if last_court_in_list and daemon_mode:
                i = 0
            else:
                i += 1

    v_print(3, "The scraper has stopped.")

    if generate_report:
        report_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../report.html")
        )
        v_print(3, f"Generating HTML report at {report_path}")
        generate_scraper_report(report_path, results)

    sys.exit(0)


if __name__ == "__main__":
    main()
