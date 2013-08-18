import signal
import sys
import traceback
import urllib2
from optparse import OptionParser
from lib.importer import build_module_list

# for use in catching the SIGINT (Ctrl+4)
from lib.string_utils import trunc

die_now = False


def signal_handler(signal, frame):
    # Trigger this with CTRL+4
    v_print(3, '**************')
    v_print(3, 'Signal caught. Finishing the current court, then exiting...')
    v_print(3, '**************')
    global die_now
    die_now = True


def scrape_court(court, binaries=False):
    """Calls the requested court(s), gets its content, then throws it away.

    Note that this is a very basic caller lacking important functionality, such
    as:
     - checking whether the HTML of the page has changed since last visited
     - checking whether the downloaded content is already in your data store
     - saving anything at all

    Nonetheless, this caller is useful for testing, and for demonstrating some
    basic pitfalls that a caller will run into.
    """
    site = court.Site().parse()

    for i in range(0, len(site.case_names)):
        # Percent encode URLs (this is a Python wart)
        download_url = urllib2.quote(site.download_urls[i], safe="%/:=&?~#+!$,;'@()*[]")

        if binaries:
            try:
                data = urllib2.urlopen(download_url).read()
                # test for empty files (thank you CA1)
                if len(data) == 0:
                    v_print(3, 'EmptyFileError: %s' % download_url)
                    v_print(3, traceback.format_exc())
                    continue
            except Exception:
                v_print(3, 'DownloadingError: %s' % download_url)
                v_print(3, traceback.format_exc())
                continue

        # Normally, you'd do your save routines here...
        v_print(1, 'Adding new document found at: %s' % download_url)
        attributes = ['adversary_numbers', 'case_dates', 'case_names',
                      'causes', 'dispositions', 'docket_attachment_numbers',
                      'docket_document_numbers', 'docket_numbers',
                      'download_urls', 'judges', 'lower_courts',
                      'lower_court_judges', 'nature_of_suit',
                      'neutral_citations', 'precedential_statuses',
                      'summaries', 'west_citations', 'west_state_citations']
        for attr in attributes:
            if getattr(site, attr) is not None:
                value = getattr(site, attr)[i]
                if type(value) == unicode:
                    value = trunc(value, 200, elipsize=True)
                    v_print(1, '    %s: %s' % (attr, value.encode('utf-8')))
                else:
                    # Dates and such...
                    v_print(1, '    %s: %s' % (attr, value))

        # Extract the contents using e.g. antiword, pdftotext, etc.
        # extract_doc_content(data)

    v_print(3, '%s: Successfully crawled.' % site.court_id)


v_print = None
def main():
    global die_now

    # this line is used for handling SIGTERM (CTRL+4), so things can die safely
    signal.signal(signal.SIGTERM, signal_handler)

    usage = ('usage: %prog -c COURTID [-d|--daemon] [-b|--binaries]\n\n'
             'To test ca1, downloading binaries, use: \n'
             '    python %prog -c opinions.united_states.federal_appellate.ca1 -b\n\n'
             'To test all federal courts, omitting binaries, use: \n'
             '    python %prog -c opinions.united_states.federal_appellate')
    parser = OptionParser(usage)
    parser.add_option('-c', '--courts', dest='court_id', metavar="COURTID",
                      help=('The court(s) to scrape and extract. This should be in '
                            'the form of a python module or package import '
                            'from the Juriscraper library, e.g. '
                            '"juriscraper.opinions.united_states.federal.ca1" or '
                            'simply "opinions" to do all opinions. If desired, '
                            'you can use slashes instead of dots to separate'
                            'the import path.'))
    parser.add_option('-d', '--daemon', action="store_true", dest='daemonmode',
                      default=False, help=('Use this flag to turn on daemon '
                                           'mode, in which all courts requested '
                                           'will be scraped in turn, non-stop.'))
    parser.add_option('-b', '--download_binaries', action='store_true',
                      dest='binaries', default=False,
                      help=('Use this flag if you wish to download the pdf, '
                            'wpd, and doc files.'))
    parser.add_option('-v',
                      '--verbosity',
                      action='count',
                      default=1,
                      help='Increase output verbosity (e.g., -vv is more than -v).')

    (options, args) = parser.parse_args()

    daemon_mode = options.daemonmode
    binaries = options.binaries
    court_id = options.court_id

    # Set up the print function
    print "Verbosity is set to: %s" % options.verbosity
    def _v_print(*verb_args):
        if verb_args[0] > (3 - options.verbosity):
            print verb_args[1]

    global v_print
    v_print = _v_print

    if not court_id:
        parser.error('You must specify a court as a package or module.')
    else:
        court_id = court_id.replace('/', '.')
        if court_id.endswith('.py'):
            court_id = court_id[:-3]

        module_strings = build_module_list(court_id)
        if len(module_strings) == 0:
            parser.error('Unable to import module or package. Aborting.')

        v_print(3, 'Starting up the scraper.')
        num_courts = len(module_strings)
        i = 0
        while i < num_courts:
            # this catches SIGINT, so the code can be killed safely.
            if die_now:
                v_print(3, 'The scraper has stopped.')
                sys.exit(1)

            package, module = module_strings[i].rsplit('.', 1)
            v_print(3, "Current court: %s.%s" % (package, module))

            mod = __import__("%s.%s" % (package, module),
                             globals(),
                             locals(),
                             [module])
            try:
                scrape_court(mod, binaries)
            except Exception:
                v_print(3, '*************!! CRAWLER DOWN !!****************')
                v_print(3, '*****scrape_court method failed on mod: %s*****' % module_strings[i])
                v_print(3, '*************!! ACTION NEEDED !!***************')
                v_print(3, traceback.format_exc())
                i += 1
                continue

            last_court_in_list = (i == (num_courts - 1))
            if last_court_in_list and daemon_mode:
                i = 0
            else:
                i += 1

    v_print(3, 'The scraper has stopped.')
    sys.exit(0)

if __name__ == '__main__':
    main()
