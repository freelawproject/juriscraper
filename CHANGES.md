# Change Log

As of this writing, in late 2020, we have issued over 400 releases. The vast
majority of these releases fix a scraper so it works better on a particular
court's website. When that's the case, we don't update the changelog, we simply
do the change, and you can find it in the git log.

The changes below represent changes in ambition, goals, or interface. In other
words, they're the ones you'll want to watch, and the others are mostly noise.

Releases are also tagged in git, if that's helpful.

## Coming up

The following changes are not yet released, but are code complete:

Features:
-
-

Changes:
- Update README.rst
- Add CONTRIBUTING.md
- Update `lactapp_1` scraper, site has changed #1357

Fixes:
- Fix `ca9` download URLs #1515

## Current

**2.6.81 - 2025-07-28**


Features:
- Add `masssuperct` new scraper for Massachusetts Superior Court #1498
- Fix document URL parsing in plain‑text email minute‑entry notifications #1362
- Add `bap9` backscraper #1008
- Add `ca9` backscraper

Changes:
- Update `lactapp_1` scraper, site has changed #1357
- improve `ind` add new fields for lower court details and judge names #1266


**2.6.80 - 2025-07-16**

Features:
- Add error handling for scrapers with expected results #1447
- Add a check to verify ACMS user data is loaded before querying attachment pages #1495
- Add `alaska_slip` and `alaska_u` new scrapers #1478

Changes:
- Expanded ACMS URL matching to support both HTTP and HTTPS protocols.

Fixes:
- Fix `visuper_p` adaptation to new html tags #1489
- Fix `ariz` update download URLs #1474
- handle empty cases in `ca7` scraper #1484
- fix `idaho_civil` preformat date to prevent parsing errors #1284


**2.6.79 - 2025-07-08**

Changes:
- Updates `PacerSession` class to make ACMS authentication optional, and disabled it by default.

**2.6.78 - 2025-06-18**

Features:
- Added support for parsing ACMS NDA notifications
- Enhances `PacerSession` class to support ACMS authentication.
- Adds case purchasing functionality to `ACMSDocketReport`.
- Added support for parsing docket numbers with case types with up to five letters
- Introduces logic to purchase ACMS docket entry attachment pages.

Changes:
- Refactor `ACMSDocketReport` to handle missing "date entered" values gracefully
  and expands the use of raw data fields for reliable date information. #1459
- make `nytrial` back scraping dynamic #1402
- Improve `alaska` scraper to handle case page to retrieve download_url #937

Fixes:
- Improve `ny` cleanup_content to remove email protection that was causing
  duplicates #1450
- Fix `minn` move `need_special_headers` to `__init__` #1470

**2.6.77 - 2025-06-17**

Changes:
- New scraper `lactapp_4` for Lousiana Court of Appeals, Fourth Circuit
- Update `uscgcoca` add backscraper #1431
- Update `tenn` add backscraper #1425

Fixes:
- Add "lower_court_ids" to fields returned by OpinionSite #1432
- Fix `va` collecting bad docket_number values #1441
- Fix `mich` change date expected key to `date_filed` #1445

**2.6.76 - 2025-06-12**

Changes:
-  Fix `tex` get opinions from the orders on causes page #1410
-  Fix `sd`
-  Fix `bap1` not scraping recent data #1422

**2.6.75 - 2025-06-09**

Changes:
- Update kan and kanctapp scrapers
- update `nc` scraper to OpinionSiteLinear and new website #1373

**2.6.74 - 2025-06-04**

- Add `test_hashes` optional argument to `sample_caller`. Helpful to detect
timestamped opinions and check if `Site.cleanup_content` is working #1392
- fix tenn scraper parsing error #1413
- fix package release process #1426

**2.6.71 - 2025-05-30**

Changes:
- Added support for Python 3.13

Fixes:
- Improve test speed by reducing the size of the uscfc_vaccine example array
- Fix `asbca` scraper to use special headers #1411
- Fix `uscgcoca` by using `self.needs_special_headers` #1419

**2.6.70 - 2025-05-23**

Features:
- Fix for CA4 - minor edge case bug

**2.6.69 - 2025-05-21**

Features:
- New scraper `ncbizct` for North Carolina Business Court

Fixes:
- Fixes for `prapp` with backscraper

**2.6.68 - 2025-05-12**

- Add auth token to ny trial courts
- Clean up ala scraped case names #1272


**2.6.67 - 2025-05-08**

