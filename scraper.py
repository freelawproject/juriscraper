#!/usr/bin/env python

from optparse import OptionParser

def scrape(scraper, verbosity=0):
    '''Scrape the courts'''
    mod = __import__(scraper)
    site = mod.Site()

    html = site.download()
    site.parse()

    return site


def main():
    usage = "usage: %prog --court [--verbosity] "
    parser = OptionParser(usage)
    parser.add_option('-v', '--verbosity',
                      dest='verbosity',
                      metavar="VERBOSITY",
                      help="Log level to use during execution (0-2).")
    parser.add_option('-s', '--scraper',
                      dest='scraper',
                      metavar="SCRAPER",
                      help=("The scraper to use. Should be in the form of a ",
                            "Python module, e.g. 'opinions.federal.ca1' or ",
                            "'video.state.ca'"))
    (options, args) = parser.parse_args()

    if options.verbosity:
        try:
            verbosity = int(options.verbosity)
        except:
            parser.error('Verbosity level must be an int.')
    else:
        verbosity = 0

    if not options.scraper:
        parser.error("You must specify a scraper to execute.")

    scrape(options.scraper, verbosity)
    exit(0)

if __name__ == '__main__':
    main()
