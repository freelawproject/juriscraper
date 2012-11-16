import signal
import sys
import traceback
import urllib2
from optparse import OptionParser

# for use in catching the SIGINT (Ctrl+4)
die_now = False


def signal_handler(signal, frame):
    # Trigger this with CTRL+4
    print '**************'
    print 'Signal caught. Finishing the current court, then exiting...'
    print '**************'
    global die_now
    die_now = True


def scrape_court(court, binaries=False):
    '''Calls the requested court(s), gets its content, then throws it away.

    Note that this is a very basic caller lacking important functionality, such
    as:
     - checking whether the HTML of the page has changed since last visited
     - checking whether the downloaded content is already in your data store
     - saving anything at all

    Nonetheless, this caller is useful for testing, and for demonstrating some
    basic pitfalls that a caller will run into.
    '''
    site = court.Site().parse()

    for i in range(0, len(site.case_names)):
        # Percent encode URLs (this is a Python wart)
        download_url = urllib2.quote(site.download_urls[i], safe="%/:=&?~#+!$,;'@()*[]")

        if binaries:
            try:
                data = urllib2.urlopen(download_url).read()
                # test for empty files (thank you CA1)
                if len(data) == 0:
                    print 'EmptyFileError: %s' % download_url
                    print traceback.format_exc()
                    continue
            except Exception:
                print 'DownloadingError: %s' % download_url
                print traceback.format_exc()
                continue

        # Normally, you'd do your save routines here...
        print 'Adding new document found at: %s' % download_url
        attributes = ['adversary_numbers', 'case_dates', 'case_names',
                      'causes', 'dispositions', 'docket_attachment_numbers',
                      'docket_document_numbers', 'docket_numbers',
                      'download_urls', 'judges', 'lower_courts',
                      'lower_court_judges', 'nature_of_suit',
                      'neutral_citations', 'precedential_statuses',
                      'summaries', 'west_citations']
        for attr in attributes:
            if getattr(site, attr) is not None:
                print ('    %s: %s' % (attr, getattr(site, attr)[i])).encode('utf-8')

        # Extract the contents using e.g. antiword, pdftotext, etc.
        # extract_doc_content(data)

    print '%s: Successfully crawled.' % site.court_id


def build_module_list(court_id, parser):
    '''Takes the user's argument, and builds up a list of modules to import.

    This is a simple recursive function that iteratively looks for __all__
    attributes. If it finds one, it inspects each of the items in it to see if
    each of those has such an attribute. If they lack it, the item is added to
    a list of modules.
    '''
    module_strings = []

    def find_all_attr_or_punt(court_id):
        '''Checks that we have an __all__ attribute. If so, recuses. If not,
        adds the item to our list
        '''
        try:
            # Test that we have an __all__ attribute (proving that it's a
            # package) something like: opinions.united_states.federal
            all_attr = __import__(court_id, globals(), locals(), ['*']).__all__

            # Build the modules back up to full imports
            all_attr = ["%s.%s" % (court_id, item) for item in all_attr]
            for module in all_attr:
                # If we've made it this far, we have an __all__ attribute, so
                # we should see if the items within that attribute do too. And
                # so forth, recurively...
                find_all_attr_or_punt(module)
        except AttributeError:
            # Lacks the __all__ attribute. Probably of the form:
            # juriscraper.opinions.united_states.federal_appellate.ca1,
            # therefore, we add it to our list!
            module_strings.append(court_id)
        except ImportError:
            # Something has gone wrong.
            parser.error('Unable to import module or package. Aborting.')

    find_all_attr_or_punt(court_id)

    return module_strings


def main():
    global die_now

    # this line is used for handling SIGTERM (CTRL+4), so things can die safely
    signal.signal(signal.SIGTERM, signal_handler)

    usage = ('usage: %prog -c COURTID [-d|--daemon] [-b|--binaries]\n\n'
             'To test ca1, downloading binaries, use: \n'
             '    python %prog -c opinions.united_states.federal_appellate.ca1 -b\n\n'
             'To test all federal courts, disregarding binaries, use: \n'
             '    python %prog -c opinions.united_states.federal_appellate')
    parser = OptionParser(usage)
    parser.add_option('-c', '--courts', dest='court_id', metavar="COURTID",
                      help=('The court(s) to scrape and extract. This should be in '
                            'the form of a python module or package import '
                            'from the Juriscraper library, e.g. '
                            '"juriscraper.opinions.united_states.federal.ca1" or '
                            'simply "opinions" to do all opinions.'))
    parser.add_option('-d', '--daemon', action="store_true", dest='daemonmode',
                      default=False, help=('Use this flag to turn on daemon '
                                           'mode, in which all courts requested '
                                           'will be scraped in turn, non-stop.'))
    parser.add_option('-b', '--download_binaries', action='store_true',
                      dest='binaries', default=False,
                      help=('Use this flag if you wish to download the pdf, '
                            'wpd, and doc files.'))

    (options, args) = parser.parse_args()

    daemon_mode = options.daemonmode
    court_id = options.court_id
    binaries = options.binaries

    if not court_id:
        parser.error('You must specify a court as a package or module.')
    else:
        module_strings = build_module_list(court_id, parser)

        print 'Starting up the scraper.'
        num_courts = len(module_strings)
        i = 0
        while i < num_courts:
            # this catches SIGINT, so the code can be killed safely.
            if die_now == True:
                print 'The scraper has stopped.'
                sys.exit(1)

            package, module = module_strings[i].rsplit('.', 1)
            print "Current court: %s.%s" % (package, module)

            mod = __import__("%s.%s" % (package, module),
                             globals(),
                             locals(),
                             [module])
            try:
                scrape_court(mod, binaries)
            except Exception:
                print '*************!! CRAWLER DOWN !!****************'
                print '*****scrape_court method failed on mod: %s*****' % module_strings[i]
                print '*************!! ACTION NEEDED !!***************'
                print traceback.format_exc()
                i += 1
                continue

            last_court_in_list = (i == (num_courts - 1))
            if last_court_in_list and daemon_mode:
                i = 0
            else:
                i += 1

    print 'The scraper has stopped.'
    sys.exit(0)

if __name__ == '__main__':
    main()