- New scraper `lactapp_2` for Lousiana Court of Appeals, Second Circuit
- Fix `me` Update maine scraper and add backscraper
- Update `sd` backscraper and extract from text
- Fix `bia` scraper and add extract from text test cases
- Implement `cleanup_content` for `ny` sites #1393


**2.6.66 - 2025-04-29**

- Add backscraper for `dcd` #1336
- Update `sd` backscraper and extract from text
- Implement datestring format validation in test_ScraperExtractFromTextTest #838
- Implement `or` extract_from_text to collection regional citations #1226
- Fix `bia` scraper

**2.6.65 - 2025-04-11**

- `nh` was blocking; fixed by updating the user agent string #1370
- Update `vtsuperct_*` scrapers to inherit `extract_from_text` from `vt` #1150


**2.6.64 - 2025-04-10**

- Fix `me` Update maine scraper and add backscraper #1360
- Sites were blocking `cafc` scrapers. Fixed by passing a browser user agent #1366


**2.6.63 - 2025-03-25**

- Make `ga` backscraper take kwargs; fix a bug in 2018 #1349
- Implement extract from text for `ga` #1349
- Fix `ill` oral argument scraper #1356

**2.6.62 - 2025-03-19**

- Fix `uscgcoca` and `asbca` by replicating browser request headers #1352
- Fix `uscgcoca` citation regex #1351

**2.6.61 - 2025-03-06**

- Fix `ca8` opinion scraper by setting `request.verify = False` #1346

**2.6.60 - 2025-03-05**

- Fix `ca7` scrapers url from http to https

**2.6.59 - 2025-03-04**

- Change `colo` user agent to prevent site block #1341

**2.6.58 - 2025-02-26**

- Fixes:
  - Add backscraper for `mesuperct` #1328
  - Fix `mont` cleanup_content, would fail when content was bytes #1323

**2.6.57 - 2025-02-25**

