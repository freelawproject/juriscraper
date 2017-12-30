|Build Status|

What is This?
=============

Juriscraper is a scraper library started several years ago that gathers judicial opinions, oral arguments, and PACER data in the American court system. It is currently able to scrape:

-  a variety of pages and reports within the PACER system
-  opinions from all major appellate Federal courts
-  opinions from all state courts of last resort except for Georgia (typically their "Supreme Court")
-  oral arguments from all appellate federal courts that offer them

Juriscraper is part of a two-part system. The second part is your code,
which calls Juriscraper. Your code is responsible for calling a scraper,
downloading and saving its results. A reference implementation of the
caller has been developed and is in use at
`CourtListener.com <https://www.courtlistener.com>`__. The code for that
caller can be `found
here <https://github.com/freelawproject/courtlistener/tree/master/cl/scrapers/management/commands>`__.
There is also a basic sample caller `included in
Juriscraper <https://github.com/freelawproject/juriscraper/blob/master/juriscraper/sample_caller.py>`__
that can be used for testing or as a starting point when developing your
own.

Some of the design goals for this project are:

-  extensibility to support video, oral argument audio, etc.
-  extensibility to support geographies (US, Cuba, Mexico, California)
-  Mime type identification through magic numbers
-  Generalized architecture with minimal code repetition
-  XPath-based scraping powered by lxml's html parser
-  return all meta data available on court websites (caller can pick
   what it needs)
-  no need for a database
-  clear log levels (DEBUG, INFO, WARN, CRITICAL)
-  friendly as possible to court websites

Installation & Dependencies
===========================

First step: Install Python 2.7.x, then:

::

    # -- Install the dependencies
    # On Ubuntu/Debian Linux:
        sudo apt-get install libxml2-dev libxslt-dev libyaml-dev
    # On macOS with Homebrew <https://brew.sh>:
        brew install libyaml

    # -- Install PhantomJS
    # On Ubuntu/Debian Linux
        wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-1.9.7-linux-x86_64.tar.bz2
        tar -x -f phantomjs-1.9.7-linux-x86_64.tar.bz2
        sudo mkdir -p /usr/local/phantomjs
        sudo mv phantomjs-1.9.7-linux-x86_64/bin/phantomjs /usr/local/phantomjs
        rm -r phantomjs-1.9.7*  # Cleanup
    # On macOS with Homebrew:
        brew install phantomjs

    # Finally, install the code.
    pip install juriscraper

    # create a directory for logs (this can be skipped, and no logs will be created)
    sudo mkdir -p /var/log/juriscraper


Joining the Project as a Developer
==================================

For scrapers to be merged:

-  Running tests via ``tox`` must pass, listing the results for any new
   scrapers. The test suite will be run automatically by
   `Travis-CI <https://travis-ci.org/freelawproject/juriscraper>`__. If changes are being made to the pacer code, the pacer tests must also pass when run. These tests are skipped by default. To run them, set environment variables for PACER_USERNAME and PACER_PASSWORD.
-  A \*\_example\* file must be included in the ``tests/examples``
   directory (this is needed for the tests to run your code).
-  Your code should be
   `PEP8 <http://www.python.org/dev/peps/pep-0008/>`__ compliant with no
   major Pylint problems or Intellij inspection issues.
-  Your code should efficiently parse a page, returning no exceptions or
   speed warnings during tests on a modern machine.

When you're ready to develop a scraper, get in touch, and we'll find you
a scraper that makes sense and that nobody else is working on. We have `a wiki
list <https://github.com/freelawproject/juriscraper/wiki/Court-Websites>`__
of courts that you can browse yourself. There are templates for new
scrapers `here (for
opinions) <https://github.com/freelawproject/juriscraper/blob/master/juriscraper/opinions/opinion_template.py>`__
and `here (for oral
arguments) <https://github.com/freelawproject/juriscraper/blob/master/juriscraper/oral_args/oral_argument_template.py>`__.

When you're done with your scraper, fork this repository, push your
changes into your fork, and then send a pull request for your changes.
Be sure to remember to update the ``__init__.py`` file as well, since it
contains a list of completed scrapers.

Before we can accept any changes from any contributor, we need a signed
and completed Contributor License Agreement. You can find this agreement
in the root of the repository. While an annoying bit of paperwork, this
license is for your protection as a Contributor as well as the
protection of Free Law Project and our users; it does not change your
rights to use your own Contributions for any other purpose.


Getting Set Up as a Developer
=============================

To get set up as a developer of Juriscraper, you'll want to install the code
from git. To do that, install the dependencies and phantomjs as described above.
Instead of installing Juriscraper via pip, do the following:

::

    git clone https://github.com/freelawproject/juriscraper.git .
    pip install -r requirements.txt
    python setup.py test

You may need to also install Juriscraper locally with:

::

   pip install .

If you've not installed juriscraper, you can run `sample_caller.py` as:

::

   PYTHONPATH=`pwd` python  juriscraper/sample_caller.py


