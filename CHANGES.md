# Change Log

As of this writing, in late 2020, we have issued over 400 releases. The vast
majority of these releases fix a scraper so it works better on a particular
court's website. When that's the case, we don't update the changelog, we simply
do the change, and you can find it in the git log.

The changes below represent changes in ambition, goals, or interface. In other
words, they're the ones you'll want to watch, and the others are mostly noise.

Releases are also tagged in git, if that's helpful.

## Coming up

- N/A

## Current

**2.5.95 - 2024-02-14**

Features:

- The GET method of the PacerSession class now supports custom timeouts for flexible request management.
- Adds a method to check if a district court docket entry is sealed..

Changes:

- Update the DownloadConfirmationPage class to reduce the read timeout of the GET request within the query method.

## Past

**2.5.94 - 2024-02-13**

Features:

Changes:

- Update minnag
- Update alaska/app

**2.5.93 - 2024-02-09**

Features:

Changes:

- Update fladistctapp

**2.5.92 - 2024-02-09**

Features:

Changes:

- Update Nev/NevApp scrapers

**2.5.91 - 2024-02-09**

Features:

- Add expected_content_types to OpinionSite and OralArgSite

Changes:

- Fixes for pacer.email, pacer.utils

**2.5.90 - 2024-02-01**

Features:

Changes:

- Fix Colo Ct App

**2.5.89 - 2024-01-31**

Features:

Changes:

- Fix Armed Forces Scraper

**2.5.88 - 2024-01-31**

Features:

Changes:

- Fix Guam
- Fix Fla Dist Court

**2.5.87 - 2024-01-31**

Features:

Changes:

- Fix PA Superior Court

**2.5.86 - 2024-01-31**

Features:

Changes:

- Fix Maryland Supreme and lower courts

**2.5.85 - 2024-01-30**

Features:

Changes:

- Fix Connecticut and Connecticut Court of Appeals

**2.5.84 - 2024-01-26**

Features:

Changes:

- Update Nevada/Nev App (again)

**2.5.83 - 2024-01-25**

Features:

Changes:

- Fix Hawaii App
- Nevada/Nev App
- VI Superior
- Cal AG
- LA Ct APP
- Updates the SSL Adapter
- Various RECAP Pacer Fixes

**2.5.82 - 2024-01-12**

Features:

Changes:

- Fix CADC

**2.5.81 - 2024-01-12**

Features:

Changes:

- Fix colo / Nytrial courts

**2.5.80 - 2024-01-10**

Features:

Changes:

- Fix compatibility with newer lxml
- Replace lxml sanitier with nh3

**2.5.78 - 2024-01-08**

Features:

- Add ten new NY Trial Courts
- Add Maine Superior Court

Changes:

- Add child_courts attribute
- Fix VI chore
- Update python dep.

**2.5.76 - 2023-12-28**

Features:

- Add Bankruptcy Appellate Panel 1st Circuit

Changes:

**2.5.75 - 2023-12-28**

Features:

-

Changes:

- Fix BAP1 and update test for it

**2.5.74 - 2023-12-13**

Features:

- Add NevApp

Changes:

- Fix Nevada Supreme and Colorado Ct App


**2.5.72 - 2023-12-12**

Features:

- Add VI Superior Court scraper

Changes:

- Fix CA2 Oral Arguments Scraper

**2.5.71 - 2023-12-11**

Features:

-

Changes:

- Fix avoid populating case's date_filed with the entry date_filed from emails

**2.5.70 - 2023-11-21**

Features:

-

Changes:

- Fix LA Supreme

**2.5.69 - 2023-11-21**

Features:

- Fix VI Tests
- Puerto Rico and Coast Guard court ids to match CL
- Fix Arizona App Dist 2
- Fix CA2 OA scraper

Changes:

- Shrink VA to be faster
- Fix Conn App Ct date handler

**2.5.68 - 2023-11-20**

Features:

- Fix Okla AG content cleanup

Changes:

-

**2.5.67 - 2023-11-20**

Features:

- Fix Connecticut Court of Appeals

Changes:

-

**2.5.66 - 2023-11-19**

Features:

- Fix Oklahoma Scrapers

Changes:

-
**2.5.65 - 2023-11-19**

Features:

-

Changes:

- Remove selenium from Colorado scrapers

**2.5.64 - 2023-11-19**

Features:

-

Changes:

- Fix alabama to remove selenium


**2.5.63 - 2023-11-18**

