What is this?
=============
Juriscraper is a scraper library that is used to scrape the American court system.
It is currently able to scrape all major appellate Federal courts, and we are
currently working on adding state courts.

Juriscraper is part of a two-part system. The second part is the 'caller', which
should be developed by the system using Juriscraper. The caller is responsible
for calling a scraper, downloading and saving its results. A reference
implementation of the caller has been developed and is in use at [CourtListener.com][2].
The code for that caller can be [found here][1]. There is also a basic
sample caller [included in Juriscraper][5] that can be used for testing or as a
starting point when developing your own.

Some of the design goals for this project are:

 - extensibility to support video, oral argument audio, etc.
 - extensibility to support geographies (US, Cuba, Mexico, California)
 - Mime type identification through magic numbers
 - Generalized architecture with no code repetition
 - XPath-based scraping powered by lxml's html parser
 - return all meta data available on court websites (caller can pick what it needs)
 - no need for a database
 - clear log levels (DEBUG, INFO, WARN, CRITICAL)
 - friendly to court websites


Installation & dependencies
===========================
    # install the dependencies
    sudo apt-get install python-pip  # If you don't have it already...
    sudo apt-get install libxml2-dev libxslt-dev  # In Ubuntu prior to 14.04 this is named libxslt-devel
    sudo pip install chardet==1.0.1
    sudo pip install requests==2.2.1
    sudo pip install lxml==3.0.1
    sudo pip install python-dateutil==1.5  # Newer have known incompatibilities with Python < 3
    sudo mkdir /var/log/juriscraper/

    # Install selenium and PhantomJS
    sudo pip install selenium
    wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-1.9.7-linux-x86_64.tar.bz2
    tar -x -f phantomjs-1.9.7-linux-x86_64.tar.bz2
    sudo mkdir -p /usr/local/phantomjs
    sudo mv phantomjs-1.9.7-linux-x86_64/bin/phantomjs /usr/local/phantomjs
    rm -r phantomjs-1.9.7*  # Cleanup
    
    # install the code
    sudo mkdir /usr/local/juriscraper
    cd /usr/local/juriscraper
    hg clone https://bitbucket.org/mlissner/juriscraper .

    # add Juriscraper to your python path (in Ubuntu/Debian)
    sudo ln -s /usr/local/juriscraper /usr/lib/python2.7/dist-packages/juriscraper

    # create a directory for logs
    sudo mkdir -p /var/log/juriscraper


Joining the project as a developer
==================================
We use a few tools pretty frequently while building these scrapers. The first is
[a sister project called xpath-tester][3] that helps debug XPath queries.
xpath-tester can be installed locally in a few minutes or is available at
[http://xpath.courtlistener.com][7].

We also generally use Eclipse with the PyDev and Aptana tools installed. This
is useful because it allows syntax highlighting and PyLint integration.

For scrapers to be merged:

 - `python tests/tests.py` must pass, listing the results for any new scrapers
 - a *_example file should be included (this is needed for the tests to
   run your code)
 - your code should be [PEP8][4] compliant with no major Pylint problems
 - your code should efficiently parse a page, returning no exceptions or
   speed warnings

When you're ready to develop a scraper, get in touch, and we'll find you one
that makes sense and that nobody else is working on. Alternatively, we have
[a list][6] of courts that you can browse yourself. There is also a template
in the opinions directory that you may use to begin scraper development.

When you're done with your scraper, fork this repository, push your changes into
your fork, and then send a pull request for your changes. Be sure to
remember to update the `__init__.py` file as well, since it contains a list of
completed scrapers.

Before we can accept any changes from any contributor, we need a signed and
completed Contributor License Agreement. You can find this agreement in the
root of the repository. While an annoying bit of paperwork, this license is for
your protection as a Contributor as well as the protection of Free Law Project
and our users; it does not change your rights to use your own Contributions for
any other purpose.


Usage
======
The scrapers are written in Python, and can can scrape a court as follows:

    from juriscraper.opinions.united_states.federal_appellate import ca1

    # Create a site object
    site = ca1.Site()

    # Populate it with data, downloading the page if necessary
    site.parse()

    # Print out the object
    print str(site)

It's also possible to iterate over all courts in a Python package, even if
they're not known before starting the scraper. For example:

    court_id = 'juriscraper.opinions.united_states.federal'
    scrapers = __import__(court_id,
                          globals(),
                          locals(),
                          ['*']).__all__
    for scraper in scrapers:
        mod = __import__('%s.%s' % (court_id, scraper),
                         globals(),
                         locals(),
                         [scraper])
        site = mod.Site()

This can be useful if you wish to create a command line scraper that iterates
over all courts of a certain jurisdiction that is provided by a script or a user.
See `lib/importer.py` for an example that's used in the sample caller.

Development of a `to_xml()` or `to_json()` method has not yet been completed, as
all callers have thus far been able to work directly with the Python objects. We
welcome contributions in this area.


Tests
=====
We got that! You can (and should) run the tests with `python tests/tests.py`.


Version History
===============
**Past**

 - 0.1 - Supports all 13 Federal Circuit courts and the U.S. Supreme Court

**Current**

 - 0.2 - Supports all federal courts of special jurisdiction (Veterans, Tax, etc.)

**Future Roadmap**

 - 0.3 - Support for all federal bankruptcy appellate panels (1st, 9th and 10th Cir.)
 - 0.4 - Support for all state courts of last resort (typically the "Supreme" court)
 - 0.5 - Support for all intermediate appellate state courts
 - 0.6 - Support for all courts of U.S. territories (Guam, American Samoa, etc.)
 - 0.7 - Support for all federal district courts with non-PACER opinion listings
 - 0.8 - Support for all federal district courts with PACER written opinion reports (+JPML)
 - 0.9 - Support for all federal district bankruptcy courts
 - 1.0 - For every court above where a backscraper is possible, it is implemented.
 - 1.1 - Support video, oral argument audio, and transcripts everywhere available

**Beyond**
 - add other countries, starting with courts issuing opinions in English.

License
========
Juriscraper is licensed under the permissive BSD license.

[1]: https://bitbucket.org/mlissner/search-and-awareness-platform-courtlistener/src/tip/alert/scrapers/management/commands/cl_scrape_and_extract.py?at=default
[2]: http://courtlistener.com
[3]: https://bitbucket.org/mlissner/lxml-xpath-tester
[4]: http://www.python.org/dev/peps/pep-0008/
[5]: https://bitbucket.org/mlissner/juriscraper/src/tip/sample_caller.py
[6]: http://people.ischool.berkeley.edu/~bcarver/mediawiki/index.php/Court_Documents
[7]: http://xpath.courtlistener.com
[8]: http://phantomjs.org
[9]: http://phantomjs.org/download.html
