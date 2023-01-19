import os
import signal
import sys
import traceback
from collections import defaultdict
from optparse import OptionParser
from urllib import parse, request

from juriscraper.lib.importer import build_module_list, site_yielder
from juriscraper.lib.string_utils import trunc
from juriscraper.report import generate_scraper_report

die_now = False


def signal_handler(signal, frame):
    # Trigger this with CTRL+4
    v_print(3, "**************")
    v_print(3, "Signal caught. Finishing the current court, then exiting...")
    v_print(3, "**************")
    global die_now
    die_now = True


def extract_doc_content(data):
    # Your data extraction routines here. (pdftotext, abiword, etc.)
    return data


def scrape_court(site, binaries=False):
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

        if binaries:
            try:
                opener = request.build_opener()
                for cookie_dict in site.cookies:
                    opener.addheaders.append(
                        (
                            "Cookie",
                            f"{cookie_dict['name']}={cookie_dict['value']}",
                        )
                    )
                data = opener.open(download_url).read()
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

            # Extract the data using e.g. antiword, pdftotext, etc., then
            # clean it up.
            data = extract_doc_content(data)
            data = site.cleanup_content(data)

        # Normally, you'd do your save routines here...
        v_print(1, "\nAdding new item:")
        for k, v in item.items():
            if isinstance(v, str):
                value = trunc(v, 200, ellipsis="...")
                v_print(1, f'    {k}: "{value}"')
            else:
                # Dates and such...
                v_print(1, f"    {k}: {v}")

    v_print(3, f"\n{site.court_id}: Successfully crawled {len(site)} items.")

    with open("/Users/Palin/Code/juriscraper/xutput.txt", "a") as f:
        if len(site) == 0:
            f.writelines(
                f"{site.court_id}: Unsuccessfully crawled {len(site)} items.\n"
            )
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
        "-r",
        "--report",
        action="store_true",
        default=False,
        help="Generate a report.html with the outcome of running the scrapers",
    )

    (options, args) = parser.parse_args()

    daemon_mode = options.daemonmode
    binaries = options.binaries
    court_id = options.court_id
    backscrape = options.backscrape
    generate_report = options.report

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
                        mod.Site().back_scrape_iterable, mod
                    ):
                        site.parse()
                        scrape_court(site, binaries)
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
                        site, binaries
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
                with open(
                    "/Users/Palin/Code/juriscraper/xutput.txt", "a"
                ) as f:
                    f.writelines(
                        f"{site.court_id}: Unsuccessfully crawled parsed \n"
                    )

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
