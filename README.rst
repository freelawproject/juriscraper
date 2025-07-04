+---------------+---------------------+-------------------+
| |Lint Badge|  | |Test Badge|        |  |Version Badge|  |
+---------------+---------------------+-------------------+


.. |Lint Badge| image:: https://github.com/freelawproject/juriscraper/workflows/Lint/badge.svg
.. |Test Badge| image:: https://github.com/freelawproject/juriscraper/workflows/Tests/badge.svg
.. |Version Badge| image:: https://badge.fury.io/py/juriscraper.svg


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
here <https://github.com/freelawproject/courtlistener/blob/main/cl/scrapers/management/commands/cl_scrape_opinions.py>`__.
There is also a basic sample caller `included in
Juriscraper <https://github.com/freelawproject/juriscraper/blob/main/sample_caller.py>`__
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

First step: Install Python 3.9+.x, then:

Install the dependencies
------------------------

On Ubuntu based distributions/Debian Linux::

    sudo apt-get install libxml2-dev libxslt-dev libyaml-dev

On Arch based distributions::

    sudo pacman -S libxml2 libxslt libyaml

On macOS with Homebrew <https://brew.sh>::

    brew install libyaml


Then install the code
---------------------

::

    pip install juriscraper

You can set an environment variable for where you want to stash your logs (this
can be skipped, and `/var/log/juriscraper/debug.log` will be used as the
default if it exists on the filesystem)::

    export JURISCRAPER_LOG=/path/to/your/log.txt

Finally, do your WebDriver
--------------------------
Some websites are too difficult to crawl without some sort of automated
WebDriver. For these, Juriscraper either uses a locally-installed copy of
geckodriver or can be configured to connect to a remote webdriver. If you prefer
the local installation, you can download Selenium FireFox Geckodriver::

    # choose OS compatible package from:
    #   https://github.com/mozilla/geckodriver/releases/tag/v0.26.0
    # un-tar/zip your download
    sudo mv geckodriver /usr/local/bin

If you prefer to use a remote webdriver, like `Selenium's docker image <https://hub.docker.com/r/selenium/standalone-firefox>`__, you can
configure it with the following variables:

``WEBDRIVER_CONN``: Use this to set the connection string to your remote
webdriver. By default, this is ``local``, meaning it will look for a local
installation of geckodriver. Instead, you can set this to something like,
``'http://YOUR_DOCKER_IP:4444/wd/hub'``, which will switch it to using a remote
driver and connect it to that location.

``SELENIUM_VISIBLE``: Set this to any value to disable headless mode in your
selenium driver, if it supports it. Otherwise, it defaults to headless.

For example, if you want to watch a headless browser run, you can do so by
starting selenium with::

    docker run \
        -p 4444:4444 \
        -p 5900:5900 \
        -v /dev/shm:/dev/shm \
        selenium/standalone-firefox-debug

That'll launch it on your local machine with two open ports. 4444 is the
default on the image for accessing the webdriver. 5900 can be used to connect
via a VNC viewer, and can be used to watch progress if the ``SELENIUM_VISIBLE``
variable is set.

Once you have selenium running like that, you can do a test like::

    WEBDRIVER_CONN='http://localhost:4444/wd/hub' \
        SELENIUM_VISIBLE=yes \
        python sample_caller.py -c juriscraper.opinions.united_states.state.kan_p

Kansas's precedential scraper uses a webdriver. If you do this and watch
selenium, you should see it in action.


Code Style & Linting
====================

We use `Ruff <https://docs.astral.sh/ruff/>`__ for code formatting and linting. Ruff replaces tools like flake8, isort,
black, and autoflake with a single fast tool.

Ruff is automatically run via `pre-commit hooks <https://pre-commit.com>`__, which you can set up like this:

::

    uv tool install pre-commit --with pre-commit-uv
    pre-commit install

To run Ruff manually on all files:

::

    pre-commit run ruff-format --all-files
    pre-commit run ruff --all-files

To run only on staged files:

::

    pre-commit run ruff-format
    pre-commit run ruff

You can also `integrate Ruff into your editor <https://docs.astral.sh/ruff/editors/setup/>`__ for automatic formatting and diagnostics.

Formatting Guidelines
----------------------

Beyond what Ruff will catch:

- If you manually make whitespace or formatting changes, do them in a **separate commit** from logic changes.
- Avoid combining whitespace reformatting with functional changes, as it makes code review harder.

Joining the Project as a Developer
==================================

For scrapers to be merged:

-  Automated testing should pass. The test suite will be run automatically by Github Actions. If changes are being made to the pacer code, the pacer tests must also pass when run. These tests are skipped by default. To run them, set environment variables for PACER_USERNAME and PACER_PASSWORD.

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
of courts that you can browse yourself.

There are templates for new scrapers available:

- `Opinion scraper template <https://github.com/freelawproject/juriscraper/blob/master/juriscraper/opinions/opinion_template.py>`__
- `Oral argument scraper template <https://github.com/freelawproject/juriscraper/blob/master/juriscraper/oral_args/oral_argument_template.py>`__

When you're done with your scraper:

1. Fork this repository.
2. Push your changes to your fork.
3. Submit a pull request.

Be sure to update the ``__init__.py`` file that registers completed scrapers.

Before we can accept any changes from any contributor, we need a signed
and completed Contributor License Agreement. You can find this agreement
in the root of the repository. While an annoying bit of paperwork, this
license is for your protection as a Contributor as well as the
protection of Free Law Project and our users; it does not change your
rights to use your own Contributions for any other purpose.


Development
===========

Requirements (for Development)
------------------------------

To work on Juriscraper (e.g. to write or edit scrapers, run tests, or contribute code), you'll need:

- Python 3.9 or newer
- `uv <https://github.com/astral-sh/uv>`__, a fast and modern Python package manager
- Git
- Optionally: Docker, if you want to run Selenium tests with a remote webdriver

See below for OS-specific instructions for installing `uv`.

Environment Setup with uv
--------------------------

This project uses uv, a fast and modern Python package manager, to manage the development environment.

1. Install uv

- Ubuntu based distributions / Debian:

::

    curl -LsSf https://astral.sh/uv/install.sh | sh


- Arch Linux based distributions:

::

    sudo pacman -S uv

- macOS:

::

    curl -LsSf https://astral.sh/uv/install.sh | sh

2. Clone the Repository

::

    git clone https://github.com/freelawproject/juriscraper.git

3. Set Up the Environment

Create a development environment using uv and the included pyproject.toml and uv.lock files:

::

    uv venv

Activate the environment:

- Linux/macOS:

::

    source .venv/bin/activate

4. Run Tests with tox

Then, you can run its tests with `tox <https://tox.readthedocs.io/en/latest/>`__.
Install tox with `uv <https://docs.astral.sh/uv/>`__ as a `tool <https://docs.astral.sh/uv/concepts/tools/>`__, adding the `tox-uv extension <https://github.com/tox-dev/tox-uv>`__:

::

    uv tool install tox --with tox-uv

To run juriscraper’s tests for all Python versions, run:

::

    tox

To run tests for a single Python version, pass the environment name, such as for Python 3.13:

::

    tox -e py313

To pass extra arguments to pytest, add them after a ``--`` separator, like:

::

    tox -e py313 -- --pdb

Network tests
-------------

The tests in ``tests/network`` interact with PACER.
By default, they are skipped, as they require working credentials.
To run them, set the environment variables ``PACER_USERNAME`` and ``PACER_PASSWORD`` to your PACER credentials, for example:

::

    export PACER_USERNAME=the-coolest-lawyer
    export PACER_PASSWORD=hunter2

Then, run the tests as usual:

::

    tox -e py313

Or, to run only the network tests:

::

    tox -e py313 -- tests/network

``sample_caller.py``
--------------------

This script demonstrates how to use Juriscraper.
Run it with:

::

    uv run sample_caller.py

It requires options to select which courts to scrape, per its help output.
For example, to test ca1, run:

::

    uv run sample_caller.py -c juriscraper.opinions.united_states.federal_appellate.ca1

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
    print(str(site))

    # Print it out as JSON
    print(site.to_json())

    # Iterate over the item
    for opinion in site:
        print(opinion)

That will print out all the current meta data for a site, including
links to the objects you wish to download (typically opinions or oral
arguments). If you download those opinions, we also recommend running the
``cleanup_content()`` method against the items that you download (PDFs,
HTML, etc.). See the ``sample_caller.py`` for an example and see
``cleanup_content()`` for an explanation of what it does.
Note that if cleanup_content() is not implemented in the scraper,
it will simply return the original content unchanged.

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
        print(str(site))

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

   PYTHONPATH=`pwd` python juriscraper/pacerdocket.py tests/examples/pacer/dockets/district/nysd.html


Tests
=====

We got that! You can (and should) run the tests with
``tox``. This will run ``python setup.py test`` for all supported Python runtimes,
iterating over all of the ``*_example*`` files and run the scrapers against them.

Each scraper has one or more ``*_example*`` files.  When creating a new scraper,
or covering a new use case for an existing scraper, you will have to create an
example file yourself.  Please see the files under ``tests/examples/`` to see
for yourself how the naming structure works.  What you want to put in your new
example file is the HTML/json/xml that the scraper in question needs to test
parsing.  Sometimes creating these files can be tricky, but more often than not,
it is as simple as getting the data to display in your browser, viewing then copying
the page source, then pasting that text into your new example file.

Each ``*_example*`` file has a corresponding ``*_example*.compare.json`` file. This
file contains a json data object that represents the data extracted when parsing
the corresponding ``*_example*`` file.  These are used to ensure that each scraper
parses the exact data we expect from each of its ``*_example*`` files. You do not
need to create these ``*_example*.compare.json`` files yourself.  Simply create
your ``*_example*`` file, then run the test suite.  It will fail the first time,
indicating that a new ``*_example*.compare.json`` file was generated.  You should
review that file, make sure the data is correct, then re-run the test suite.  This
time, the tests should pass (or at least they shouldn't fail because of the newly
generated ``*_example*.compare.json`` file).  Once the tests are passing,
feel free to commit, but **please remember** to include the new ``*_example*``
**and** ``*_example*.compare.json`` files in your commit.

Individual tests can be run with:

   tox -e py -- tests/local/test_DateTest.py::DateTest::test_date_range_creation

Or, to run and drop to the Python debugger if it fails, but you must install `nost` to have `nosetests`:

  uv run nosetests -v --pdb tests/local/test_DateTest.py:DateTest.test_date_range_creation


Future Goals
============
-  Support for additional PACER pages and utilities
-  Support opinions from for all courts of U.S. territories (Guam, American Samoa, etc.)
-  Support opinions from for all federal district courts with non-PACER opinion listings
-  For every court above where a backscraper is possible, it is implemented.
-  Support video, additional oral argument audio, and transcripts everywhere available


Deployment
==========
Deployment to PyPI should happen automatically when a tagged version is pushed
to master in the format v*.*.*. If you do not have push permission on master,
this will also work for merged, tagged pull requests. Update the version number
in ``pyproject.toml``, tag your commit with the correct tag (v.*.*.*), and do a
PR with that.

License
=======

Juriscraper is licensed under the permissive BSD license.

|forthebadge made-with-python|

.. |forthebadge made-with-python| image:: http://ForTheBadge.com/images/badges/made-with-python.svg
    :target: https://www.python.org/