- Fixes:
  - fix cafc oral argument scraper PR (#1325)[https://github.com/freelawproject/juriscraper/pull/1325]
  - ignore future date sanity check when date filed is approximate #1321
  - new exception InvalidDocumentError to be raised when an error page is detected #1329
  - update mont parsing; and raise InvalidDocumentError #1329

- Features
  - Add workflow to check for new entries in CHANGES.md file


**2.6.56 - 2025-02-19**

- Fixes:
  - n/a

- Features:
  - MT upgrade to opinion site linear
  - Add citation extraction and author for MT


**2.6.55 - 2025-02-10**

- Fixes:
  - `cafc` opinion scraper now requests using `verify=False` #1314
  - recap: support for parsing docket_numbers wrapped in a `tel:` href tag
     in appellate dockets. #915

- Features:
  - recap: improvement to the download_pdf method to handle cases where
  attachment pages are returned instead of the expected PDF documents. #1309

**2.6.54 - 2025-01-24**

- Fixes:
  - `ca6` oral argument scraper is no longer failing
  - update the pypi.yml github actions workflow to solve a bug with twine and
    packaging packages interaction. It now forces the update of packaging
  - due to that bug, we discarded the 2.6.53 version

**2.6.52 - 2025-01-20**

- Fixes:
  - `AppellateDocketReport.download_pdf` now returns a two-tuple containing the
    response object or None and a str. This aligns with the changes introduced
    in v 2.5.1.

**2.6.51 - 2025-01-14**

- Fixes:
  - `extract_from_text` now returns plain citation strings, instead of parsed dicts

**2.6.50 - 2025-01-10**

- Fixes:
  - add tests to ensure that `extract_from_text` does not fail
    when it does not find what it looks for; and that it always
    returns a dict
  - updated `pasuperct`, `bia`, `bap1`, `nm` and `sd` `extract_from_text` methods
  - refactored `pacer.email._parse_bankruptcy_short_description`
  - added tests for new courts `flsb`, `nceb`
  - added tests for multi docket NEFs

- Features
  - `pacer.email._parse_bankruptcy_short_description` now supports Multi Docket NEFs

**2.6.49 - 2025-01-08**

- Fixes:
  - `nh` scrapers no longer depend on harcoded year filter
  - Fixed `absca` tests that were failing due to change of year
  - `pasuperct` now collects citations
  - `pa`, `pasuperct` and `pacommcwt` now paginate results


**2.6.48 - 2024-12-31**

- Fixes:
  - updated `idaho_*` scrapers to OpinionSiteLinear
  - updated `cadc` scrapers to new site
  - `okla` now skips rows with no docket number
  - fixes for PACER appellate dockets parsing

**2.6.47 - 2024-12-12**

- Fixes:
  - standardize usage of download methods in scrapers (_download, _request_url_get, _request_url_post)
  - refactor scrapers to do not return "Per Curiam" as value for "author_str" or "judges"

- Features
  - added `extract_from_text` to `sc`


**2.6.46 - 2024-12-10**

- Fixes:
  - Support for parsing the new format of appellate attachment pages has been added

**2.6.45 - 2024-12-05**

- Features:
  - AbstractSite now supports saving responses and response headers.
  Use it with new optional argument for the sample caller `save-responses`.
  - Delete `--daemon` and `--report` options

**2.6.44 - 2024-11-27**

- Fixes:
  - Fixes `colo`

**2.6.43 - 2024-11-21**

- Fixes:
  - Fixes `ky` and `colo`

**2.6.42 - 2024-11-21**

- Fixes:
  - Fix `mass` and `massctapp` cleanup content method

**2.6.40 - 2024-11-20**

- Fixes:
  - Fix `mass` and `massctapp` scrapers, scrape new endpoint
  - Exclude "Commonwealth" string from short case names

**2.6.39 - 2024-11-18**

- Fixes:
  - Fix `Kansas, Ohio Ct App's 1-13` opinion scraper

**2.6.38 - 2024-11-08**

- Fixes:
  - Fix `uscfc` opinion scraper

- Features:
  - RECAP: add new sealed document phrase

**2.6.37 - 2024-10-22**

Fixes:
  - Fix for `okla` cleanup_content

**2.6.35 - 2024-10-22**

Fixes:
  - Fix for `okla` cleanup_content

**2.6.34 - 2024-10-22**

Fixes:
  - Fix for `okla` cleanup_content

**2.6.32 - 2024-10-21**

Features:
  - added `okla` cleanup_content

Fixes:
  - updated `coloctapp` cleanup_content


**2.6.31 - 2024-10-21**

Fixes:
  - `neb` now handles rows with no links
  - `coloctapp` update cleanup_content
  - fix `la` xpath selector that was skipping some cases

Features:
  - new scraper `lactapp_5` for Lousiana Court of Appeals, Fifth Circuit
  - now sending a `logger.error` call to Sentry when an scraped date is in the future

**2.6.30 - 2024-10-10**

Fixes:
  - fix `CADC` oral arguments

**2.6.29 - 2024-10-10**

Fixes:
  - fix `or` and `orctapp` scraper, scraping new endpoint
  - fix cache control headers in `AbstractSite`
  - fix `sc` expected content types

**2.6.28 - 2024-09-27**

Features:
  - new scraper `sc_u`

Fixes:
  - handle `illappct` (oral args) rows with no download link
  - `ca11` update to Oral Argument Site Linear
  - `cadc_u` change docket number getter
  - `sc` implement new site

**2.6.27 - 2024-09-16**

Fixes:
  - Fixes `coloctapp`



**2.6.25 - 2024-09-16**

Fixes:
  - Handle `nh` edge cases
  - Update `ohioctapp` to return "lower_courts" in order to disambiguate dockets across districts
  - Update `lib.string_utils.clean_string` to no longer delete semicolons

**2.6.25 - 2024-09-10**

Fixes:
  - `ny` Fixes NY
  - Updates nyappdiv to inherit ny
  - fixes tests

**2.6.24 - 2024-09-05**

Fixes:
  - `vt` now collects neutral citations
  - Fix `ca8` and updated to OpinionSiteLinear
  - Update README

**2.6.23 - 2024-09-03**

Fixes:
  - `wis` now collects neutral citations
  - `ky` now skips rows with no documents

Features:
  - new scraper `wisctapp`

**2.6.21 - 2024-08-30**

Fixes:
  - `fladistctapp` docket numbers are now unique across districts
  - updated `ca11` html selectors
  - updated `pa` to new API format
  - set needs_special_headers to True for `vt`

Features:
  - implemented dynamic backscraper and extract_from_text for `conn`

**2.6.20 - 2024-08-28**

Fixes:
  - Changed to nested format for attachments in the InternetArchive report

**2.6.19 - 2024-08-26**

Fixes:
  - `nh` renamed to `nh_p` and working by using special headers

Features:
  - New scraper: `nh_u`
  - Handle new bankruptcy attachment page format
  - Make docket history report parser more robust

**2.6.18 - 2024-08-22**

Features:
  - SCOTUS backscraper

Fixes:
  - Improvements to bankruptcy docket parsing
  - Added `njd` regression tests files

**2.6.17 - 2024-08-19**

Fixes:
  - RECAP:
    - email: now parses short description for `okeb`
    - Fixed IndexOutOfRange error in DocketReport::_set_metadata_values method
  - Scrapers:
    - fixed `cal` SSL errors
    - now collecting citations for `minn`

**2.6.16 - 2024-08-12**

Fixes:
  - Fixed Minnesota and implemented it's backscraper

**2.6.15 - 2024-08-07**

Features:
  - Added support for parsing PACER bankruptcy and district docket number components.

**2.6.14 - 2024-08-07**

Features:
  - Add special site headers attribute.
  - NY Api changes

Fixes:
  - ND (with dynamic backscraper)
  - PA
  - Ark

**2.6.13 - 2024-08-01**

Features:
  - Adds the de_seq_num to the download method.

Fixes:
  - Adds headers attribute to the massappct_u scraper.
  - Updates the URL for the oklaag scraper.
  - Updates the setup.py configuration to address deprecated setuptools options and improves test management using pytest.

**2.6.12 - 2024-07-22**

Features:
  - Update free opinion report to store the params used for each request

**2.6.11 - 2024-07-22**

Fixes:
  - Oklahoma opinion scrapers
  - CAFC oral argument scraper
  - ASBCA opinion scrapers
  - renamed logger from "Logger" to "juriscraper.lib.log_tools", which follows hierarchical naming convention

Features:
  - RECAP email: Support short_description parsing for tnmb and nhb
  - md backscraper
  - OpinionSiteLinear now supports returning "other_dates" key
  - New scraper for ky and kyctapp

**2.6.10 - 2024-07-11**

Features:
  - Fixes colo scraper expected_content_type


**2.6.9 - 2024-07-10**

Features:

- Fixes for
  - Idaho Civil
  - Idaho Criminal
  - Idaho Ct Appeals Civil, Criminal, Unpublished
  - N. Mariana Islands
  - Disables Mississippi
  - Disables Missouri
  - Fix Nebraska/App
  - Pacer Email TXNB
- Adds
  - ColoCtApp Dynamic backscraper

**2.6.8 - 2024-07-03**

Features:

- Fix for RI

**2.6.7 - 2024-07-03**

Features:

- Minor fixes for MA and RI

**2.6.6 - 2024-07-02**

Features:

- Implemented backscraper for nj, njtaxct_u, njtaxct_p, njsuperctappdiv_p, njsuperctappdiv_u

**2.6.5 - 2024-07-02**

Changes:

- Fixes for
  - Mass
  - RI
  - NJ
  - BIA
  - CalAG


**2.6.4 - 2024-06-11**

Changes:

- Add dynamic backscrapers for:
  - tex
  - nmcca
  - wyo
  - vtsuperct
  - alaska

- Fixed wrong xpath selectors and updated to OpinionSiteLinear
  - dcd
  - nd
  - ca1

- Solved bug with python3.12 tests in Github Actions


**2.6.3 - 2024-05-24**

Changes:

- PACER: Refactor login logic for PACER sessions.
- pacer.email: Added short description parsing for `pamb`


**2.6.2 - 2024-05-20**

Features:

- Added parser for ACMS attachment pages
- Added dynamic backscraper for `tax`

Changes:

- PACER: fix error string false positives
- pacer.email: support multidocket NEF short description parsing for `njb`

**2.6.1 - 2024-05-15**

Features:

- Added dynamic backscrapers for these scrapers and their inheriting classes
  - afcca
  - olc
  - bap10
  - fla
  - nyappterm
  - ill

- pacer.email: Added short description parsing for `deb` and `mdb`

Changes:
- Updated `cal` and `calctapp_*` to OpinionSiteLinear

**2.6.0 - 2024-04-03**

Features:

- Added scrapers for fisa and fiscr courts

Changes:

- Breaking change has been made to the FreeOpinionReport its 'data' property now
 returns a dictionary containing the FreeOpinionRow fields, instead of returning
 a Python object with their properties. This change aligns the method of
 returning 'data' in this report with that of other reports.
- Fixes to texag, tex

## Past

**2.5.95 - 2024-02-14**

Features:

- The GET method of the PacerSession class now supports custom timeouts for flexible request management.
- Adds a method to check if a district court docket entry is sealed..

Changes:

- Update the DownloadConfirmationPage class to reduce the read timeout of the GET request within the query method.

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