Usage
=====

The scrapers are written in Python, and can can scrape a court as
follows:

::

    from juriscraper.opinions.united_states.federal_appellate import ca1

    # Create a site object
    site = ca1.Site()

    # Populate it with data, downloading the page if necessary
    site.parse()

    # Print out the object
    print str(site)

    # Print it out as JSON
    print site.to_json()

    # Iterate over the item
    for opinion in site:
        print opinion

That will print out all the current meta data for a site, including
links to the objects you wish to download (typically opinions or oral
arguments). If you download those opinions, we also recommend running the
``_cleanup_content()`` method against the items that you download (PDFs,
HTML, etc.). See the ``sample_caller.py`` for an example and see
``_cleanup_content()`` for an explanation of what it does.

It's also possible to iterate over all courts in a Python package, even
if they're not known before starting the scraper. For example:

::

    # Start with an import path. This will do all federal courts.
    court_id = 'juriscraper.opinions.united_states.federal'
    # Import all the scrapers
    scrapers = __import__(
        court_id,
        globals(),
        locals(),
        ['*']
    ).__all__
    for scraper in scrapers:
        mod = __import__(
            '%s.%s' % (court_id, scraper),
            globals(),
            locals(),
            [scraper]
        )
        # Create a Site instance, then get the contents
        site = mod.Site()
        site.parse()
        print str(site)

This can be useful if you wish to create a command line scraper that
iterates over all courts of a certain jurisdiction that is provided by a
script. See ``lib/importer.py`` for an example that's used in
the sample caller.

District Court Parser
=====================
A sample driver to run the PACER District Court parser on an html file is included.
It takes HTML file(s) as arguments and outputs JSON to stdout.

Example usage:

::

   PYTHONPATH=`pwd` juriscraper/pacerdocket.py tests/examples/pacer/dockets/district/nysd.html


Tests
=====

We got that! You can (and should) run the tests with
``tox``. This will run ``python setup.py test`` for all supported Python runtimes,
iterating over all of the ``*_example*`` files and run the scrapers against them.

Individual tests can be run with:

   python -m unittest tests.test_pacer.DocketParseTest.test_district_court_dockets

Or, to run and drop to the Python debugger if it fails, but you must install `nost` to have `nosetests`:

  nosetests -v --pdb tests/test_pacer.py:DocketParseTest.test_district_court_dockets

In addition, we use `Travis-CI <https://travis-ci.org/>`__ to
automatically run the tests whenever code is committed to the repository
or whenever a pull request is created. You can make sure that your pull
request is good to go by waiting for the automated tests to complete.

The current status of Travis CI on our master branch is:

|Build Status|

Version History
===============

**Past**

-  0.1 - Supports opinions from all 13 Federal Circuit courts and the
   U.S. Supreme Court
-  0.2 - Supports opinions from all federal courts of special
   jurisdiction (Veterans, Tax, etc.)
-  0.8 - Supports oral arguments for all possible Federal Circuit
   courts.
-  0.9 - Supports all state courts of last resort (typically the
   "Supreme" court)
-  1.0 - Support opinions from for all possible federal bankruptcy
   appellate panels (9th and 10th Cir.)
-  1.1.* - Major code reorganization and first release on the Python Package Index (PyPi)
-  1.2.* - Continued improvements.
-  1.3.* - Adds support for scraping some parts of PACER.
-  1.4.* - Python 3 compatibility.
-  1.5.* - Adds support for querying and parsing PACER dockets.
-  1.6.* - Adds automatic relogin code to PACER sessions, with reorganization of old login APIs.
- 1.7.* - Adds support for hidden PACER APIs.
- 1.8.* - Standardization of string fields in PACER objects so they return the empty string when they have no value instead of returning None sometimes and the empty string others. (This follows Django conventions.)

**Current**

- 1.9.* - Re-organization, simplification, and standardization of PACER classes.

**Immediate Future Goals**

-  Support opinions from for all intermediate appellate state courts
-  Support opinions from for all courts of U.S. territories (Guam, American Samoa, etc.)
-  Support opinions from for all federal district courts with non-PACER opinion listings
-  For every court above where a backscraper is possible, it is implemented.
-  Support video, additional oral argument audio, and transcripts everywhere available


Deployment
==========

Deployment to PyPi should happen automatically by Travis CI whenever a new tag is created in Github on the master branch. It will fail if the version has not been updated or if Travis CI failed.

If you wish to create a new version manually, the process is:

1. Update version info in ``setup.py``

1. Install the requirements in requirements_dev.txt

1. Set up a config file at ~/.pypirc

1. Generate a distribution

    ::

        python setup.py bdist_wheel

1. Upload the distribution

    ::

        twine upload dist/* -r pypi (or pypitest)


License
=======

Juriscraper is licensed under the permissive BSD license.

.. |Build Status| image:: https://travis-ci.org/freelawproject/juriscraper.svg?branch=master
   :target: https://travis-ci.org/freelawproject/juriscraper