Features:


Changes:

- Fix Scotus Slip Opinions

**2.5.62 - 2023-11-18**

Features:


Changes:

- Fix NH Supreme Court


**2.5.60 - 2023-11-18**

Features:

- Add Oregon Court of Appeals

Changes:

- Fix Oregon Supreme Court


**2.5.59 - 2023-11-18**

Features:


Changes:

- Fix Most remaining downed scrapers
- Fix mismatched court_ids

**2.5.58 - 2023-11-13**

Features:


Changes:

- Fix 40 or so scrapers -- all state scrapers

**2.5.57 - 2023-11-09**

Features:

- Add support for parsing ACMS Docket reports.

Changes:

- Abstract out date regexes into a new class attribute named DATE_REGEX.
- Update deprecated key in setup.cfg file.
- Refactor the message in the SlownessException to limit the precision to the right of the decimal point to three digits.
- Refactor the regex pattern in the scraper for Colorado Appeals Court


**2.5.56 - 2023-10-09**

Features:

- N/A

Changes:

- Fix Mass/MassAppCt

**2.5.54 - 2023-10-06**

Features:

- N/A

Changes:

- Add missing ca prefix mappings
- Handle cadc/cavc docid prefix collision

**2.5.53 - 2023-09-23**

Features:

- Parse attachments from dockets

Changes:

- Fix attachment page numbers for old district court attachments
- Add missing prefix maps for special courts

**2.5.52 - 2023-07-06**

Features:

- N/A

Changes:

- Fix Nebraska/App court to ignore unpublished notes (A-XX-XXXX)

**2.5.51 - 2023-06-29**

Features:

- N/A

Changes:

- Fix case_name and judge parsing in case_query pages.

**2.5.50 - 2023-06-19**

Features:

- N/A

Changes:

- Fix INSB bankruptcy docket number parsing.

**2.5.49 - 2023-05-31**

Features:

- N/A

Changes:

- Fix docket report parsing on view multiple documents layout.

**2.5.48 - 2023-05-25**

Features:

- N/A

Changes:

- Updated version of pinned dependencies.

**2.5.47 - 2023-05-04**

Features:

- N/A

Changes:

- Replace unmaintained cchardet with charset-normalizer.

**2.5.46 - 2023-05-02**

Features:

- N/A

Changes:

- Fix List of creditors query a valid POST param.

**2.5.45 - 2023-04-28**

Features:

- N/A

Changes:

- Fix List of creditors parsing error.

**2.5.44 - 2023-04-24**

Features:

- N/A

Changes:

- Parse short_description from recap email subject.
- Parse date_entered and ordered_by for docket reports.

**2.5.43 - 2023-04-14**

Features:

- N/A

Changes:

- Get a valid POST param before requesting the list of creditors.

**2.5.42 - 2023-04-13**

Features:

- Added ListOfCreditors report parser.

Changes:

- N/A

**2.5.41 - 2023-04-05**

Features:

- N/A

Changes:

- Fix ClaimsActivity report alternative POST param for insb.

**2.5.40 - 2023-04-04**

Features:

- Added ClaimsActivity report parser.

Changes:

- N/A

**2.5.39 - 2023-03-09**

Features:

- N/A

Changes:

- Fix return null value if there is no document number in email notification.
- Added support for parsing a new format of email recipients in notifications.

**2.5.38 - 2023-03-09**

Features:

- N/A

Changes:

- Added pacer_seq_no field to appellate RSS feed data.

**2.5.37 - 2023-03-07**

Features:

- N/A

Changes:

- Get pacer_case_id from case URL when there is no attached document in a email
  notification.

**2.5.36 - 2023-03-03**

Features:

- N/A

Changes:

- Added support for parsing district/bankruptcy download confirmation pages.

**2.5.35 - 2023-02-28**

Features:

- N/A

Changes:

- Improved performance of parsing date-times in RSS feeds.

**2.5.34 - 2023-02-21**

Features:

- N/A

Changes:

- Added support for parsing appellate RSS Feeds

**2.5.33 - 2023-01-13**

Features:

- N/A

Changes:

- Fix the CA9 Published/Unpublished II

**2.5.32 - 2023-01-13**

Features:

- N/A

Changes:

- Fix the CA9 Published/Unpublished

**2.5.31 - 2023-01-13**

Features:

- N/A

Changes:

- Fix the four Kansas Scrapers for updated website.

**2.5.30 - 2023-01-11**

