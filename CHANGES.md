# Change Log

As of this writing, in late 2020, we have issued over 400 releases. The vast
majority of these releases fix a scraper so it works better on a particular 
court's website. When that's the case, we don't update the changelog, we simply
do the change, and you can find it in the git log. 

The changes below represent changes in ambition, goals, or interface. In other 
words, they're the ones you'll want to watch, and the others are mostly noise.

Releases are also tagged in git, if that's helpful.

## Current

- 2.1.* - Removes support for deprecated phantomjs location; it had been deprecated for two years.
 
## Past

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
-  1.6.* - Adds automatic relogin code to PACER sessions, with reorganization of old login APIs.
-  1.5.* - Adds support for querying and parsing PACER dockets.
-  1.4.* - Python 3 compatibility (this was later dropped due to dependencies).
-  1.3.* - Adds support for scraping some parts of PACER.
-  1.2.* - Continued improvements.
-  1.1.* - Major code reorganization and first release on the Python Package Index (PyPi)
-  1.0 - Support opinions from for all possible federal bankruptcy
   appellate panels (9th and 10th Cir.)
-  0.9 - Supports all state courts of last resort (typically the
   "Supreme" court)
-  0.8 - Supports oral arguments for all possible Federal Circuit
   courts.
-  0.2 - Supports opinions from all federal courts of special
   jurisdiction (Veterans, Tax, etc.)
-  0.1 - Supports opinions from all 13 Federal Circuit courts and the
   U.S. Supreme Court





