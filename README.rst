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

First step: Install Python 3.9+, then:

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

Contributing
============

We welcome contributions! If you'd like to get involved, please take a look at our
`CONTRIBUTING.md <CONTRIBUTING.md>`__
guide for instructions on setting up your environment, running tests, and more.

License
=======

Juriscraper is licensed under the permissive BSD license.

|forthebadge made-with-python|

.. |forthebadge made-with-python| image:: http://ForTheBadge.com/images/badges/made-with-python.svg
    :target: https://www.python.org/