Features:

- Disabled scrapers for
  - ME

Changes:

- N/A

**2.5.29 - 2023-01-06**

Features:

- Added scrapers for
  - Alabama Supreme Court
  - Alabama Court of Civil Appeals
  - Alabama Court of Criminal Appeals
  - Colorado Supreme Court
  - Colorado Court of Appeals

Changes:

- N/A


**2.5.28 - 2022-12-22**

Features:

- Added scraper for WVA CT APP

Changes:

- Fix docket report parsing when there is no valid content and if there is
  bad script content.
- Fix avoid parsing the download confirmation page if a PDF binary is returned.
- Fix parsing text/plain content multipart email notifications.

**2.5.27 - 2022-12-13**

Features:

 - Added AppellateAttachmentPage report to parse appellate attachment pages.

Changes:

- N/A


**2.5.26 - 2022-11-15**

Features:

 - N/A

Changes:

- Fix download PDF documents returned after a redirection.

**2.5.25 - 2022-11-07**

Features:

 - N/A

Changes:

- Update to support J. Jackson

**2.5.24 - 2022-11-02**

Features:

 - N/A

Changes:

- Added support for parsing multi-docket NEFs

**2.5.23 - 2022-10-26**

Features:

 - N/A

Changes:

 - Fix docket report entries table parsing for wiwb.
 - Ignore claims filings notifications for email report.
 - Fix UnicodeEncodeError when parsing a docket report.

**2.5.22 - 2022-10-12**

Features:

 - N/A

Changes:

 - Fix email report decoding.

**2.5.21 - 2022-10-11**

Features:

 - N/A

Changes:

 - Fix NEFs description parsing for cacb.

**2.5.20 - 2022-10-06**

Features:

 - N/A

Changes:

 - Fix regression caught in COURTLISTENER-36Q, to properly handle
   window.location redirects on weird PACER sites.


**2.5.19 - 2022-09-29**

Features:

 - N/A

Changes:

 - Fix performance when downloading large PDFs (see #564)

**2.5.18 - 2022-09-29**

Features:

 - N/A

Changes:

 - Skip appellate attachment page when querying the download confirmation page
 - Skip appellate attachment page when downloading the free document
 - Fix getting filed date on email notifications

**2.5.17 - 2022-09-28**

Features:

 - N/A

Changes:

 - Added DownloadConfirmationPage report to parse the PACER download
 confirmation page and get the following data:
  - document_number
  - docket_number
  - cost
  - billable_pages
  - document_description
  - transaction_date

**2.5.16 - 2022-09-11**

Features:

 - N/A

Changes:

 - Fix for OA CA1

**2.5.15 - 2022-09-06**

Features:

 - N/A

Changes:

 - Update Selenium version 4.0.0.a7


**2.5.14 - 2022-09-02**

Features:

 - N/A

Changes:

 - Update Selenium version

**2.5.13 - 2022-08-24**

Features:

 - N/A

Changes:

 - Added support to get attached documents from NEFs.

**2.5.12 - 2022-08-12**

Features:

 - N/A

Changes:

 - Added support to parse NDAs and download their free documents.

**2.5.11 - 2022-07-29**

Features:

 - N/A

Changes:

 - Fix Tax Scraper

**2.5.10 - 2022-07-28**

Features:

 - N/A

Changes:

 - Bug fix

**2.5.9 - 2022-07-28**

Features:

 - N/A

Changes:

 - Fix CA4

**2.5.8 - 2022-07-26**

Features:

 - N/A

Changes:

 - Fix Michigan Supreme Court

**2.5.7 - 2022-06-29**

Features:

 - N/A

Changes:

 - Added support for more PACER download document errors messages
 - Update thomas name in test files
 - Drop future opinions
 - Update url pattern for Wyoming
 - Fix all failing Illinois Oral Argument Scrapers

**2.5.6 - 2022-05-17**

Features:

 - N/A

Changes:

 - Fix Mass Land Court scraper

**2.5.5 - 2022-05-17**

Features:

 - N/A

Changes:

 - Fix failing CAFC Oral Argument Scraper and Back Scraper.

**2.5.4 - 2022-05-13**

Features:

 - Fix Rhode Island scraper

Changes:

 - Update to Rhode island Published and Unpublished opinions.

**2.5.1 - 2022-04-25**

Features:

 - The `download_pdf` function used by PACER reports now returns a two-tuple
   containing the response object or None and a str. If there is an error,
   the response object will be None and the str will have the error message. If
   not, the response object will be populated and the str will be empty.

    To adapt to the new version you can change old code like this:

        r = report.download_pdf(...)

    To something like:

        r, _ = report.download_pdf(...)

    If you wish, you could instead capture errors with something like:

        r, msg = report.download_pdf(...)
        if msg:
            do_something()

Changes:

 - Python 3.7 is no longer supported.

 - See notes re features.


**2.4.11 - 2022-04-22**

Features:

- N/A

Changes:

- Add MIME parser to parse PACER emails notifications
- Small fix to fetch free PACER documents using magic links

**2.4.10 - 2022-02-08**

Features:

- N/A

Changes:

- Small fix for NM

**2.4.9 - 2022-02-08**

Features:

- N/A

Changes:

- Updates Ark, ArkCtApp, NM, NMCtApp to self throttle. Add login HTTP validation for PACER

**2.4.8 - 2022-02-02**

Features:

- N/A

Changes:

- Fixes for CGCCA, Conn, Conn App Ct.  Added pacer case_queries examples

**2.4.7 - 2022-01-21**

Features:

- N/A

Changes:

- Fix tax court. Fixes for Illinois Supreme and Illinois Appeals.

**2.4.6 - 2022-01-19**

Features:

- N/A

Changes:

- Update the site_yielder method for backscraping to reset the site object after each iterable.

**2.4.5 - 2022-01-18**

Features:

- N/A

Changes:

- Update OLC backscraper to function with CL more reliably.

**2.4.4 - 2022-01-14**

Features:

- Add DOJ Office of Legal Counsel Opinions (OLC)

Changes:

- Typo fixes

**2.4.3 - 2022-01-05**

Features:

- None

Changes:

- Add init file for admin agency backscrapers. This was missing and causing a failure for tools to find the file.

**2.4.0 - 2022-01-05**

Features:

- Updated citation parsing for websites.
- Drop Neutral, West and West_state citations.
- Add citation and parallel citation

Changes:

- This version is a major release. Updated Opinion Sites to drop support for specific citation formats.  Instead, we now let the user or more generally eyecite determine the specific citation format.
- Selenium support for Texas Court scrapers is removed.  This is part of removing selenium from all scrapers.
- Also includes a small fix for the Board of Immigration Appeals docket numbers.  

- 2.3.29, 2022-01-03 - Update GA Supremes, MDAG
- 2.3.28, 2021-12-30 - Add Board of Immigration Appeals (BIA), updates OA CA9, Fix NH
- 2.3.27, 2021-12-29 - Add cadc_pi, massappct_u, lactapp_1, cgcca
- 2.3.26, 2021-12-20 - Add Guam, Utah Ct App, Fix Ariz Ct App. Dist 2, Fix Ga Ct. App
- 2.3.25, 2021-12-08 - Update US Tax Court (new website)
- 2.3.24, 2021-12-06 - Fix new PACER session code
- 2.3.23, 2021-12-02 - Updates feedparser, adds Python 3.9 and 3.10 tests, and broadens our regex for parsing in re case names from PACER dockets.
- 2.3.22, 2021-11-30 - Further CAFC fixes
- 2.3.21, 2021-11-29 - Fixes CAFC, adds pre-commit
- 2.3.20, 2021-11-17 - Fixes CA10 scraper, major code refactor
- 2.3.19, 2021-11-16 - Fix PA, IL. Update PACER to use new auth API. Update geonames cache with latest population data. Throw exception in Free Opinions report when IP address on blocklist.
- 2.3.18, 2021-10-18 - Fix GA, CA9, CA10 Oral args
- 2.3.17, 2021-08-17 - Add anonymizing function for PACER dockets
- 2.3.16 - Yanked
- 2.3.15, 2021-07-19 - Fix PACER downloaders
- 2.3.14 - Yanked
- 2.3.13, 2021-06-18 - Fix typing
- 2.3.12, 2021-06-18 - Add PACER email parsers
- 2.3.11, 2021-05-02 - Fix PACER auth function
- 2.3.10, 2021-04-13 - Simplify harmonize function
- 2.3.9, 2021-04-12 - Simplify case name cleanup util
- 2.3.8, 2021-04-01 - More ME fixes
- 2.3.7, 2021-04-01 - Add backscrapers scrapers for ME
- 2.3.6, 2021-03-05 - Clean up deprecation warnings
- 2.3.5, 2021-03-05 - Fix pypi
- 2.3.4, 2021-02-09 - Fix IA scraper
- 2.3.3, 2020-11-24 - Fix remote selenium connection code
- 2.3.2, 2020-11-06 - Remove html_unescape helper method. Replace with calls
  directly to unescape. This fixes [#354](https://github.com/freelawproject/juriscraper/issues/354).
- 2.3.1, 2020-11-06 - Fix for connection to Selenium via Firefox
- 2.3.0, 2020-11-06 - Big selenium upgrade, removes support for phantomjs, and
  moves exclusively to using Mozilla's `geckodriver`. `geckodriver` can be
  accessed either locally or via a remote connection. See README for details on
  how to set the correct environment variables for your system.

    PhantomJS has not been supported for several years. Though it has served us
    well, the writing is on the wall that, like so many other once-useful
    technologies, it too had to be abandoned, only to be replaced by
    another tool. A tool that will be different in many ways, yet the same in
    its inevitable abandonment and mortality. Long live PhantomJS: Born a
    humble ghost; dying an immortal specter.
- 2.2.0, 2020-11-08 - Remove `_get_adapter_instance` method. It is unused, was
  a protected method, and causes many deprecation warnings in py3.
- 2.1.* - Removes support for deprecated phantomjs location; it had been deprecated for two years.
- 2.0.* - Adds support for Python 3.8 and supports Python 3, exclusively.  Begins testing to Github workflows and remove CircleCI.
- 1.28.* - Changes the API for the InternetArchive parser so that it aligns with the rest of the parsers. Its constructor now requires a court_id value.
- 1.27.* - Add merging of multi-event RSS entries
- 1.26.* - Adds support for the Los Angeles Superior Court Media Access Portal (LASC MAP)
- 1.25.* - Major refactor of tests to split them into network and local tests. Should make CI more consistent.
- 1.24.* - Adds support for bankruptcy claims register parsing and querying
- 1.23.* - Adds support for the advacned case report when it returns search results instead of a single item.
- 1.22.* - Adds support for de_seqno values parsed from PACER RSS, dockets, docket history reports, and attachment pages.
- 1.21.* - Adds support for the case report, which is the term we use to describe the page you see when you press the "Query" button in a district court PACER website. This is the page at the iQuery.pl URL.
- 1.20.* - Tweaks the API of the query method in the FreeOpinionReport object
  to consistently return None instead of sometimes returning []. Version bumped
  because of breaking API changes.
- 1.19.* - Adds support for NextGen PACER logins, but drops support for the PACER training website. The training website now uses a different login flow than the rest of PACER.
- 1.18.* - Adds support for appellate docket parsing!
- 1.17.* - Adds support for criminal data in PACER
- 1.16.* - Adds PACER RSS feed parsers.
- 1.15.* - Adds date termination parsing to parties on PACER dockets.
- 1.14.* - Adds new parser for PACER's docket history report
- 1.13.* - Fixes issues with Python build compatibility
- 1.12.* - Adds new parsers for PACER's show_case_doc URLs
- 1.11.* - Adds system for identifying invalid dockets in PACER.
- 1.10.* - Better parsing for PACER attachment pages.
- 1.9.* - Re-organization, simplification, and standardization of PACER classes.
- 1.8.* - Standardization of string fields in PACER objects so they return the empty string when they have no value instead of returning None sometimes and the empty string others. (This follows Django conventions.)
- 1.7.* - Adds support for hidden PACER APIs.
- 1.6.* - Adds automatic relogin code to PACER sessions, with reorganization of old login APIs.
- 1.5.* - Adds support for querying and parsing PACER dockets.
- 1.4.* - Python 3 compatibility (this was later dropped due to dependencies).
- 1.3.* - Adds support for scraping some parts of PACER.
- 1.2.* - Continued improvements.
- 1.1.* - Major code reorganization and first release on the Python Package Index (PyPi)
- 1.0 - Support opinions from for all possible federal bankruptcy
   appellate panels (9th and 10th Cir.)
- 0.9 - Supports all state courts of last resort (typically the
   "Supreme" court)
- 0.8 - Supports oral arguments for all possible Federal Circuit
   courts.
- 0.2 - Supports opinions from all federal courts of special
   jurisdiction (Veterans, Tax, etc.)
- 0.1 - Supports opinions from all 13 Federal Circuit courts and the
   U.S. Supreme Court





